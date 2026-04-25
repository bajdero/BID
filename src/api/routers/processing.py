"""
src/api/routers/processing.py
Image-processing pipeline endpoints for a single project.

POST   /projects/{project_id}/process          — enqueue selected photos
POST   /projects/{project_id}/process/all      — enqueue all NEW photos
DELETE /projects/{project_id}/process/{folder}/{photo} — reset photo to NEW
GET    /projects/{project_id}/process/status   — current queue snapshot
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.deps import get_db, get_processing_service, get_project_path
from src.api.schemas.common import ErrorResponse
from src.api.schemas.processing import (
    ProcessRequest,
    ProcessResponse,
    ProcessStatusResponse,
)
from src.api.services.processing import PathTraversalError, ProcessingService

# Shared response spec reused across all processing endpoints.
_ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Bad request — path traversal or invalid input."},
    404: {"model": ErrorResponse, "description": "Project or photo not found."},
    500: {"model": ErrorResponse, "description": "Unexpected server-side processing error."},
}

router = APIRouter(
    prefix="/projects/{project_id}",
    tags=["processing"],
)


@router.post(
    "/process",
    response_model=ProcessResponse,
    status_code=202,
    summary="Enqueue selected photos for processing",
    responses=_ERROR_RESPONSES,
)
async def process_selected(
    project_id: str,
    body: ProcessRequest,
    project_path: Path = Depends(get_project_path),
    db: Session = Depends(get_db),
    svc: ProcessingService = Depends(get_processing_service),
) -> ProcessResponse:
    """
    Validate and enqueue the photos listed in *body.photos*.
    Returns immediately; processing runs in the background.
    """
    try:
        return await svc.enqueue_photos(
            project_id=project_id,
            project_path=project_path,
            photos=body.photos,
            profiles=body.profiles,
            db=db,
        )
    except PathTraversalError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/process/all",
    response_model=ProcessResponse,
    status_code=202,
    summary="Enqueue all NEW photos in the project",
    responses=_ERROR_RESPONSES,
)
async def process_all(
    project_id: str,
    project_path: Path = Depends(get_project_path),
    db: Session = Depends(get_db),
    svc: ProcessingService = Depends(get_processing_service),
) -> ProcessResponse:
    """
    Scan the project source_folder and enqueue every photo whose state is
    ``new``, ``export_fail``, or ``error``.
    """
    return await svc.enqueue_all_new(
        project_id=project_id,
        project_path=project_path,
        db=db,
    )


@router.delete(
    "/process/{folder}/{photo}",
    status_code=200,
    summary="Reset a photo to NEW state (re-queue)",
    responses=_ERROR_RESPONSES,
)
async def reset_photo(
    project_id: str,
    folder: str,
    photo: str,
    project_path: Path = Depends(get_project_path),
    db: Session = Depends(get_db),
    svc: ProcessingService = Depends(get_processing_service),
) -> dict:
    """
    Reset the photo identified by *folder/photo* back to state ``new`` so it
    will be picked up by the next ``process/all`` run.

    Returns HTTP 404 if the photo is not found in the source index.
    """
    try:
        found = await svc.reset_photo(
            project_id=project_id,
            folder=folder,
            photo=photo,
            db=db,
        )
    except PathTraversalError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not found:
        raise HTTPException(
            status_code=404,
            detail=f"Photo '{folder}/{photo}' not found in project '{project_id}'.",
        )
    return {"detail": f"Photo '{folder}/{photo}' reset to 'new'."}


@router.get(
    "/process/status",
    response_model=ProcessStatusResponse,
    summary="Current processing-queue status",
    responses={404: {"model": ErrorResponse, "description": "Project not found."}},
)
async def get_process_status(
    project_id: str,
    project_path: Path = Depends(get_project_path),
    svc: ProcessingService = Depends(get_processing_service),
) -> ProcessStatusResponse:
    """Return a snapshot of the in-flight and completed task counters."""
    return svc.get_status(project_id)
