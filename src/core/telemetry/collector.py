"""Telemetry collector service capturing synthesis latency and background network metrics."""

from __future__ import annotations

import logging
from concurrent.futures import Future, ThreadPoolExecutor

from src.core.models.telemetry import NetworkMetric
from src.core.storage.db import get_db_engine
from src.core.storage.repositories import SqlTelemetryRepository
from src.core.telemetry.network_probe import NetworkProbe

logger = logging.getLogger(__name__)


class TelemetryCollector:
    """Collects per-sentence synthesis response times and LAN/Tailscale ping metrics."""

    def __init__(
        self,
        repository: SqlTelemetryRepository | None = None,
        probe: NetworkProbe | None = None,
        session_id: int | None = None,
    ):
        engine = get_db_engine()
        self.repository = repository or SqlTelemetryRepository(engine)
        self.probe = probe or NetworkProbe()
        self.session_id = session_id

        self.buffered_metrics: list[NetworkMetric] = []
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="telemetry_probe")
        self._pending_probes: dict[int, Future[tuple[float | None, float | None]]] = {}

    def start_background_probe(self, sentence_index: int) -> None:
        """Trigger an asynchronous LAN & Tailscale ping probe for a sentence."""
        future = self._executor.submit(self.probe.probe_all)
        self._pending_probes[sentence_index] = future

    def record_sentence_metric(
        self,
        sentence_index: int,
        response_time_seconds: float,
        status: str = "SUCCESS",
        lan_ping_ms: float | None = None,
        tailscale_ping_ms: float | None = None,
    ) -> NetworkMetric:
        """Record synthesis response time and attach network ping results."""
        # Check if an asynchronous probe was running for this sentence
        if sentence_index in self._pending_probes:
            try:
                future = self._pending_probes.pop(sentence_index)
                probe_lan, probe_tail = future.result(timeout=1.0)
                if lan_ping_ms is None:
                    lan_ping_ms = probe_lan
                if tailscale_ping_ms is None:
                    tailscale_ping_ms = probe_tail
            except Exception as err:
                logger.debug(f"Async network probe resolution error for sentence {sentence_index}: {err}")

        metric = NetworkMetric(
            session_id=self.session_id if self.session_id is not None else 0,
            sentence_index=sentence_index,
            response_time_seconds=response_time_seconds,
            lan_ping_ms=lan_ping_ms,
            tailscale_ping_ms=tailscale_ping_ms,
            status=status,
        )
        self.buffered_metrics.append(metric)
        return metric

    def flush(self, session_id: int | None = None) -> int:
        """Assign session_id and persist all buffered telemetry metrics to the database."""
        target_session_id = session_id if session_id is not None else self.session_id
        if target_session_id is None:
            logger.warning("Cannot flush telemetry metrics without a valid session_id.")
            return 0

        # Update session_id on all buffered items
        for m in self.buffered_metrics:
            m.session_id = target_session_id

        count = len(self.buffered_metrics)
        if count > 0:
            try:
                self.repository.log_metrics(self.buffered_metrics)
                logger.info(f"Persisted {count} telemetry records for session {target_session_id}")
                self.buffered_metrics.clear()
            except Exception as err:
                logger.error(f"Failed to persist telemetry metrics: {err}")
                raise

        return count

    def shutdown(self) -> None:
        """Shut down background thread executor."""
        self._executor.shutdown(wait=False)
