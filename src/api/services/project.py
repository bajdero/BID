"""
src/api/services/project.py
ProjectService — CRUD for project directories and their config files (P1-03).

Wraps bid.project_manager.ProjectManager and bid.validators, adding:
- REST-safe error handling (no SystemExit, raises HTTPException-friendly errors).
- SQLite audit-log queries.
"""
from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from bid.config import load_export_options, load_settings
from bid.validators import validate_export_profile
from src.api.config import settings
from src.api.models.audit import AuditLog
from src.api.schemas.projects import (
    AuditLogEntry,
    ExportProfileValidateResponse,
    ExportProfilesResponse,
    ProjectCreate,
    ProjectInfo,
    ProjectSettings,
)

logger = logging.getLogger("BID.api")


def _load_json_safe(path: Path) -> dict:
    """Read a JSON file; return empty dict on any error."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _project_info(project_path: Path) -> ProjectInfo:
    """Build a ProjectInfo from a project directory path."""
    pid = project_path.name

    # Load settings to get source/export folder values.
    raw = _load_json_safe(project_path / "settings.json")
    source_folder = raw.get("source_folder", "")
    export_folder = raw.get("export_folder", "")

    # Last-modified from settings.json mtime.
    try:
        mtime = (project_path / "settings.json").stat().st_mtime
        last_modified = datetime.fromtimestamp(mtime).strftime("%Y-%m-%dT%H:%M:%S")
    except Exception:
        last_modified = ""

    # Photo count from source_dict.json (legacy) or SQLite record count.
    photo_count = 0
    source_dict = project_path / "source_dict.json"
    if source_dict.exists():
        try:
            data = json.loads(source_dict.read_text(encoding="utf-8"))
            for folder in data.values():
                if isinstance(folder, dict):
                    photo_count += len(folder)
        except Exception:
            pass

    return ProjectInfo(
        id=pid,
        name=pid.replace("_", " "),
        path=str(project_path),
        last_modified=last_modified,
        photo_count=photo_count,
        source_folder=source_folder,
        export_folder=export_folder,
    )


class ProjectService:
    """
    Stateless service for project directory management.
    A new instance is safe to create per-request.
    """

    # ------------------------------------------------------------------
    # Listing and retrieval
    # ------------------------------------------------------------------

    def list_projects(self) -> list[ProjectInfo]:
        """Return a ProjectInfo for every sub-directory in PROJECTS_DIR."""
        projects_dir = settings.PROJECTS_DIR
        if not projects_dir.exists():
            return []
        return [
            _project_info(p)
            for p in sorted(projects_dir.iterdir())
            if p.is_dir()
        ]

    def get_project(self, project_id: str) -> ProjectInfo:
        """Return project details; raises FileNotFoundError if not found."""
        project_path = settings.PROJECTS_DIR / project_id
        if not project_path.exists():
            raise FileNotFoundError(project_id)
        return _project_info(project_path)

    # ------------------------------------------------------------------
    # Create / delete
    # ------------------------------------------------------------------

    def create_project(self, body: ProjectCreate) -> ProjectInfo:
        """
        Create a new project directory with settings.json and export_option.json.
        Raises FileExistsError if a project with the same normalized name exists.
        """
        pid = body.name.replace(" ", "_")
        project_path = settings.PROJECTS_DIR / pid

        if project_path.exists():
            raise FileExistsError(f"Project '{pid}' already exists.")

        settings.PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        project_path.mkdir(parents=True)

        settings_data = {
            "source_folder": body.source_folder,
            "export_folder": body.export_folder,
        }
        _write_json(project_path / "settings.json", settings_data)
        _write_json(project_path / "export_option.json", body.export_profiles)

        logger.info(f"[PROJECT] Created project '{pid}' → {project_path}")
        return _project_info(project_path)

    def delete_project(self, project_id: str) -> None:
        """
        Remove the project directory from disk.
        Raises FileNotFoundError if the project does not exist.
        """
        project_path = settings.PROJECTS_DIR / project_id
        if not project_path.exists():
            raise FileNotFoundError(project_id)
        shutil.rmtree(project_path)
        logger.info(f"[PROJECT] Deleted project '{project_id}'")

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def get_settings(self, project_path: Path) -> ProjectSettings:
        """Load and return settings.json for the project."""
        raw = _load_json_safe(project_path / "settings.json")
        return ProjectSettings(
            source_folder=raw.get("source_folder", ""),
            export_folder=raw.get("export_folder", ""),
        )

    def update_settings(self, project_path: Path, update: ProjectSettings) -> ProjectSettings:
        """Overwrite settings.json with new values."""
        data = update.model_dump()
        existing = _load_json_safe(project_path / "settings.json")
        existing.update(data)
        _write_json(project_path / "settings.json", existing)
        logger.info(f"[PROJECT] Updated settings for {project_path.name}")
        return self.get_settings(project_path)

    # ------------------------------------------------------------------
    # Export profiles
    # ------------------------------------------------------------------

    def get_export_profiles(self, project_path: Path) -> ExportProfilesResponse:
        """Load export_option.json and return as a typed response."""
        raw = _load_json_safe(project_path / "export_option.json")
        # Validate shape loosely — unknown keys are kept as-is.
        return ExportProfilesResponse(profiles=raw)  # type: ignore[arg-type]

    def update_export_profiles(
        self, project_path: Path, profiles: dict
    ) -> ExportProfilesResponse:
        """Overwrite export_option.json with the new profiles dict."""
        _write_json(project_path / "export_option.json", profiles)
        logger.info(f"[PROJECT] Updated export profiles for {project_path.name}")
        return self.get_export_profiles(project_path)

    def validate_profile(
        self, name: str, profile: dict
    ) -> ExportProfileValidateResponse:
        """Run bid.validators.validate_export_profile() and return structured result."""
        errors = validate_export_profile(name, profile)
        return ExportProfileValidateResponse(valid=len(errors) == 0, errors=errors)

    # ------------------------------------------------------------------
    # Audit logs
    # ------------------------------------------------------------------

    def get_audit_logs(
        self,
        db: Session,
        project_id: str,
        *,
        limit: int = 500,
        offset: int = 0,
        action: str | None = None,
        folder: str | None = None,
    ) -> list[AuditLogEntry]:
        """Query audit logs for *project_id* with optional filters."""
        q = db.query(AuditLog).filter(AuditLog.project_id == project_id)
        if action:
            q = q.filter(AuditLog.action == action)
        if folder:
            q = q.filter(AuditLog.folder == folder)
        rows = q.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
        return [
            AuditLogEntry(
                id=row.id,
                project_id=row.project_id,
                folder=row.folder,
                filename=row.filename,
                action=row.action,
                old_value=row.old_value,
                new_value=row.new_value,
                timestamp=row.timestamp.isoformat() if row.timestamp else "",
                user_id=row.user_id,
            )
            for row in rows
        ]
