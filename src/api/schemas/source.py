"""
src/api/schemas/source.py
Pydantic models for source-index responses.

PhotoEntry matches the schema specified in web_architecture.md §2.3.
All paths are relative; absolute resolution happens in the service layer.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# All legal photo states (mirrors bid.source_manager.SourceState).
PhotoState = Literal[
    "downloading",
    "new",
    "processing",
    "ok",
    "ok_old",
    "error",
    "export_fail",
    "deleted",
    "skip",
]


class PhotoEntry(BaseModel):
    """Full metadata record for a single source photo (read response schema)."""

    # Content-based identity (SHA-256 hex digest).
    hash_id: str
    # Relative path from project source_folder (e.g. "Session1/IMG_001.jpg").
    path: str
    state: PhotoState
    # Keys = export profile name; values = paths relative to export_folder.
    exported: dict[str, str] = Field(default_factory=dict)

    description: str = ""
    tags: list[str] = Field(default_factory=list)

    # Human-readable size string and raw byte count.
    size: str = ""
    size_bytes: int = 0

    # EXIF creation date string (e.g. "2026:03:23 15:00:00") and mtime float.
    created: str = ""
    mtime: float = 0.0

    # Flat EXIF/IPTC/XMP dict (tag name → string value).
    exif: dict[str, str] = Field(default_factory=dict)

    # Quality scoring — populated by future ML pipeline.
    quality_score: float | None = None
    quality_model: Literal["exif_rules", "ml"] | None = None

    # Processing result fields.
    error_msg: str | None = None
    duration_sec: float | None = None

    # Event system integration.
    event_folder: str | None = None
    event_id: str | None = None
    event_name: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "hash_id": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
                "path": "Session1/IMG_001.jpg",
                "state": "ok",
                "exported": {
                    "fb": "fb/Session1/YAPA2026-03-23_Session1_IMG_001.jpg"
                },
                "description": "Keynote speaker on stage",
                "tags": ["keynote", "stage"],
                "size": "8.2 MB",
                "size_bytes": 8601600,
                "created": "2026:03:23 15:00:00",
                "mtime": 1742738400.0,
                "exif": {
                    "Make": "Canon",
                    "Model": "EOS R5",
                    "ISO": "800",
                },
                "quality_score": None,
                "quality_model": None,
                "error_msg": None,
                "duration_sec": 1.42,
                "event_folder": "Session1",
                "event_id": "evt-001",
                "event_name": "BID Annual Conference 2026",
            }
        }
    )


class SourceTree(BaseModel):
    """Nested folder → photo mapping for the processing-state panel."""

    # Outer key = folder name; inner key = filename; value = PhotoEntry.
    folders: dict[str, dict[str, PhotoEntry]] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "folders": {
                    "Session1": {
                        "IMG_001.jpg": {
                            "hash_id": "a1b2c3d4...",
                            "path": "Session1/IMG_001.jpg",
                            "state": "ok",
                            "exported": {},
                            "description": "",
                            "tags": [],
                            "size": "8.2 MB",
                            "size_bytes": 8601600,
                            "created": "2026:03:23 15:00:00",
                            "mtime": 1742738400.0,
                            "exif": {},
                            "quality_score": None,
                            "quality_model": None,
                            "error_msg": None,
                            "duration_sec": None,
                            "event_folder": None,
                            "event_id": None,
                            "event_name": None,
                        }
                    }
                }
            }
        }
    )
