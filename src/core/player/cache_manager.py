"""Local disk audio cache manager using SHA-256 sentence content hashing."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from src.core.config import get_settings

logger = logging.getLogger(__name__)


class AudioCacheManager:
    """Manages cached speech synthesis audio files on the local filesystem."""

    def __init__(self, base_dir: str | Path | None = None):
        cfg = get_settings()
        self.base_dir = Path(base_dir or cfg.audio_cache_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def compute_key(sentence_text: str, voice: str, speed: float) -> str:
        """Generate deterministic SHA-256 cache key from sentence text and speech settings."""
        normalized = f"{sentence_text.strip()}:{voice}:{speed:.2f}"
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _get_book_dir(self, book_id: int) -> Path:
        """Return and create target directory for a given book."""
        book_dir = self.base_dir / str(book_id)
        book_dir.mkdir(parents=True, exist_ok=True)
        return book_dir

    def get_cached_audio(self, book_id: int, key: str) -> Path | None:
        """Look up audio file by book ID and cache key; returns Path if exists."""
        book_dir = self._get_book_dir(book_id)
        # Check standard audio formats
        for ext in ("mp3", "wav", "ogg"):
            candidate = book_dir / f"{key}.{ext}"
            if candidate.exists() and candidate.stat().st_size > 0:
                return candidate
        return None

    def save_audio(
        self, book_id: int, key: str, audio_bytes: bytes, ext: str = "mp3"
    ) -> Path:
        """Write synthesized audio bytes to local disk cache."""
        book_dir = self._get_book_dir(book_id)
        target_path = book_dir / f"{key}.{ext}"
        target_path.write_bytes(audio_bytes)
        logger.debug(f"Saved audio cache: {target_path} ({len(audio_bytes)} bytes)")
        return target_path

    def clear_book_cache(self, book_id: int) -> int:
        """Remove all cached audio segments for a specific book. Returns deleted count."""
        book_dir = self._get_book_dir(book_id)
        count = 0
        for f in book_dir.iterdir():
            if f.is_file():
                f.unlink(missing_ok=True)
                count += 1
        return count
