"""
src/api/models/database.py
SQLAlchemy 2.0 engine, session factory, and declarative base.

Design rules (from web_architecture.md §2.1.2):
- SQLite is the Phase-1 persistence backend.
- All file paths stored in the DB are *relative* strings; absolute resolution
  happens at runtime using project settings.
- `init_db()` creates all tables on application startup.
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.api.config import settings


def _make_engine(url: str):
    """Create a SQLAlchemy engine with driver-specific options."""
    kwargs: dict = {}
    if url.startswith("sqlite"):
        # SQLite needs check_same_thread=False for multi-threaded FastAPI workers.
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


engine = _make_engine(str(settings.DATABASE_URL))

SessionLocal: sessionmaker[Session] = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Create all tables declared under Base.  Called once during app lifespan startup."""
    # Import models so their table definitions are registered on Base.metadata.
    from src.api.models import audit, source  # noqa: F401

    Base.metadata.create_all(bind=engine)
