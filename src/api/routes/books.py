"""Books API blueprint: catalog listing, sentence retrieval, and file ingestion."""

from __future__ import annotations

import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Blueprint, jsonify, request

from src.api.schemas.book_schemas import (
    BookDetailResponse,
    BookSentenceResponse,
    BookSentencesListResponse,
    BookSummaryResponse,
    BookUploadSuccessResponse,
)
from src.core.ingestion.service import IngestionService
from src.core.storage.db import get_db_engine
from src.core.storage.repositories import SqlBookRepository

logger = logging.getLogger(__name__)

books_bp = Blueprint("books", __name__)


def _format_dt(val: Any) -> str | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.isoformat()
    return str(val)


@books_bp.route("", methods=["GET"])
def list_books() -> Any:
    """List all cataloged books with pagination."""
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))

    engine = get_db_engine()
    book_repo = SqlBookRepository(engine)
    books = book_repo.list_books(limit=limit, offset=offset)

    result = [
        BookSummaryResponse(
            id=b.id or 0,
            title=b.title,
            author=b.author,
            total_chapters=b.total_chapters,
            total_sentences=b.total_sentences,
            total_words=b.total_words,
            created_at=_format_dt(b.created_at),
        ).model_dump()
        for b in books
    ]
    return jsonify(result)


@books_bp.route("/<int:book_id>", methods=["GET"])
def get_book_detail(book_id: int) -> Any:
    """Retrieve detailed metadata for a book."""
    engine = get_db_engine()
    book_repo = SqlBookRepository(engine)
    book = book_repo.get_book(book_id)
    if not book:
        return jsonify({"error": f"Book {book_id} not found"}), 404

    return jsonify(
        BookDetailResponse(
            id=book.id or 0,
            title=book.title,
            author=book.author,
            source_path=book.source_path,
            content_hash=book.content_hash,
            total_chapters=book.total_chapters,
            total_sentences=book.total_sentences,
            total_words=book.total_words,
            created_at=_format_dt(book.created_at),
        ).model_dump()
    )


@books_bp.route("/<int:book_id>/sentences", methods=["GET"])
def get_book_sentences(book_id: int) -> Any:
    """Fetch all indexed sentences for a book for text synchronization."""
    engine = get_db_engine()
    book_repo = SqlBookRepository(engine)

    book = book_repo.get_book(book_id)
    if not book:
        return jsonify({"error": f"Book {book_id} not found"}), 404

    sentences = book_repo.get_book_sentences(book_id)
    return jsonify(
        BookSentencesListResponse(
            book_id=book_id,
            total_sentences=len(sentences),
            sentences=[
                BookSentenceResponse(
                    sentence_index=s.sentence_index,
                    chapter_index=s.chapter_index,
                    text_content=s.text_content,
                    word_count=s.word_count,
                )
                for s in sentences
            ],
        ).model_dump()
    )


@books_bp.route("/ingest", methods=["POST"])
def ingest_book_file() -> Any:
    """Upload and catalog a text or markdown book file."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    uploaded_file = request.files["file"]
    if not uploaded_file.filename:
        return jsonify({"error": "Empty filename"}), 400

    filename = uploaded_file.filename.lower()
    if not (filename.endswith(".txt") or filename.endswith(".md")):
        return jsonify({"error": "Unsupported file format. Only .txt and .md files are supported."}), 400

    title = request.form.get("title") or Path(uploaded_file.filename).stem.replace("_", " ").title()
    author = request.form.get("author") or "Unknown"

    # Save to temporary file for parsing
    suffix = ".txt" if filename.endswith(".txt") else ".md"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
        uploaded_file.save(temp_file.name)
        temp_path = temp_file.name

    try:
        engine = get_db_engine()
        ingestion_service = IngestionService(
            book_repo=SqlBookRepository(engine),
        )
        book = ingestion_service.ingest_file(
            file_path=temp_path,
            title=title,
            author=author,
        )
        return (
            jsonify(
                BookUploadSuccessResponse(
                    book_id=book.id or 0,
                    title=book.title,
                    total_chapters=book.total_chapters,
                    total_sentences=book.total_sentences,
                    total_words=book.total_words,
                ).model_dump()
            ),
            201,
        )
    except Exception as exc:
        logger.error(f"Book ingestion failed: {exc}")
        return jsonify({"error": f"Failed to ingest book: {exc}"}), 500
    finally:
        try:
            Path(temp_path).unlink(missing_ok=True)
        except Exception:
            pass
