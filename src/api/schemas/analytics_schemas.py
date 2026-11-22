"""Pydantic validation schemas for Telemetry and Analytics."""

from __future__ import annotations

from pydantic import BaseModel


class AnalyticsSummaryResponse(BaseModel):
    total_listening_minutes: float
    total_words_absorbed: int
    total_sessions: int
    avg_sentence_response_time_sec: float
    avg_lan_ping_ms: float
    avg_tailscale_ping_ms: float
    recent_sessions_count: int
