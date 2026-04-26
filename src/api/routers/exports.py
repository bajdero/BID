"""
src/api/routers/exports.py
Export-conflict management endpoints.

GET  /projects/{project_id}/exports/conflicts        — list blocked exports
POST /projects/{project_id}/exports/conflicts/resolve — resolve conflicts
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.deps import get_db, get_project_path, get_source_service
from src.api.schemas.common import ConflictItem, ConflictResolutionRequest, ErrorResponse
from src.api.services.source import SourceService

_ERROR_RESPONSES = {
    404: {"model": ErrorResponse, "description": "Project not found."},
    500: {"model": ErrorResponse, "description": "Unexpected server error."},
}

router = APIRouter(
    prefix="/projects/{project_id}/exports",
    tags=["exports"],
)


@router.get(
    "/conflicts",
    response_model=list[ConflictItem],
    summary="List blocked / missing export files",
    responses=_ERROR_RESPONSES,
)
def list_conflicts(
    project_id: str,
    project_path: Path = Depends(get_project_path),
    db: Session = Depends(get_db),
    svc: SourceService = Depends(get_source_service),
) -> list[ConflictItem]:
    """
    Return export entries where the expected output file is missing or has
    zero bytes on disk — indicating the photo needs to be re-processed.
    """
    return svc.get_conflicts(db=db, project_id=project_id, project_path=project_path)


@router.post(
    "/conflicts/resolve",
    summary="Resolve export conflicts",
    responses={
        200: {"description": "Number of resolved conflicts and the action applied."},
        **_ERROR_RESPONSES,
    },
)
def resolve_conflicts(
    project_id: str,
    body: ConflictResolutionRequest,
    project_path: Path = Depends(get_project_path),
    db: Session = Depends(get_db),
    svc: SourceService = Depends(get_source_service),
) -> dict:
    """
    Apply *body.action* to the matching conflict records.

    - ``action="replace"`` resets state to ``new`` (re-queues for processing).
    - ``action="skip"``    marks the photo as ``skip``.
    """
    resolved = svc.resolve_conflicts(db=db, project_id=project_id, request=body)
    return {"resolved": resolved, "action": body.action}
