"""Unit tests for Bookmark and Session API endpoints."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

import pytest
from flask.testing import FlaskClient
from sqlalchemy import Engine

from src.api.app import create_app
from src.core.models.book import Book
from src.core.storage.repositories import SqlBookRepository


@pytest.fixture
def app_client(test_engine: Engine) -> Generator[FlaskClient, None, None]:
    """Create Flask test client with in-memory database engine."""
    with patch("src.api.routes.player.get_db_engine", return_value=test_engine):
        app = create_app({"TESTING": True})
        with app.test_client() as client:
            yield client


def test_get_bookmark_defaults_for_new_book(app_client: FlaskClient) -> None:
    """Test fetching bookmark for book without history returns default 0 index."""
    resp = app_client.get("/api/bookmarks/999")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["book_id"] == 999
    assert data["current_sentence_index"] == 0
    assert data["completion_percentage"] == 0.0


def test_update_and_get_bookmark(app_client: FlaskClient, test_engine: Engine) -> None:
    """Test updating bookmark position and verifying retrieval."""
    book_repo = SqlBookRepository(test_engine)
    book = Book(
        id=None,
        title="Bookmark Test Book",
        author="Author",
        source_path="test.txt",
        content_hash="x" * 64,
        total_chapters=1,
        total_sentences=10,
        total_words=100,
    )
    book_id = book_repo.save_book(book, [])

    # Update bookmark to sentence 4
    update_payload = {
        "book_id": book_id,
        "current_chapter": 1,
        "current_sentence_index": 4,
        "completion_percentage": 40.0,
    }
    post_resp = app_client.post("/api/bookmarks", json=update_payload)
    assert post_resp.status_code == 200
    assert post_resp.get_json()["status"] == "updated"

    # Get updated bookmark
    get_resp = app_client.get(f"/api/bookmarks/{book_id}")
    assert get_resp.status_code == 200
    bm = get_resp.get_json()
    assert bm["book_id"] == book_id
    assert bm["current_sentence_index"] == 4
    assert bm["completion_percentage"] == 40.0


def test_record_reading_session(app_client: FlaskClient, test_engine: Engine) -> None:
    """Test posting a reading session row."""
    payload = {
        "book_id": 1,
        "duration_seconds": 120,
        "sentences_read": 8,
        "words_read": 110,
        "start_time": "2026-11-21T12:00:00Z",
        "end_time": "2026-11-21T12:02:00Z",
    }
    resp = app_client.post("/api/sessions", json=payload)
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["book_id"] == 1
    assert body["duration_seconds"] == 120
    assert body["sentences_read"] == 8
    assert body["words_read"] == 110
