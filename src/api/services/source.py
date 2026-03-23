"""
src/api/services/source.py
SourceService — SQLite CRUD for PhotoRecord and conflict helpers.

Design rules:
- All paths stored/returned as relative strings.
- Absolute resolution uses the project's settings.json at runtime.
- Every state change appends an AuditLog entry.
"""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from bid.config import load_settings
from src.api.models.audit import AuditLog
from src.api.models.source import PhotoRecord
from src.api.schemas.common import ConflictItem, ConflictResolutionRequest
from src.api.schemas.source import PhotoEntry, SourceTree

logger = logging.getLogger("BID.api")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _record_to_entry(record: PhotoRecord) -> PhotoEntry:
    """Convert a PhotoRecord ORM row to the PhotoEntry response schema."""
    return PhotoEntry(
        hash_id=record.hash_id,
        path=record.path_rel,
        state=record.state,  # type: ignore[arg-type]
        exported=record.exported,
        description=record.description,
        tags=record.tags,
        size=record.size_display,
        size_bytes=record.size_bytes,
        created=record.created_date,
        mtime=record.mtime,
        exif=record.exif_data,
        error_msg=record.error_msg,
        duration_sec=record.duration_sec,
        event_folder=record.event_folder,
        event_id=record.event_id,
        event_name=record.event_name,
    )


def _append_audit(
    db: Session,
    project_id: str,
    folder: str,
    filename: str,
    action: str,
    old_value: str | None,
    new_value: str | None,
) -> None:
    entry = AuditLog(
        project_id=project_id,
        folder=folder,
        filename=filename,
        action=action,
        old_value=old_value,
        new_value=new_value,
    )
    db.add(entry)


def set_state(
    db: Session,
    record: PhotoRecord,
    new_state: str,
    *,
    flush: bool = True,
) -> None:
    """Transition a PhotoRecord to a new state and log the change."""
    old_state = record.state
    record.state = new_state
    _append_audit(
        db,
        project_id=record.project_id,
        folder=record.folder,
        filename=record.filename,
        action="state_change",
        old_value=old_state,
        new_value=new_state,
    )
    if flush:
        db.flush()


def compute_hash(path: Path) -> str:
    """Return SHA-256 hex digest for the file at *path* (64-character string)."""
    sha256 = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65_536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_or_create_record(
    db: Session,
    project_id: str,
    folder: str,
    filename: str,
    photo_abs: Path,
    source_folder: Path,
) -> PhotoRecord:
    """
    Return the existing PhotoRecord for (project_id, folder, filename), or create
    a minimal new one populated from the file on disk.
    """
    record = (
        db.query(PhotoRecord)
        .filter_by(project_id=project_id, folder=folder, filename=filename)
        .first()
    )
    if record is not None:
        return record

    stat = photo_abs.stat()
    size_bytes = stat.st_size
    mtime = stat.st_mtime
    size_mb = size_bytes / (1024 * 1024)
    size_display = f"{size_mb:.1f} MB" if size_mb >= 1 else f"{size_bytes / 1024:.0f} KB"

    path_rel = f"{folder}/{filename}"

    # Hash computation is intentionally synchronous — files may be large.
    hash_id = compute_hash(photo_abs)

    record = PhotoRecord(
        project_id=project_id,
        folder=folder,
        filename=filename,
        path_rel=path_rel,
        hash_id=hash_id,
        state="new",
        size_display=size_display,
        size_bytes=size_bytes,
        mtime=mtime,
    )
    db.add(record)
    db.flush()
    logger.debug(f"[SOURCE] Created record {project_id}:{path_rel} hash={hash_id[:8]}")
    return record


# ---------------------------------------------------------------------------
# SourceService
# ---------------------------------------------------------------------------


class SourceService:
    """
    Stateless service encapsulating all source-index DB operations.
    A new instance is safe to create per-request.
    """

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def get_photo(
        self, db: Session, project_id: str, folder: str, filename: str
    ) -> PhotoRecord | None:
        return (
            db.query(PhotoRecord)
            .filter_by(project_id=project_id, folder=folder, filename=filename)
            .first()
        )

    def get_source_tree(self, db: Session, project_id: str) -> SourceTree:
        records = (
            db.query(PhotoRecord).filter_by(project_id=project_id).all()
        )
        folders: dict[str, dict[str, PhotoEntry]] = {}
        for record in records:
            folders.setdefault(record.folder, {})[record.filename] = _record_to_entry(record)
        return SourceTree(folders=folders)

    # ------------------------------------------------------------------
    # Conflict management
    # ------------------------------------------------------------------

    def get_conflicts(
        self, db: Session, project_id: str, project_path: Path
    ) -> list[ConflictItem]:
        """
        Return photos whose state is 'export_fail' or whose exported files
        are missing / zero-byte on disk.
        """
        settings_data = load_settings(project_path / "settings.json")
        export_folder = Path(settings_data["export_folder"])

        records = (
            db.query(PhotoRecord)
            .filter(
                PhotoRecord.project_id == project_id,
                PhotoRecord.state.in_(["ok", "export_fail"]),
            )
            .all()
        )

        conflicts: list[ConflictItem] = []
        for record in records:
            for profile, rel_path in record.exported.items():
                abs_path = export_folder / rel_path
                if not abs_path.exists() or abs_path.stat().st_size == 0:
                    conflicts.append(
                        ConflictItem(
                            profile=profile,
                            folder=record.folder,
                            photo=record.filename,
                            target_path=rel_path,
                            reason="missing_or_empty",
                        )
                    )
        return conflicts

    def resolve_conflicts(
        self,
        db: Session,
        project_id: str,
        request: ConflictResolutionRequest,
    ) -> int:
        """
        Apply *request.action* to matching records and return the count resolved.

        action="replace" → reset state to "new" (re-queue for processing).
        action="skip"    → mark as "skip" (excluded from future runs).
        """
        if request.mode == "all":
            records = (
                db.query(PhotoRecord)
                .filter(
                    PhotoRecord.project_id == project_id,
                    PhotoRecord.state.in_(["ok", "export_fail"]),
                )
                .all()
            )
        elif request.mode == "selection":
            if not request.items:
                return 0
            records = []
            for folder, photo in request.items:
                rec = self.get_photo(db, project_id, folder, photo)
                if rec:
                    records.append(rec)
        else:
            return 0

        new_state = "new" if request.action == "replace" else "skip"
        resolved = 0
        for record in records:
            set_state(db, record, new_state)
            resolved += 1

        db.commit()
        logger.info(
            f"[SOURCE] Resolved {resolved} conflicts in project '{project_id}' "
            f"(action={request.action!r})"
        )
        return resolved
