"""Integration tests for document ingestion and database cataloging."""

from __future__ import annotations

import tempfile
from pathlib import Path

from sqlalchemy import Engine

from src.ingestion.service import IngestionService
from src.storage.repositories import SqlBookmarkRepository, SqlBookRepository


def test_ingest_plain_text_file(test_engine: Engine):
    sample_content = (
        "Chapter 1: The Beginning\n\n"
        "It was the best of times, it was the worst of times. "
        "We had everything before us, we had nothing before us.\n\n"
        "Chapter 2: The Journey\n\n"
        "The travelers prepared their horses at dawn. "
        "The road ahead was fraught with uncertainty."
    )
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(sample_content)
        temp_path = f.name

    try:
        book_repo = SqlBookRepository(test_engine)
        bookmark_repo = SqlBookmarkRepository(test_engine)
        service = IngestionService(book_repo=book_repo, bookmark_repo=bookmark_repo)

        book = service.ingest_file(temp_path, title="A Tale of Two Chapters", author="Charles Dickens")
        assert book.id is not None
        assert book.title == "A Tale of Two Chapters"
        assert book.author == "Charles Dickens"
        assert book.total_chapters == 2
        assert book.total_sentences == 4
        assert book.total_words > 0

        # Verify database records
        db_book = book_repo.get_by_id(book.id)
        assert db_book is not None
        assert db_book.content_hash == book.content_hash

        sentences = book_repo.get_sentences(book.id, start_idx=0, limit=10)
        assert len(sentences) == 4
        assert sentences[0].sentence_index == 0
        assert sentences[3].sentence_index == 3

        # Verify initial bookmark created at sentence 0
        bookmark = bookmark_repo.get_bookmark(book.id)
        assert bookmark is not None
        assert bookmark.current_sentence_index == 0
        assert bookmark.completion_percentage == 0.0

        # Duplicate ingestion check: re-ingesting identical content returns existing book
        dup_book = service.ingest_file(temp_path, title="Duplicate Import")
        assert dup_book.id == book.id
    finally:
        Path(temp_path).unlink(missing_ok=True)
