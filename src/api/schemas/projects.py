"""
src/api/schemas/projects.py
Pydantic request/response schemas for the project management API (P1-03).

Mirrors the data structures in web_architecture.md §2.1.1 and §2.2.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Export profiles
# ---------------------------------------------------------------------------


class LogoOrientationSettings(BaseModel):
    size: int = Field(ge=10, le=2000, description="Logo width in pixels.")
    opacity: int = Field(ge=0, le=100, description="Opacity 0–100.")
    x_offset: int = Field(ge=0, description="Horizontal offset in pixels.")
    y_offset: int = Field(ge=0, description="Vertical offset in pixels.")
    placement: Literal["top-left", "top-right", "bottom-left", "bottom-right"] = (
        "bottom-right"
    )


class ExportProfile(BaseModel):
    """Full export-profile definition (mirrors bid.validators constraints)."""

    size_type: Literal["longer", "width", "height", "shorter"]
    size: int = Field(ge=100, le=10000, description="Target size in pixels.")
    format: Literal["JPEG", "PNG"]
    quality: int = Field(ge=1, le=100, description="JPEG quality 1–100.")
    ratio: list[float] | None = Field(
        default=None,
        description="Allowed aspect-ratio range [min, max].",
    )
    logo: dict[str, LogoOrientationSettings] | None = None
    logo_required: bool = False

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "size_type": "longer",
                "size": 1200,
                "format": "JPEG",
                "quality": 85,
                "ratio": None,
                "logo": {
                    "landscape": {
                        "size": 200,
                        "opacity": 60,
                        "x_offset": 10,
                        "y_offset": 10,
                        "placement": "bottom-right",
                    }
                },
                "logo_required": False,
            }
        }
    )


class ExportProfilesResponse(BaseModel):
    """Response for GET /export-profiles — maps profile name → profile definition."""

    profiles: dict[str, ExportProfile]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "profiles": {
                    "web": {
                        "size_type": "longer",
                        "size": 800,
                        "format": "JPEG",
                        "quality": 80,
                        "logo": None,
                        "logo_required": False,
                    }
                }
            }
        }
    )


class ExportProfileValidateRequest(BaseModel):
    """Body for POST /export-profiles/validate."""

    name: str = Field(..., min_length=1, description="Profile key name.")
    profile: dict[str, Any] = Field(..., description="Raw profile dict to validate.")


class ExportProfileValidateResponse(BaseModel):
    """Validation result for a single export profile."""

    valid: bool
    errors: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Project settings
# ---------------------------------------------------------------------------


class ProjectSettings(BaseModel):
    """Mirrors the settings.json file structure."""

    source_folder: str = Field(..., description="Absolute path to the source image folder.")
    export_folder: str = Field(..., description="Absolute path to the export destination.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_folder": "/data/source/my_project",
                "export_folder": "/data/export/my_project",
            }
        }
    )


# ---------------------------------------------------------------------------
# Project CRUD
# ---------------------------------------------------------------------------


class ProjectInfo(BaseModel):
    """Summary record for one project — returned in list and detail responses."""

    id: str = Field(..., description="Project directory name (URL-safe identifier).")
    name: str = Field(..., description="Human-readable project name.")
    path: str = Field(..., description="Absolute path on disk.")
    last_modified: str = Field(..., description="ISO-formatted last-modification time.")
    photo_count: int = Field(default=0, description="Number of indexed photos.")
    source_folder: str = Field(default="", description="Configured source folder path.")
    export_folder: str = Field(default="", description="Configured export folder path.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "my_project",
                "name": "my project",
                "path": "/data/projects/my_project",
                "last_modified": "2026-03-23T15:00:00",
                "photo_count": 142,
                "source_folder": "/data/source/my_project",
                "export_folder": "/data/export/my_project",
            }
        }
    )


class ProjectCreate(BaseModel):
    """Body for POST /projects."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=r"^[a-zA-Z0-9 _\-]+$",
        description="Project display name (only letters, digits, spaces, underscores, hyphens).",
    )
    source_folder: str = Field(..., description="Absolute path to the source folder.")
    export_folder: str = Field(..., description="Absolute path to the export folder.")
    export_profiles: dict[str, Any] = Field(
        default_factory=dict,
        description="Initial export profile definitions.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Conference 2026",
                "source_folder": "/data/source/conference2026",
                "export_folder": "/data/export/conference2026",
                "export_profiles": {},
            }
        }
    )


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------


class AuditLogEntry(BaseModel):
    """Single audit log record returned by GET /audit/logs."""

    id: int
    project_id: str
    folder: str
    filename: str
    action: str
    old_value: str | None = None
    new_value: str | None = None
    timestamp: str
    user_id: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "project_id": "my_project",
                "folder": "Session1",
                "filename": "IMG_001.jpg",
                "action": "state_change",
                "old_value": "new",
                "new_value": "ok",
                "timestamp": "2026-03-23T15:30:00",
                "user_id": None,
            }
        }
    )
