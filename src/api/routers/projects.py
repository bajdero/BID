"""
src/api/routers/projects.py
Project management endpoints (P1-03).

GET    /projects                              – list all projects
POST   /projects                             – create new project
GET    /projects/{id}                        – project details
DELETE /projects/{id}                        – delete project
GET    /projects/{id}/settings               – project settings
PUT    /projects/{id}/settings               – update settings
GET    /projects/{id}/export-profiles        – export profile definitions
PUT    /projects/{id}/export-profiles        – update export profiles
POST   /projects/{id}/export-profiles/validate – validate a single profile
GET    /projects/{id}/audit/logs             – immutable audit log stream
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.api.deps import get_db, get_project_path, get_project_service
from src.api.schemas.common import ErrorResponse
from src.api.schemas.projects import (
    AuditLogEntry,
    ExportProfileValidateRequest,
    ExportProfileValidateResponse,
    ExportProfilesResponse,
    ProjectCreate,
    ProjectInfo,
    ProjectSettings,
)
from src.api.services.project import ProjectService

_ERR = {
    400: {"model": ErrorResponse, "description": "Bad request."},
    404: {"model": ErrorResponse, "description": "Project not found."},
    409: {"model": ErrorResponse, "description": "Project already exists."},
    500: {"model": ErrorResponse, "description": "Server error."},
}

router = APIRouter(prefix="/projects", tags=["projects"])


# ---------------------------------------------------------------------------
# Collection endpoints (no project_id)
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=list[ProjectInfo],
    summary="List all projects",
    responses=_ERR,
)
def list_projects(
    db: Session = Depends(get_db),
    svc: ProjectService = Depends(get_project_service),
) -> list[ProjectInfo]:
    """Return a summary record for every project directory in PROJECTS_DIR."""
    return svc.list_projects(db)


@router.post(
    "",
    response_model=ProjectInfo,
    status_code=201,
    summary="Create a new project",
    responses=_ERR,
)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    svc: ProjectService = Depends(get_project_service),
) -> ProjectInfo:
    """
    Create a new project directory with *settings.json* and *export_option.json*.

    The project identifier (URL segment) is derived by replacing spaces with
    underscores in *body.name*.  Returns **409 Conflict** if a project with the
    same normalised name already exists.
    """
    try:
        return svc.create_project(body, db)
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Item endpoints (project_id required)
# ---------------------------------------------------------------------------


@router.get(
    "/{project_id}",
    response_model=ProjectInfo,
    summary="Get project details",
    responses=_ERR,
)
def get_project(
    project_id: str,
    project_path: Path = Depends(get_project_path),
    db: Session = Depends(get_db),
    svc: ProjectService = Depends(get_project_service),
) -> ProjectInfo:
    """Return full details for a single project."""
    return svc.get_project(project_id, db)


@router.delete(
    "/{project_id}",
    status_code=204,
    summary="Delete a project",
    responses=_ERR,
)
def delete_project(
    project_id: str,
    project_path: Path = Depends(get_project_path),
    svc: ProjectService = Depends(get_project_service),
) -> None:
    """
    Permanently remove the project directory and all its files from disk.

    **This action is irreversible.**  Source and export files are NOT deleted —
    only the project metadata directory is removed.
    """
    try:
        svc.delete_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.") from exc


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


@router.get(
    "/{project_id}/settings",
    response_model=ProjectSettings,
    summary="Get project settings",
    responses=_ERR,
)
def get_settings(
    project_id: str,
    project_path: Path = Depends(get_project_path),
    svc: ProjectService = Depends(get_project_service),
) -> ProjectSettings:
    """Return the contents of the project's *settings.json*."""
    return svc.get_settings(project_path)


@router.put(
    "/{project_id}/settings",
    response_model=ProjectSettings,
    summary="Update project settings",
    responses=_ERR,
)
def update_settings(
    project_id: str,
    body: ProjectSettings,
    project_path: Path = Depends(get_project_path),
    svc: ProjectService = Depends(get_project_service),
) -> ProjectSettings:
    """Overwrite the project's *settings.json* with *body* and return the saved values."""
    return svc.update_settings(project_path, body)


# ---------------------------------------------------------------------------
# Export profiles
# ---------------------------------------------------------------------------


@router.get(
    "/{project_id}/export-profiles",
    response_model=ExportProfilesResponse,
    summary="Get export profile definitions",
    responses=_ERR,
)
def get_export_profiles(
    project_id: str,
    project_path: Path = Depends(get_project_path),
    svc: ProjectService = Depends(get_project_service),
) -> ExportProfilesResponse:
    """Return all export profiles defined in the project's *export_option.json*."""
    return svc.get_export_profiles(project_path)


@router.put(
    "/{project_id}/export-profiles",
    response_model=ExportProfilesResponse,
    summary="Update export profiles",
    responses=_ERR,
)
def update_export_profiles(
    project_id: str,
    body: dict[str, Any],
    project_path: Path = Depends(get_project_path),
    svc: ProjectService = Depends(get_project_service),
) -> ExportProfilesResponse:
    """Replace the project's *export_option.json* with the supplied profiles dict."""
    return svc.update_export_profiles(project_path, body)


@router.post(
    "/{project_id}/export-profiles/validate",
    response_model=ExportProfileValidateResponse,
    summary="Validate a single export profile",
    responses=_ERR,
)
def validate_export_profile(
    project_id: str,
    body: ExportProfileValidateRequest,
    project_path: Path = Depends(get_project_path),
    svc: ProjectService = Depends(get_project_service),
) -> ExportProfileValidateResponse:
    """
    Run the BID validator against *body.profile* and return a list of any errors.
    The project directory does not need any existing profiles for this to work.
    """
    return svc.validate_profile(body.name, body.profile)


# ---------------------------------------------------------------------------
# Audit logs
# ---------------------------------------------------------------------------


@router.get(
    "/{project_id}/audit/logs",
    response_model=list[AuditLogEntry],
    summary="Immutable audit log stream",
    responses=_ERR,
)
def get_audit_logs(
    project_id: str,
    project_path: Path = Depends(get_project_path),
    db: Session = Depends(get_db),
    svc: ProjectService = Depends(get_project_service),
    limit: int = Query(default=100, ge=1, le=1000, description="Max records to return."),
    offset: int = Query(default=0, ge=0, description="Pagination offset."),
    action: str | None = Query(default=None, description="Filter by action type."),
    folder: str | None = Query(default=None, description="Filter by folder name."),
) -> list[AuditLogEntry]:
    """
    Return the immutable audit trail for a project, newest first.

    Filterable by `action` (e.g. `state_change`, `metadata_update`) and `folder`.
    Supports pagination via `limit` / `offset`.
    """
    return svc.get_audit_logs(
        db, project_id, limit=limit, offset=offset, action=action, folder=folder
    )
