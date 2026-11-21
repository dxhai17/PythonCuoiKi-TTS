"""Unit tests for Player API endpoints and audio streaming."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from flask.testing import FlaskClient
from sqlalchemy import Engine

from src.api.app import create_app
from src.core.models.book import Book, BookSentence
from src.core.storage.repositories import SqlBookRepository


@pytest.fixture
def app_client(test_engine: Engine) -> Generator[FlaskClient, None, None]:
    """Create Flask test client with in-memory database engine."""
    with patch("src.api.routes.player.get_db_engine", return_value=test_engine), \
         patch("src.api.routes.books.get_db_engine", return_value=test_engine):
        app = create_app({"TESTING": True})
        with app.test_client() as client:
            yield client


def test_audio_stream_missing_book(app_client: FlaskClient) -> None:
    """Test requesting audio for non-existent book returns 404."""
    resp = app_client.get("/api/audio/999/0")
    assert resp.status_code == 404


def test_audio_stream_invalid_speed(app_client: FlaskClient) -> None:
    """Test requesting audio with out-of-range speed returns 400."""
    resp = app_client.get("/api/audio/1/0?speed=5.0")
    assert resp.status_code == 400


def test_audio_stream_success(app_client: FlaskClient, test_engine: Engine, tmp_path: Path) -> None:
    """Test successful audio synthesis streaming."""
    book_repo = SqlBookRepository(test_engine)
    book = Book(
        id=None,
        title="Test Book",
        author="Author",
        source_path="test.txt",
        content_hash="a" * 64,
        total_chapters=1,
        total_sentences=1,
        total_words=5,
    )
    sentences = [
        BookSentence(
            id=None,
            book_id=0,
            chapter_index=1,
            sentence_index=0,
            text_content="Hello world testing audio stream.",
            word_count=5,
            content_hash="b" * 64,
        )
    ]
    book_id = book_repo.save_book(book, sentences)

    # Create a dummy audio file
    dummy_audio = tmp_path / "dummy.mp3"
    dummy_audio.write_bytes(b"ID3dummy-mp3-bytes-content")

    with patch("src.core.player.cache_manager.AudioCacheManager.get_cached_audio") as mock_cache:
        mock_cache.return_value = dummy_audio

        resp = app_client.get(f"/api/audio/{book_id}/0")
        assert resp.status_code == 200
        assert resp.content_type == "audio/mpeg"
        assert resp.data == b"ID3dummy-mp3-bytes-content"
