"""Unit tests for NetworkProbe, TelemetryCollector, and TelemetryRepository."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from sqlalchemy import Engine

from src.models.session import ReadingSession
from src.storage.repositories import SqlSessionRepository, SqlTelemetryRepository
from src.telemetry.collector import TelemetryCollector
from src.telemetry.network_probe import NetworkProbe


def test_network_probe_measure_rtt_success() -> None:
    """Test measure_rtt returns round-trip time on successful socket connection."""
    probe = NetworkProbe(lan_host="192.168.1.1", tailscale_host="100.100.100.100")

    with patch("socket.socket") as mock_socket_cls:
        mock_sock = MagicMock()
        mock_socket_cls.return_value = mock_sock

        rtt = probe.measure_rtt("192.168.1.1", port=80, timeout=0.1)
        assert rtt is not None
        assert rtt >= 0.0
        mock_sock.connect.assert_called_once_with(("192.168.1.1", 80))
        mock_sock.close.assert_called_once()


def test_network_probe_measure_rtt_connection_refused() -> None:
    """Test that connection refused (TCP RST) still counts as valid packet round-trip."""
    probe = NetworkProbe()

    with patch("socket.socket") as mock_socket_cls:
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = ConnectionRefusedError("Port closed")
        mock_socket_cls.return_value = mock_sock

        rtt = probe.measure_rtt("10.0.0.1", port=80, timeout=0.1)
        assert rtt is not None
        assert rtt >= 0.0


def test_network_probe_measure_rtt_timeout() -> None:
    """Test that socket timeout returns None."""
    probe = NetworkProbe()

    with patch("socket.socket") as mock_socket_cls:
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = TimeoutError("Timed out")
        mock_socket_cls.return_value = mock_sock

        rtt = probe.measure_rtt("10.0.0.1", port=80, timeout=0.1)
        assert rtt is None


def test_network_probe_probe_all() -> None:
    """Test concurrent probe of LAN and Tailscale hosts."""
    probe = NetworkProbe(lan_host="192.168.1.1", tailscale_host="100.100.100.100")

    with patch.object(probe, "measure_rtt") as mock_rtt:
        mock_rtt.side_effect = lambda host, port, timeout: 2.5 if host == "192.168.1.1" else 25.0

        lan_ms, tail_ms = probe.probe_all(timeout=0.1)
        assert lan_ms == 2.5
        assert tail_ms == 25.0


def test_telemetry_collector_buffering_and_flush(test_engine: Engine) -> None:
    """Test TelemetryCollector buffering metrics and flushing to repository."""
    sess_repo = SqlSessionRepository(test_engine)
    telem_repo = SqlTelemetryRepository(test_engine)

    # 1. Create a dummy session
    now = datetime.now(UTC)
    session = ReadingSession(
        book_id=1,
        start_time=now,
        end_time=now,
        duration_seconds=120,
        sentences_read=5,
        words_read=80,
    )
    session_id = sess_repo.record_session(session)

    # 2. Mock probe
    mock_probe = MagicMock(spec=NetworkProbe)
    mock_probe.probe_all.return_value = (3.2, 28.4)

    collector = TelemetryCollector(
        repository=telem_repo,
        probe=mock_probe,
    )

    collector.start_background_probe(sentence_index=0)
    metric = collector.record_sentence_metric(
        sentence_index=0,
        response_time_seconds=0.35,
        status="SUCCESS",
    )

    assert metric.sentence_index == 0
    assert metric.response_time_seconds == 0.35
    assert metric.lan_ping_ms == 3.2
    assert metric.tailscale_ping_ms == 28.4
    assert len(collector.buffered_metrics) == 1

    # 3. Flush to DB
    flushed_count = collector.flush(session_id=session_id)
    assert flushed_count == 1
    assert len(collector.buffered_metrics) == 0

    # 4. Verify aggregated query
    agg = telem_repo.get_aggregated_metrics(book_id=1)
    assert agg["total_listening_minutes"] == 2.0
    assert agg["total_words_absorbed"] == 80
    assert agg["total_sessions"] == 1
    assert agg["avg_sentence_response_time_sec"] == 0.35
    assert agg["avg_lan_ping_ms"] == 3.2
    assert agg["avg_tailscale_ping_ms"] == 28.4

    collector.shutdown()
