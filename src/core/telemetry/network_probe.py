"""Network probing service measuring round-trip latency to LAN and Tailscale hosts."""

from __future__ import annotations

import logging
import socket
import time
from concurrent.futures import ThreadPoolExecutor

from src.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class NetworkProbe:
    """Probes network latency to LAN and Tailscale endpoints using non-blocking TCP handshakes."""

    def __init__(
        self,
        lan_host: str | None = None,
        tailscale_host: str | None = None,
        settings: Settings | None = None,
        default_timeout: float = 0.5,
    ):
        cfg = settings or get_settings()
        self.lan_host = lan_host or cfg.lan_ping_host
        self.tailscale_host = tailscale_host or cfg.tailscale_ping_host
        self.default_timeout = default_timeout

    def measure_rtt(self, host: str, port: int = 80, timeout: float | None = None) -> float | None:
        """Measure TCP connect round-trip latency in milliseconds.

        Returns RTT in ms, or None if host is unreachable or connection timed out.
        Note: ConnectionRefusedError (TCP RST received) indicates successful RTT packet travel.
        """
        to = timeout if timeout is not None else self.default_timeout
        start = time.perf_counter()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(to)
            sock.connect((host, port))
            sock.close()
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            return round(elapsed_ms, 2)
        except ConnectionRefusedError:
            # Remote host actively refused port with RST -> successful round-trip network packet delivery
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            return round(elapsed_ms, 2)
        except TimeoutError:
            logger.debug(f"Ping timeout ({to}s) to host: {host}")
            return None
        except OSError as err:
            logger.debug(f"Network error probing {host}: {err}")
            return None

    def probe_lan(self, port: int = 80, timeout: float | None = None) -> float | None:
        """Measure round-trip latency to LAN host."""
        return self.measure_rtt(self.lan_host, port=port, timeout=timeout)

    def probe_tailscale(self, port: int = 80, timeout: float | None = None) -> float | None:
        """Measure round-trip latency to Tailscale host."""
        return self.measure_rtt(self.tailscale_host, port=port, timeout=timeout)

    def probe_all(self, timeout: float | None = None) -> tuple[float | None, float | None]:
        """Concurrently probe both LAN and Tailscale endpoints within timeout.

        Returns (lan_ping_ms, tailscale_ping_ms).
        """
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix="net_probe") as executor:
            future_lan = executor.submit(self.probe_lan, 80, timeout)
            future_tail = executor.submit(self.probe_tailscale, 80, timeout)
            lan_ms = future_lan.result()
            tail_ms = future_tail.result()
            return (lan_ms, tail_ms)
