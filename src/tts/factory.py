"""Text-to-Speech factory with provider resolution and mock injection."""

from __future__ import annotations

import os

from src.config import get_settings
from src.tts.base import TTSProvider


class TTSFactory:
    """Resolves and instantiates the active speech synthesis provider."""

    @classmethod
    def create_provider(
        cls,
        provider_name: str | None = None,
        voice: str | None = None,
    ) -> TTSProvider:
        """
        Instantiate the requested or configured TTS provider.

        If environment variable MOCK_TTS=true or TESTING=true is present,
        MockTTSProvider is injected to guarantee zero external network calls.
        """
        cfg = get_settings()

        # Check for automated test environment
        if os.getenv("MOCK_TTS", "false").lower() in ("true", "1", "yes") or os.getenv("TESTING") == "true":
            from tests.conftest import MockTTSProvider
            return MockTTSProvider()

        name = (provider_name or cfg.tts_provider).lower()
        default_voice = voice or cfg.tts_default_voice

        if name in ("edge", "edge-tts", "edgetts"):
            from src.tts.edge_tts_adapter import EdgeTTSProvider
            return EdgeTTSProvider(default_voice=default_voice)

        elif name in ("openai", "openai-tts"):
            from src.tts.openai_adapter import OpenAITTSProvider
            return OpenAITTSProvider(default_voice=default_voice)

        else:
            from src.tts.edge_tts_adapter import EdgeTTSProvider
            return EdgeTTSProvider(default_voice=default_voice)
