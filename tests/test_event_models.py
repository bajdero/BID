"""
tests/test_event_models.py
Unit tests for bid.events.models — data classes and parsing.
"""
import pytest
from datetime import datetime, timezone, timedelta

from bid.events.models import (
    Event,
    EventMatch,
    EventSource,
    EventStatus,
    Schedule,
    SourceType,
)


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------

SAMPLE_EVENT_JSON = {
    "id": "event-26-3",
    "type": "#abdfff",
    "name": "Grupa ELORE",
    "time": "12:06 - 12:13",
    "status": "was",
    "start": 1773486360000,
    "duration": 420000,
}

SAMPLE_FUTURE_EVENT_JSON = {
    "id": "event-27-3",
    "type": "#ffd700",
    "name": "Słowo daję",
    "time": "19:10 - 19:40",
    "status": "will",
    "start": 1773511800000,
    "duration": 1800000,
}

SAMPLE_HTML_ENTITY_EVENT_JSON = {
    "id": "event-26-15",
    "type": "#abdfff",
    "name": "Bartek Kazimierczak &amp; Paweł Pikus",
    "time": "13:25 - 13:35",
    "status": "was",
    "start": 1773491100000,
    "duration": 600000,
}

SAMPLE_SCHEDULE_JSON = {
    "time": "sobota, 16:17:23",
    "title": "Sobota KONKURS",
    "schedule": [
        SAMPLE_EVENT_JSON,
        {
            "id": "event-26-1",
            "type": "#cba9ff",
            "name": "Kankan ",
            "time": "12:00 - 12:04",
            "status": "was",
            "start": 1773486000000,
            "duration": 240000,
        },
        SAMPLE_FUTURE_EVENT_JSON,
    ],
    "next_day": "",
    "last_update": "2026-03-14 16:17:23",
}


# ---------------------------------------------------------------------------
# EventStatus tests
# ---------------------------------------------------------------------------

class TestEventStatus:
    def test_from_str_was(self):
        assert EventStatus.from_str("was") == EventStatus.WAS

    def test_from_str_will(self):
        assert EventStatus.from_str("will") == EventStatus.WILL

    def test_from_str_case_insensitive(self):
        assert EventStatus.from_str("WAS") == EventStatus.WAS
        assert EventStatus.from_str("Was") == EventStatus.WAS

    def test_from_str_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown event status"):
            EventStatus.from_str("cancelled")

    def test_is_known(self):
        assert EventStatus.is_known("was") is True
        assert EventStatus.is_known("will") is True
        assert EventStatus.is_known("live") is False


# ---------------------------------------------------------------------------
# Event tests
# ---------------------------------------------------------------------------

class TestEvent:
    def test_from_json_basic(self):
        event = Event.from_json(SAMPLE_EVENT_JSON)
        assert event.id == "event-26-3"
        assert event.name == "Grupa ELORE"
        assert event.status == EventStatus.WAS
        assert event.type_color == "#abdfff"
        assert event.time_display == "12:06 - 12:13"

    def test_from_json_timestamps(self):
        event = Event.from_json(SAMPLE_EVENT_JSON)
        # start = 1773486360000 ms = 1773486360 seconds since epoch
        expected_start = datetime.fromtimestamp(1773486360, tz=timezone.utc)
        assert event.start == expected_start
        assert event.duration == timedelta(milliseconds=420000)
        assert event.end == expected_start + timedelta(milliseconds=420000)

    def test_from_json_html_entity_decoded(self):
        event = Event.from_json(SAMPLE_HTML_ENTITY_EVENT_JSON)
        assert event.name == "Bartek Kazimierczak & Paweł Pikus"
        assert "&amp;" not in event.name

    def test_from_json_missing_key_raises(self):
        with pytest.raises(KeyError):
            Event.from_json({"id": "test", "name": "Test"})

    def test_from_json_unknown_status_raises(self):
        data = {**SAMPLE_EVENT_JSON, "status": "cancelled"}
        with pytest.raises(ValueError, match="Unknown event status"):
            Event.from_json(data)

    def test_contains_timestamp_inside(self):
        event = Event.from_json(SAMPLE_EVENT_JSON)
        # Timestamp in the middle of the event
        mid = event.start + event.duration / 2
        assert event.contains_timestamp(mid) is True

    def test_contains_timestamp_at_start(self):
        event = Event.from_json(SAMPLE_EVENT_JSON)
        assert event.contains_timestamp(event.start) is True

    def test_contains_timestamp_at_end_exclusive(self):
        event = Event.from_json(SAMPLE_EVENT_JSON)
        assert event.contains_timestamp(event.end) is False

    def test_contains_timestamp_outside(self):
        event = Event.from_json(SAMPLE_EVENT_JSON)
        before = event.start - timedelta(hours=1)
        assert event.contains_timestamp(before) is False

    def test_contains_timestamp_naive_treated_as_utc(self):
        event = Event.from_json(SAMPLE_EVENT_JSON)
        naive_mid = (event.start + event.duration / 2).replace(tzinfo=None)
        assert event.contains_timestamp(naive_mid) is True

    def test_safe_name(self):
        event = Event.from_json(SAMPLE_HTML_ENTITY_EVENT_JSON)
        safe = event.safe_name
        # Characters forbidden on Windows filesystems should be removed
        assert "<" not in safe
        assert ">" not in safe
        assert '"' not in safe
        assert ":" not in safe
        assert " " not in safe  # spaces converted to underscores
        # & is valid on both Windows and Linux — should be preserved after HTML decode
        assert "amp;" not in safe  # HTML entity should be decoded

    def test_safe_name_trailing_chars(self):
        data = {**SAMPLE_EVENT_JSON, "name": "test..."}
        event = Event.from_json(data)
        assert not event.safe_name.endswith(".")


