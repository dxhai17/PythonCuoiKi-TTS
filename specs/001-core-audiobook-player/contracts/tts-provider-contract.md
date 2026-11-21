# Interface Contract: TTS Provider Protocol

**Feature**: `001-core-audiobook-player`
**Date**: 2026-11-20

## Overview

The `TTSProvider` contract enforces a pluggable, vendor-agnostic speech synthesis interface across Microsoft Edge-TTS, OpenAI TTS, and Google Cloud TTS. It decouples audio generation from player playback controls and enables deterministic offline mocking in automated test suites.

---

## Python Protocol Definition (`src/tts/base.py`)

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class AudioSynthesisResult:
    audio_bytes: bytes
    audio_format: str  # e.g., "mp3", "wav"
    duration_seconds: float
    response_time_seconds: float
    cached: bool = False

class TTSProvider(ABC):
    """Abstract interface for all Speech Synthesis engines."""

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
        voice: Optional[str] = None,
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
```

---

## Provider Implementations

| Provider Class | Underlying Engine | Default Voice | Requirements |
|---|---|---|---|
| `EdgeTTSProvider` | Microsoft Edge-TTS | `en-US-ChristopherNeural` (or `vi-VN-NamMinhNeural`) | Zero API keys, internet connection |
| `OpenAITTSProvider` | OpenAI Audio Speech API | `alloy` / `echo` / `fable` | `OPENAI_API_KEY` in `.env` |
| `MockTTSProvider` | Test Double | `mock-voice` | In-memory dummy MP3/WAV for unit tests |

---

## Factory & Provider Resolution

The application resolves the active provider through `TTSFactory.create_provider()`:
1. Reads `TTS_PROVIDER` environment variable (`edge-tts` by default).
2. If `openai` is requested: checks that `OPENAI_API_KEY` is present; raises `ConfigError` if missing.
3. If running under `pytest` (`TESTING=true` or pytest fixture): automatically injects `MockTTSProvider` to prevent live external network calls (Constitutions Principle II & Project Rules).
