"""Headless Matplotlib visual dashboard chart generators.

Strictly enforces Constitution Principle IV (Headless execution and decoupled rendering).
"""

from __future__ import annotations

import io
import logging
import os
from datetime import UTC, datetime, timedelta

# Ensure writable matplotlib config directory in restricted environments
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

# Enforce headless Agg backend before importing pyplot
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.core.storage.repositories import SqlSessionRepository, SqlTelemetryRepository

logger = logging.getLogger(__name__)

# Dark theme palette matching frontend
BG_COLOR = "#1e293b"
CARD_BG = "#0f172a"
TEXT_COLOR = "#f8fafc"
TEXT_MUTED = "#94a3b8"
ACCENT_BLUE = "#38bdf8"
ACCENT_GREEN = "#10b981"
ACCENT_AMBER = "#f59e0b"
GRID_COLOR = "#334155"


def generate_listening_trends_chart(
    session_repo: SqlSessionRepository,
    days: int = 7,
) -> bytes:
    """Generate high-contrast PNG chart showing daily listening minutes and word counts."""
    sessions = session_repo.get_recent_sessions(days=days)

    # Aggregate by day
    today = datetime.now(UTC).date()
    day_labels = [(today - timedelta(days=i)).strftime("%a %d") for i in reversed(range(days))]
    day_dates = [(today - timedelta(days=i)) for i in reversed(range(days))]

    minutes_by_day = dict.fromkeys(day_dates, 0.0)
    words_by_day = dict.fromkeys(day_dates, 0)

    for s in sessions:
        s_date = s.start_time.date() if isinstance(s.start_time, datetime) else datetime.fromisoformat(str(s.start_time)).date()
        if s_date in minutes_by_day:
            minutes_by_day[s_date] += s.duration_seconds / 60.0
            words_by_day[s_date] += s.words_read

    mins_values = [minutes_by_day[d] for d in day_dates]
    words_values = [words_by_day[d] for d in day_dates]

    fig, ax1 = plt.subplots(figsize=(7, 3.5), facecolor=CARD_BG)
    ax1.set_facecolor(BG_COLOR)

    # Bars for listening minutes
    ax1.bar(day_labels, mins_values, color=ACCENT_BLUE, width=0.5, label="Listening (mins)")
    ax1.set_ylabel("Minutes Listened", color=ACCENT_BLUE, fontsize=10, fontweight="bold")
    ax1.tick_params(axis="y", labelcolor=ACCENT_BLUE)
    ax1.tick_params(axis="x", labelcolor=TEXT_MUTED, labelsize=9)
    ax1.grid(True, linestyle="--", alpha=0.3, color=GRID_COLOR, axis="y")

    # Secondary axis for words read
    ax2 = ax1.twinx()
    ax2.plot(day_labels, words_values, color=ACCENT_GREEN, marker="o", linewidth=2.2, label="Words Absorbed")
    ax2.set_ylabel("Words Read", color=ACCENT_GREEN, fontsize=10, fontweight="bold")
    ax2.tick_params(axis="y", labelcolor=ACCENT_GREEN)

    plt.title(f"Reading Trends (Past {days} Days)", color=TEXT_COLOR, fontsize=12, fontweight="bold", pad=12)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def generate_latency_metrics_chart(
    telemetry_repo: SqlTelemetryRepository,
    days: int = 7,
) -> bytes:
    """Generate high-contrast PNG chart showing TTS generation latency and LAN/Tailscale ping."""
    metrics = telemetry_repo.get_aggregated_metrics(days=days)

    labels = ["TTS Latency (s)", "LAN Ping (ms)", "Tailscale Ping (ms)"]
    values = [
        metrics.get("avg_sentence_response_time_sec", 0.0),
        metrics.get("avg_lan_ping_ms", 0.0),
        metrics.get("avg_tailscale_ping_ms", 0.0),
    ]
    colors = [ACCENT_AMBER, ACCENT_GREEN, ACCENT_BLUE]

    fig, ax = plt.subplots(figsize=(6.5, 3.2), facecolor=CARD_BG)
    ax.set_facecolor(BG_COLOR)

    y_pos = range(len(labels))
    bars = ax.barh(y_pos, values, color=colors, height=0.45, align="center")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, color=TEXT_COLOR, fontsize=10, fontweight="bold")
    ax.tick_params(axis="x", labelcolor=TEXT_MUTED)
    ax.grid(True, linestyle="--", alpha=0.3, color=GRID_COLOR, axis="x")

    # Annotate bar values
    for bar in bars:
        width = bar.get_width()
        unit = "s" if bar.get_y() < 0.5 else "ms"
        ax.text(
            width + (max(values) * 0.03 if max(values) > 0 else 0.1),
            bar.get_y() + bar.get_height() / 2,
            f"{width:.2f} {unit}",
            va="center",
            ha="left",
            color=TEXT_COLOR,
            fontsize=9,
            fontweight="bold",
        )

    plt.title("Operational Latency Overview", color=TEXT_COLOR, fontsize=12, fontweight="bold", pad=12)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()
