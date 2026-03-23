"""
src/api/schemas/processing.py
Pydantic models for the image-processing endpoints.

Schemas are derived from web_architecture.md §2.3.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProcessRequest(BaseModel):
    """
    Body for POST /projects/{id}/process.

    photos: list of (folder, photo) tuples identifying the source photos to process.
    profiles: optional allowlist of export profile keys.  None means all profiles.
    """

    photos: list[tuple[str, str]] = Field(
        ...,
        description="List of (folder, photo) pairs to process.",
        min_length=1,
    )
    profiles: list[str] | None = Field(
        default=None,
        description="Export profile keys to apply.  None = all profiles.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "photos": [
                    ["Session1", "IMG_001.jpg"],
                    ["Session1", "IMG_002.jpg"],
                ],
                "profiles": ["fb", "print"],
            }
        }
    )


class ProcessResponse(BaseModel):
    """Returned immediately after photos are enqueued (non-blocking)."""

    task_id: str
    queued: int
    skipped: int = 0
    message: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "a3f1b2c4-5d6e-7f8a-9b0c-1d2e3f4a5b6c",
                "queued": 2,
                "skipped": 0,
                "message": "2 photo(s) enqueued for processing.",
            }
        }
    )


class PhotoTaskStatus(BaseModel):
    """Status snapshot of a single in-flight processing task."""

    folder: str
    photo: str
    state: Literal["processing", "queued"] = "processing"
    profile: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "folder": "Session1",
                "photo": "IMG_001.jpg",
                "state": "processing",
                "profile": "fb",
            }
        }
    )


class ProcessStatusResponse(BaseModel):
    """Current state of the processing queue for a project."""

    queue_length: int
    active: list[PhotoTaskStatus]
    completed: int = 0
    failed: int = 0

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "queue_length": 1,
                "active": [
                    {
                        "folder": "Session1",
                        "photo": "IMG_001.jpg",
                        "state": "processing",
                        "profile": "fb",
                    }
                ],
                "completed": 5,
                "failed": 0,
            }
        }
    )


class ProcessResult(BaseModel):
    """Result produced by a single completed photo-processing task."""

    success: bool
    # Keys are export profile names; values are paths relative to export_folder.
    exported: dict[str, str] = Field(default_factory=dict)
    duration_sec: float = 0.0
    error_msg: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "exported": {
                    "fb": "fb/Session1/YAPA2026-03-23_Session1_IMG_001.jpg"
                },
                "duration_sec": 1.42,
                "error_msg": None,
            }
        }
    )
