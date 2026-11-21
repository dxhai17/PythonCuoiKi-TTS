"""Shared pytest fixtures and mock implementations for deterministic offline testing."""

from __future__ import annotations

import io
import time
import wave
from collections.abc import Generator

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.pool import StaticPool

from src.core.storage.migrations import run_migrations
from src.core.tts.base import AudioSynthesisResult, TTSProvider


def generate_dummy_wav(duration_seconds: float = 0.5, sample_rate: int = 16000) -> bytes:
    """Generate minimal valid PCM WAV bytes in-memory for testing."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        # Generate silence
        num_frames = int(duration_seconds * sample_rate)
        wav_file.writeframes(b"\x00\x00" * num_frames)
    return buf.getvalue()


class MockTTSProvider(TTSProvider):
    """Test double implementing TTSProvider without external network access."""

    def __init__(self, simulated_latency: float = 0.05, should_fail: bool = False):
        self.simulated_latency = simulated_latency
        self.should_fail = should_fail
        self.call_history: list[dict] = []

    @property
    def provider_name(self) -> str:
        return "mock-tts"

    @property
    def default_voice(self) -> str:
        return "mock-voice-neutral"

    def synthesize(
        self,
        text: str,
        voice: str | None = None,
        speed: float = 1.0,
    ) -> AudioSynthesisResult:
        if self.should_fail:
            from src.tts.base import TTSProviderError
            raise TTSProviderError("Simulated speech synthesis service failure")

        start = time.perf_counter()
        if self.simulated_latency > 0:
            time.sleep(self.simulated_latency)
        elapsed = time.perf_counter() - start

        # Approx 150 words per minute -> 2.5 words per second
        word_count = max(1, len(text.split()))
        estimated_duration = max(0.5, word_count / 2.5) / speed
        dummy_audio = generate_dummy_wav(duration_seconds=0.1)

        self.call_history.append({
            "text": text,
            "voice": voice or self.default_voice,
            "speed": speed,
            "elapsed": elapsed,
        })

        return AudioSynthesisResult(
            audio_bytes=dummy_audio,
            audio_format="wav",
            duration_seconds=estimated_duration,
            response_time_seconds=elapsed,
            cached=False,
        )


@pytest.fixture
def mock_tts_provider() -> MockTTSProvider:
    """Provide a fresh MockTTSProvider instance for testing."""
    return MockTTSProvider()


@pytest.fixture
def test_engine() -> Generator[Engine, None, None]:
    """Provide an isolated in-memory SQLite database engine with migrations applied."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    run_migrations(engine)
    yield engine
    engine.dispose()
