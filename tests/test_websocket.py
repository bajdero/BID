"""
tests/test_websocket.py
WebSocket integration tests for the BID real-time layer (Phase 2 / P2-05).

Test design:
- Uses FastAPI's built-in TestClient.websocket_connect() for synchronous
  WebSocket test connections against the ASGI app.
- All image processing is mocked to keep tests fast and I/O-free.
- Each test class is independent; fixtures isolate state.

Authentication:
- A JWT access token is minted via create_access_token() (from auth service)
  and passed as a query parameter: ?token=<JWT>
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.services.auth import create_access_token
from src.api.websocket.manager import ConnectionManager
from src.api.websocket.schemas import (
    ErrorMessage,
    PingMessage,
    ProgressMessage,
    QueueMetricsMessage,
    ServerClosingMessage,
    StateChangeMessage,
    parse_client_message,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ws_url(project_id: str, token: str) -> str:
    return f"/api/v1/projects/{project_id}/ws?token={token}"


def _make_token(username: str = "test_admin", role: str = "admin") -> str:
    """Mint a short-lived JWT access token for the given user."""
    return create_access_token(username, role)


# ---------------------------------------------------------------------------
# WS schema unit tests (fast, no network)
# ---------------------------------------------------------------------------


class TestWSSchemas:
    """Unit tests for the WebSocket message schema layer."""

    def test_state_change_serialises(self):
        msg = StateChangeMessage(
            project_id="proj",
            folder="Session1",
            photo="img.jpg",
            old_state="new",
            new_state="processing",
        )
        data = json.loads(msg.model_dump_json())
        assert data["type"] == "state_change"
        assert data["project_id"] == "proj"
        assert data["new_state"] == "processing"
        assert "timestamp" in data

    def test_progress_serialises(self):
        msg = ProgressMessage(
            project_id="p",
            folder="f",
            photo="x.jpg",
            status="completed",
            duration_sec=1.5,
            exported_paths={"web": "export/web/x.jpg"},
        )
        data = json.loads(msg.model_dump_json())
        assert data["type"] == "progress"
        assert data["status"] == "completed"
        assert data["exported_paths"] == {"web": "export/web/x.jpg"}

    def test_queue_metrics_serialises(self):
        msg = QueueMetricsMessage(
            queue_length=5,
            active_workers=2,
            max_workers=4,
            completed_total=10,
            failed_total=1,
        )
        data = json.loads(msg.model_dump_json())
        assert data["type"] == "queue_metrics"
        assert data["queue_length"] == 5

    def test_parse_subscribe_message(self):
        raw = json.dumps({"type": "subscribe", "folders": ["Session1", "Session2"]})
        msg = parse_client_message(raw)
        assert msg is not None
        assert msg.type == "subscribe"
        assert msg.folders == ["Session1", "Session2"]

    def test_parse_pong_message(self):
        raw = json.dumps({"type": "pong"})
        msg = parse_client_message(raw)
        assert msg is not None
        assert msg.type == "pong"

    def test_parse_unknown_type_returns_none(self):
        raw = json.dumps({"type": "unknown_future_type"})
        assert parse_client_message(raw) is None

    def test_parse_invalid_json_returns_none(self):
        assert parse_client_message("{invalid") is None

    def test_server_closing_defaults(self):
        msg = ServerClosingMessage()
        assert msg.reconnect_after == 5
        assert msg.type == "server_closing"


# ---------------------------------------------------------------------------
# ConnectionManager unit tests (fast, no network)
# ---------------------------------------------------------------------------


class TestConnectionManager:
    """Unit tests for ConnectionManager in isolation."""

    @pytest.mark.asyncio
    async def test_connect_adds_to_registry(self):
        manager = ConnectionManager()

        class MinimalWS:
            async def accept(self):
                pass

        ws = MinimalWS()
        await manager.connect(ws, "proj1")
        assert manager.connection_count("proj1") == 1
        assert manager.has_connections("proj1")

    def test_disconnect_removes_from_registry(self):
        manager = ConnectionManager()
        ws = MagicMock()
        # Manually inject a connection
        manager._connections["proj1"] = {ws}
        manager.disconnect(ws, "proj1")
        assert manager.connection_count("proj1") == 0
        assert not manager.has_connections("proj1")

    def test_disconnect_removes_empty_project_key(self):
        manager = ConnectionManager()
        ws = MagicMock()
        manager._connections["proj1"] = {ws}
        manager.disconnect(ws, "proj1")
        assert "proj1" not in manager._connections

    @pytest.mark.asyncio
    async def test_broadcast_to_project_sends_json(self):
        manager = ConnectionManager()
        sent: list[str] = []

        class FakeWS:
            async def accept(self):
                pass
            async def send_text(self, data: str):
                sent.append(data)

        ws = FakeWS()
        await manager.connect(ws, "proj1")
        await manager.broadcast_to_project("proj1", {"type": "ping"})
        assert len(sent) == 1
        assert json.loads(sent[0])["type"] == "ping"

    @pytest.mark.asyncio
    async def test_broadcast_to_empty_project_does_nothing(self):
        manager = ConnectionManager()
        # Should not raise
        await manager.broadcast_to_project("no_such_project", {"type": "ping"})

    @pytest.mark.asyncio
    async def test_dead_socket_removed_on_send_failure(self):
        manager = ConnectionManager()

        class DeadWS:
            async def accept(self):
                pass
            async def send_text(self, data: str):
                raise RuntimeError("socket dead")

        ws = DeadWS()
        await manager.connect(ws, "proj1")
        assert manager.has_connections("proj1")
        await manager.broadcast_to_project("proj1", {"type": "ping"})
        # Dead socket should be cleaned up after failed send
        assert not manager.has_connections("proj1")

    @pytest.mark.asyncio
    async def test_broadcast_all_reaches_multiple_projects(self):
        manager = ConnectionManager()
        received: dict[str, list[str]] = {"p1": [], "p2": []}

        class TrackingWS:
            def __init__(self, project):
                self.project = project
            async def accept(self):
                pass
            async def send_text(self, data: str):
                received[self.project].append(data)

        await manager.connect(TrackingWS("p1"), "p1")
        await manager.connect(TrackingWS("p2"), "p2")
        await manager.broadcast_all({"type": "queue_metrics"})
        assert len(received["p1"]) == 1
        assert len(received["p2"]) == 1

    def test_connection_count_global(self):
        manager = ConnectionManager()
        manager._connections["p1"] = {MagicMock(), MagicMock()}
        manager._connections["p2"] = {MagicMock()}
        assert manager.connection_count() == 3


# ---------------------------------------------------------------------------
# WebSocket endpoint integration tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def ws_client(api_test_app):
    """
    Return a TestClient for WS tests.  The ConnectionManager and
    ProcessingService are wired from the app lifespan.
    """
    with TestClient(api_test_app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture()
def project_id(sample_api_project):
    return sample_api_project.name


@pytest.fixture()
def valid_token():
    return _make_token()


class TestWSAuthentication:
    """Tests for WebSocket JWT authentication."""

    def test_ws_rejects_missing_token(self, ws_client, project_id):
        with pytest.raises(Exception):
            with ws_client.websocket_connect(
                f"/api/v1/projects/{project_id}/ws"
            ) as ws:
                ws.receive_text()

    def test_ws_rejects_invalid_token(self, ws_client, project_id):
        with pytest.raises(Exception):
            with ws_client.websocket_connect(
                f"/api/v1/projects/{project_id}/ws?token=not.a.valid.jwt"
            ) as ws:
                ws.receive_text()

    def test_ws_rejects_invalid_project_id(self, ws_client, valid_token):
        # Path traversal attempt
        with pytest.raises(Exception):
            with ws_client.websocket_connect(
                f"/api/v1/projects/../secret/ws?token={valid_token}"
            ) as ws:
                ws.receive_text()

    def test_ws_connects_with_valid_token(self, api_test_app, project_id):
        """A valid token should allow the WebSocket upgrade to succeed."""
        token = _make_token()
        # We need to patch the DB lookup so the token sub resolves to a user
        from src.api.models.user import UserRecord
        test_user = UserRecord(
            id=1,
            username="test_admin",
            email="admin@test.local",
            hashed_password="x",
            role="admin",
            is_active=True,
        )
        with patch("src.api.websocket.router._authenticate_ws_token", return_value=test_user):
            with TestClient(api_test_app) as client:
                with client.websocket_connect(
                    _ws_url(project_id, token)
                ) as ws:
                    # Connection accepted — we can send a message and not crash
                    ws.send_text(json.dumps({"type": "pong"}))
                    # No exception means connection was established successfully


class TestWSSubscription:
    """Tests for folder subscription filtering."""

    def test_subscribe_message_accepted(self, api_test_app, project_id):
        """Client can send a subscribe message without the connection closing."""
        from src.api.models.user import UserRecord
        test_user = UserRecord(
            id=1, username="test_admin", email="admin@test.local",
            hashed_password="x", role="admin", is_active=True,
        )
        with patch("src.api.websocket.router._authenticate_ws_token", return_value=test_user):
            with TestClient(api_test_app) as client:
                with client.websocket_connect(
                    _ws_url(project_id, _make_token())
                ) as ws:
                    ws.send_text(json.dumps({
                        "type": "subscribe",
                        "folders": ["Session1", "Session2"],
                    }))
                    # Send pong to keep alive briefly then disconnect cleanly
                    ws.send_text(json.dumps({"type": "pong"}))

    def test_subscribe_empty_folders_resets_to_all(self, api_test_app, project_id):
        """An empty folders list means 'subscribe to all' — no error."""
        from src.api.models.user import UserRecord
        test_user = UserRecord(
            id=1, username="test_admin", email="admin@test.local",
            hashed_password="x", role="admin", is_active=True,
        )
        with patch("src.api.websocket.router._authenticate_ws_token", return_value=test_user):
            with TestClient(api_test_app) as client:
                with client.websocket_connect(
                    _ws_url(project_id, _make_token())
                ) as ws:
                    ws.send_text(json.dumps({"type": "subscribe", "folders": []}))
                    ws.send_text(json.dumps({"type": "pong"}))


class TestWSPingPong:
    """Tests for heartbeat ping/pong behaviour."""

    def test_ping_message_schema(self):
        """PingMessage serialises correctly."""
        msg = PingMessage()
        data = json.loads(msg.model_dump_json())
        assert data["type"] == "ping"

    def test_pong_parse_roundtrip(self):
        """A pong JSON string parses to PongMessage."""
        raw = json.dumps({"type": "pong"})
        msg = parse_client_message(raw)
        assert msg is not None
        assert msg.type == "pong"


class TestWSDisconnectCleanup:
    """Tests for connection cleanup on disconnect."""

    def test_disconnect_removes_connection(self):
        """ConnectionManager removes the socket after disconnect is called."""
        manager = ConnectionManager()
        ws = MagicMock()
        manager._connections["proj"] = {ws}
        assert manager.has_connections("proj")
        manager.disconnect(ws, "proj")
        assert not manager.has_connections("proj")

    def test_double_disconnect_is_safe(self):
        """Calling disconnect twice for the same socket does not raise."""
        manager = ConnectionManager()
        ws = MagicMock()
        manager._connections["proj"] = {ws}
        manager.disconnect(ws, "proj")
        manager.disconnect(ws, "proj")  # Second call — should not raise

    def test_disconnect_unknown_project_is_safe(self):
        """Disconnecting a socket for a project with no connections is a no-op."""
        manager = ConnectionManager()
        ws = MagicMock()
        manager.disconnect(ws, "nonexistent_project")  # Should not raise


class TestWSBroadcast100Photos:
    """Verify that 100 broadcast operations complete without loss."""

    @pytest.mark.asyncio
    async def test_100_broadcasts_no_loss(self):
        """Broadcast 100 progress messages; all should arrive."""
        manager = ConnectionManager()
        received: list[dict] = []

        class CollectingWS:
            async def accept(self):
                pass
            async def send_text(self, data: str):
                received.append(json.loads(data))

        ws = CollectingWS()
        await manager.connect(ws, "proj1")

        for i in range(100):
            msg = ProgressMessage(
                project_id="proj1",
                folder="Session1",
                photo=f"photo_{i:04d}.jpg",
                status="completed",
                duration_sec=1.0,
            )
            await manager.broadcast_to_project("proj1", msg.model_dump())

        assert len(received) == 100
        assert all(r["type"] == "progress" for r in received)
        photos = [r["photo"] for r in received]
        assert photos == [f"photo_{i:04d}.jpg" for i in range(100)]


class TestProcessingServiceWSHooks:
    """Unit tests for ProcessingService WebSocket broadcast hooks."""

    @pytest.mark.asyncio
    async def test_set_ws_manager_assigns_manager(self):
        from src.api.services.processing import ProcessingService
        svc = ProcessingService(max_workers=1)
        manager = MagicMock()
        svc.set_ws_manager(manager)
        assert svc._ws_manager is manager
        svc.shutdown()

    def test_ws_manager_defaults_to_none(self):
        from src.api.services.processing import ProcessingService
        svc = ProcessingService(max_workers=1)
        assert svc._ws_manager is None
        svc.shutdown()

    @pytest.mark.asyncio
    async def test_task_runner_broadcasts_state_change_and_progress(self):
        """_task_runner() should emit state_change then progress:completed."""
        import asyncio
        from pathlib import Path
        from unittest.mock import AsyncMock, patch
        from src.api.services.processing import ProcessingService

        broadcast_calls: list[tuple[str, dict]] = []

        class FakeManager:
            async def broadcast_to_project(self, project_id: str, payload: dict):
                broadcast_calls.append((project_id, payload))

        svc = ProcessingService(max_workers=1)
        svc._ws_manager = FakeManager()

        dummy_result = {
            "success": True,
            "exported": {},
            "duration": 0.1,
            "error_msg": None,
        }

        with patch(
            "src.api.services.processing.process_photo_task",
            return_value=dummy_result,
        ), patch(
            "src.api.services.processing.get_or_create_record",
        ) as mock_record, patch(
            "src.api.services.processing.set_state",
        ), patch(
            "src.api.services.processing.SessionLocal",
        ) as mock_session_cls:
            # Mock the database record
            mock_rec = MagicMock()
            mock_rec.id = 42
            mock_rec.state = "new"
            mock_rec.exported = {}
            mock_rec.event_folder = None
            mock_rec.created_date = "2026-01-01"
            mock_record.return_value = mock_rec

            # Mock the session context manager
            mock_session = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            mock_session.get = MagicMock(return_value=mock_rec)
            mock_session_cls.return_value = mock_session

            await svc._task_runner(
                record_id=42,
                project_id="proj1",
                folder="Session1",
                photo="test.jpg",
                photo_abs=Path("/fake/Session1/test.jpg"),
                export_folder=Path("/fake/export"),
                export_settings={"web": {}},
                existing_exports={},
                event_folder=None,
                created_date="2026-01-01",
                old_state="new",
            )

        svc.shutdown()

        types_emitted = [call[1]["type"] for call in broadcast_calls]
        assert "state_change" in types_emitted
        assert "progress" in types_emitted

        progress_msg = next(c[1] for c in broadcast_calls if c[1]["type"] == "progress")
        assert progress_msg["status"] == "completed"
        assert progress_msg["folder"] == "Session1"
        assert progress_msg["photo"] == "test.jpg"

    @pytest.mark.asyncio
    async def test_task_runner_broadcasts_error_on_failure(self):
        """_task_runner() should emit error message when processing fails."""
        from pathlib import Path
        from unittest.mock import patch
        from src.api.services.processing import ProcessingService

        broadcast_calls: list[dict] = []

        class FakeManager:
            async def broadcast_to_project(self, project_id: str, payload: dict):
                broadcast_calls.append(payload)

        svc = ProcessingService(max_workers=1)
        svc._ws_manager = FakeManager()

        dummy_result = {
            "success": False,
            "exported": {},
            "duration": 0.0,
            "error_msg": "EXIF read error",
        }

        with patch(
            "src.api.services.processing.process_photo_task",
            return_value=dummy_result,
        ), patch(
            "src.api.services.processing.get_or_create_record",
        ) as mock_record, patch(
            "src.api.services.processing.set_state",
        ), patch(
            "src.api.services.processing.SessionLocal",
        ) as mock_session_cls:
            mock_rec = MagicMock()
            mock_rec.id = 1
            mock_rec.state = "new"
            mock_rec.exported = {}
            mock_rec.event_folder = None
            mock_rec.created_date = "2026-01-01"
            mock_record.return_value = mock_rec

            mock_session = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            mock_session.get = MagicMock(return_value=mock_rec)
            mock_session_cls.return_value = mock_session

            await svc._task_runner(
                record_id=1,
                project_id="proj2",
                folder="Session1",
                photo="bad.jpg",
                photo_abs=Path("/fake/Session1/bad.jpg"),
                export_folder=Path("/fake/export"),
                export_settings={},
                existing_exports={},
                event_folder=None,
                created_date="2026-01-01",
                old_state="error",
            )

        svc.shutdown()

        types = [c["type"] for c in broadcast_calls]
        assert "error" in types
        error_msg = next(c for c in broadcast_calls if c["type"] == "error")
        assert "EXIF" in error_msg["message"]


class TestEventBroadcastService:
    """Unit tests for EventBroadcastService."""

    def test_is_polling_returns_false_before_start(self):
        from src.api.services.events import EventBroadcastService
        svc = EventBroadcastService()
        assert not svc.is_polling("proj1")

    def test_stop_nonexistent_project_is_safe(self):
        from src.api.services.events import EventBroadcastService
        svc = EventBroadcastService()
        svc.stop_polling("nonexistent")  # Should not raise

    def test_stop_all_clears_tasks(self):
        from src.api.services.events import EventBroadcastService
        svc = EventBroadcastService()
        # Inject a fake task
        fake_task = MagicMock()
        fake_task.done.return_value = False
        svc._tasks["proj1"] = fake_task
        svc.stop_all()
        fake_task.cancel.assert_called_once()
        assert "proj1" not in svc._tasks
