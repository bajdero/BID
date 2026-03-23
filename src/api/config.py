"""
src/api/config.py
Application-wide settings loaded from environment variables or a .env file.
All defaults are tuned for local development (single SQLite file, localhost CORS).
"""
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve project root (three levels up from this file: src/api/config.py → root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """FastAPI application settings — override via environment variables or .env."""

    # ------------------------------------------------------------------ Database
    # SQLite path is relative to CWD when running uvicorn from the project root.
    DATABASE_URL: str = Field(
        default=f"sqlite:///{_PROJECT_ROOT / 'data' / 'bid.sqlite3'}",
        description="SQLAlchemy database connection URL (SQLite or PostgreSQL).",
    )

    # ------------------------------------------------------------- Project store
    # Absolute path to the directory that contains all project sub-directories.
    PROJECTS_DIR: Path = Field(
        default=_PROJECT_ROOT / "projects",
        description="Root directory for project sub-folders.",
    )

    # ---------------------------------------------------------- Processing queue
    MAX_CONCURRENT_TASKS: int = Field(
        default=5,
        ge=1,
        le=16,
        description="Maximum number of image-processing tasks running in parallel.",
    )

    # -------------------------------------------------------------------- CORS
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins for the frontend.",
    )

    # ----------------------------------------------------------------- Versions
    API_VERSION: str = Field(default="1.0.0", description="SemVer for this API build.")
    BID_VERSION: str = Field(default="2.0.0-dev", description="BID product version.")

    # -------------------------------------------------------------------- Auth
    SECRET_KEY: str = Field(
        default="change-me-in-production-use-a-long-random-string",
        description="HMAC secret key for signing JWT tokens.  Override via SECRET_KEY env var.",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm.")
    # Access token lifetime (seconds); default 30 minutes.
    ACCESS_TOKEN_EXPIRE_SECONDS: int = Field(default=1800, ge=60)
    # Refresh token lifetime (seconds); default 7 days.
    REFRESH_TOKEN_EXPIRE_SECONDS: int = Field(default=604800, ge=60)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # Allow extra env vars from the host environment without failing.
        extra="ignore",
    )


settings = Settings()
