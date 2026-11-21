"""Backward-compatibility aliases re-exporting from src.core.tts.base."""

from __future__ import annotations

from src.core.tts.base import (
    AudioSynthesisResult,
    RateLimitError,
    TTSProvider,
    TTSProviderError,
)

__all__ = [
    "AudioSynthesisResult",
    "RateLimitError",
    "TTSProvider",
    "TTSProviderError",
]
