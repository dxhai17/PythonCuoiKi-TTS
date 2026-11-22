"""Microsoft Edge-TTS speech synthesis adapter."""

from __future__ import annotations

import asyncio
import io
import logging
import time

import edge_tts

from src.core.tts.base import AudioSynthesisResult, RateLimitError, TTSProvider, TTSProviderError

logger = logging.getLogger(__name__)


class EdgeTTSProvider(TTSProvider):
    """Zero-cost speech synthesis adapter using Microsoft Edge-TTS."""

    def __init__(self, default_voice: str = "en-US-ChristopherNeural"):
        self._default_voice = default_voice

    @property
    def provider_name(self) -> str:
        return "edge-tts"

    @property
    def default_voice(self) -> str:
        return self._default_voice

    async def _synthesize_async(
        self, text: str, voice: str, rate_str: str
    ) -> bytes:
        """Asynchronously stream MP3 audio chunks from Edge-TTS service."""
        communicate = edge_tts.Communicate(text, voice, rate=rate_str)
        buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buffer.write(chunk["data"])
        return buffer.getvalue()

    def synthesize(
        self,
        text: str,
        voice: str | None = None,
        speed: float = 1.0,
    ) -> AudioSynthesisResult:
        """
        Synthesize text into MP3 audio via Edge-TTS.

        Speed mapping: 1.0 -> '+0%', 1.25 -> '+25%', 0.8 -> '-20%'
        """
        selected_voice = voice or self.default_voice
        rate_offset = int(round((speed - 1.0) * 100))
        rate_str = f"{rate_offset:+d}%"

        start_time = time.perf_counter()
        try:
            # Handle event loop in thread-safe manner
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                        audio_data = pool.submit(
                            asyncio.run, self._synthesize_async(text, selected_voice, rate_str)
                        ).result(timeout=15.0)
                else:
                    audio_data = loop.run_until_complete(
                        self._synthesize_async(text, selected_voice, rate_str)
                    )
            except RuntimeError:
                audio_data = asyncio.run(
                    self._synthesize_async(text, selected_voice, rate_str)
                )

            elapsed = time.perf_counter() - start_time

            if not audio_data:
                raise TTSProviderError("Edge-TTS returned empty audio stream.")

            # Rough estimate of duration: ~150 words per minute / speed
            word_count = max(1, len(text.split()))
            estimated_duration = max(0.5, (word_count / 2.5) / speed)

            return AudioSynthesisResult(
                audio_bytes=audio_data,
                audio_format="mp3",
                duration_seconds=estimated_duration,
                response_time_seconds=elapsed,
                cached=False,
            )

        except Exception as exc:
            elapsed = time.perf_counter() - start_time
            err_str = str(exc).lower()
            if "429" in err_str or "rate limit" in err_str:
                raise RateLimitError(f"Edge-TTS rate limit exceeded: {exc}") from exc
            logger.error(f"Edge-TTS synthesis error after {elapsed:.2f}s: {exc}")
            raise TTSProviderError(f"Speech synthesis failed: {exc}") from exc