# ---------------------------------------------------------------------------
# Schedule tests
# ---------------------------------------------------------------------------

class TestSchedule:
    def test_from_json_basic(self):
        schedule = Schedule.from_json(SAMPLE_SCHEDULE_JSON, source_url="http://test")
        assert schedule.title == "Sobota KONKURS"
        assert len(schedule.events) == 3
        assert schedule.source_url == "http://test"
        assert schedule.last_update == "2026-03-14 16:17:23"

    def test_events_sorted_chronologically(self):
        schedule = Schedule.from_json(SAMPLE_SCHEDULE_JSON)
        starts = [e.start for e in schedule.events]
        assert starts == sorted(starts)

    def test_active_events_only_was(self):
        schedule = Schedule.from_json(SAMPLE_SCHEDULE_JSON)
        active = schedule.active_events
        assert all(e.status == EventStatus.WAS for e in active)
        # "will" event should be excluded
        assert not any(e.id == "event-27-3" for e in active)

    def test_active_events_count(self):
        schedule = Schedule.from_json(SAMPLE_SCHEDULE_JSON)
        # 2 events have status="was", 1 has "will"
        assert len(schedule.active_events) == 2

    def test_time_range(self):
        schedule = Schedule.from_json(SAMPLE_SCHEDULE_JSON)
        time_range = schedule.time_range
        assert time_range is not None
        earliest, latest = time_range
        assert earliest <= latest

    def test_time_range_empty_schedule(self):
        data = {"title": "Empty", "schedule": []}
        schedule = Schedule.from_json(data)
        assert schedule.time_range is None

    def test_malformed_event_skipped(self):
        """Malformed events are skipped with a warning, not crashing."""
        data = {
            "title": "Test",
            "schedule": [
                SAMPLE_EVENT_JSON,
                {"id": "bad", "name": "Missing required fields"},
            ],
        }
        schedule = Schedule.from_json(data)
        assert len(schedule.events) == 1


# ---------------------------------------------------------------------------
# EventSource tests
# ---------------------------------------------------------------------------

class TestEventSource:
    def test_to_dict_from_dict_roundtrip(self):
        source = EventSource(
            location="https://example.com/schedule.json",
            source_type=SourceType.URL,
            label="Day 1",
            enabled=True,
        )
        d = source.to_dict()
        restored = EventSource.from_dict(d)
        assert restored.location == source.location
        assert restored.source_type == source.source_type
        assert restored.label == source.label
        assert restored.enabled == source.enabled

    def test_from_dict_with_last_loaded(self):
        d = {
            "location": "/path/to/file.json",
            "source_type": "file",
            "label": "Local",
            "enabled": True,
            "last_loaded": "2026-03-14T12:00:00+00:00",
            "error": None,
        }
        source = EventSource.from_dict(d)
        assert source.last_loaded is not None
        assert source.source_type == SourceType.FILE


# ---------------------------------------------------------------------------
# EventMatch tests
# ---------------------------------------------------------------------------

class TestEventMatch:
    def test_matched_with_event(self):
        event = Event.from_json(SAMPLE_EVENT_JSON)
        schedule = Schedule.from_json(SAMPLE_SCHEDULE_JSON)
        match = EventMatch(event=event, schedule=schedule, confidence=1.0)
        assert match.matched is True

    def test_unmatched(self):
        match = EventMatch(event=None, schedule=None, confidence=0.0)
        assert match.matched is False
