"""Centralized application configuration loader using python-dotenv and Pydantic."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load .env file at startup
load_dotenv()


class Settings(BaseModel):
    """Application settings with defaults from environment variables."""

    # Database settings
    db_host: str = Field(default_factory=lambda: os.getenv("DB_HOST", "127.0.0.1"))
    db_port: int = Field(default_factory=lambda: int(os.getenv("DB_PORT", "3306")))
    db_user: str = Field(default_factory=lambda: os.getenv("DB_USER", "root"))
    db_password: str = Field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))
    db_name: str = Field(default_factory=lambda: os.getenv("DB_NAME", "studylab_audiobook"))

    # SQLite fallback (enabled via DB_USE_SQLITE=true or when DB_HOST is empty)
    db_use_sqlite: bool = Field(
        default_factory=lambda: os.getenv("DB_USE_SQLITE", "false").lower() in ("true", "1", "yes")
    )
    sqlite_path: str = Field(default_factory=lambda: os.getenv("SQLITE_PATH", ".studylab/studylab.db"))

    # Speech synthesis settings
    tts_provider: str = Field(default_factory=lambda: os.getenv("TTS_PROVIDER", "edge-tts"))
    tts_default_voice: str = Field(
        default_factory=lambda: os.getenv("TTS_DEFAULT_VOICE", "en-US-ChristopherNeural")
    )
    openai_api_key: str | None = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY") or None
    )

    # Telemetry and ping probe targets
    lan_ping_host: str = Field(default_factory=lambda: os.getenv("LAN_PING_HOST", "192.168.1.1"))
    tailscale_ping_host: str = Field(
        default_factory=lambda: os.getenv("TAILSCALE_PING_HOST", "100.100.100.100")
    )

    # Local audio cache directory
    audio_cache_dir: str = Field(
        default_factory=lambda: os.getenv("AUDIO_CACHE_DIR", ".studylab/cache/audio")
    )

    def get_database_url(self) -> str:
        """Construct database connection string."""
        if self.db_use_sqlite or not self.db_host:
            # Ensure parent directory for SQLite file exists
            path = Path(self.sqlite_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{self.sqlite_path}"

        # Standard MySQL connection via PyMySQL driver
        pw_part = f":{self.db_password}" if self.db_password else ""
        return (
            f"mysql+pymysql://{self.db_user}{pw_part}@{self.db_host}:{self.db_port}/"
            f"{self.db_name}?charset=utf8mb4"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
