"""
tests/test_event_sorter.py
Unit tests for bid.events.sorter — folder generation and source_dict annotation.
"""
import json
import os
import pytest
from datetime import datetime, timezone, timedelta

from bid.events.models import Event, EventMatch, EventStatus, Schedule
from bid.events.sorter import (
    UNDEFINED_FOLDER,
    annotate_source_dict_with_events,
    create_event_folders,
    generate_folder_map,
    get_export_subfolder,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

EVENTS_DATA = [
    {
        "id": "event-1",
        "name": "Kankan",
        "time": "12:00 - 12:04",
        "status": "was",
        "start": 1773486000000,
        "duration": 240000,
    },
    {
        "id": "event-2",
        "name": "Setup ELORE",
        "time": "12:04 - 12:06",
        "status": "was",
        "start": 1773486240000,
        "duration": 120000,
    },
    {
        "id": "event-3",
        "name": "Grupa ELORE",
        "time": "12:06 - 12:13",
        "status": "was",
        "start": 1773486360000,
        "duration": 420000,
    },
    {
        "id": "event-future",
        "name": "Future Event",
        "time": "19:00 - 19:30",
        "status": "will",
        "start": 1773511200000,
        "duration": 1800000,
    },
]


def make_schedule(events=None) -> Schedule:
    return Schedule.from_json({
        "title": "Test Schedule",
        "schedule": events or EVENTS_DATA,
    })


@pytest.fixture
def schedule():
    return make_schedule()


# ---------------------------------------------------------------------------
# generate_folder_map
# ---------------------------------------------------------------------------

class TestGenerateFolderMap:
    def test_basic_mapping(self, schedule):
        folder_map = generate_folder_map([schedule])
        # Should have 3 active events + undefined
        assert "__undefined__" in folder_map
        assert folder_map["__undefined__"] == UNDEFINED_FOLDER
        assert len(folder_map) == 4  # 3 events + undefined

    def test_sequential_numbering(self, schedule):
        folder_map = generate_folder_map([schedule])
        # Active events (status=was) sorted by start time
        assert folder_map["event-1"] == "01_Kankan"
        assert folder_map["event-2"] == "02_Setup_ELORE"
        assert folder_map["event-3"] == "03_Grupa_ELORE"

    def test_future_events_excluded(self, schedule):
        folder_map = generate_folder_map([schedule])
        assert "event-future" not in folder_map

    def test_empty_schedules(self):
        folder_map = generate_folder_map([])
        assert folder_map == {"__undefined__": UNDEFINED_FOLDER}

    def test_multiple_schedules_merged(self):
        s1 = make_schedule([EVENTS_DATA[0]])
        s2 = make_schedule([EVENTS_DATA[2]])
        folder_map = generate_folder_map([s1, s2])
        assert folder_map["event-1"] == "01_Kankan"
        assert folder_map["event-3"] == "02_Grupa_ELORE"  # renumbered sequentially


# ---------------------------------------------------------------------------
# get_export_subfolder
# ---------------------------------------------------------------------------

class TestGetExportSubfolder:
    def test_matched_event(self, schedule):
        folder_map = generate_folder_map([schedule])
        event = Event.from_json(EVENTS_DATA[0])
        match = EventMatch(event=event, schedule=schedule, confidence=1.0)
        assert get_export_subfolder(match, folder_map) == "01_Kankan"

    def test_unmatched(self, schedule):
        folder_map = generate_folder_map([schedule])
        match = EventMatch(event=None, schedule=None, confidence=0.0)
        assert get_export_subfolder(match, folder_map) == UNDEFINED_FOLDER

    def test_event_not_in_map_falls_back(self, schedule):
        folder_map = {"__undefined__": UNDEFINED_FOLDER}
        event = Event.from_json(EVENTS_DATA[0])
        match = EventMatch(event=event, schedule=schedule, confidence=1.0)
        assert get_export_subfolder(match, folder_map) == UNDEFINED_FOLDER


# ---------------------------------------------------------------------------
# create_event_folders
# ---------------------------------------------------------------------------

class TestCreateEventFolders:
    def test_creates_directories(self, tmp_path, schedule):
        export_folder = str(tmp_path / "export")
        profiles = {"fb": {}, "insta": {}}
        folder_map = generate_folder_map([schedule])
        created = create_event_folders(export_folder, profiles, folder_map)

        # Check directories exist
        for profile in profiles:
            for folder_name in folder_map.values():
                dir_path = os.path.join(export_folder, profile, folder_name)
                assert os.path.isdir(dir_path), f"Missing: {dir_path}"

        # Count: 2 profiles × (3 events + 1 undefined) = 8
        assert len(created) == 8

    def test_idempotent(self, tmp_path, schedule):
        """Running create twice should not fail."""
        export_folder = str(tmp_path / "export")
        profiles = {"fb": {}}
        folder_map = generate_folder_map([schedule])
        create_event_folders(export_folder, profiles, folder_map)
        create_event_folders(export_folder, profiles, folder_map)


# ---------------------------------------------------------------------------
# annotate_source_dict_with_events
# ---------------------------------------------------------------------------

class TestAnnotateSourceDict:
    def test_annotation_adds_keys(self, schedule):
        """Each photo should get event_folder, event_id, event_name keys."""
        event1 = Event.from_json(EVENTS_DATA[0])
        # Create a photo with timestamp matching event-1 (need local time with offset)
        local_time = event1.start + timedelta(hours=2)
        created_str = local_time.strftime("%Y:%m:%d %H:%M:%S")

        source_dict = {
            "session1": {
                "photo1.tif": {
                    "created": created_str,
                    "mtime": event1.start.timestamp(),
                },
            },
        }

        summary = annotate_source_dict_with_events(
            source_dict, [schedule], local_tz_offset_hours=2.0
        )
        meta = source_dict["session1"]["photo1.tif"]
        assert "event_folder" in meta
        assert "event_id" in meta
        assert "event_name" in meta

    def test_matched_photo_gets_event_folder(self, schedule):
        event1 = Event.from_json(EVENTS_DATA[0])
        # Use UTC timestamp directly as mtime
        source_dict = {
            "session1": {
                "photo1.tif": {
                    "created": None,
                    "mtime": event1.start.timestamp() + 60,  # 1 min into event
                },
            },
        }

        summary = annotate_source_dict_with_events(
            source_dict, [schedule], local_tz_offset_hours=0.0
        )
        meta = source_dict["session1"]["photo1.tif"]
        assert meta["event_folder"] == "01_Kankan"
        assert meta["event_id"] == "event-1"

    def test_unmatched_photo_gets_undefined(self, schedule):
        source_dict = {
            "session1": {
                "photo1.tif": {
                    "created": "2020:01:01 00:00:00",  # Way outside schedule
                    "mtime": None,
                },
            },
        }

        annotate_source_dict_with_events(
            source_dict, [schedule], local_tz_offset_hours=0.0
        )
        meta = source_dict["session1"]["photo1.tif"]
        assert meta["event_folder"] == UNDEFINED_FOLDER
        assert meta["event_id"] is None

    def test_no_timestamp_gets_undefined(self, schedule):
        source_dict = {
            "session1": {
                "photo1.tif": {
                    "created": None,
                    "mtime": None,
                },
            },
        }

        annotate_source_dict_with_events(source_dict, [schedule])
        meta = source_dict["session1"]["photo1.tif"]
        assert meta["event_folder"] == UNDEFINED_FOLDER

    def test_summary_returned(self, schedule):
        source_dict = {
            "session1": {
                "a.tif": {"created": None, "mtime": None},
                "b.tif": {"created": None, "mtime": None},
            },
        }
        summary = annotate_source_dict_with_events(source_dict, [schedule])
        assert "session1/a.tif" in summary
        assert "session1/b.tif" in summary
