"""Domain model for NetworkMetric telemetry entity.

Canonical field constraints cited from data-model.md:
- NetworkMetric.session_id: INT, NOT NULL, FK to reading_sessions.id ON DELETE CASCADE
- NetworkMetric.sentence_index: INT, NOT NULL
- NetworkMetric.response_time_seconds: FLOAT, NOT NULL, >= 0.0
- NetworkMetric.lan_ping_ms: FLOAT, DEFAULT NULL
- NetworkMetric.tailscale_ping_ms: FLOAT, DEFAULT NULL
- NetworkMetric.status: VARCHAR(32), NOT NULL, DEFAULT 'SUCCESS'
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class NetworkMetric:
    """Represents operational synthesis and ping latency telemetry per sentence."""
    session_id: int
    sentence_index: int
    response_time_seconds: float
    id: int | None = None
    lan_ping_ms: float | None = None
    tailscale_ping_ms: float | None = None
    status: str = "SUCCESS"
    recorded_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.response_time_seconds < 0.0:
            raise ValueError("response_time_seconds must be >= 0.0")
        if self.sentence_index < 0:
            raise ValueError("sentence_index must be >= 0")
