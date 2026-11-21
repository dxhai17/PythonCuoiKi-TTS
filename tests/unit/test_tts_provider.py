"""Unit tests for TTS providers and provider factory."""

from __future__ import annotations

import pytest

from src.tts.base import TTSProvider, TTSProviderError
from src.tts.factory import TTSFactory
from tests.conftest import MockTTSProvider


def test_mock_tts_provider_synthesis():
    provider = MockTTSProvider(simulated_latency=0.01)
    assert provider.provider_name == "mock-tts"
    assert provider.default_voice == "mock-voice-neutral"

    result = provider.synthesize("Hello world, this is a test.")
    assert len(result.audio_bytes) > 0
    assert result.audio_format == "wav"
    assert result.duration_seconds > 0
    assert result.response_time_seconds >= 0.01


def test_mock_tts_provider_failure():
    failing_provider = MockTTSProvider(should_fail=True)
    with pytest.raises(TTSProviderError):
        failing_provider.synthesize("This should fail.")


def test_tts_factory_mock_injection(monkeypatch):
    monkeypatch.setenv("MOCK_TTS", "true")
    provider = TTSFactory.create_provider()
    assert isinstance(provider, TTSProvider)
    assert provider.provider_name == "mock-tts"
