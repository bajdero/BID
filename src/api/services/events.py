"""
src/api/services/events.py
EventBroadcastService — wraps bid/events/EventManager for async polling
and broadcasts scan_update messages over WebSocket when the event schedule
changes.

Phase 2 scope: infrastructure only.
  - Detect schedule changes via EventManager.schedules_fingerprint()
  - Broadcast scan_update when the fingerprint changes
  - start_polling / stop_polling API matches future project lifecycle hooks

Full event management UI is deferred to Phase 7 (M9).
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

logger = logging.getLogger("BID.api.events")

# Default polling cadence (seconds) — 5 minutes, matching the desktop app.
_DEFAULT_POLL_INTERVAL = 300


class EventBroadcastService:
    """Polls the bid/events/EventManager on a timer and broadcasts schedule
    changes as WebSocket messages.

    One service instance should be created per-project when event sources are
    configured.  Use :meth:`start_polling` / :meth:`stop_polling` to manage
    the lifecycle.

    The service holds no state between polls; EventManager loads and parses
    sources on each call to ``load_all()``.
    """

    def __init__(self) -> None:
        # project_id → active polling Task
        self._tasks: dict[str, asyncio.Task] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_polling(
        self,
        project_id: str,
        project_path: Path,
        interval_seconds: int = _DEFAULT_POLL_INTERVAL,
    ) -> None:
        """Start a background polling task for *project_id*.

        If a task is already running for this project it is left unchanged
        (idempotent).
        """
        if project_id in self._tasks and not self._tasks[project_id].done():
            return

        task = asyncio.create_task(
            self._poll_loop(project_id, project_path, interval_seconds),
            name=f"event-poll-{project_id}",
        )
        self._tasks[project_id] = task
        logger.info(
            f"[EVENTS] Polling started — project={project_id!r} "
            f"interval={interval_seconds}s"
        )

    def stop_polling(self, project_id: str) -> None:
        """Cancel the polling task for *project_id* (no-op if not running)."""
        task = self._tasks.pop(project_id, None)
        if task is not None and not task.done():
            task.cancel()
            logger.info(f"[EVENTS] Polling stopped — project={project_id!r}")

    def stop_all(self) -> None:
        """Cancel all active polling tasks (called on app shutdown)."""
        for project_id in list(self._tasks):
            self.stop_polling(project_id)

    def is_polling(self, project_id: str) -> bool:
        """Return True if a non-done polling task exists for *project_id*."""
        task = self._tasks.get(project_id)
        return task is not None and not task.done()

    # ------------------------------------------------------------------
    # Background polling coroutine (private)
    # ------------------------------------------------------------------

    async def _poll_loop(
        self,
        project_id: str,
        project_path: Path,
        interval_seconds: int,
    ) -> None:
        """Periodically load event schedules and broadcast scan_update on change."""
        from bid.events.manager import EventManager
        from src.api.websocket.manager import get_manager
        from src.api.websocket.schemas import ScanUpdateMessage

        try:
            manager = EventManager(project_path)
        except Exception as exc:
            logger.warning(
                f"[EVENTS] EventManager init failed for {project_id!r}: {exc}"
            )
            return

        last_fingerprint: frozenset = frozenset()

        while True:
            try:
                await asyncio.sleep(interval_seconds)

                # Run the blocking EventManager.load_all() in the thread pool
                loop = asyncio.get_event_loop()
                try:
                    await loop.run_in_executor(None, manager.load_all)
                except Exception as exc:
                    logger.warning(
                        f"[EVENTS] load_all failed for {project_id!r}: {exc}"
                    )
                    continue

                new_fp = manager.schedules_fingerprint()
                if new_fp == last_fingerprint:
                    continue

                last_fingerprint = new_fp
                logger.info(
                    f"[EVENTS] Schedule changed — broadcasting scan_update "
                    f"project={project_id!r}"
                )

                # Count new/updated items from the loaded schedules
                try:
                    schedules = manager.load_all()
                    updated_folders: list[str] = [
                        s.title for s in schedules if s.title
                    ]
                    new_count = sum(len(s.events) for s in schedules)
                except Exception:
                    updated_folders = []
                    new_count = 0

                try:
                    ws_manager = get_manager()
                    await ws_manager.broadcast_to_project(
                        project_id,
                        ScanUpdateMessage(
                            project_id=project_id,
                            found_new=True,
                            new_count=new_count,
                            updated_folders=updated_folders,
                        ).model_dump(),
                    )
                except RuntimeError:
                    # ConnectionManager not yet initialised (e.g. in tests)
                    pass

            except asyncio.CancelledError:
                logger.info(
                    f"[EVENTS] Poll loop cancelled — project={project_id!r}"
                )
                break
            except Exception:
                logger.exception(
                    f"[EVENTS] Unexpected error in poll loop for {project_id!r}"
                )


# ---------------------------------------------------------------------------
# Module-level singleton (mirrors ProcessingService / ConnectionManager pattern)
# ---------------------------------------------------------------------------

_service_instance: EventBroadcastService | None = None


def get_event_service() -> EventBroadcastService:
    """Return the application-singleton EventBroadcastService."""
    if _service_instance is None:
        raise RuntimeError(
            "EventBroadcastService has not been initialised. "
            "Call set_event_service() during application startup."
        )
    return _service_instance


def set_event_service(svc: EventBroadcastService) -> None:
    """Register the singleton instance (called from the FastAPI lifespan handler)."""
    global _service_instance
    _service_instance = svc
