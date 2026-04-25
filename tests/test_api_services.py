"""
tests/test_api_services.py
Unit tests for ProcessingService and SourceService helper functions.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.models.database import Base
from src.api.models.source import PhotoRecord
from src.api.schemas.common import ConflictResolutionRequest
from src.api.services.processing import (
    PathTraversalError,
    ProcessingService,
    _make_relative_exports,
    resolve_within,
    validate_path_component,
)
from src.api.services.source import (
    SourceService,
    compute_hash,
    get_or_create_record,
    set_state,
)


# ---------------------------------------------------------------------------
# In-memory DB fixture (shared across this module)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def mem_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db(mem_engine):
    """Yield a fresh session for each test, rolling back on teardown."""
    Session = sessionmaker(bind=mem_engine)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ---------------------------------------------------------------------------
# Path validation helpers
# ---------------------------------------------------------------------------


class TestValidatePathComponent:
    def test_valid_names(self):
        for name in ["Session1", "IMG_001.jpg", "folder-name", "2026.03.23"]:
            validate_path_component(name)  # should not raise

    def test_empty_rejected(self):
        with pytest.raises(PathTraversalError):
            validate_path_component("")

    def test_dotdot_rejected(self):
        with pytest.raises(PathTraversalError):
            validate_path_component("..")

    def test_dotdot_in_name_rejected(self):
        with pytest.raises(PathTraversalError):
            validate_path_component("../evil")

    def test_forward_slash_rejected(self):
        with pytest.raises(PathTraversalError):
            validate_path_component("a/b")

    def test_backslash_rejected(self):
        with pytest.raises(PathTraversalError):
            validate_path_component("a\\b")


class TestResolveWithin:
    def test_valid_path(self, tmp_path):
        sub = tmp_path / "session"
        sub.mkdir()
        (sub / "img.jpg").touch()
        result = resolve_within(tmp_path, "session", "img.jpg")
        assert result == (tmp_path / "session" / "img.jpg").resolve()

    def test_traversal_rejected(self, tmp_path):
        with pytest.raises(PathTraversalError):
            resolve_within(tmp_path, "..", "etc", "passwd")


class TestMakeRelativeExports:
    def test_relative_conversion(self, tmp_path):
        export_folder = tmp_path / "export"
        abs_exports = {"fb": str(export_folder / "fb" / "YAPA_img.jpg")}
        rel = _make_relative_exports(abs_exports, export_folder)
        assert rel["fb"] == str(Path("fb") / "YAPA_img.jpg")

    def test_fallback_on_non_relative(self, tmp_path):
        export_folder = tmp_path / "export"
        other = tmp_path / "other" / "img.jpg"
        rel = _make_relative_exports({"fb": str(other)}, export_folder)
        # Paths outside export_folder are skipped — no absolute paths in DB.
        assert "fb" not in rel


# ---------------------------------------------------------------------------
# compute_hash
# ---------------------------------------------------------------------------


class TestComputeHash:
    def test_known_content(self, tmp_path):
        f = tmp_path / "test.bin"
        f.write_bytes(b"hello world")
        expected = hashlib.sha256(b"hello world").hexdigest()
        assert compute_hash(f) == expected

    def test_different_content_different_hash(self, tmp_path):
        a = tmp_path / "a.bin"
        b = tmp_path / "b.bin"
        a.write_bytes(b"aaa")
        b.write_bytes(b"bbb")
        assert compute_hash(a) != compute_hash(b)


# ---------------------------------------------------------------------------
# get_or_create_record
# ---------------------------------------------------------------------------


class TestGetOrCreateRecord:
    def test_creates_new_record(self, db, tmp_path):
        source_folder = tmp_path / "source"
        source_folder.mkdir()
        session_dir = source_folder / "S1"
        session_dir.mkdir()
        img = session_dir / "a.jpg"
        img.write_bytes(b"\xff\xd8" + b"\x00" * 100)  # minimal JPEG-like bytes

        record = get_or_create_record(db, "proj1", "S1", "a.jpg", img, source_folder)
        assert record.project_id == "proj1"
        assert record.folder == "S1"
        assert record.filename == "a.jpg"
        assert record.state == "new"
        assert record.path_rel == "S1/a.jpg"
        assert len(record.hash_id) == 64  # SHA-256 hex

    def test_returns_existing_record(self, db, tmp_path):
        source_folder = tmp_path / "source2"
        source_folder.mkdir()
        session_dir = source_folder / "S2"
        session_dir.mkdir()
        img = session_dir / "b.jpg"
        img.write_bytes(b"\x00" * 10)

        # Create twice — should return same record on second call.
        r1 = get_or_create_record(db, "proj2", "S2", "b.jpg", img, source_folder)
        r2 = get_or_create_record(db, "proj2", "S2", "b.jpg", img, source_folder)
        assert r1.id == r2.id


# ---------------------------------------------------------------------------
# set_state
# ---------------------------------------------------------------------------


class TestSetState:
    def test_state_transition(self, db, tmp_path):
        source_folder = tmp_path / "source3"
        source_folder.mkdir()
        session_dir = source_folder / "S3"
        session_dir.mkdir()
        img = session_dir / "c.jpg"
        img.write_bytes(b"\x00" * 5)

        record = get_or_create_record(db, "proj3", "S3", "c.jpg", img, source_folder)
        assert record.state == "new"

        set_state(db, record, "processing")
        assert record.state == "processing"

    def test_audit_log_created(self, db, tmp_path):
        from src.api.models.audit import AuditLog

        source_folder = tmp_path / "source4"
        source_folder.mkdir()
        session_dir = source_folder / "S4"
        session_dir.mkdir()
        img = session_dir / "d.jpg"
        img.write_bytes(b"\x00" * 5)

        record = get_or_create_record(db, "proj4", "S4", "d.jpg", img, source_folder)
        set_state(db, record, "ok")

        logs = db.query(AuditLog).filter_by(project_id="proj4", action="state_change").all()
        assert any(log.new_value == "ok" for log in logs)


# ---------------------------------------------------------------------------
# SourceService
# ---------------------------------------------------------------------------


class TestSourceService:
    def test_get_photo_not_found(self, db):
        svc = SourceService()
        result = svc.get_photo(db, "noproj", "S1", "ghost.jpg")
        assert result is None

    def test_get_source_tree_empty(self, db):
        svc = SourceService()
        tree = svc.get_source_tree(db, "empty_project")
        assert tree.folders == {}

    def test_resolve_all_replace(self, db, tmp_path):
        # Set up project settings for the conflict resolver.
        proj_path = tmp_path / "proj_conflict"
        proj_path.mkdir()
        source_folder = tmp_path / "src_c"
        export_folder = tmp_path / "exp_c"
        source_folder.mkdir()
        export_folder.mkdir()

        import json
        settings = {"source_folder": str(source_folder), "export_folder": str(export_folder)}
        with (proj_path / "settings.json").open("w") as f:
            json.dump(settings, f)
        with (proj_path / "export_option.json").open("w") as f:
            json.dump({}, f)

        # Add two export_fail records.
        for i in range(2):
            r = PhotoRecord(
                project_id=proj_path.name,
                folder="S1",
                filename=f"img{i}.jpg",
                path_rel=f"S1/img{i}.jpg",
                state="export_fail",
            )
            db.add(r)
        db.flush()

        svc = SourceService()
        req = ConflictResolutionRequest(mode="all", action="replace")
        resolved = svc.resolve_conflicts(db=db, project_id=proj_path.name, request=req)
        assert resolved == 2

    def test_resolve_selection(self, db, tmp_path):
        proj_path = tmp_path / "proj_sel"
        proj_path.mkdir()
        source_folder = tmp_path / "src_sel"
        export_folder = tmp_path / "exp_sel"
        source_folder.mkdir()
        export_folder.mkdir()

        import json
        settings = {"source_folder": str(source_folder), "export_folder": str(export_folder)}
        with (proj_path / "settings.json").open("w") as f:
            json.dump(settings, f)
        with (proj_path / "export_option.json").open("w") as f:
            json.dump({}, f)

        r = PhotoRecord(
            project_id=proj_path.name,
            folder="S1",
            filename="target.jpg",
            path_rel="S1/target.jpg",
            state="export_fail",
        )
        db.add(r)
        db.flush()

        svc = SourceService()
        req = ConflictResolutionRequest(
            mode="selection",
            action="skip",
            items=[("S1", "target.jpg")],
        )
        resolved = svc.resolve_conflicts(db=db, project_id=proj_path.name, request=req)
        assert resolved == 1
        db.refresh(r)
        assert r.state == "skip"


# ---------------------------------------------------------------------------
# ProcessingService.get_status
# ---------------------------------------------------------------------------


class TestProcessingServiceStatus:
    def test_initial_status_empty(self):
        svc = ProcessingService(max_workers=2)
        status = svc.get_status("any_project")
        assert status.queue_length == 0
        assert status.active == []
        assert status.completed == 0
        assert status.failed == 0
        svc.shutdown()
