"""
src/api/websocket/router.py
WebSocket endpoint for real-time event streaming.

Endpoint: GET /api/v1/projects/{project_id}/ws
           (upgraded to WebSocket by the client)

Authentication:
  JWT access token passed as a query parameter:
      ws://host/api/v1/projects/{id}/ws?token=<access_token>

  The browser WebSocket API does not support custom request headers, so the
  query-param pattern is the standard approach for browser-based WS auth.
  The token is validated using the same ``decode_token()`` used by REST routes.

Client → Server messages (JSON):
  {"type": "subscribe", "folders": ["Session1"]}   — subscribe to subset of folders
  {"type": "pong"}                                  — heartbeat response

Server → Client messages:  see src/api/websocket/schemas.py
"""
from __future__ import annotations

import asyncio
import logging
import re

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from jose import JWTError
from sqlalchemy.orm import Session

from src.api.config import settings
from src.api.models.database import SessionLocal
from src.api.models.user import UserRecord
from src.api.services.auth import decode_token
from src.api.websocket.manager import get_manager
from src.api.websocket.schemas import (
    PingMessage,
    ServerClosingMessage,
    parse_client_message,
)

logger = logging.getLogger("BID.api.websocket")

router = APIRouter(tags=["websocket"])

# Project-id safety: same pattern as deps.py get_project_path()
_SAFE_PROJECT_ID_RE = re.compile(r"^[a-zA-Z0-9_\-\.]+$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _authenticate_ws_token(token: str, db: Session) -> UserRecord | None:
    """
    Validate a JWT access token and return the corresponding UserRecord.

    Returns None on any validation failure so the caller can send an
    appropriate close code without raising.
    """
    try:
        payload = decode_token(token)
    except (JWTError, Exception):
        return None

    if payload.get("type") != "access":
        return None

    username: str = payload.get("sub", "")
    user: UserRecord | None = (
        db.query(UserRecord).filter_by(username=username).first()
    )
    if user is None or not user.is_active:
        return None
    return user


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------


@router.websocket("/projects/{project_id}/ws")
async def websocket_project(
    websocket: WebSocket,
    project_id: str,
    token: str = "",
) -> None:
    """
    WebSocket endpoint for real-time project events.

    **Authentication:** Pass the JWT access token as ``?token=<access_token>``.

    **Subscription:** After connecting, optionally send a ``subscribe`` frame to
    receive updates only for specific sub-folders:
    ```json
    {"type": "subscribe", "folders": ["Session1", "Session2"]}
    ```
    An empty ``folders`` list (or omitting the message entirely) means
    *all folders* in the project.

    **Heartbeat:** The server sends ``{"type": "ping"}`` every
    ``WS_HEARTBEAT_INTERVAL`` seconds.  Reply with ``{"type": "pong"}`` to
    keep the connection alive.  Connections that fail to pong within
    ``WS_HEARTBEAT_TIMEOUT`` seconds are closed.
    """
    # ── Validate project_id format ─────────────────────────────────────────
    if not _SAFE_PROJECT_ID_RE.match(project_id):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # ── Authenticate ───────────────────────────────────────────────────────
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    with SessionLocal() as db:
        user = _authenticate_ws_token(token, db)

    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # ── Register connection ────────────────────────────────────────────────
    manager = get_manager()
    await manager.connect(websocket, project_id)

    # Per-connection subscription state:  None = subscribe to all folders
    subscribed_folders: set[str] | None = None

    # Heartbeat tracking: asyncio.Event set by the receive loop on pong receipt
    _pong_received = asyncio.Event()

    # ── Heartbeat coroutine ────────────────────────────────────────────────
    async def _heartbeat() -> None:
        """Send periodic pings and close the connection on missed pong."""
        while True:
            await asyncio.sleep(settings.WS_HEARTBEAT_INTERVAL)
            _pong_received.clear()
            try:
                await websocket.send_text(
                    PingMessage().model_dump_json()
                )
            except Exception:
                break  # socket already dead
            try:
                await asyncio.wait_for(
                    _pong_received.wait(),
                    timeout=settings.WS_HEARTBEAT_TIMEOUT,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    f"[WS] Heartbeat timeout — closing "
                    f"project={project_id!r} user={user.username!r}"
                )
                try:
                    await websocket.close(code=status.WS_1001_GOING_AWAY)
                except Exception:
                    pass
                break

    heartbeat_task = asyncio.create_task(_heartbeat())

    try:
        while True:
            try:
                raw = await websocket.receive_text()
            except WebSocketDisconnect:
                break
            except Exception:
                break

            msg = parse_client_message(raw)
            if msg is None:
                # Ignore unknown or malformed frames — keep connection alive
                continue

            if msg.type == "subscribe":
                if msg.folders:
                    subscribed_folders = set(msg.folders)
                    logger.debug(
                        f"[WS] Subscribe filter updated — "
                        f"project={project_id!r} folders={subscribed_folders!r}"
                    )
                else:
                    # Empty list means subscribe to all
                    subscribed_folders = None

            elif msg.type == "pong":
                _pong_received.set()

    finally:
        heartbeat_task.cancel()
        manager.disconnect(websocket, project_id)
