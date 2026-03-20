"""
bid/events/matcher.py
Match photos to events based on timestamps.

Core algorithm:
  1. Parse the photo's creation timestamp (EXIF DateTimeOriginal or file mtime).
  2. Iterate through *active* events (status=was) from all loaded schedules.
  3. If the timestamp falls within [event.start, event.end), assign to that event.
  4. If no exact match, the photo is "unmatched" (goes to an undefined folder).

Thread-safe: pure functions, no shared mutable state.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Sequence

from bid.events.models import Event, EventMatch, Schedule

logger = logging.getLogger("BID")


def parse_photo_timestamp(
    created_str: str | None,
    file_mtime: float | None = None,
    local_tz_offset_hours: float = 0.0,
    local_tz=None,
) -> datetime | None:
    """Parse a photo timestamp from various string formats.

    Tries EXIF-format first (``"YYYY:MM:DD HH:MM:SS"``), then common ISO
    variants.  Falls back to ``file_mtime`` (epoch float) if parsing fails.

    Args:
        created_str:         EXIF DateTimeOriginal string (or similar).
        file_mtime:          File modification time as epoch seconds (fallback).
        local_tz_offset_hours: Fixed timezone offset in hours applied to naive
                              timestamps.  Ignored when *local_tz* is provided.
        local_tz:            A ``datetime.tzinfo`` / ``ZoneInfo`` object.  When
                             provided it takes priority over
                             ``local_tz_offset_hours`` and handles DST
                             transitions automatically (e.g.
                             ``ZoneInfo("Europe/Warsaw")``).

    Returns:
        Timezone-aware UTC datetime, or None if nothing can be parsed.
    """
    # Determine the tzinfo to attach to naive parsed datetimes.
    # A proper ZoneInfo object (local_tz) is preferred because it picks
    # the correct CET/CEST offset for each individual photo date.
    if local_tz is not None:
        effective_tz = local_tz
    else:
        effective_tz = timezone(timedelta(hours=local_tz_offset_hours))

    if created_str:
        for fmt in (
            "%Y:%m:%d %H:%M:%S",      # EXIF standard
            "%Y-%m-%d %H:%M:%S",      # ISO-like
            "%Y:%m:%d %H:%M:%S.%f",   # EXIF with fractional seconds
            "%Y-%m-%dT%H:%M:%S",      # ISO 8601
            "%Y-%m-%dT%H:%M:%S%z",    # ISO 8601 with TZ
        ):
            try:
                dt = datetime.strptime(created_str.strip(), fmt)
                if dt.tzinfo is None:
                    # EXIF timestamps are local time — apply offset then convert to UTC
                    dt = dt.replace(tzinfo=effective_tz)
                return dt.astimezone(timezone.utc)
            except (ValueError, TypeError):
                continue

    # Fallback to file modification time
    if file_mtime is not None:
        try:
            return datetime.fromtimestamp(file_mtime, tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            pass

    logger.warning(f"[EVENT] Cannot parse timestamp: created={created_str!r}, mtime={file_mtime}")
    return None


def match_photo_to_event(
    photo_timestamp: datetime,
    schedules: Sequence[Schedule],
) -> EventMatch:
    """Match a single photo's timestamp against all loaded schedules.

    Performs an exact window match: the photo belongs to an event if its
    timestamp falls within ``[event.start, event.end)``.

    Only events with ``status=WAS`` are considered (via ``Schedule.active_events``).

    Args:
        photo_timestamp: UTC-aware datetime of the photo.
        schedules:       All loaded schedules to search.

    Returns:
        EventMatch with the best match (or unmatched if no event covers the timestamp).
    """
    if photo_timestamp.tzinfo is None:
        photo_timestamp = photo_timestamp.replace(tzinfo=timezone.utc)

    # Collect all active events across all schedules
    candidates: list[tuple[Event, Schedule]] = []
    for schedule in schedules:
        for event in schedule.active_events:
            candidates.append((event, schedule))

    # Sort by start time for deterministic results
    candidates.sort(key=lambda pair: pair[0].start)

    # Exact match: timestamp within event window
    for event, schedule in candidates:
        if event.contains_timestamp(photo_timestamp):
            logger.debug(
                f"[EVENT] Exact match: {photo_timestamp.isoformat()} → "
                f"'{event.name}' [{event.time_display}]"
            )
            return EventMatch(event=event, schedule=schedule, confidence=1.0)

    # No exact match
    logger.debug(
        f"[EVENT] No match for timestamp {photo_timestamp.isoformat()} "
        f"across {len(candidates)} active events"
    )
    return EventMatch(event=None, schedule=None, confidence=0.0)


def match_photo_dict_entry(
    photo_meta: dict,
    schedules: Sequence[Schedule],
    local_tz_offset_hours: float = 0.0,
    local_tz=None,
) -> EventMatch:
    """Convenience wrapper: match a source_dict photo entry to an event.

    Args:
        photo_meta:           Dict from source_dict (has ``"created"``, ``"mtime"``).
        schedules:            All loaded schedules.
        local_tz_offset_hours: Fixed TZ offset. Ignored when *local_tz* is provided.
        local_tz:             A ``tzinfo`` / ``ZoneInfo`` object for DST-aware matching.

    Returns:
        EventMatch result.
    """
    ts = parse_photo_timestamp(
        created_str=photo_meta.get("created"),
        file_mtime=photo_meta.get("mtime"),
        local_tz_offset_hours=local_tz_offset_hours,
        local_tz=local_tz,
    )
    if ts is None:
        return EventMatch(event=None, schedule=None, confidence=0.0)
    return match_photo_to_event(ts, schedules)


def build_timeline(
    schedules: Sequence[Schedule],
) -> list[tuple[Event, Schedule]]:
    """Build a merged chronological timeline of all active events.

    Useful for generating the sequential folder numbering.

    Args:
        schedules: All loaded schedules.

    Returns:
        List of (event, schedule) tuples sorted by start time.
    """
    timeline: list[tuple[Event, Schedule]] = []
    for schedule in schedules:
        for event in schedule.active_events:
            timeline.append((event, schedule))
    timeline.sort(key=lambda pair: pair[0].start)
    return timeline
