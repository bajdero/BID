"""
src/api/models/source.py
PhotoRecord ORM model — persists per-photo processing state and metadata.

Path rules:
- `folder`   : directory name relative to the project source_folder root
                (e.g. "Session1")
- `filename` : bare filename (e.g. "IMG_001.jpg")
- `path_rel` : folder/filename joined with forward slash
                (e.g. "Session1/IMG_001.jpg") — relative to source_folder
- `exported` : JSON dict mapping profile name → path relative to export_folder
                (e.g. {"fb": "fb/YAPA2026-03-23_Session1_IMG_001.jpg"})
All absolute paths are resolved at runtime from the project's settings.json.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.api.models.database import Base


def _utcnow() -> datetime:
    """Return current UTC time as a naive datetime (SQLite-compatible)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class PhotoRecord(Base):
    __tablename__ = "photo_records"

    __table_args__ = (
        # Composite unique key: one record per photo per project.
        UniqueConstraint("project_id", "folder", "filename", name="uq_photo_project"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(256), nullable=False, index=True)

    # ---- Path components (all relative) -------------------------------------
    folder: Mapped[str] = mapped_column(String(512), nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    # Combined convenience column — kept in sync with folder/filename.
    path_rel: Mapped[str] = mapped_column(String(1024), nullable=False, default="")

    # ---- Identity -----------------------------------------------------------
    # SHA-256 hex digest of the source file content (web_architecture §2.1.2).
    hash_id: Mapped[str] = mapped_column(String(64), nullable=False, default="", index=True)

    # ---- Processing state ---------------------------------------------------
    # Valid values match bid.source_manager.SourceState constants.
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="new", index=True)

    # ---- JSON columns (stored as text, accessed via properties) -------------
    # Backing columns use leading-underscore names; the column name in SQL is
    # the unprefixed name, set by the first positional arg to mapped_column().
    _exported: Mapped[str] = mapped_column(
        "exported", Text, nullable=False, default="{}"
    )
    _tags: Mapped[str] = mapped_column(
        "tags", Text, nullable=False, default="[]"
    )
    _exif_data: Mapped[str] = mapped_column(
        "exif_data", Text, nullable=False, default="{}"
    )

    # ---- Scalar metadata ----------------------------------------------------
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    size_display: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_date: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    mtime: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # ---- Processing results -------------------------------------------------
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_sec: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ---- Event system integration -------------------------------------------
    event_folder: Mapped[str | None] = mapped_column(String(512), nullable=True)
    event_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    event_name: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # ---- Timestamps ---------------------------------------------------------
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow
    )

    # =========================================================================
    # JSON property helpers — transparent serialisation/deserialisation
    # =========================================================================

    @property
    def exported(self) -> dict[str, str]:
        try:
            return json.loads(self._exported)
        except (ValueError, TypeError):
            return {}

    @exported.setter
    def exported(self, value: dict[str, str]) -> None:
        self._exported = json.dumps(value, ensure_ascii=False)

    @property
    def tags(self) -> list[str]:
        try:
            return json.loads(self._tags)
        except (ValueError, TypeError):
            return []

    @tags.setter
    def tags(self, value: list[str]) -> None:
        self._tags = json.dumps(value, ensure_ascii=False)

    @property
    def exif_data(self) -> dict[str, str]:
        try:
            return json.loads(self._exif_data)
        except (ValueError, TypeError):
            return {}

    @exif_data.setter
    def exif_data(self, value: dict[str, str]) -> None:
        self._exif_data = json.dumps(value, ensure_ascii=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PhotoRecord {self.project_id}:{self.folder}/{self.filename} [{self.state}]>"
