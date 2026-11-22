"""Domain models for Book, BookSentence, and Bookmark entities.

Canonical field constraints cited from data-model.md:
- Book.title: VARCHAR(255), NOT NULL
- Book.author: VARCHAR(255), DEFAULT 'Unknown'
- Book.source_path: VARCHAR(1024), NOT NULL
- Book.content_hash: CHAR(64), NOT NULL, UNIQUE
- Book.total_chapters: INT, NOT NULL, DEFAULT 1
- Book.total_sentences: INT, NOT NULL, DEFAULT 0, >= 0
- Book.total_words: INT, NOT NULL, DEFAULT 0, >= 0
- BookSentence.book_id: INT, NOT NULL, FK to books.id ON DELETE CASCADE
- BookSentence.chapter_index: INT, NOT NULL, DEFAULT 1
- BookSentence.sentence_index: INT, NOT NULL, UNIQUE with book_id
- BookSentence.text_content: TEXT, NOT NULL
- BookSentence.word_count: INT, NOT NULL, >= 0
- BookSentence.content_hash: CHAR(64), NOT NULL
- BookSentence.cached_audio_path: VARCHAR(1024), DEFAULT NULL
- Bookmark.book_id: INT, NOT NULL, UNIQUE, FK to books.id ON DELETE CASCADE
- Bookmark.current_chapter: INT, NOT NULL, DEFAULT 1
- Bookmark.current_sentence_index: INT, NOT NULL, DEFAULT 0
- Bookmark.completion_percentage: FLOAT, NOT NULL, DEFAULT 0.0 (0.0 to 100.0)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Book:
    """Represents an ingested book or document in the library catalog."""
    title: str
    source_path: str
    content_hash: str
    id: int | None = None
    author: str = "Unknown"
    total_chapters: int = 1
    total_sentences: int = 0
    total_words: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if len(self.title) > 255:
            self.title = self.title[:255]
        if len(self.author) > 255:
            self.author = self.author[:255]
        if len(self.source_path) > 1024:
            self.source_path = self.source_path[:1024]
        if len(self.content_hash) != 64:
            raise ValueError(f"Invalid content_hash length: {len(self.content_hash)}. Expected 64-char SHA-256.")
        if self.total_sentences < 0:
            raise ValueError("total_sentences must be >= 0")
        if self.total_words < 0:
            raise ValueError("total_words must be >= 0")


@dataclass
class BookSentence:
    """Represents an atomic speech unit within an ingested book."""
    book_id: int
    chapter_index: int
    sentence_index: int
    text_content: str
    word_count: int
    content_hash: str
    id: int | None = None
    cached_audio_path: str | None = None

    def __post_init__(self) -> None:
        if self.word_count < 0:
            raise ValueError("word_count must be >= 0")
        if len(self.content_hash) != 64:
            raise ValueError(f"Invalid content_hash length: {len(self.content_hash)}. Expected 64-char SHA-256.")


@dataclass
class Bookmark:
    """Represents a reader's persistent reading progress in a specific book."""
    book_id: int
    id: int | None = None
    current_chapter: int = 1
    current_sentence_index: int = 0
    completion_percentage: float = 0.0
    last_read_at: datetime | None = None

    def __post_init__(self) -> None:
        if not (0.0 <= self.completion_percentage <= 100.0):
            # Clamp percentage between 0.0 and 100.0
            self.completion_percentage = max(0.0, min(100.0, self.completion_percentage))
        if self.current_sentence_index < 0:
            raise ValueError("current_sentence_index must be >= 0")
