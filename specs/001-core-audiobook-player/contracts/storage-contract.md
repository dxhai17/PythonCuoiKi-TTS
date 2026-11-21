# Interface Contract: Storage & Repository Layer

**Feature**: `001-core-audiobook-player`
**Date**: 2026-11-20

## Overview

The storage contract defines the database access boundary. In compliance with the project rules and Constitution Principle I & IV:
1. **Parameterized Queries**: Every SQL query is parameterized (`:param` syntax via SQLAlchemy engine or `%s` with PyMySQL) to strictly prevent SQL injection.
2. **Connection Pooling**: Database interactions use a centralized connection pool (`DatabasePool`) managing live sessions, health checks (`pool_pre_ping`), and connection re-use.
3. **Decoupled Repositories**: Domain logic never invokes raw database handles directly; domain services communicate through repository interfaces.

---

## Python Repository Interfaces (`src/storage/repositories.py`)

```python
from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime
from src.models.book import Book, BookSentence, Bookmark
from src.models.session import ReadingSession
from src.models.telemetry import NetworkMetric

class BookRepository(ABC):
    @abstractmethod
    def save_book(self, book: Book, sentences: List[BookSentence]) -> int:
        """Insert book and sentences atomically within a transaction. Returns book_id."""
        pass

    @abstractmethod
    def get_by_id(self, book_id: int) -> Optional[Book]:
        """Fetch book by surrogate ID."""
        pass

    @abstractmethod
    def get_by_hash(self, content_hash: str) -> Optional[Book]:
        """Fetch book by SHA-256 content hash."""
        pass

    @abstractmethod
    def list_books(self, limit: int = 50, offset: int = 0) -> List[Book]:
        """List cataloged books ordered by last accessed."""
        pass

    @abstractmethod
    def get_sentences(self, book_id: int, start_idx: int = 0, limit: int = 100) -> List[BookSentence]:
        """Fetch range of sentences for a book."""
        pass

class BookmarkRepository(ABC):
    @abstractmethod
    def get_bookmark(self, book_id: int) -> Optional[Bookmark]:
        """Get current bookmark for a book."""
        pass

    @abstractmethod
    def update_bookmark(self, book_id: int, chapter_idx: int, sentence_idx: int, percentage: float) -> None:
        """Update or insert bookmark position."""
        pass

class SessionRepository(ABC):
    @abstractmethod
    def record_session(self, session: ReadingSession) -> int:
        """Persist a completed reading session. Returns session_id."""
        pass

    @abstractmethod
    def get_recent_sessions(self, book_id: Optional[int] = None, days: int = 7) -> List[ReadingSession]:
        """Query sessions within past N days."""
        pass

class TelemetryRepository(ABC):
    @abstractmethod
    def log_metrics(self, metrics: List[NetworkMetric]) -> None:
        """Batch insert sentence-level synthesis & latency telemetry."""
        pass

    @abstractmethod
    def get_aggregated_metrics(self, session_id: Optional[int] = None, days: int = 7) -> dict:
        """Return average response time, LAN latency, and Tailscale latency."""
        pass
```

---

## Database Pool Contract (`src/storage/db.py`)

- **Factory**: `get_db_engine()` initializes a singleton SQLAlchemy `Engine` with:
  ```python
  engine = create_engine(
      database_url,
      pool_size=5,
      max_overflow=10,
      pool_pre_ping=True,
      pool_recycle=3600,
  )
  ```
- **Transaction Manager**: `get_db_connection()` context manager handles connection acquisition, auto-commit on success, and rollback on unhandled exceptions.
