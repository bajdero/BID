"""
tests/test_event_manager.py
Integration tests for bid.events.manager — EventManager lifecycle.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch

from bid.events.manager import EVENT_SOURCES_FILENAME, EventManager
from bid.events.models import EventSource, Schedule, SourceType


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

VALID_SCHEDULE_JSON = {
    "title": "Test Day",
    "schedule": [
        {
            "id": "event-1",
            "name": "Act One",
            "time": "12:00 - 12:10",
            "status": "was",
            "start": 1773486000000,
            "duration": 600000,
        },
        {
            "id": "event-2",
            "name": "Act Two",
            "time": "12:15 - 12:30",
            "status": "was",
            "start": 1773486900000,
            "duration": 900000,
        },
    ],
    "last_update": "2026-03-14 16:00:00",
}


@pytest.fixture
def project_dir(tmp_path):
    """Minimal project directory with settings.json."""
    proj = tmp_path / "project"
    proj.mkdir()
    settings = {
        "source_folder": str(tmp_path / "source"),
        "export_folder": str(tmp_path / "export"),
    }
    (proj / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
    (tmp_path / "source").mkdir()
    (tmp_path / "export").mkdir()
    return proj


@pytest.fixture
def json_file(tmp_path):
    """A local JSON schedule file."""
    f = tmp_path / "schedule.json"
    f.write_text(json.dumps(VALID_SCHEDULE_JSON, ensure_ascii=False), encoding="utf-8")
    return f


# ---------------------------------------------------------------------------
# Source management
# ---------------------------------------------------------------------------

class TestEventManagerSources:
    def test_add_source(self, project_dir):
        mgr = EventManager(project_dir)
        src = mgr.add_source("https://example.com/schedule.json", label="Day 1")
        assert src.source_type == SourceType.URL
        assert len(mgr.sources) == 1

    def test_add_duplicate_raises(self, project_dir):
        mgr = EventManager(project_dir)
        mgr.add_source("https://example.com/schedule.json")
        with pytest.raises(ValueError, match="already registered"):
            mgr.add_source("https://example.com/schedule.json")

    def test_add_file_source(self, project_dir, json_file):
        mgr = EventManager(project_dir)
        src = mgr.add_source(str(json_file))
        assert src.source_type == SourceType.FILE

    def test_remove_source(self, project_dir):
        mgr = EventManager(project_dir)
        mgr.add_source("https://example.com/a.json")
        assert mgr.remove_source("https://example.com/a.json") is True
        assert len(mgr.sources) == 0

    def test_remove_nonexistent(self, project_dir):
        mgr = EventManager(project_dir)
        assert mgr.remove_source("https://example.com/nope.json") is False

    def test_list_sources(self, project_dir):
        mgr = EventManager(project_dir)
        mgr.add_source("https://example.com/a.json", label="A")
        mgr.add_source("https://example.com/b.json", label="B")
        sources = mgr.list_sources()
        assert len(sources) == 2
        assert sources[0]["label"] == "A"

    def test_persistence_roundtrip(self, project_dir):
        """Sources survive save/load cycle."""
        mgr1 = EventManager(project_dir)
        mgr1.add_source("https://example.com/a.json", label="Test")

        mgr2 = EventManager(project_dir)
        assert len(mgr2.sources) == 1
        assert mgr2.sources[0].location == "https://example.com/a.json"
        assert mgr2.sources[0].label == "Test"


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

class TestEventManagerLoading:
    def test_load_file_source(self, project_dir, json_file):
        mgr = EventManager(project_dir)
        mgr.add_source(str(json_file), label="Local")
        schedules = mgr.load_all()
        assert len(schedules) == 1
        assert schedules[0].title == "Test Day"
        assert mgr.has_events is True

    def test_load_all_builds_folder_map(self, project_dir, json_file):
        mgr = EventManager(project_dir)
        mgr.add_source(str(json_file))
        mgr.load_all()
        assert "event-1" in mgr.folder_map
        assert "event-2" in mgr.folder_map
        assert "__undefined__" in mgr.folder_map

    def test_load_disabled_source_skipped(self, project_dir, json_file):
        mgr = EventManager(project_dir)
        src = mgr.add_source(str(json_file))
        src.enabled = False
        schedules = mgr.load_all()
        assert len(schedules) == 0
        assert mgr.has_events is False

    def test_load_missing_source_graceful(self, project_dir, tmp_path):
        mgr = EventManager(project_dir)
        mgr.add_source(str(tmp_path / "missing.json"))
        schedules = mgr.load_all()
        assert len(schedules) == 0
        assert mgr.sources[0].error is not None


# ---------------------------------------------------------------------------
# Annotation
# ---------------------------------------------------------------------------

class TestEventManagerAnnotation:
    def test_annotate_source_dict(self, project_dir, json_file):
        from bid.events.models import Event

        mgr = EventManager(project_dir, tz_offset_hours=0.0)
        mgr.add_source(str(json_file))
        mgr.load_all()

        event1 = Event.from_json(VALID_SCHEDULE_JSON["schedule"][0])
        source_dict = {
            "session": {
                "photo.tif": {
                    "created": None,
                    "mtime": event1.start.timestamp() + 60,
                },
            },
        }

        summary = mgr.annotate(source_dict)
        assert len(summary) == 1
        meta = source_dict["session"]["photo.tif"]
        assert meta["event_folder"] == "01_Act_One"

    def test_annotate_without_schedules_returns_empty(self, project_dir):
        mgr = EventManager(project_dir)
        summary = mgr.annotate({"session": {"photo.tif": {}}})
        assert summary == {}


# ---------------------------------------------------------------------------
# Folder creation
# ---------------------------------------------------------------------------

class TestEventManagerFolders:
    def test_ensure_export_folders(self, project_dir, json_file, tmp_path):
        mgr = EventManager(project_dir)
        mgr.add_source(str(json_file))
        mgr.load_all()

        export_dir = str(tmp_path / "export")
        profiles = {"fb": {}, "insta": {}}
        created = mgr.ensure_export_folders(export_dir, profiles)
        assert len(created) > 0

        # Verify directories exist
        import os
        for d in created:
            assert os.path.isdir(d)
