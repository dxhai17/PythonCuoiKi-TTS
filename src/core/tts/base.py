"""Abstract Text-to-Speech (TTS) provider protocol and error hierarchy."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class TTSProviderError(Exception):
    """Base exception for speech synthesis errors."""
    pass


class RateLimitError(TTSProviderError):
    """Raised when TTS provider rate limits or quotas are exceeded."""
    pass


@dataclass(frozen=True)
class AudioSynthesisResult:
    """Represents the output and performance metrics of a speech synthesis request."""
    audio_bytes: bytes
    audio_format: str  # e.g., "mp3", "wav"
    duration_seconds: float
    response_time_seconds: float
    cached: bool = False


class TTSProvider(ABC):
    """Abstract interface for all speech synthesis engines."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the unique identifier for the provider (e.g., 'edge-tts', 'openai')."""
        pass

    @property
    @abstractmethod
    def default_voice(self) -> str:
        """Return the default voice model identifier."""
        pass

    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice: str | None = None,
        speed: float = 1.0,
    ) -> AudioSynthesisResult:
        """
        Synthesize speech from input text synchronously or via internal event loop.

        Args:
            text: Plain text sentence to synthesize.
            voice: Voice identifier. If None, uses default_voice.
            speed: Speech rate multiplier (e.g. 0.75 - 2.0).

        Returns:
            AudioSynthesisResult containing audio data and generation metrics.

        Raises:
            TTSProviderError: When synthesis fails due to network or API error.
            RateLimitError: When API quota or rate limits are exceeded.
        """
        pass
