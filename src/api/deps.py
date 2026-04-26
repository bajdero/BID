"""
src/api/deps.py
FastAPI dependency injection helpers.

All dependencies use the FastAPI `Depends()` pattern so they can be
overridden in tests via app.dependency_overrides.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from src.api.config import settings
from src.api.models.database import SessionLocal
from src.api.models.user import UserRecord
from src.api.services.auth import AuthService, decode_token
from src.api.services.processing import ProcessingService, get_service
from src.api.services.project import ProjectService
from src.api.services.source import SourceService
from src.api.websocket.manager import ConnectionManager, get_manager

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


def get_project_service() -> ProjectService:
    """Return a new (stateless) ProjectService instance."""
    return ProjectService()


def get_auth_service() -> AuthService:
    """Return a new (stateless) AuthService instance."""
    return AuthService()


def get_connection_manager() -> ConnectionManager:
    """Return the application-singleton ConnectionManager."""
    return get_manager()


# --------------------------------------------------------------------------
# JWT auth
# --------------------------------------------------------------------------

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> Optional[UserRecord]:
    """
    Extract and validate the Bearer JWT from the Authorization header.

    Returns the UserRecord when a valid token is provided; returns None when
    no token is present (allows unauthenticated access on optional routes).
    Raises HTTP 401 for malformed or expired tokens.
    """
    if credentials is None:
        return None

    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Token type must be 'access'.")

    username: str = payload.get("sub", "")
    user = db.query(UserRecord).filter_by(username=username).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User account not found or deactivated.")
    return user


def require_authenticated_user(
    user: Optional[UserRecord] = Depends(get_current_user),
) -> UserRecord:
    """
    Raise HTTP 401 when no authenticated user is available.
    Use as a dependency on routes that must be protected.
    """
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user


def require_admin(
    user: UserRecord = Depends(require_authenticated_user),
) -> UserRecord:
    """
    Raise HTTP 403 when the authenticated user does not have the 'admin' role.
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin role required for this operation.",
        )
    return user
