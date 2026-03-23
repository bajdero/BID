"""
src/api/deps.py
FastAPI dependency injection helpers.

All dependencies use the FastAPI `Depends()` pattern so they can be
overridden in tests via app.dependency_overrides.
"""
from __future__ import annotations

import re
from pathlib import Path

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.config import settings
from src.api.models.database import SessionLocal
from src.api.services.processing import ProcessingService, get_service
from src.api.services.source import SourceService

# --------------------------------------------------------------------------
# Project identifier validation
# --------------------------------------------------------------------------

# Only alphanumeric characters, underscores, hyphens, and dots are allowed.
# This prevents directory traversal via the project_id URL segment.
_SAFE_PROJECT_ID_RE = re.compile(r"^[a-zA-Z0-9_\-\.]+$")


def get_project_path(project_id: str) -> Path:
    """
    Resolve the project directory from *project_id* and validate it exists.

    Raises HTTP 400 for unsafe identifiers, HTTP 404 if the directory is absent.
    """
    if not _SAFE_PROJECT_ID_RE.match(project_id):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid project identifier {project_id!r}. "
                "Only letters, digits, underscores, hyphens, and dots are allowed."
            ),
        )
    project_path = settings.PROJECTS_DIR / project_id
    if not project_path.exists() or not project_path.is_dir():
        raise HTTPException(
            status_code=404, detail=f"Project '{project_id}' not found."
        )
    return project_path


# --------------------------------------------------------------------------
# Database session
# --------------------------------------------------------------------------


def get_db():
    """Yield a per-request SQLAlchemy session and close it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------------------------------------------------------------------------
# Service singletons
# --------------------------------------------------------------------------


def get_processing_service() -> ProcessingService:
    """Return the application-singleton ProcessingService."""
    return get_service()


def get_source_service() -> SourceService:
    """Return a new (stateless) SourceService instance."""
    return SourceService()
