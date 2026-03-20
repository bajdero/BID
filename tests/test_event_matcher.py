"""
tests/test_event_matcher.py
Unit tests for bid.events.matcher — timestamp parsing and photo-event matching.
"""
import pytest
from datetime import datetime, timezone, timedelta

from bid.events.matcher import (
    build_timeline,
    match_photo_dict_entry,
    match_photo_to_event,
    parse_photo_timestamp,
)
from bid.events.models import Event, EventStatus, Schedule


# ---------------------------------------------------------------------------
# Fixtures — reusable schedule data
# ---------------------------------------------------------------------------

def make_schedule(events_data: list[dict], title: str = "Test") -> Schedule:
    """Helper to build a Schedule from raw event dicts."""
    return Schedule.from_json({
        "title": title,
        "schedule": events_data,
        "last_update": "2026-03-14 16:00:00",
    })


EVENTS_DATA = [
    {
        "id": "event-1",
        "name": "Kankan",
        "time": "12:00 - 12:04",
        "status": "was",
        "start": 1773486000000,  # 2026-03-14 12:00:00 UTC+2 ≈ 10:00 UTC
        "duration": 240000,       # 4 min
    },
    {
        "id": "event-2",
        "name": "Setup ELORE",
        "time": "12:04 - 12:06",
        "status": "was",
        "start": 1773486240000,
        "duration": 120000,       # 2 min
    },
    {
        "id": "event-3",
        "name": "Grupa ELORE",
        "time": "12:06 - 12:13",
        "status": "was",
        "start": 1773486360000,
        "duration": 420000,       # 7 min
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


@pytest.fixture
def schedule():
    return make_schedule(EVENTS_DATA)


# ---------------------------------------------------------------------------
# parse_photo_timestamp
# ---------------------------------------------------------------------------

class TestParsePhotoTimestamp:
    def test_exif_format(self):
        ts = parse_photo_timestamp("2026:03:14 12:06:30")
        assert ts is not None
        assert ts.tzinfo is not None

    def test_exif_format_with_tz_offset(self):
        ts = parse_photo_timestamp("2026:03:14 12:06:30", local_tz_offset_hours=2.0)
        assert ts is not None
        # Should be converted to UTC: 12:06:30 + 2h offset → 10:06:30 UTC
        assert ts.hour == 10
        assert ts.minute == 6

    def test_iso_format(self):
        ts = parse_photo_timestamp("2026-03-14 12:06:30")
        assert ts is not None

    def test_iso_t_format(self):
        ts = parse_photo_timestamp("2026-03-14T12:06:30")
        assert ts is not None

    def test_iso_with_tz(self):
        ts = parse_photo_timestamp("2026-03-14T12:06:30+02:00")
        assert ts is not None
        assert ts.tzinfo == timezone.utc

    def test_fallback_to_mtime(self):
        ts = parse_photo_timestamp(None, file_mtime=1773486360.0)
        assert ts is not None
        assert ts.tzinfo is not None

    def test_empty_string_fallback_to_mtime(self):
        ts = parse_photo_timestamp("", file_mtime=1773486360.0)
        assert ts is not None

    def test_invalid_string_no_mtime_returns_none(self):
        ts = parse_photo_timestamp("not-a-date")
        assert ts is None

    def test_none_everything_returns_none(self):
        ts = parse_photo_timestamp(None)
        assert ts is None


# ---------------------------------------------------------------------------
# match_photo_to_event
# ---------------------------------------------------------------------------

class TestMatchPhotoToEvent:
    def test_exact_match_at_start(self, schedule):
        event1 = schedule.active_events[0]
        result = match_photo_to_event(event1.start, [schedule])
        assert result.matched is True
        assert result.event.id == "event-1"
        assert result.confidence == 1.0

    def test_exact_match_in_middle(self, schedule):
        event3 = [e for e in schedule.active_events if e.id == "event-3"][0]
        mid = event3.start + event3.duration / 2
        result = match_photo_to_event(mid, [schedule])
        assert result.matched is True
        assert result.event.id == "event-3"

    def test_no_match_before_schedule(self, schedule):
        before = schedule.active_events[0].start - timedelta(hours=1)
        result = match_photo_to_event(before, [schedule])
        assert result.matched is False
        assert result.event is None

    def test_no_match_after_schedule(self, schedule):
        last = schedule.active_events[-1]
        after = last.end + timedelta(hours=1)
        result = match_photo_to_event(after, [schedule])
        assert result.matched is False

    def test_future_events_excluded(self, schedule):
        """Events with status='will' should not be matched."""
        future_event = [e for e in schedule.events if e.id == "event-future"][0]
        mid = future_event.start + future_event.duration / 2
        result = match_photo_to_event(mid, [schedule])
        # Should NOT match — status is 'will'
        assert result.matched is False

    def test_multiple_schedules(self):
        """Matching across multiple loaded schedules."""
        s1 = make_schedule([EVENTS_DATA[0]], title="Day 1")
        s2 = make_schedule([EVENTS_DATA[2]], title="Day 2")
        event3_start = Event.from_json(EVENTS_DATA[2]).start
        mid = event3_start + timedelta(seconds=30)
        result = match_photo_to_event(mid, [s1, s2])
        assert result.matched is True
        assert result.event.id == "event-3"

    def test_empty_schedules(self):
        result = match_photo_to_event(
            datetime.now(timezone.utc),
            [],
        )
        assert result.matched is False


# ---------------------------------------------------------------------------
# match_photo_dict_entry
# ---------------------------------------------------------------------------

class TestMatchPhotoDictEntry:
    def test_with_created_timestamp(self, schedule):
        event1 = schedule.active_events[0]
        # Convert start to EXIF format with +2h offset
        local_time = event1.start + timedelta(hours=2)
        exif_str = local_time.strftime("%Y:%m:%d %H:%M:%S")
        meta = {"created": exif_str, "mtime": None}
        result = match_photo_dict_entry(meta, [schedule], local_tz_offset_hours=2.0)
        assert result.matched is True
        assert result.event.id == "event-1"

    def test_with_mtime_fallback(self, schedule):
        event1 = schedule.active_events[0]
        meta = {"created": None, "mtime": event1.start.timestamp()}
        result = match_photo_dict_entry(meta, [schedule])
        assert result.matched is True

    def test_no_timestamp_data(self, schedule):
        meta = {"created": None, "mtime": None}
        result = match_photo_dict_entry(meta, [schedule])
        assert result.matched is False


# ---------------------------------------------------------------------------
# build_timeline
# ---------------------------------------------------------------------------

class TestBuildTimeline:
    def test_timeline_sorted(self, schedule):
        timeline = build_timeline([schedule])
        starts = [event.start for event, _ in timeline]
        assert starts == sorted(starts)

    def test_only_active_events(self, schedule):
        timeline = build_timeline([schedule])
        statuses = [event.status for event, _ in timeline]
        assert all(s == EventStatus.WAS for s in statuses)

    def test_multiple_schedules_merged(self):
        s1 = make_schedule([EVENTS_DATA[0]], title="A")
        s2 = make_schedule([EVENTS_DATA[2]], title="B")
        timeline = build_timeline([s1, s2])
        assert len(timeline) == 2
        # Should be sorted by start time
        assert timeline[0][0].id == "event-1"
        assert timeline[1][0].id == "event-3"
