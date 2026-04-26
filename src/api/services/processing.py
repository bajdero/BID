"""
src/api/services/processing.py
ProcessingService — wraps bid.image_processing.process_photo_task() and manages
the in-process async task queue.

Concurrency model:
- Each HTTP request enqueues asyncio Tasks via asyncio.create_task().
- An asyncio.Semaphore limits how many tasks execute simultaneously.
- The CPU-bound PIL work runs inside a ThreadPoolExecutor so the event loop
  stays responsive.
- Each background task opens its own SQLAlchemy session so the request-scope
  session can be closed immediately after enqueueing.

Security:
- Path traversal protection: folder/filename components are validated before
  any filesystem access (web_architecture.md §4.2).
- Photo paths are resolved with Path.resolve() and checked with is_relative_to()
  to ensure they stay inside the declared source_folder.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from bid.config import load_export_options, load_settings
from bid.image_processing import process_photo_task
from src.api.models.database import SessionLocal
from src.api.models.source import PhotoRecord
from src.api.path_utils import PathTraversalError, resolve_within, validate_path_component
from src.api.schemas.processing import (
    PhotoTaskStatus,
    ProcessResponse,
    ProcessStatusResponse,
)
from src.api.services.source import get_or_create_record, set_state

# Forward reference: imported lazily inside methods to avoid circular imports
# with the websocket package (websocket.manager imports nothing from services).
if TYPE_CHECKING:  # noqa: F821
    from src.api.websocket.manager import ConnectionManager

logger = logging.getLogger("BID.api")


def _make_relative_exports(
    abs_exports: dict[str, str], export_folder: Path
) -> dict[str, str]:
    """Convert absolute export paths to paths relative to *export_folder*.

    Paths that cannot be made relative (i.e. they fall outside export_folder)
    are silently skipped to prevent absolute paths from being persisted in the
    database, which would later allow arbitrary filesystem probing.
    """
    rel: dict[str, str] = {}
    export_folder_resolved = export_folder.resolve()
    for profile, abs_path in abs_exports.items():
        try:
            resolved = Path(abs_path).resolve()
            if not resolved.is_relative_to(export_folder_resolved):
                logger.warning(
                    f"[PROCESS] Export path {abs_path!r} is not within "
                    f"export_folder {export_folder!r}; skipping profile {profile!r}."
                )
                continue
            rel[profile] = str(resolved.relative_to(export_folder_resolved))
        except (ValueError, OSError):
            logger.warning(
                f"[PROCESS] Could not make {abs_path!r} relative to "
                f"{export_folder!r}; skipping profile {profile!r}."
            )
    return rel


# ── Singleton management ──────────────────────────────────────────────────────

_service_instance: ProcessingService | None = None


def get_service() -> "ProcessingService":
    """Return the application-singleton ProcessingService.  Must be initialised first."""
    if _service_instance is None:
        raise RuntimeError(
            "ProcessingService has not been initialised.  "
            "Call set_service() during application startup."
        )
    return _service_instance


def set_service(svc: "ProcessingService") -> None:
    """Register the singleton instance (called from the FastAPI lifespan handler)."""
    global _service_instance
    _service_instance = svc


# ── Service class ─────────────────────────────────────────────────────────────


class ProcessingService:
    """
    Thread-safe service for enqueueing and executing photo-processing tasks.

    Typical lifecycle:
      startup  → ProcessingService(max_workers=N)  (registered via set_service)
      request  → await service.enqueue_photos(...)
      request  → service.get_status(...)
      request  → await service.reset_photo(...)
      shutdown → service.shutdown()
    """

    def __init__(self, max_workers: int = 5) -> None:
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="bid-worker",
        )
        self._sem = asyncio.Semaphore(max_workers)
        self._max_workers = max_workers
        # active tasks keyed by "{project_id}:{folder}/{photo}"
        self._active: dict[str, dict[str, Any]] = {}
        self._queued: int = 0  # tasks created but not yet through the semaphore
        self._completed: int = 0
        self._failed: int = 0
        # Optional ConnectionManager — set post-init from main.py lifespan.
        # Kept optional to allow ProcessingService to be instantiated in tests
        # without a running WebSocket layer.
        self._ws_manager: "ConnectionManager | None" = None
        self._metrics_task: asyncio.Task | None = None

    def set_ws_manager(self, manager: "ConnectionManager") -> None:
        """Register the ConnectionManager for WebSocket broadcasting.

        Called from the FastAPI lifespan handler after both services have been
        initialised.  Once set, processing events are broadcast to connected
        WebSocket clients in real time.
        """
        self._ws_manager = manager
        if self._metrics_task is None or self._metrics_task.done():
            self._metrics_task = asyncio.create_task(self._broadcast_metrics_loop())
            logger.info("[PROCESS] WebSocket manager registered; metrics loop started.")

    def shutdown(self) -> None:
        """Gracefully shut down the thread pool (called on app shutdown)."""
        if self._metrics_task is not None:
            self._metrics_task.cancel()
        self._executor.shutdown(wait=False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def enqueue_photos(
        self,
        project_id: str,
        project_path: Path,
        photos: list[tuple[str, str]],
        profiles: list[str] | None,
        db: Session,
    ) -> ProcessResponse:
        """
        Validate *photos* and submit them to the processing queue.

        Returns immediately with a ProcessResponse; actual processing runs
        as background asyncio Tasks.
        """
        settings_data = load_settings(project_path / "settings.json")
        source_folder = Path(settings_data["source_folder"])
        export_folder = Path(settings_data["export_folder"])

        all_profiles = load_export_options(project_path / "export_option.json")
        export_settings: dict[str, Any] = (
            {k: v for k, v in all_profiles.items() if k in profiles}
            if profiles is not None
            else all_profiles
        )

        queued = 0
        skipped = 0

        for folder, photo in photos:
            validate_path_component(folder)  # raises PathTraversalError on bad input
            validate_path_component(photo)

            photo_abs = resolve_within(source_folder, folder, photo)
            if not photo_abs.exists():
                logger.warning(f"[PROCESS] Source photo not found: {photo_abs}")
                skipped += 1
                continue

            record = get_or_create_record(
                db, project_id, folder, photo, photo_abs, source_folder
            )
            if record.state == "processing":
                skipped += 1
                continue

            old_state = record.state  # capture actual state before the transition
            set_state(db, record, "processing")
            db.flush()
            record_id: int = record.id  # capture before commit frees the session

            self._queued += 1
            asyncio.create_task(
                self._task_runner(
                    record_id=record_id,
                    project_id=project_id,
                    folder=folder,
                    photo=photo,
                    photo_abs=photo_abs,
                    export_folder=export_folder,
                    export_settings=export_settings,
                    existing_exports=record.exported.copy(),
                    event_folder=record.event_folder,
                    created_date=record.created_date,
                    old_state=old_state,
                )
            )
            queued += 1

        db.commit()

        task_batch_id = str(uuid.uuid4())
        return ProcessResponse(
            task_id=task_batch_id,
            queued=queued,
            skipped=skipped,
            message=f"Queued {queued} photo(s) for processing.",
        )

    async def enqueue_all_new(
        self,
        project_id: str,
        project_path: Path,
        db: Session,
    ) -> ProcessResponse:
        """
        Scan the project source_folder for image files not yet processed
        (state == "new", "export_fail", or "error") and enqueue them.
        """
        settings_data = load_settings(project_path / "settings.json")
        source_folder = Path(settings_data["source_folder"])

        image_extensions = {
            ".jpg", ".jpeg", ".tif", ".tiff", ".png", ".heic", ".heif",
        }

        photos: list[tuple[str, str]] = []
        if source_folder.exists():
            for folder_dir in sorted(source_folder.iterdir()):
                if not folder_dir.is_dir():
                    continue
                for img_file in sorted(folder_dir.iterdir()):
                    if img_file.suffix.lower() not in image_extensions:
                        continue
                    if not img_file.is_file():
                        continue
                    existing = (
                        db.query(PhotoRecord)
                        .filter_by(
                            project_id=project_id,
                            folder=folder_dir.name,
                            filename=img_file.name,
                        )
                        .first()
                    )
                    if existing and existing.state not in ("new", "export_fail", "error"):
                        continue
                    photos.append((folder_dir.name, img_file.name))

        if not photos:
            return ProcessResponse(
                task_id="none",
                queued=0,
                skipped=0,
                message="No photos eligible for processing.",
            )

        return await self.enqueue_photos(project_id, project_path, photos, None, db)

    def get_status(self, project_id: str) -> ProcessStatusResponse:
        """Return a snapshot of the processing queue for *project_id*."""
        active_list = [
            PhotoTaskStatus(folder=info["folder"], photo=info["photo"])
            for key, info in self._active.items()
            if info["project_id"] == project_id
        ]
        return ProcessStatusResponse(
            queue_length=self._queued,
            active=active_list,
            completed=self._completed,
            failed=self._failed,
        )

    def get_global_metrics(self) -> dict:
        """
        Return aggregate metrics across all projects.

        Used by GET /api/v1/metrics/queue.
        """
        return {
            "queue_length": self._queued,
            "active_workers": len(self._active),
            "max_workers": self._max_workers,
            "completed_total": self._completed,
            "failed_total": self._failed,
        }

    async def reset_photo(
        self,
        project_id: str,
        folder: str,
        photo: str,
        db: Session,
    ) -> bool:
        """
        Reset a photo's state to "new" so it will be re-queued on the next
        process/all call.  Returns False if the record does not exist.
        """
        validate_path_component(folder)
        validate_path_component(photo)

        record = (
            db.query(PhotoRecord)
            .filter_by(project_id=project_id, folder=folder, filename=photo)
            .first()
        )
        if record is None:
            return False

        set_state(db, record, "new")
        db.commit()
        return True

    # ------------------------------------------------------------------
    # Background task runner (private)
    # ------------------------------------------------------------------

    async def _broadcast_metrics_loop(self) -> None:
        """Broadcast queue_metrics to all connected clients every 5 seconds.

        Only fires when a ConnectionManager is registered and at least one
        client is connected, to avoid unnecessary work during idle periods.
        """
        from src.api.websocket.schemas import QueueMetricsMessage

        while True:
            try:
                await asyncio.sleep(5)
                if self._ws_manager is None or not self._ws_manager.has_connections():
                    continue
                msg = QueueMetricsMessage(**self.get_global_metrics())
                await self._ws_manager.broadcast_all(msg.model_dump())
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("[PROCESS] Error in metrics broadcast loop")

    async def _task_runner(
        self,
        *,
        record_id: int,
        project_id: str,
        folder: str,
        photo: str,
        photo_abs: Path,
        export_folder: Path,
        export_settings: dict[str, Any],
        existing_exports: dict[str, str],
        event_folder: str | None,
        created_date: str,
        old_state: str,
    ) -> None:
        """
        Semaphore-gated coroutine that runs process_photo_task() in a thread
        and writes results back to SQLite using a fresh DB session.
        """
        task_key = f"{project_id}:{folder}/{photo}"

        async with self._sem:
            self._queued -= 1  # task is now actively executing, no longer waiting
            self._active[task_key] = {
                "project_id": project_id,
                "folder": folder,
                "photo": photo,
            }
            loop = asyncio.get_event_loop()

            # Broadcast state_change: <old_state> → processing
            if self._ws_manager is not None:
                from src.api.websocket.schemas import StateChangeMessage
                await self._ws_manager.broadcast_to_project(
                    project_id,
                    StateChangeMessage(
                        project_id=project_id,
                        folder=folder,
                        photo=photo,
                        old_state=old_state,
                        new_state="processing",
                    ).model_dump(),
                )

            try:
                # Resolve existing absolute export paths from stored relative paths.
                abs_existing: dict[str, str] = {
                    profile: str(export_folder / rel)
                    for profile, rel in existing_exports.items()
                }

                result: dict[str, Any] = await loop.run_in_executor(
                    self._executor,
                    lambda: process_photo_task(
                        photo_path=str(photo_abs),
                        folder_name=folder,
                        photo_name=photo,
                        created_date=created_date,
                        export_folder=str(export_folder),
                        export_settings=export_settings,
                        existing_exports=abs_existing,
                        event_folder=event_folder,
                    ),
                )

                new_state = "ok" if result.get("success") else "error"
                exported_rel = _make_relative_exports(
                    result.get("exported", {}), export_folder
                )
                duration = result.get("duration", 0.0)
                error_msg = result.get("error_msg")

                # Write result to DB using a dedicated session.
                with SessionLocal() as session:
                    record = session.get(PhotoRecord, record_id)
                    if record is not None:
                        record.exported = exported_rel
                        record.duration_sec = float(duration)
                        record.error_msg = error_msg
                        set_state(session, record, new_state, flush=False)
                        session.commit()

                if result.get("success"):
                    self._completed += 1
                    logger.info(
                        f"[PROCESS] OK: {project_id}:{folder}/{photo}"
                        f" — {len(exported_rel)} export(s) in {duration:.2f}s"
                    )
                    if self._ws_manager is not None:
                        from src.api.websocket.schemas import ProgressMessage
                        await self._ws_manager.broadcast_to_project(
                            project_id,
                            ProgressMessage(
                                project_id=project_id,
                                folder=folder,
                                photo=photo,
                                status="completed",
                                duration_sec=float(duration),
                                exported_paths=exported_rel,
                            ).model_dump(),
                        )
                else:
                    self._failed += 1
                    logger.error(
                        f"[PROCESS] FAILED: {project_id}:{folder}/{photo}"
                        f" — {error_msg}"
                    )
                    if self._ws_manager is not None:
                        from src.api.websocket.schemas import ErrorMessage
                        await self._ws_manager.broadcast_to_project(
                            project_id,
                            ErrorMessage(
                                project_id=project_id,
                                folder=folder,
                                photo=photo,
                                message=error_msg or "Unknown processing error",
                            ).model_dump(),
                        )

            except Exception as exc:
                self._failed += 1
                logger.exception(
                    f"[PROCESS] Unexpected error for {project_id}:{folder}/{photo}: {exc}"
                )
                with SessionLocal() as session:
                    record = session.get(PhotoRecord, record_id)
                    if record is not None:
                        record.error_msg = str(exc)
                        set_state(session, record, "error", flush=False)
                        session.commit()

            finally:
                self._active.pop(task_key, None)
