"""Lookahead audio buffer manager with pre-fetch queue and cache coordination."""

from __future__ import annotations

import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

from src.player.cache_manager import AudioCacheManager
from src.tts.base import AudioSynthesisResult, TTSProvider

logger = logging.getLogger(__name__)


class LookaheadBuffer:
    """Coordinates just-in-time audio synthesis and background lookahead pre-fetching."""

    def __init__(
        self,
        book_id: int,
        sentences: list[tuple[int, str]],  # (sentence_index, text_content)
        tts_provider: TTSProvider,
        cache_manager: AudioCacheManager | None = None,
        voice: str | None = None,
        speed: float = 1.0,
    ):
        self.book_id = book_id
        self.sentences_map = dict(sentences)
        self.tts_provider = tts_provider
        self.cache_manager = cache_manager or AudioCacheManager()
        self.voice = voice or tts_provider.default_voice
        self.speed = speed

        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="tts-lookahead")
        self._lock = threading.Lock()
        self._futures: dict[int, Future[tuple[Path, AudioSynthesisResult]]] = {}

    def update_speed_or_voice(self, speed: float | None = None, voice: str | None = None) -> None:
        """Update playback speed or voice and cancel pending pre-fetches."""
        with self._lock:
            if speed is not None:
                self.speed = speed
            if voice is not None:
                self.voice = voice
            self._futures.clear()

    def _fetch_or_synthesize(self, sentence_idx: int) -> tuple[Path, AudioSynthesisResult]:
        """Fetch from disk cache or invoke speech synthesis."""
        text_content = self.sentences_map.get(sentence_idx, "")
        if not text_content:
            raise IndexError(f"Sentence index {sentence_idx} not found in book {self.book_id}")

        cache_key = self.cache_manager.compute_key(text_content, self.voice, self.speed)
        cached_file = self.cache_manager.get_cached_audio(self.book_id, cache_key)

        if cached_file:
            # Cache hit: instant retrieval (<5ms)
            word_count = max(1, len(text_content.split()))
            result = AudioSynthesisResult(
                audio_bytes=b"",
                audio_format=cached_file.suffix.lstrip("."),
                duration_seconds=max(0.5, (word_count / 2.5) / self.speed),
                response_time_seconds=0.002,
                cached=True,
            )
            return cached_file, result

        # Cache miss: synthesize and persist
        synth_result = self.tts_provider.synthesize(
            text_content, voice=self.voice, speed=self.speed
        )
        saved_file = self.cache_manager.save_audio(
            self.book_id, cache_key, synth_result.audio_bytes, ext=synth_result.audio_format
        )
        return saved_file, synth_result

    def pre_fetch(self, next_sentence_idx: int) -> None:
        """Asynchronously pre-fetch sentence audio in background thread."""
        if next_sentence_idx not in self.sentences_map:
            return

        with self._lock:
            if next_sentence_idx in self._futures and not self._futures[next_sentence_idx].done():
                return
            future = self._executor.submit(self._fetch_or_synthesize, next_sentence_idx)
            self._futures[next_sentence_idx] = future

    def get_sentence_audio(self, sentence_idx: int) -> tuple[Path, AudioSynthesisResult]:
        """
        Retrieve audio file and telemetry for target sentence index.
        Awaits pre-fetch future if already submitted, or synthesizes directly.
        """
        future = None
        with self._lock:
            future = self._futures.pop(sentence_idx, None)

        if future is not None:
            try:
                return future.result(timeout=15.0)
            except Exception as exc:
                logger.warning(f"Pre-fetch future failed for sentence {sentence_idx}: {exc}")

        return self._fetch_or_synthesize(sentence_idx)

    def shutdown(self) -> None:
        """Cancel pending tasks and shutdown thread pool."""
        self._executor.shutdown(wait=False, cancel_futures=True)
