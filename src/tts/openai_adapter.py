"""OpenAI Text-to-Speech provider adapter."""

from __future__ import annotations

import logging
import os
import time

from src.tts.base import AudioSynthesisResult, RateLimitError, TTSProvider, TTSProviderError

logger = logging.getLogger(__name__)


class OpenAITTSProvider(TTSProvider):
    """Speech synthesis adapter using OpenAI Audio Speech API."""

    def __init__(self, default_voice: str = "alloy"):
        self._default_voice = default_voice
        self.api_key = os.getenv("OPENAI_API_KEY")

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def default_voice(self) -> str:
        return self._default_voice

    def synthesize(
        self,
        text: str,
        voice: str | None = None,
        speed: float = 1.0,
    ) -> AudioSynthesisResult:
        """Synthesize text via OpenAI API."""
        if not self.api_key:
            raise TTSProviderError("OPENAI_API_KEY environment variable is required to use OpenAITTSProvider.")

        selected_voice = voice or self.default_voice
        start_time = time.perf_counter()

        try:
            import json
            import urllib.error
            import urllib.request

            req = urllib.request.Request(
                "https://api.openai.com/v1/audio/speech",
                data=json.dumps({
                    "model": "tts-1",
                    "input": text,
                    "voice": selected_voice,
                    "speed": speed,
                }).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=15.0) as resp:
                audio_bytes = resp.read()

            elapsed = time.perf_counter() - start_time
            word_count = max(1, len(text.split()))
            estimated_duration = max(0.5, (word_count / 2.5) / speed)

            return AudioSynthesisResult(
                audio_bytes=audio_bytes,
                audio_format="mp3",
                duration_seconds=estimated_duration,
                response_time_seconds=elapsed,
                cached=False,
            )

        except urllib.error.HTTPError as http_err:
            elapsed = time.perf_counter() - start_time
            if http_err.code == 429:
                raise RateLimitError(f"OpenAI rate limit exceeded: {http_err}") from http_err
            raise TTSProviderError(f"OpenAI TTS API HTTP error {http_err.code}: {http_err.reason}") from http_err
        except Exception as exc:
            raise TTSProviderError(f"OpenAI TTS failed: {exc}") from exc
