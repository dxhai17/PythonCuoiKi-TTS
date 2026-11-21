"""Session tracker service managing active listening duration, words consumed, and bookmark persistence."""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime

from src.core.models.session import ReadingSession
from src.core.storage.db import get_db_engine
from src.core.storage.repositories import SqlBookmarkRepository, SqlSessionRepository

logger = logging.getLogger(__name__)


class SessionTracker:
    """Instruments and records reading session metrics and persistent bookmarks."""

    def __init__(
        self,
        book_id: int,
        total_sentences: int,
        bookmark_repo: SqlBookmarkRepository | None = None,
        session_repo: SqlSessionRepository | None = None,
    ):
        engine = get_db_engine()
        self.book_id = book_id
        self.total_sentences = total_sentences
        self.bookmark_repo = bookmark_repo or SqlBookmarkRepository(engine)
        self.session_repo = session_repo or SqlSessionRepository(engine)

        self.start_dt = datetime.now(UTC)
        self.start_perf = time.perf_counter()
        self._last_active_start = time.perf_counter()
        self.total_active_seconds = 0.0
        self.is_paused = False

        self.sentences_read = 0
        self.words_read = 0
        self.latest_sentence_index = 0

    def pause(self) -> None:
        """Mark session paused and accumulate active seconds."""
        if not self.is_paused:
            self.total_active_seconds += time.perf_counter() - self._last_active_start
            self.is_paused = True

    def resume(self) -> None:
        """Resume active timer."""
        if self.is_paused:
            self._last_active_start = time.perf_counter()
            self.is_paused = False

    def record_sentence_completed(
        self, sentence_index: int, word_count: int, chapter_idx: int = 1
    ) -> None:
        """Update words absorbed, sentence count, and flush bookmark to database."""
        self.sentences_read += 1
        self.words_read += word_count
        self.latest_sentence_index = sentence_index

        pct = (
            ((sentence_index + 1) / self.total_sentences) * 100.0
            if self.total_sentences > 0
            else 0.0
        )
        self.bookmark_repo.update_bookmark(
            book_id=self.book_id,
            chapter_idx=chapter_idx,
            sentence_idx=sentence_index,
            percentage=pct,
        )

    def finalize_session(self) -> ReadingSession | None:
        """Finalize session timer, persist ReadingSession row, and return entity."""
        if not self.is_paused:
            self.total_active_seconds += time.perf_counter() - self._last_active_start
            self.is_paused = True

        duration_sec = max(1, int(round(self.total_active_seconds)))
        end_dt = datetime.now(UTC)

        # Only save if user listened to sentences or had a non-trivial duration
        if self.sentences_read == 0 and duration_sec < 2:
            return None

        session = ReadingSession(
            book_id=self.book_id,
            start_time=self.start_dt,
            end_time=end_dt,
            duration_seconds=duration_sec,
            sentences_read=self.sentences_read,
            words_read=self.words_read,
        )
        sess_id = self.session_repo.record_session(session)
        session.id = sess_id
        logger.info(
            f"Saved reading session {sess_id} for book {self.book_id}: "
            f"{self.sentences_read} sentences, {self.words_read} words, {duration_sec}s"
        )
        return session
