"""
bid/events/models.py
Data models for the event-based photo sorting system.

Defines strongly-typed dataclasses for:
  - Event: a single schedule entry (performance, setup, break)
  - Schedule: an ordered list of events for a day/concert
  - EventSource: metadata about a JSON source (URL or file path)
  - EventMatch: result of matching a photo to an event

All timestamps are stored as timezone-aware UTC datetimes internally.
JSON `start` fields arrive as epoch milliseconds.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any


class EventStatus(str, Enum):
    """Known event statuses from the JSON schedule.

    Only ``WAS`` events are processed for photo sorting.
    Other statuses are preserved for future extension.
    """
    WAS = "was"
    WILL = "will"
    NOW = "now"

    @classmethod
    def from_str(cls, value: str) -> EventStatus:
        """Parse a status string (case-insensitive).

        Returns the matching enum member, or raises ValueError
        for unknown statuses.
        """
        normalized = value.strip().lower()
        for member in cls:
            if member.value == normalized:
                return member
        raise ValueError(
            f"Unknown event status: {value!r}. "
            f"Known statuses: {[m.value for m in cls]}"
        )

    @classmethod
    def is_known(cls, value: str) -> bool:
        """Check if a raw status string maps to a known enum value."""
        try:
            cls.from_str(value)
            return True
        except ValueError:
            return False


@dataclass(frozen=True, slots=True)
class Event:
    """A single entry in the event schedule.

    Attributes:
        id:        Unique event identifier (e.g. ``"event-26-3"``).
        name:      Display name (HTML entities decoded).
        start:     Event start time (UTC-aware datetime).
        end:       Event end time (UTC-aware datetime).
        duration:  Duration as timedelta.
        status:    Event status enum.
        type_color: Color code hint from the JSON (e.g. ``"#abdfff"``).
        time_display: Human-readable time string from JSON (e.g. ``"12:06 - 12:13"``).
        raw:       Original JSON dict (for debugging / future fields).
    """
    id: str
    name: str
    start: datetime
    end: datetime
    duration: timedelta
    status: EventStatus
    type_color: str = ""
    time_display: str = ""
    raw: dict = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Event:
        """Construct an Event from a single schedule-item dict.

        Args:
            data: Dict with keys ``id``, ``name``, ``start`` (epoch ms),
                  ``duration`` (ms), ``status``, optionally ``type``, ``time``.

        Returns:
            Parsed Event instance.

        Raises:
            KeyError: If required keys are missing.
            ValueError: If ``status`` is unrecognised.
        """
        start_ms: int = int(data["start"])
        dur_ms: int = int(data["duration"])

        start_dt = datetime.fromtimestamp(start_ms / 1000.0, tz=timezone.utc)
        dur_td = timedelta(milliseconds=dur_ms)
        end_dt = start_dt + dur_td

        raw_name = str(data["name"])
        # Decode HTML entities (e.g. &amp; → &)
        clean_name = html.unescape(raw_name).strip()

        return cls(
            id=str(data["id"]),
            name=clean_name,
            start=start_dt,
            end=end_dt,
            duration=dur_td,
            status=EventStatus.from_str(str(data["status"])),
            type_color=str(data.get("type", "")),
            time_display=str(data.get("time", "")),
            raw=dict(data),
        )

    def contains_timestamp(self, ts: datetime) -> bool:
        """Check whether a timestamp falls within this event's window.

        Uses inclusive start, exclusive end: ``[start, end)``.
        """
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return self.start <= ts < self.end

    @property
    def safe_name(self) -> str:
        """Filesystem-safe version of the event name.

        Replaces characters forbidden on Windows/Linux and collapses whitespace.
        """
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', self.name)
        sanitized = re.sub(r'\s+', '_', sanitized.strip())
        # Remove trailing underscores/dots (Windows issue)
        sanitized = sanitized.rstrip('_.')
        return sanitized or "unnamed"


@dataclass(frozen=True, slots=True)
class Schedule:
    """An ordered collection of events for one concert/day.

    Attributes:
        title:        Day/concert title (e.g. ``"Sobota KONKURS"``).
        events:       Chronologically ordered list of *all* events.
        last_update:  Server-reported last update time (raw string).
        source_url:   URL or file path this schedule was loaded from.
        raw:          Original JSON dict.
    """
    title: str
    events: tuple[Event, ...]
    last_update: str = ""
    source_url: str = ""
    raw: dict = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_json(cls, data: dict[str, Any], source_url: str = "") -> Schedule:
        """Build a Schedule from the top-level JSON response.

        Args:
            data: Parsed JSON dict with ``title``, ``schedule`` (list), etc.
            source_url: The URL or file path this data was loaded from.

        Returns:
            Schedule with all events parsed and sorted by start time.
        """
        raw_events = data.get("schedule", [])
        events = []
        for item in raw_events:
            try:
                events.append(Event.from_json(item))
            except (KeyError, ValueError) as exc:
                import logging
                logging.getLogger("BID").warning(
                    f"Skipping malformed event in {source_url}: {exc} — data={item}"
                )
        # Sort chronologically (should already be, but enforce)
        events.sort(key=lambda e: e.start)

        return cls(
            title=html.unescape(str(data.get("title", ""))).strip(),
            events=tuple(events),
            last_update=str(data.get("last_update", "")),
            source_url=source_url,
            raw=dict(data),
        )

    @property
    def active_events(self) -> tuple[Event, ...]:
        """Only events with status ``WAS`` or ``NOW`` — the ones to sort photos into.

        """
        return tuple(e for e in self.events if e.status in (EventStatus.WAS, EventStatus.NOW))

    @property
    def time_range(self) -> tuple[datetime, datetime] | None:
        """Earliest start and latest end across *active* events, or None."""
        active = self.active_events
        if not active:
            return None
        return (active[0].start, active[-1].end)


class SourceType(str, Enum):
    """How the event JSON was provided."""
    URL = "url"
    FILE = "file"


@dataclass(slots=True)
class EventSource:
    """Metadata about a registered JSON event source.

    Attributes:
        location:   URL or filesystem path.
        source_type: Whether this is a remote URL or a local file.
        label:      Optional human-readable label.
        enabled:    Whether this source is active.
        schedule:   Parsed schedule (populated after loading).
        last_loaded: When the source was last successfully fetched.
        error:      Last error message (None if OK).
    """
    location: str
    source_type: SourceType
    label: str = ""
    enabled: bool = True
    schedule: Schedule | None = None
    last_loaded: datetime | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON persistence (excludes parsed schedule)."""
        return {
            "location": self.location,
            "source_type": self.source_type.value,
            "label": self.label,
            "enabled": self.enabled,
            "last_loaded": self.last_loaded.isoformat() if self.last_loaded else None,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EventSource:
        """Deserialize from persisted JSON."""
        last_loaded = None
        if data.get("last_loaded"):
            try:
                last_loaded = datetime.fromisoformat(data["last_loaded"])
            except (ValueError, TypeError):
                pass
        return cls(
            location=data["location"],
            source_type=SourceType(data.get("source_type", "url")),
            label=data.get("label", ""),
            enabled=data.get("enabled", True),
            last_loaded=last_loaded,
            error=data.get("error"),
        )


@dataclass(frozen=True, slots=True)
class EventMatch:
    """Result of matching a single photo to an event (or lack thereof).

    Attributes:
        event:     The matched Event, or None if unmatched.
        schedule:  The Schedule the event belongs to (for context).
        confidence: Match confidence (1.0 = timestamp within window,
                    0.5 = nearest-neighbour fallback, 0.0 = unmatched).
    """
    event: Event | None
    schedule: Schedule | None = None
    confidence: float = 0.0

    @property
    def matched(self) -> bool:
        return self.event is not None and self.confidence > 0.0
