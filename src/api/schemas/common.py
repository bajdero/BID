"""
src/api/schemas/common.py
Shared Pydantic request/response models used across multiple routers.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    """Standard error envelope returned by exception handlers."""

    detail: str
    field: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"detail": "Project 'my_project' not found.", "field": None}
        }
    )


class HealthResponse(BaseModel):
    status: str = "ok"

    model_config = ConfigDict(json_schema_extra={"example": {"status": "ok"}})


class VersionResponse(BaseModel):
    api_version: str
    bid_version: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"api_version": "1.0.0", "bid_version": "2.0.0-dev"}
        }
    )


class QueueMetricsResponse(BaseModel):
    """Operational metrics for the processing queue."""

    queue_length: int = Field(..., description="Number of tasks currently waiting.")
    active_workers: int = Field(..., description="Tasks actively processing right now.")
    max_workers: int = Field(..., description="Configured concurrency ceiling.")
    completed_total: int = Field(..., description="Tasks completed since last restart.")
    failed_total: int = Field(..., description="Tasks that ended in error since last restart.")
    utilization_pct: float = Field(
        ..., ge=0.0, le=100.0, description="active_workers / max_workers × 100."
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "queue_length": 3,
                "active_workers": 2,
                "max_workers": 5,
                "completed_total": 142,
                "failed_total": 1,
                "utilization_pct": 40.0,
            }
        }
    )


class ConflictItem(BaseModel):
    """A single blocked / missing export entry."""

    profile: str
    folder: str
    photo: str
    # Path relative to the project export_folder (portable across machines).
    target_path: str
    reason: str = "missing_or_empty"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "profile": "fb",
                "folder": "Session1",
                "photo": "IMG_001.jpg",
                "target_path": "fb/Session1/YAPA2026-03-23_Session1_IMG_001.jpg",
                "reason": "missing_or_empty",
            }
        }
    )


class ConflictResolutionRequest(BaseModel):
    """
    Request body for POST /exports/conflicts/resolve.

    mode:
      "all"       – apply action to every conflict in the project.
      "selection" – apply action to the photos listed in `items`.

    action:
      "replace"  – reset state to "new" so the photo is re-queued.
      "skip"     – mark the photo as "skip" (do not process again).
    """

    mode: Literal["all", "selection"]
    action: Literal["replace", "skip"]
    # Required when mode == "selection": list of (folder, photo) tuples.
    items: list[tuple[str, str]] | None = Field(default=None)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mode": "selection",
                "action": "replace",
                "items": [["Session1", "IMG_001.jpg"], ["Session1", "IMG_002.jpg"]],
            }
        }
    )
