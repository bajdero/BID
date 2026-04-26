"""
src/api/websocket/schemas.py
Pydantic schemas for all WebSocket message frames (server→client and client→server).

Usage pattern — server sends:
    await ws.send_text(StateChangeMessage(...).model_dump_json())

Usage pattern — server receives and dispatches:
    raw = await ws.receive_text()
    msg = parse_client_message(raw)
    match msg.type:
        case "subscribe": ...
        case "pong": ...
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Server → Client messages
# ---------------------------------------------------------------------------


class StateChangeMessage(BaseModel):
    """Photo processing state transition."""

    type: Literal["state_change"] = "state_change"
    project_id: str
    folder: str
    photo: str
    old_state: str
    new_state: str
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class ProgressMessage(BaseModel):
    """Per-photo processing completion (or start) notification."""

    type: Literal["progress"] = "progress"
    project_id: str
    folder: str
    photo: str
    status: Literal["started", "completed", "failed"]
    duration_sec: float | None = None
    exported_paths: dict[str, str] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class ScanUpdateMessage(BaseModel):
    """Source folder scanning result — new or updated photos discovered."""

    type: Literal["scan_update"] = "scan_update"
    project_id: str
    found_new: bool
    new_count: int
    updated_folders: list[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class MonitorUpdateMessage(BaseModel):
    """Photo state change from DOWNLOADING → NEW (ready to process)."""

    type: Literal["monitor_update"] = "monitor_update"
    project_id: str
    folder: str
    photo: str
    ready: bool
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class ErrorMessage(BaseModel):
    """Processing error notification for a specific photo."""

    type: Literal["error"] = "error"
    project_id: str
    folder: str
    photo: str
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class QueueMetricsMessage(BaseModel):
    """Real-time aggregate queue status broadcast."""

    type: Literal["queue_metrics"] = "queue_metrics"
    queue_length: int
    active_workers: int
    max_workers: int
    completed_total: int
    failed_total: int
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class ExportConflictMessage(BaseModel):
    """Blocked export detected — expected output file is missing or zero-byte."""

    type: Literal["export_conflict"] = "export_conflict"
    project_id: str
    profile: str
    folder: str
    photo: str
    target_path: str
    status: Literal["blocked"] = "blocked"
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class PingMessage(BaseModel):
    """Server-initiated application-level heartbeat ping."""

    type: Literal["ping"] = "ping"
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class ServerClosingMessage(BaseModel):
    """Server is shutting down — client should reconnect after the given delay."""

    type: Literal["server_closing"] = "server_closing"
    reconnect_after: int = 5  # seconds


# ---------------------------------------------------------------------------
# Client → Server messages
# ---------------------------------------------------------------------------


class SubscribeMessage(BaseModel):
    """Client subscribes to a subset of folder updates.

    Send ``folders=[]`` (empty list) to subscribe to **all** folders in the
    project (the default on connection open).
    """

    type: Literal["subscribe"] = "subscribe"
    folders: list[str] = Field(default_factory=list)


class PongMessage(BaseModel):
    """Client response to a server ping heartbeat."""

    type: Literal["pong"] = "pong"


# Discriminated union for client → server parsing
ClientMessage = Annotated[
    Union[SubscribeMessage, PongMessage],
    Field(discriminator="type"),
]


def parse_client_message(raw: str) -> ClientMessage | None:
    """
    Parse a raw JSON string from the client into a typed message model.

    Returns None when the payload cannot be parsed or has an unknown ``type``.
    Unknown message types are ignored rather than raising to keep the connection
    alive across protocol versions.
    """
    try:
        data: dict[str, Any] = json.loads(raw)
    except (ValueError, TypeError):
        return None

    msg_type = data.get("type")
    try:
        if msg_type == "subscribe":
            return SubscribeMessage.model_validate(data)
        if msg_type == "pong":
            return PongMessage.model_validate(data)
    except Exception:
        return None
    return None
