"""
src/api/routers/sources.py
Source-index read endpoints.

GET  /projects/{project_id}/sources          — full source tree (P4-04)
GET  /projects/{project_id}/sources/{folder}/{photo}  — single photo entry
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.deps import get_db, get_source_service
from src.api.schemas.common import ErrorResponse
from src.api.schemas.source import PhotoEntry, SourceTree
from src.api.services.source import SourceService

_ERR = {
    404: {"model": ErrorResponse, "description": "Project or photo not found."},
}

router = APIRouter(prefix="/projects/{project_id}/sources", tags=["sources"])


@router.get(
    "",
    response_model=SourceTree,
    summary="Get project source tree",
    responses=_ERR,
)
def get_source_tree(
    project_id: str,
    db: Session = Depends(get_db),
    svc: SourceService = Depends(get_source_service),
) -> SourceTree:
    """Return the full folder→photo index for the given project."""
    return svc.get_source_tree(db=db, project_id=project_id)


@router.get(
    "/{folder}/{photo}",
    response_model=PhotoEntry,
    summary="Get a single photo entry",
    responses=_ERR,
)
def get_photo(
    project_id: str,
    folder: str,
    photo: str,
    db: Session = Depends(get_db),
    svc: SourceService = Depends(get_source_service),
) -> PhotoEntry:
    """Return the metadata record for a single source photo."""
    from src.api.services.source import _record_to_entry  # noqa: PLC0415

    record = svc.get_photo(db=db, project_id=project_id, folder=folder, filename=photo)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Photo '{folder}/{photo}' not found in project '{project_id}'.",
        )
    return _record_to_entry(record)
