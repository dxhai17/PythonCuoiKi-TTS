"""Audio playback controller using pygame.mixer with headless fallback support."""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable
from pathlib import Path

logger = logging.getLogger(__name__)


class AudioPlayer:
    """Manages audio playback, pause, resume, and playback completion events."""

    def __init__(self, headless_dummy: bool = False):
        self._paused = False
        self._is_dummy = headless_dummy
        self._init_mixer(headless_dummy)

    def _init_mixer(self, force_dummy: bool) -> None:
        """Initialize pygame.mixer with fallback to dummy audio driver for headless environments."""
        import pygame

        if force_dummy or os.getenv("TESTING") == "true":
            os.environ["SDL_AUDIODRIVER"] = "dummy"
            self._is_dummy = True

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            logger.debug("pygame.mixer initialized successfully.")
        except Exception as exc:
            logger.warning(f"Failed to initialize standard audio output ({exc}). Falling back to dummy audio driver.")
            try:
                os.environ["SDL_AUDIODRIVER"] = "dummy"
                self._is_dummy = True
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
            except Exception as dummy_exc:
                logger.error(f"Cannot initialize dummy audio driver: {dummy_exc}")
                self._is_dummy = True

    def play_file(self, file_path: str | Path) -> None:
        """Load and start playback of target audio file."""
        import pygame
        path_str = str(Path(file_path).resolve())
        self._paused = False

        if not self._is_dummy:
            try:
                pygame.mixer.music.load(path_str)
                pygame.mixer.music.play()
                logger.debug(f"Started playback: {path_str}")
            except Exception as exc:
                logger.error(f"Failed to play audio file '{path_str}': {exc}")
                self._is_dummy = True

    def pause(self) -> None:
        """Pause active playback."""
        import pygame
        if not self._paused and not self._is_dummy:
            pygame.mixer.music.pause()
        self._paused = True

    def resume(self) -> None:
        """Resume paused playback."""
        import pygame
        if self._paused and not self._is_dummy:
            pygame.mixer.music.unpause()
        self._paused = False

    def toggle_pause(self) -> bool:
        """Toggle play/pause state. Returns True if now paused, False if playing."""
        if self._paused:
            self.resume()
            return False
        else:
            self.pause()
            return True

    def stop(self) -> None:
        """Stop playback completely."""
        import pygame
        if not self._is_dummy:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
        self._paused = False

    def is_playing(self) -> bool:
        """Check if audio is actively playing (and not paused)."""
        import pygame
        if self._paused:
            return False
        if self._is_dummy:
            return False
        return bool(pygame.mixer.music.get_busy())

    def is_paused(self) -> bool:
        """Return True if playback is currently paused."""
        return self._paused

    def wait_until_finished(
        self,
        poll_interval: float = 0.05,
        poll_callback: Callable[[], bool] | None = None,
        dummy_duration: float = 0.5,
    ) -> bool:
        """
        Block while audio is playing.
        Invokes poll_callback if provided. If callback returns True, aborts waiting.
        Returns True if finished naturally, False if interrupted by callback.
        """
        import pygame

        if self._is_dummy:
            # Simulate playback duration for headless mode
            start = time.perf_counter()
            while time.perf_counter() - start < dummy_duration:
                if self._paused:
                    time.sleep(poll_interval)
                    continue
                if poll_callback and poll_callback():
                    return False
                time.sleep(poll_interval)
            return True

        while pygame.mixer.music.get_busy() or self._paused:
            if poll_callback and poll_callback():
                return False
            time.sleep(poll_interval)
        return True
