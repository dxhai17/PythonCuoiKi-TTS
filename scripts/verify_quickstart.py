"""End-to-End validation script for quickstart.md scenarios."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from src.api.app import create_app


def main() -> None:
    print("=== Running Quickstart End-to-End Validation Scenario ===")
    app = create_app({"TESTING": True})

    with app.test_client() as client:
        # 1. Test GET /api/books (Catalog listing)
        resp = client.get("/api/books")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        books = resp.get_json()
        print(f"[PASS] GET /api/books: {len(books)} books currently in catalog.")

        # 2. Test Ingesting sample text file
        sample_path = Path("test_sample.txt")
        if not sample_path.exists():
            sample_path.write_text("The Wright brothers flew at Kitty Hawk. It was a cold December morning.")

        with open(sample_path, "rb") as f:
            resp = client.post(
                "/api/books/ingest",
                data={
                    "title": "The First Flight",
                    "author": "Orville Wright",
                    "file": (f, "test_sample.txt"),
                },
                content_type="multipart/form-data",
            )
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.data}"
        book_data = resp.get_json()
        book_id = book_data["book_id"]
        total_sentences = book_data["total_sentences"]
        print(f"[PASS] POST /api/books/ingest -> Book ID {book_id}, sentences: {total_sentences}")

        # 3. Test GET /api/books/<book_id>/sentences (Text synchronization)
        resp = client.get(f"/api/books/{book_id}/sentences")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        sentences_payload = resp.get_json()
        sentences = sentences_payload["sentences"]
        assert len(sentences) == total_sentences
        print(f"[PASS] GET /api/books/{book_id}/sentences -> Fetched {len(sentences)} indexed sentences.")

        # 4. Test GET /api/bookmarks/<book_id> (Initial position restoration)
        resp = client.get(f"/api/bookmarks/{book_id}")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        bookmark = resp.get_json()
        print(f"[PASS] GET /api/bookmarks/{book_id} -> Position sentence index: {bookmark['current_sentence_index']}")

        # 5. Test POST /api/bookmarks (Auto-sync bookmark)
        resp = client.post(
            "/api/bookmarks",
            json={
                "book_id": book_id,
                "current_chapter": 0,
                "current_sentence_index": min(1, total_sentences - 1),
                "completion_percentage": 50.0,
            },
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        print(f"[PASS] POST /api/bookmarks -> Saved progress for Book ID {book_id}")

        # 6. Test POST /api/sessions (Record reading telemetry)
        now_iso = datetime.now(timezone.utc).isoformat()
        resp = client.post(
            "/api/sessions",
            json={
                "book_id": book_id,
                "start_time": now_iso,
                "end_time": now_iso,
                "duration_seconds": 120.0,
                "sentences_read": 2,
                "words_read": 25,
            },
        )
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}"
        print(f"[PASS] POST /api/sessions -> Saved reading session for Book ID {book_id}")

        # 7. Test GET /api/analytics/summary (Dashboard KPIs)
        resp = client.get("/api/analytics/summary")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        summary = resp.get_json()
        print(f"[PASS] GET /api/analytics/summary -> Minutes: {summary['total_listening_minutes']}, Sessions: {summary['total_sessions']}")

        # 8. Test GET /api/analytics/charts/listening-trends.png (Headless Matplotlib)
        resp = client.get("/api/analytics/charts/listening-trends.png")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        assert resp.content_type == "image/png"
        assert len(resp.data) > 1000
        print(f"[PASS] GET /api/analytics/charts/listening-trends.png -> Streamed {len(resp.data)} bytes PNG")

        # 9. Test GET /api/analytics/charts/latency-metrics.png (Headless Matplotlib)
        resp = client.get("/api/analytics/charts/latency-metrics.png")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        assert resp.content_type == "image/png"
        assert len(resp.data) > 1000
        print(f"[PASS] GET /api/analytics/charts/latency-metrics.png -> Streamed {len(resp.data)} bytes PNG")

    print("\n=======================================================")
    print("  ALL QUICKSTART SCENARIOS VERIFIED SUCCESSFULLY (PASS)")
    print("=======================================================")


if __name__ == "__main__":
    main()
