"""Player API blueprint: audio streaming, bookmarks, and reading sessions."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Blueprint, jsonify, request, send_file
from pydantic import ValidationError

from src.api.schemas.player_schemas import (
    BookmarkResponse,
    BookmarkUpdateRequest,
    ReadingSessionCreateRequest,
    ReadingSessionResponse,
)
from src.core.models.session import ReadingSession
from src.core.player.cache_manager import AudioCacheManager
from src.core.storage.db import get_db_engine
from src.core.storage.repositories import (
    SqlBookmarkRepository,
    SqlBookRepository,
    SqlSessionRepository,
)
from src.core.tts.factory import TTSFactory

logger = logging.getLogger(__name__)

player_bp = Blueprint("player", __name__)


@player_bp.route("/audio/<int:book_id>/<int:sentence_index>", methods=["GET"])
def stream_sentence_audio(book_id: int, sentence_index: int) -> Any:
    """Stream synthesized MP3 audio for an indexed sentence."""
    try:
        speed = float(request.args.get("speed", 1.0))
        if speed < 0.5 or speed > 3.0:
            return jsonify({"error": "Speed must be between 0.5 and 3.0"}), 400
    except ValueError:
        return jsonify({"error": "Invalid speed query parameter"}), 400

    voice = request.args.get("voice")

    engine = get_db_engine()
    book_repo = SqlBookRepository(engine)

    book = book_repo.get_book(book_id)
    if not book:
        return jsonify({"error": f"Book ID {book_id} not found"}), 404

    sentences = book_repo.get_book_sentences(book_id)
    sentence = next((s for s in sentences if s.sentence_index == sentence_index), None)
    if not sentence:
        return jsonify({"error": f"Sentence {sentence_index} not found for book {book_id}"}), 404

    voice_name = voice or "en-US-ChristopherNeural"
    cache_manager = AudioCacheManager()
    cache_key = AudioCacheManager.compute_key(sentence.text_content, voice_name, speed)
    cached_path = cache_manager.get_cached_audio(book_id=book_id, key=cache_key)

    if cached_path and Path(cached_path).exists():
        response = send_file(cached_path, mimetype="audio/mpeg")
        response.headers["Cache-Control"] = "public, max-age=86400"
        return response

    # Synthesize audio on demand
    tts_provider = TTSFactory.create_provider(voice=voice_name)
    try:
        synth_result = tts_provider.synthesize(
            text=sentence.text_content,
            voice=voice_name,
            speed=speed,
        )
        saved_path = cache_manager.save_audio(
            book_id=book_id,
            key=cache_key,
            audio_bytes=synth_result.audio_bytes,
            ext="mp3",
        )
        response = send_file(saved_path, mimetype="audio/mpeg")
        response.headers["Cache-Control"] = "public, max-age=86400"
        return response
    except Exception as exc:
        logger.error(f"Failed to synthesize audio for book {book_id} sentence {sentence_index}: {exc}")
        return jsonify({"error": f"Speech synthesis failed: {exc}"}), 500


@player_bp.route("/bookmarks/<int:book_id>", methods=["GET"])
def get_bookmark(book_id: int) -> Any:
    """Retrieve saved bookmark for a book."""
    engine = get_db_engine()
    bookmark_repo = SqlBookmarkRepository(engine)
    bookmark = bookmark_repo.get_bookmark(book_id)
    if not bookmark:
        return jsonify(
            {
                "book_id": book_id,
                "current_chapter": 1,
                "current_sentence_index": 0,
                "completion_percentage": 0.0,
                "last_read_at": None,
            }
        )

    last_read_str = (
        bookmark.last_read_at.isoformat()
        if isinstance(bookmark.last_read_at, datetime)
        else str(bookmark.last_read_at)
        if bookmark.last_read_at
        else None
    )
    return jsonify(
        BookmarkResponse(
            book_id=bookmark.book_id,
            current_chapter=bookmark.current_chapter,
            current_sentence_index=bookmark.current_sentence_index,
            completion_percentage=bookmark.completion_percentage,
            last_read_at=last_read_str,
        ).model_dump()
    )


@player_bp.route("/bookmarks", methods=["POST"])
def update_bookmark() -> Any:
    """Update bookmark reading position."""
    data = request.get_json() or {}
    try:
        req = BookmarkUpdateRequest(**data)
    except ValidationError as err:
        return jsonify({"error": "Validation error", "details": err.errors()}), 400

    engine = get_db_engine()
    bookmark_repo = SqlBookmarkRepository(engine)
    bookmark_repo.update_bookmark(
        book_id=req.book_id,
        chapter_idx=req.current_chapter,
        sentence_idx=req.current_sentence_index,
        percentage=req.completion_percentage,
    )
    return jsonify({"status": "updated"})


@player_bp.route("/sessions", methods=["POST"])
def record_session() -> Any:
    """Record a completed reading session."""
    data = request.get_json() or {}
    try:
        req = ReadingSessionCreateRequest(**data)
    except ValidationError as err:
        return jsonify({"error": "Validation error", "details": err.errors()}), 400

    from datetime import datetime

    engine = get_db_engine()
    session_repo = SqlSessionRepository(engine)

    start_dt = datetime.fromisoformat(req.start_time.replace("Z", "+00:00"))
    end_dt = datetime.fromisoformat(req.end_time.replace("Z", "+00:00"))

    session = ReadingSession(
        book_id=req.book_id,
        start_time=start_dt,
        end_time=end_dt,
        duration_seconds=int(req.duration_seconds),
        sentences_read=req.sentences_read,
        words_read=req.words_read,
    )
    session_id = session_repo.record_session(session)

    return (
        jsonify(
            ReadingSessionResponse(
                id=session_id,
                book_id=session.book_id,
                duration_seconds=session.duration_seconds,
                sentences_read=session.sentences_read,
                words_read=session.words_read,
                created_at=datetime.utcnow().isoformat(),
            ).model_dump()
        ),
        201,
    )
