"""Interactive Terminal UI (TUI) for audiobook playback using Rich and readchar."""

from __future__ import annotations

import logging
import queue
import threading
import time

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from src.player.audio_player import AudioPlayer
from src.player.buffer_manager import LookaheadBuffer
from src.player.session_tracker import SessionTracker
from src.storage.db import get_db_engine
from src.storage.repositories import SqlBookmarkRepository, SqlBookRepository
from src.tts.factory import TTSFactory

logger = logging.getLogger(__name__)
console = Console()


def _read_keys_worker(key_queue: queue.Queue[str], stop_event: threading.Event) -> None:
    """Background worker continuously capturing single keystrokes non-blockingly."""
    try:
        import readchar
        while not stop_event.is_set():
            try:
                # readkey() is blocking, but readchar works cleanly across terminals
                key = readchar.readkey()
                key_queue.put(key)
                if key in ("q", "Q"):
                    break
            except Exception:
                time.sleep(0.05)
    except Exception as exc:
        logger.debug(f"Keyboard listener stopped: {exc}")


def run_player_tui(
    book_id: int,
    start_sentence_index: int | None = None,
    speed: float = 1.0,
    voice: str | None = None,
    headless_dummy: bool = False,
) -> int:
    """
    Run interactive Terminal UI reading session.
    Returns 0 on clean exit, non-zero on error.
    """
    engine = get_db_engine()
    book_repo = SqlBookRepository(engine)
    bookmark_repo = SqlBookmarkRepository(engine)

    # 1. Fetch book metadata
    book = book_repo.get_by_id(book_id)
    if not book:
        raise LookupError(f"Book with ID {book_id} not found.")

    # 2. Fetch sentences
    all_sentences = book_repo.get_sentences(book_id, start_idx=0, limit=100000)
    if not all_sentences:
        raise LookupError(f"Book '{book.title}' contains no indexed sentences.")

    total_sentences = len(all_sentences)
    sentences_map = {s.sentence_index: s.text_content for s in all_sentences}

    # 3. Resolve starting sentence from bookmark or argument
    current_index = 0
    if start_sentence_index is not None:
        current_index = max(0, min(start_sentence_index, total_sentences - 1))
    else:
        saved_bm = bookmark_repo.get_bookmark(book_id)
        if saved_bm:
            current_index = min(saved_bm.current_sentence_index, total_sentences - 1)

    # 4. Initialize TTS, Cache, Buffer & SessionTracker
    tts_provider = TTSFactory.create_provider(voice=voice)
    buffer = LookaheadBuffer(
        book_id=book_id,
        sentences=[(s.sentence_index, s.text_content) for s in all_sentences],
        tts_provider=tts_provider,
        voice=voice,
        speed=speed,
    )
    player = AudioPlayer(headless_dummy=headless_dummy)
    tracker = SessionTracker(
        book_id=book_id,
        total_sentences=total_sentences,
        bookmark_repo=bookmark_repo,
    )
    from src.telemetry.collector import TelemetryCollector
    collector = TelemetryCollector()

    # 5. Session metrics state
    current_speed = speed
    status_label = "PLAYING"
    last_latency = 0.0
    last_was_cached = False

    # Key event queue and listener thread
    key_queue: queue.Queue[str] = queue.Queue()
    stop_event = threading.Event()
    key_thread = threading.Thread(
        target=_read_keys_worker, args=(key_queue, stop_event), daemon=True
    )
    key_thread.start()

    def build_view() -> Panel:
        """Construct Rich layout panel."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=4),
            Layout(name="sentence", size=8),
            Layout(name="upcoming", size=3),
            Layout(name="footer", size=5),
        )

        pct = (current_index / total_sentences) * 100.0 if total_sentences > 0 else 0.0

        # Header Table
        header_table = Table.grid(expand=True)
        header_table.add_column(justify="left")
        header_table.add_column(justify="right")
        header_table.add_row(
            f"[bold cyan]📖 {book.title}[/bold cyan] [dim]by {book.author}[/dim]",
            f"[bold yellow]{status_label}[/bold yellow] | Speed: [bold]{current_speed:.1f}x[/bold]",
        )
        header_table.add_row(
            f"Progress: Sentence {current_index + 1} of {total_sentences} ({pct:.1f}%)",
            f"Latency: {last_latency:.2f}s ({'Cache Hit' if last_was_cached else 'Synthesized'})",
        )
        layout["header"].update(Panel(header_table, border_style="dim"))

        # Current Sentence Panel
        cur_text = sentences_map.get(current_index, "[No text]")
        layout["sentence"].update(
            Panel(
                f"[bold white]{cur_text}[/bold white]",
                title=f"Speaking [Sentence #{current_index + 1}]",
                border_style="bright_blue",
                padding=(1, 2),
            )
        )

        # Upcoming Sentence
        next_text = sentences_map.get(current_index + 1, "[End of Book]")
        layout["upcoming"].update(
            Panel(f"[dim italic]{next_text}[/dim italic]", title="Next", border_style="dim")
        )

        # Footer & Stats
        mins = tracker.total_active_seconds / 60.0
        footer_table = Table.grid(expand=True)
        footer_table.add_column(justify="left")
        footer_table.add_column(justify="right")
        footer_table.add_row(
            "[bold white][Space][/bold white] Play/Pause  "
            "[bold white][← / →][/bold white] Skip Sentences  "
            "[bold white][↑ / ↓][/bold white] Speed ±0.1x  "
            "[bold white][q][/bold white] Quit",
            f"Session: [bold green]{mins:.1f} mins[/bold green] | Words: [bold green]{tracker.words_read}[/bold green]",
        )
        layout["footer"].update(Panel(footer_table, border_style="dim"))

        return Panel(layout, title="StudyLab Audiobook Reader", border_style="blue")

    try:
        with Live(build_view(), console=console, refresh_per_second=8, screen=True) as live:
            while current_index < total_sentences:
                # 1. Pre-fetch next sentence in background
                buffer.pre_fetch(current_index + 1)

                # 2. Get audio for current sentence
                status_label = "BUFFERING"
                live.update(build_view())
                collector.start_background_probe(current_index)

                try:
                    audio_path, synth_metrics = buffer.get_sentence_audio(current_index)
                    last_latency = synth_metrics.response_time_seconds
                    last_was_cached = synth_metrics.cached
                    collector.record_sentence_metric(
                        sentence_index=current_index,
                        response_time_seconds=last_latency,
                        status="SUCCESS",
                    )
                except Exception as err:
                    logger.error(f"Failed to obtain audio for sentence {current_index}: {err}")
                    status_label = f"ERROR: {err}"
                    collector.record_sentence_metric(
                        sentence_index=current_index,
                        response_time_seconds=0.0,
                        status=f"ERROR: {err}"[:32],
                    )
                    live.update(build_view())
                    time.sleep(2.0)
                    current_index += 1
                    continue

                # 3. Play audio
                status_label = "PLAYING"
                player.play_file(audio_path)
                sentence_words = len(sentences_map.get(current_index, "").split())

                # Wait loop for sentence to finish playing while polling key commands
                interrupted = False
                skip_delta = 0

                while player.is_playing() or player.is_paused():
                    live.update(build_view())

                    # Check for key presses
                    while not key_queue.empty():
                        key = key_queue.get_nowait()
                        if key in ("q", "Q"):
                            interrupted = True
                            break
                        elif key == " ":
                            is_paused = player.toggle_pause()
                            if is_paused:
                                tracker.pause()
                                status_label = "PAUSED"
                            else:
                                tracker.resume()
                                status_label = "PLAYING"
                        elif key in ("\x1b[C", "right", "d"):  # Right arrow / skip forward
                            skip_delta = 1
                            interrupted = True
                            break
                        elif key in ("\x1b[D", "left", "a"):  # Left arrow / skip backward
                            skip_delta = -1
                            interrupted = True
                            break
                        elif key in ("\x1b[A", "up", "w"):  # Speed up
                            current_speed = min(2.0, current_speed + 0.1)
                            buffer.update_speed_or_voice(speed=current_speed)
                        elif key in ("\x1b[B", "down", "s"):  # Speed down
                            current_speed = max(0.7, current_speed - 0.1)
                            buffer.update_speed_or_voice(speed=current_speed)

                    if interrupted:
                        player.stop()
                        break

                    time.sleep(0.05)

                if interrupted:
                    if skip_delta != 0:
                        current_index = max(0, min(current_index + skip_delta, total_sentences - 1))
                        continue
                    else:
                        # User pressed 'q'
                        break

                # Sentence finished naturally
                tracker.record_sentence_completed(current_index, sentence_words)
                current_index += 1

    finally:
        stop_event.set()
        player.stop()
        buffer.shutdown()

        # Finalize bookmark and save reading session via SessionTracker
        final_pct = (current_index / total_sentences) * 100.0 if total_sentences > 0 else 0.0
        bookmark_repo.update_bookmark(
            book_id=book_id,
            chapter_idx=1,
            sentence_idx=current_index,
            percentage=final_pct,
        )
        session = tracker.finalize_session()
        if session and session.id:
            try:
                collector.flush(session_id=session.id)
            except Exception as exc:
                logger.warning(f"Failed to persist telemetry metrics: {exc}")
        collector.shutdown()

        console.print(f"\n[bold green]✓ Playback saved.[/bold green] Bookmark restored at sentence {current_index + 1}/{total_sentences} ({final_pct:.1f}%).")

    return 0
