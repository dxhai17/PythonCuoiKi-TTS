"""Unit tests for lookahead audio pre-fetch queue and local disk caching."""

from __future__ import annotations

import tempfile

from src.player.buffer_manager import LookaheadBuffer
from src.player.cache_manager import AudioCacheManager
from tests.conftest import MockTTSProvider


def test_audio_cache_manager():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = AudioCacheManager(base_dir=tmpdir)
        key = cache.compute_key("Sentence text sample", voice="voice-1", speed=1.0)
        assert len(key) == 64  # SHA-256

        # Not yet cached
        assert cache.get_cached_audio(book_id=1, key=key) is None

        # Save audio
        saved_path = cache.save_audio(book_id=1, key=key, audio_bytes=b"RIFFdummydata", ext="wav")
        assert saved_path.exists()

        # Retrieve cached
        found_path = cache.get_cached_audio(book_id=1, key=key)
        assert found_path is not None
        assert found_path == saved_path
        assert found_path.read_bytes() == b"RIFFdummydata"


def test_lookahead_buffer():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = AudioCacheManager(base_dir=tmpdir)
        tts = MockTTSProvider(simulated_latency=0.01)

        sentences = [
            (0, "First sentence of the book."),
            (1, "Second sentence of the book."),
            (2, "Third sentence of the book."),
        ]

        buffer = LookaheadBuffer(
            book_id=1,
            sentences=sentences,
            tts_provider=tts,
            cache_manager=cache,
        )

        # Get sentence 0
        path_0, metrics_0 = buffer.get_sentence_audio(0)
        assert path_0.exists()
        assert metrics_0.cached is False

        # Requesting sentence 0 again should hit cache
        path_0_repeat, metrics_0_repeat = buffer.get_sentence_audio(0)
        assert path_0_repeat == path_0
        assert metrics_0_repeat.cached is True

        # Pre-fetch sentence 1
        buffer.pre_fetch(1)
        path_1, _ = buffer.get_sentence_audio(1)
        assert path_1.exists()
