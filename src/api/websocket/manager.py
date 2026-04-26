"""
src/api/websocket/manager.py
ConnectionManager — per-project WebSocket connection registry and broadcast helper.

Design:
- Connections are stored as ``dict[project_id, set[WebSocket]]``.
- ``broadcast_to_project`` fans out a JSON payload to every live socket for a
  project; stale sockets are silently removed on send failure.
- ``broadcast_all`` fans out to every connected socket regardless of project.
- Thread-safety: all access happens inside the asyncio event loop, so an
  asyncio.Lock is used instead of threading.Lock.
- The module exposes a singleton (``get_manager`` / ``set_manager``) that
  mirrors the ProcessingService pattern already established in Phase 1.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("BID.api.websocket")

# ---------------------------------------------------------------------------
# Singleton management (mirrors ProcessingService pattern)
# ---------------------------------------------------------------------------

_manager_instance: "ConnectionManager | None" = None


def get_manager() -> "ConnectionManager":
    """Return the application-singleton ConnectionManager.

    Raises RuntimeError if called before the FastAPI lifespan handler has
    called ``set_manager()``.
    """
    if _manager_instance is None:
        raise RuntimeError(
            "ConnectionManager has not been initialised. "
            "Call set_manager() during application startup."
        )
    return _manager_instance


def set_manager(mgr: "ConnectionManager") -> None:
    """Register the singleton instance (called from the FastAPI lifespan handler)."""
    global _manager_instance
    _manager_instance = mgr


# ---------------------------------------------------------------------------
# ConnectionManager class
# ---------------------------------------------------------------------------


class ConnectionManager:
    """Registry of active WebSocket connections, scoped by project_id.

    Typical lifecycle:
        startup  → ConnectionManager() registered via set_manager()
        connect  → await manager.connect(ws, project_id)
        event    → await manager.broadcast_to_project(project_id, payload)
        event    → await manager.broadcast_all(payload)
        disconnect → manager.disconnect(ws, project_id)
    """

    def __init__(self) -> None:
        # project_id → set of live WebSocket connections
        self._connections: dict[str, set[WebSocket]] = {}
        # websocket → subscribed folder names (None = all folders)
        self._subscriptions: dict[WebSocket, set[str] | None] = {}
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(self, websocket: WebSocket, project_id: str) -> None:
        """Accept *websocket* and register it under *project_id*."""
        await websocket.accept()
        async with self._lock:
            self._connections.setdefault(project_id, set()).add(websocket)
            self._subscriptions[websocket] = None  # default: all folders
        logger.info(
            f"[WS] Client connected — project={project_id!r}  "
            f"total={self._count()}"
        )

    def disconnect(self, websocket: WebSocket, project_id: str) -> None:
        """Remove *websocket* from the registry (synchronous, safe to call from finally)."""
        project_sockets = self._connections.get(project_id)
        if project_sockets is not None:
            project_sockets.discard(websocket)
            if not project_sockets:
                self._connections.pop(project_id, None)
        self._subscriptions.pop(websocket, None)
        logger.info(
            f"[WS] Client disconnected — project={project_id!r}  "
            f"remaining={self._count()}"
        )

    def update_subscription(
        self, websocket: WebSocket, folders: set[str] | None
    ) -> None:
        """Update the folder-subscription filter for *websocket*.

        *folders* is a non-empty set of folder names the client wants to
        receive updates for.  Pass ``None`` to subscribe to all folders
        (the default on first connect and when an empty list is received).
        """
        self._subscriptions[websocket] = folders
    # ------------------------------------------------------------------

    async def broadcast_to_project(
        self,
        project_id: str,
        payload: dict[str, Any],
    ) -> None:
        """Send *payload* as JSON text to all connections for *project_id*.

        Dead sockets are removed silently on send failure.
        """
        sockets = set(self._connections.get(project_id, set()))
        if not sockets:
            return

        dead: list[WebSocket] = []
        for ws in sockets:
            try:
                import json
                # Respect per-socket folder subscription filter.
                # If the socket is subscribed to specific folders and the payload
                # carries a "folder" key that is not in the subscription, skip it.
                sub = self._subscriptions.get(ws)
                if (
                    sub is not None
                    and "folder" in payload
                    and payload["folder"] not in sub
                ):
                    continue
                await ws.send_text(json.dumps(payload))
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.disconnect(ws, project_id)

    async def broadcast_all(self, payload: dict[str, Any]) -> None:
        """Send *payload* as JSON text to every connected client.

        Dead sockets are removed silently on send failure.
        """
        import json
        data = json.dumps(payload)
        dead: list[tuple[WebSocket, str]] = []

        for project_id, sockets in list(self._connections.items()):
            for ws in set(sockets):
                try:
                    await ws.send_text(data)
                except Exception:
                    dead.append((ws, project_id))

        for ws, project_id in dead:
            self.disconnect(ws, project_id)

    # ------------------------------------------------------------------
    # Metrics helpers
    # ------------------------------------------------------------------

    def connection_count(self, project_id: str | None = None) -> int:
        """Return number of active connections, optionally scoped to *project_id*."""
        if project_id is not None:
            return len(self._connections.get(project_id, set()))
        return self._count()

    def has_connections(self, project_id: str | None = None) -> bool:
        """Return True when at least one client is connected."""
        return self.connection_count(project_id) > 0

    def _count(self) -> int:
        return sum(len(sockets) for sockets in self._connections.values())
