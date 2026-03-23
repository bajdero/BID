"""
tests/test_api_schemas.py
Unit tests for Pydantic request/response schemas.
No filesystem or DB access required — pure model validation.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.api.schemas.common import ConflictItem, ConflictResolutionRequest
from src.api.schemas.processing import (
    PhotoTaskStatus,
    ProcessRequest,
    ProcessResponse,
    ProcessResult,
    ProcessStatusResponse,
)
from src.api.schemas.source import PhotoEntry, SourceTree


# ---------------------------------------------------------------------------
# ProcessRequest
# ---------------------------------------------------------------------------


class TestProcessRequest:
    def test_valid_minimal(self):
        req = ProcessRequest(photos=[("Session1", "IMG_001.jpg")])
        assert req.photos == [("Session1", "IMG_001.jpg")]
        assert req.profiles is None

    def test_valid_with_profiles(self):
        req = ProcessRequest(
            photos=[("A", "a.jpg"), ("B", "b.jpg")],
            profiles=["fb", "web"],
        )
        assert req.profiles == ["fb", "web"]

    def test_empty_photos_rejected(self):
        with pytest.raises(ValidationError):
            ProcessRequest(photos=[])

    def test_missing_photos_rejected(self):
        with pytest.raises(ValidationError):
            ProcessRequest(profiles=["fb"])  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# ProcessResponse
# ---------------------------------------------------------------------------


class TestProcessResponse:
    def test_defaults(self):
        r = ProcessResponse(task_id="abc", queued=3, message="ok")
        assert r.skipped == 0

    def test_with_skipped(self):
        r = ProcessResponse(task_id="abc", queued=1, skipped=2, message="ok")
        assert r.skipped == 2


# ---------------------------------------------------------------------------
# ProcessResult
# ---------------------------------------------------------------------------


class TestProcessResult:
    def test_success(self):
        r = ProcessResult(success=True, exported={"fb": "fb/IMG.jpg"}, duration_sec=1.5)
        assert r.success is True
        assert r.error_msg is None

    def test_failure(self):
        r = ProcessResult(success=False, error_msg="corrupt EXIF")
        assert r.exported == {}
        assert r.duration_sec == 0.0

    def test_invalid_missing_success(self):
        with pytest.raises(ValidationError):
            ProcessResult()  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# ProcessStatusResponse
# ---------------------------------------------------------------------------


class TestProcessStatusResponse:
    def test_empty_queue(self):
        r = ProcessStatusResponse(queue_length=0, active=[])
        assert r.completed == 0
        assert r.failed == 0

    def test_with_active_tasks(self):
        tasks = [PhotoTaskStatus(folder="S1", photo="a.jpg")]
        r = ProcessStatusResponse(queue_length=1, active=tasks, completed=5, failed=1)
        assert r.queue_length == 1
        assert r.active[0].folder == "S1"


# ---------------------------------------------------------------------------
# PhotoEntry
# ---------------------------------------------------------------------------


class TestPhotoEntry:
    def test_minimal_valid(self):
        entry = PhotoEntry(
            hash_id="abc123",
            path="Session1/IMG.jpg",
            state="new",
        )
        assert entry.exported == {}
        assert entry.tags == []
        assert entry.exif == {}

    def test_all_fields(self):
        entry = PhotoEntry(
            hash_id="deadbeef",
            path="A/B.jpg",
            state="ok",
            exported={"fb": "fb/B.jpg"},
            description="test",
            tags=["tag1"],
            size="1.2 MB",
            size_bytes=1_200_000,
            created="2026:03:23 12:00:00",
            mtime=1711187200.0,
            exif={"Artist": "John"},
            duration_sec=2.3,
            event_folder="03_GroupA",
        )
        assert entry.state == "ok"
        assert entry.duration_sec == 2.3

    @pytest.mark.parametrize(
        "state",
        [
            "downloading", "new", "processing", "ok",
            "ok_old", "error", "export_fail", "deleted", "skip",
        ],
    )
    def test_all_valid_states(self, state):
        entry = PhotoEntry(hash_id="x", path="f/p.jpg", state=state)  # type: ignore[arg-type]
        assert entry.state == state

    def test_invalid_state_rejected(self):
        with pytest.raises(ValidationError):
            PhotoEntry(hash_id="x", path="f/p.jpg", state="unknown_state")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# SourceTree
# ---------------------------------------------------------------------------


class TestSourceTree:
    def test_empty(self):
        tree = SourceTree()
        assert tree.folders == {}

    def test_nested(self):
        entry = PhotoEntry(hash_id="h", path="S1/a.jpg", state="new")
        tree = SourceTree(folders={"S1": {"a.jpg": entry}})
        assert "S1" in tree.folders
        assert tree.folders["S1"]["a.jpg"].path == "S1/a.jpg"


# ---------------------------------------------------------------------------
# ConflictResolutionRequest
# ---------------------------------------------------------------------------


class TestConflictResolutionRequest:
    def test_all_replace(self):
        req = ConflictResolutionRequest(mode="all", action="replace")
        assert req.items is None

    def test_selection_with_items(self):
        req = ConflictResolutionRequest(
            mode="selection",
            action="skip",
            items=[("S1", "a.jpg")],
        )
        assert req.items == [("S1", "a.jpg")]

    def test_invalid_mode(self):
        with pytest.raises(ValidationError):
            ConflictResolutionRequest(mode="bogus", action="replace")  # type: ignore[arg-type]

    def test_invalid_action(self):
        with pytest.raises(ValidationError):
            ConflictResolutionRequest(mode="all", action="delete")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# ConflictItem
# ---------------------------------------------------------------------------


class TestConflictItem:
    def test_default_reason(self):
        item = ConflictItem(
            profile="fb", folder="S1", photo="a.jpg", target_path="fb/a.jpg"
        )
        assert item.reason == "missing_or_empty"
