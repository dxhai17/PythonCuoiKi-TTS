"""Command-line interface entrypoint for the Smart Audiobook Reader (studylab)."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from typing import Any

from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()


def create_parser() -> argparse.ArgumentParser:
    """Construct command-line argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="studylab",
        description="Smart Audiobook Reader - Core Ingestion, Session Tracking, and Audio Player",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # 1. Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest and catalog a text or markdown book")
    ingest_parser.add_argument("file_path", help="Path to plain text (.txt) or Markdown (.md) file")
    ingest_parser.add_argument("--title", default=None, help="Book title (defaults to filename)")
    ingest_parser.add_argument("--author", default="Unknown", help="Author name")
    ingest_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # 2. List command
    list_parser = subparsers.add_parser("list", help="List all cataloged books in the library")
    list_parser.add_argument("--limit", type=int, default=50, help="Maximum number of books to display")
    list_parser.add_argument("--offset", type=int, default=0, help="Pagination offset")
    list_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # 3. Play command
    play_parser = subparsers.add_parser("play", help="Start or resume audiobook playback in interactive TUI")
    play_parser.add_argument("book_id", type=int, help="ID of the book to play")
    play_parser.add_argument("--sentence", type=int, default=None, help="Start from specific sentence index")
    play_parser.add_argument("--speed", type=float, default=1.0, help="Playback speed multiplier (0.75 - 2.0)")
    play_parser.add_argument("--voice", default=None, help="TTS voice model identifier")

    # 4. Metrics command
    metrics_parser = subparsers.add_parser("metrics", help="Display reading session history and network telemetry")
    metrics_parser.add_argument("--book-id", type=int, default=None, help="Filter telemetry by book ID")
    metrics_parser.add_argument("--days", type=int, default=7, help="Query past N days of metrics")
    metrics_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    return parser


def handle_ingest(args: argparse.Namespace) -> int:
    """Execute book ingestion."""
    from src.ingestion.service import IngestionService
    service = IngestionService()
    try:
        book = service.ingest_file(args.file_path, title=args.title, author=args.author)
        if args.json:
            print(json.dumps({
                "status": "success",
                "book_id": book.id,
                "title": book.title,
                "total_chapters": book.total_chapters,
                "total_sentences": book.total_sentences,
                "total_words": book.total_words,
            }, indent=2))
        else:
            console.print(f"[bold green]✓ Successfully ingested book:[/bold green] '{book.title}' (ID: {book.id})")
            console.print(f"  • Chapters: {book.total_chapters} | Sentences: {book.total_sentences} | Words: {book.total_words}")
        return 0
    except FileNotFoundError as err:
        sys.stderr.write(f"Error: {err}\n")
        return 1
    except ValueError as err:
        sys.stderr.write(f"Parse error: {err}\n")
        return 2
    except Exception as err:
        sys.stderr.write(f"Database/Ingestion error: {err}\n")
        return 3


def handle_list(args: argparse.Namespace) -> int:
    """List cataloged books."""
    from rich.table import Table

    from src.storage.db import get_db_engine
    from src.storage.repositories import SqlBookRepository

    repo = SqlBookRepository(get_db_engine())
    try:
        books = repo.list_books(limit=args.limit, offset=args.offset)
        if args.json:
            data = []
            for b in books:
                created_str = (
                    b.created_at.isoformat()
                    if isinstance(b.created_at, datetime)
                    else str(b.created_at)
                    if b.created_at is not None
                    else None
                )
                data.append({
                    "id": b.id,
                    "title": b.title,
                    "author": b.author,
                    "total_words": b.total_words,
                    "total_sentences": b.total_sentences,
                    "created_at": created_str,
                })
            print(json.dumps(data, indent=2))
        else:
            table = Table(title="Audiobook Library")
            table.add_column("ID", justify="right", style="cyan")
            table.add_column("Title", style="magenta")
            table.add_column("Author", style="green")
            table.add_column("Sentences", justify="right")
            table.add_column("Words", justify="right")
            for b in books:
                table.add_row(str(b.id), b.title, b.author, str(b.total_sentences), str(b.total_words))
            console.print(table)
        return 0
    except Exception as err:
        sys.stderr.write(f"Database error: {err}\n")
        return 3


def handle_play(args: argparse.Namespace) -> int:
    """Launch playback in interactive TUI."""
    try:
        from src.cli.player_view import run_player_tui
        ret: Any = run_player_tui(
            book_id=args.book_id,
            start_sentence_index=args.sentence,
            speed=args.speed,
            voice=args.voice,
        )
        return int(ret)
    except LookupError as err:
        sys.stderr.write(f"Book error: {err}\n")
        return 4
    except Exception as err:
        sys.stderr.write(f"Playback error: {err}\n")
        return 5


def handle_metrics(args: argparse.Namespace) -> int:
    """Display session history and network telemetry."""
    from rich.table import Table

    from src.storage.db import get_db_engine
    from src.storage.repositories import SqlTelemetryRepository

    repo = SqlTelemetryRepository(get_db_engine())
    try:
        metrics = repo.get_aggregated_metrics(book_id=args.book_id, days=args.days)
        if args.json:
            print(json.dumps(metrics, indent=2))
        else:
            table = Table(title="StudyLab Telemetry & Performance")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="bold green")
            table.add_row("Total Listening Minutes", f"{metrics.get('total_listening_minutes', 0.0):.1f}")
            table.add_row("Total Words Absorbed", str(metrics.get("total_words_absorbed", 0)))
            table.add_row("Total Sessions", str(metrics.get("total_sessions", 0)))
            table.add_row("Avg TTS Generation Latency", f"{metrics.get('avg_sentence_response_time_sec', 0.0):.2f}s")
            table.add_row("Avg LAN Latency", f"{metrics.get('avg_lan_ping_ms', 0.0):.1f} ms")
            table.add_row("Avg Tailscale Latency", f"{metrics.get('avg_tailscale_ping_ms', 0.0):.1f} ms")
            console.print(table)
        return 0
    except Exception as err:
        sys.stderr.write(f"Database error: {err}\n")
        return 3


def cli_entrypoint(argv: list[str] | None = None) -> int:
    """CLI entrypoint function."""
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.subcommand:
        parser.print_help()
        return 0

    if args.subcommand == "ingest":
        return handle_ingest(args)
    elif args.subcommand == "list":
        return handle_list(args)
    elif args.subcommand == "play":
        return handle_play(args)
    elif args.subcommand == "metrics":
        return handle_metrics(args)
    return 0


if __name__ == "__main__":
    sys.exit(cli_entrypoint())
