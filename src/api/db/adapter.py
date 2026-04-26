"""
src/api/db/adapter.py
Database adapter abstraction (P1-05).

Goals:
- Keep SQLite as the zero-config default backend.
- Support PostgreSQL with the same ORM models and session API.
- Centralize backend-specific SQLAlchemy engine options.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


@dataclass(frozen=True)
class DatabaseAdapter:
    """Base adapter contract for a SQLAlchemy backend."""

    url: str

    def create_engine(self) -> Engine:
        raise NotImplementedError


@dataclass(frozen=True)
class SQLiteAdapter(DatabaseAdapter):
    """SQLite adapter with thread-safety options required by FastAPI workers."""

    def create_engine(self) -> Engine:
        return create_engine(self.url, connect_args={"check_same_thread": False})


@dataclass(frozen=True)
class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL adapter (sync SQLAlchemy engine)."""

    def create_engine(self) -> Engine:
        # pool_pre_ping helps recover from stale TCP connections.
        return create_engine(self.url, pool_pre_ping=True)


def normalize_database_url(url: str) -> str:
    """
    Normalize DB URLs for cross-platform consistency.

    - Expands relative sqlite paths to absolute paths rooted at CWD.
    - Leaves absolute sqlite paths and non-sqlite URLs untouched.
    """
    if not url.startswith("sqlite"):
        return url

    # sqlite:///relative/path.db
    prefix = "sqlite:///"
    if url.startswith(prefix):
        db_path = url[len(prefix):]
        p = Path(db_path)
        if not p.is_absolute():
            return prefix + str(p.resolve())
    return url


def make_adapter(url: str) -> DatabaseAdapter:
    """Create the backend adapter instance based on DATABASE_URL scheme."""
    normalized = normalize_database_url(url)
    if normalized.startswith("sqlite"):
        return SQLiteAdapter(normalized)
    if normalized.startswith("postgresql"):
        return PostgreSQLAdapter(normalized)
    raise ValueError(
        "Unsupported DATABASE_URL scheme. Expected sqlite:// or postgresql://"
    )
