"""Integration tests for reading session persistence and bookmark resumption."""

from __future__ import annotations

import time

from sqlalchemy import Engine

from src.models.book import Book, BookSentence
from src.player.session_tracker import SessionTracker
from src.storage.repositories import (
    SqlBookmarkRepository,
    SqlBookRepository,
    SqlSessionRepository,
)


def test_session_tracking_and_bookmark_update(test_engine: Engine):
    book_repo = SqlBookRepository(test_engine)
    bm_repo = SqlBookmarkRepository(test_engine)
    sess_repo = SqlSessionRepository(test_engine)

    # 1. Create a book with 5 sentences
    book = Book(
        title="Test Book For Sessions",
        author="Author A",
        source_path="/fake/path.txt",
        content_hash="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        total_chapters=1,
        total_sentences=5,
        total_words=50,
    )
    sentences = [
        BookSentence(
            book_id=0,
            chapter_index=1,
            sentence_index=i,
            text_content=f"Sentence number {i}.",
            word_count=10,
            content_hash=f"hash_{i}_" + "0" * 57,
        )
        for i in range(5)
    ]
    book_id = book_repo.save_book(book, sentences)

    # Initial bookmark should be sentence 0
    initial_bm = bm_repo.get_bookmark(book_id)
    assert initial_bm is not None
    assert initial_bm.current_sentence_index == 0
    assert initial_bm.completion_percentage == 0.0

    # 2. Simulate reading session
    tracker = SessionTracker(
        book_id=book_id,
        total_sentences=5,
        bookmark_repo=bm_repo,
        session_repo=sess_repo,
    )

    time.sleep(0.05)
    tracker.record_sentence_completed(sentence_index=0, word_count=10)
    tracker.record_sentence_completed(sentence_index=1, word_count=10)
    tracker.pause()
    time.sleep(0.05)
    tracker.resume()
    tracker.record_sentence_completed(sentence_index=2, word_count=10)

    # 3. Finalize session
    saved_session = tracker.finalize_session()
    assert saved_session is not None
    assert saved_session.id is not None
    assert saved_session.sentences_read == 3
    assert saved_session.words_read == 30
    assert saved_session.duration_seconds >= 0

    # 4. Verify bookmark updated to sentence index 2 (60% complete)
    updated_bm = bm_repo.get_bookmark(book_id)
    assert updated_bm is not None
    assert updated_bm.current_sentence_index == 2
    assert updated_bm.completion_percentage == 60.0

    # 5. Verify session retrieval
    recent = sess_repo.get_recent_sessions(book_id=book_id)
    assert len(recent) == 1
    assert recent[0].words_read == 30
