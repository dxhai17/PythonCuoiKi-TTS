"""Integration tests for Analytics API and headless Matplotlib chart streams."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

import pytest
from flask.testing import FlaskClient
from sqlalchemy import Engine

from src.api.app import create_app


@pytest.fixture
def app_client(test_engine: Engine) -> Generator[FlaskClient, None, None]:
    """Create Flask test client with in-memory database engine."""
    with patch("src.api.routes.analytics.get_db_engine", return_value=test_engine):
        app = create_app({"TESTING": True})
        with app.test_client() as client:
            yield client


def test_get_analytics_summary(app_client: FlaskClient) -> None:
    """Test fetching analytics summary JSON."""
    resp = app_client.get("/api/analytics/summary")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "total_listening_minutes" in data
    assert "total_words_absorbed" in data
    assert "avg_sentence_response_time_sec" in data
    assert "avg_lan_ping_ms" in data
    assert "avg_tailscale_ping_ms" in data


def test_get_listening_trends_chart_png(app_client: FlaskClient) -> None:
    """Test streaming headless Matplotlib listening trends PNG chart."""
    resp = app_client.get("/api/analytics/charts/listening-trends.png")
    assert resp.status_code == 200
    assert resp.content_type == "image/png"
    assert resp.data.startswith(b"\x89PNG")  # Standard PNG magic bytes


def test_get_latency_metrics_chart_png(app_client: FlaskClient) -> None:
    """Test streaming headless Matplotlib latency overview PNG chart."""
    resp = app_client.get("/api/analytics/charts/latency-metrics.png")
    assert resp.status_code == 200
    assert resp.content_type == "image/png"
    assert resp.data.startswith(b"\x89PNG")  # Standard PNG magic bytes
