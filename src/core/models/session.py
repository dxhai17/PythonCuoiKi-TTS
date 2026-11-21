"""Domain model for ReadingSession entity.

Canonical field constraints cited from data-model.md:
- ReadingSession.book_id: INT, NOT NULL, FK to books.id ON DELETE CASCADE
- ReadingSession.start_time: DATETIME, NOT NULL
- ReadingSession.end_time: DATETIME, NOT NULL, >= start_time
- ReadingSession.duration_seconds: INT, NOT NULL, >= 0
- ReadingSession.sentences_read: INT, NOT NULL, >= 0
- ReadingSession.words_read: INT, NOT NULL, >= 0
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ReadingSession:
    """Represents a continuous listening study session."""
    book_id: int
    start_time: datetime
    end_time: datetime
    duration_seconds: int = 0
    sentences_read: int = 0
    words_read: int = 0
    id: int | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.duration_seconds < 0:
            raise ValueError("duration_seconds must be >= 0")
        if self.sentences_read < 0:
            raise ValueError("sentences_read must be >= 0")
        if self.words_read < 0:
            raise ValueError("words_read must be >= 0")
        if self.end_time < self.start_time:
            raise ValueError("end_time must be >= start_time")
