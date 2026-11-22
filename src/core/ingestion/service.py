"""Service orchestrating file ingestion, document parsing, content hashing, and catalog persistence."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from src.core.ingestion.parser import split_into_chapters_and_sentences
from src.core.ingestion.reader import DocumentReader
from src.core.models.book import Book, BookSentence
from src.core.storage.db import get_db_engine
from src.core.storage.repositories import SqlBookmarkRepository, SqlBookRepository

logger = logging.getLogger(__name__)


class IngestionService:
    """Coordinates reading, parsing, and persisting books in the library."""

    def __init__(
        self,
        book_repo: SqlBookRepository | None = None,
        bookmark_repo: SqlBookmarkRepository | None = None,
    ):
        engine = get_db_engine()
        self.book_repo = book_repo or SqlBookRepository(engine)
        self.bookmark_repo = bookmark_repo or SqlBookmarkRepository(engine)

    def ingest_file(
        self,
        file_path: str | Path,
        title: str | None = None,
        author: str = "Unknown",
    ) -> Book:
        """
        Load and parse a document file, cataloging it into the database.
        If an identical book is already ingested (by SHA-256 content hash),
        the existing record is returned without duplication.
        """
        content, filename, content_hash = DocumentReader.load_document(file_path)

        # Check for existing duplicate
        existing = self.book_repo.get_by_hash(content_hash)
        if existing:
            logger.info(f"Book with hash {content_hash} already cataloged (ID: {existing.id}). Returning existing record.")
            return existing

        resolved_title = title.strip() if title and title.strip() else Path(filename).stem.replace("_", " ").title()

        # Parse into chapters and sentences (applying 35-word clause threshold)
        parsed_chapters = split_into_chapters_and_sentences(content, max_clause_words=35)

        total_words = 0
        total_sentences = 0
        sentences: list[BookSentence] = []
        global_sentence_idx = 0

        for chap_idx, chap in enumerate(parsed_chapters, start=1):
            for s_text in chap["sentences"]:
                words = len(s_text.split())
                total_words += words
                s_hash = hashlib.sha256(s_text.encode("utf-8")).hexdigest()

                sentence_obj = BookSentence(
                    book_id=0,  # Updated after book insertion
                    chapter_index=chap_idx,
                    sentence_index=global_sentence_idx,
                    text_content=s_text,
                    word_count=words,
                    content_hash=s_hash,
                )
                sentences.append(sentence_obj)
                global_sentence_idx += 1

        total_sentences = len(sentences)

        book = Book(
            title=resolved_title,
            author=author,
            source_path=str(Path(file_path).resolve()),
            content_hash=content_hash,
            total_chapters=len(parsed_chapters),
            total_sentences=total_sentences,
            total_words=total_words,
        )

        book_id = self.book_repo.save_book(book, sentences)
        book.id = book_id
        logger.info(f"Successfully cataloged '{book.title}' with {total_sentences} sentences and {total_words} words (ID: {book_id}).")
        return book
