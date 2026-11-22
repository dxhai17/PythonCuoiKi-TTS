"""Integration tests for Book Ingestion and Cataloging API."""

from __future__ import annotations

import io
from collections.abc import Generator
from unittest.mock import patch

import pytest
from flask.testing import FlaskClient
from sqlalchemy import Engine

from src.api.app import create_app


@pytest.fixture
def app_client(test_engine: Engine) -> Generator[FlaskClient, None, None]:
    """Create Flask test client with in-memory database engine."""
    with patch("src.api.routes.books.get_db_engine", return_value=test_engine):
        app = create_app({"TESTING": True})
        with app.test_client() as client:
            yield client


def test_list_books_initially_empty(app_client: FlaskClient) -> None:
    """Test listing books returns an array."""
    resp = app_client.get("/api/books")
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_ingest_book_missing_file(app_client: FlaskClient) -> None:
    """Test upload without file returns 400 Bad Request."""
    resp = app_client.post("/api/books/ingest", data={})
    assert resp.status_code == 400
    assert "No file uploaded" in resp.get_json()["error"]


def test_ingest_book_unsupported_format(app_client: FlaskClient) -> None:
    """Test upload with unsupported extension returns 400."""
    data = {
        "file": (io.BytesIO(b"fake pdf content"), "document.pdf"),
    }
    resp = app_client.post("/api/books/ingest", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400
    assert "Unsupported file format" in resp.get_json()["error"]


def test_ingest_book_success(app_client: FlaskClient) -> None:
    """Test uploading a valid text file parses and catalogs book."""
    text_content = (
        b"# Chapter 1\n\n"
        b"The flight succeeded against all odds. It made history.\n\n"
        b"# Chapter 2\n\n"
        b"Spectators cheered from the dunes."
    )
    data = {
        "file": (io.BytesIO(text_content), "flight_log.txt"),
        "title": "Flight Logbook",
        "author": "Wilbur Wright",
    }
    resp = app_client.post("/api/books/ingest", data=data, content_type="multipart/form-data")
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["status"] == "success"
    assert body["title"] == "Flight Logbook"
    assert body["total_chapters"] == 2
    assert body["total_sentences"] == 3

    # Verify listing now returns this book
    list_resp = app_client.get("/api/books")
    assert list_resp.status_code == 200
    books = list_resp.get_json()
    assert len(books) == 1
    assert books[0]["title"] == "Flight Logbook"
