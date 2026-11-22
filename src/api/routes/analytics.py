"""Analytics API blueprint: aggregated KPI metrics and headless Matplotlib PNG charts."""

from __future__ import annotations

import io
import logging
from typing import Any

from flask import Blueprint, Response, jsonify, request, send_file

from src.api.schemas.analytics_schemas import AnalyticsSummaryResponse
from src.core.analytics.dashboard import (
    generate_latency_metrics_chart,
    generate_listening_trends_chart,
)
from src.core.storage.db import get_db_engine
from src.core.storage.repositories import SqlSessionRepository, SqlTelemetryRepository

logger = logging.getLogger(__name__)

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/summary", methods=["GET"])
def get_analytics_summary() -> Any:
    """Retrieve aggregated reading session and network latency metrics."""
    days = int(request.args.get("days", 7))
    book_id = request.args.get("book_id", type=int)

    engine = get_db_engine()
    telemetry_repo = SqlTelemetryRepository(engine)
    session_repo = SqlSessionRepository(engine)

    metrics = telemetry_repo.get_aggregated_metrics(book_id=book_id, days=days)
    recent_sessions = session_repo.get_recent_sessions(book_id=book_id, days=days)

    response = AnalyticsSummaryResponse(
        total_listening_minutes=metrics.get("total_listening_minutes", 0.0),
        total_words_absorbed=metrics.get("total_words_absorbed", 0),
        total_sessions=metrics.get("total_sessions", 0),
        avg_sentence_response_time_sec=metrics.get("avg_sentence_response_time_sec", 0.0),
        avg_lan_ping_ms=metrics.get("avg_lan_ping_ms", 0.0),
        avg_tailscale_ping_ms=metrics.get("avg_tailscale_ping_ms", 0.0),
        recent_sessions_count=len(recent_sessions),
    )
    return jsonify(response.model_dump())


@analytics_bp.route("/charts/listening-trends.png", methods=["GET"])
def get_listening_trends_chart() -> Response:
    """Stream headless Matplotlib PNG chart of daily listening habits."""
    days = int(request.args.get("days", 7))
    engine = get_db_engine()
    session_repo = SqlSessionRepository(engine)

    chart_bytes = generate_listening_trends_chart(session_repo, days=days)
    response = send_file(io.BytesIO(chart_bytes), mimetype="image/png")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@analytics_bp.route("/charts/latency-metrics.png", methods=["GET"])
def get_latency_metrics_chart() -> Response:
    """Stream headless Matplotlib PNG chart of network ping and TTS latency."""
    days = int(request.args.get("days", 7))
    engine = get_db_engine()
    telemetry_repo = SqlTelemetryRepository(engine)

    chart_bytes = generate_latency_metrics_chart(telemetry_repo, days=days)
    response = send_file(io.BytesIO(chart_bytes), mimetype="image/png")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response
