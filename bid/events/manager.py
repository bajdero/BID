"""
bid/events/manager.py
High-level orchestrator for the event-based photo sorting system.

Manages:
  - Registration and persistence of event sources (URLs / files)
  - Loading all sources and merging schedules
  - Annotating source_dict with event assignments
  - Creating export folder structures

Thread-safe: uses a threading.Lock around source list mutations.
Persistence: event sources are saved to ``event_sources.json`` in the project folder.
"""
from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence
from zoneinfo import ZoneInfo

from bid.events.models import EventSource, Schedule, SourceType
from bid.events.source_loader import detect_source_type, load_event_source
from bid.events.sorter import (
    annotate_source_dict_with_events,
    create_event_folders,
    generate_folder_map,
)

logger = logging.getLogger("BID")

EVENT_SOURCES_FILENAME = "event_sources.json"


class EventManager:
    """Central manager for event-based photo sorting.

    Typical lifecycle:
        1. ``manager = EventManager(project_dir)``
        2. ``manager.add_source("https://...", label="Saturday Competition")``
        3. ``manager.load_all()``
        4. ``manager.annotate(source_dict)``
        5. During export, read ``photo_meta["event_folder"]`` for subfolder routing.

    Attributes:
        project_dir:  Path to the BID project folder.
        sources:      List of registered EventSources.
        schedules:    List of successfully loaded Schedules.
        folder_map:   Mapping from event ID to folder name (rebuilt on load).
        tz_offset:    Local timezone offset in hours (kept for backward compat).
        local_tz:     ZoneInfo object used for DST-aware timestamp parsing.
    """

    def __init__(
        self,
        project_dir: Path | str,
        tz_offset_hours: float = 1.0,
        local_tz_name: str = "Europe/Warsaw",
    ) -> None:
        """
        Args:
            project_dir:     Path to the project directory (contains settings.json).
            tz_offset_hours: Fallback fixed TZ offset. Used only when ZoneInfo is
                             unavailable. Default 1.0 = CET (Poland winter).
            local_tz_name:   IANA timezone name for DST-aware matching.
                             Defaults to ``"Europe/Warsaw"``.
        """
        self.project_dir = Path(project_dir)
        self.tz_offset = tz_offset_hours
        try:
            self.local_tz: ZoneInfo | None = ZoneInfo(local_tz_name)
        except Exception:
            self.local_tz = None
            logger.warning(
                f"[EVENT] ZoneInfo({local_tz_name!r}) unavailable — "
                f"falling back to fixed offset {tz_offset_hours:+.1f}h"
            )
        self.sources: list[EventSource] = []
        self.schedules: list[Schedule] = []
        self.folder_map: dict[str, str] = {}
        self._lock = threading.Lock()

        # Load persisted sources (not their data — just the registrations)
        self._load_sources_config()

    # ----------------------------------------------------------------
    # Source management
    # ----------------------------------------------------------------

    def add_source(
        self,
        location: str,
        label: str = "",
        source_type: SourceType | None = None,
    ) -> EventSource:
        """Register a new event JSON source.

        Args:
            location:    URL or file path.
            label:       Human-readable label.
            source_type: Auto-detected if None.

        Returns:
            The created EventSource.

        Raises:
            ValueError: If this location is already registered.
        """
        if source_type is None:
            source_type = detect_source_type(location)

        with self._lock:
            # Check for duplicates
            for existing in self.sources:
                if existing.location == location:
                    raise ValueError(f"Source already registered: {location}")

            source = EventSource(
                location=location,
                source_type=source_type,
                label=label,
            )
            self.sources.append(source)
            self._save_sources_config()
            logger.info(f"[EVENT] Added source: {location} (type={source_type.value})")
            return source

    def remove_source(self, location: str) -> bool:
        """Remove a registered source by location.

        Returns:
            True if found and removed, False otherwise.
        """
        with self._lock:
            for i, source in enumerate(self.sources):
                if source.location == location:
                    self.sources.pop(i)
                    self._save_sources_config()
                    logger.info(f"[EVENT] Removed source: {location}")
                    return True
        return False

    def list_sources(self) -> list[dict]:
        """Return a summary of all registered sources.

        Returns:
            List of dicts with source metadata.
        """
        return [s.to_dict() for s in self.sources]

    # ----------------------------------------------------------------
    # Loading
    # ----------------------------------------------------------------

    def load_all(self, timeout: float = 15.0) -> list[Schedule]:
        """Load (or reload) all enabled event sources.

        Failed sources are logged but do not abort the entire load.
        The ``folder_map`` is rebuilt after all sources are loaded.

        Args:
            timeout: Network timeout per source.

        Returns:
            List of successfully loaded schedules.
        """
        loaded: list[Schedule] = []
        errors: list[str] = []

        with self._lock:
            for source in self.sources:
                if not source.enabled:
                    logger.debug(f"[EVENT] Skipping disabled source: {source.location}")
                    continue
                try:
                    schedule = load_event_source(source, timeout=timeout)
                    loaded.append(schedule)
                except Exception as exc:
                    errors.append(f"{source.location}: {exc}")
                    logger.error(f"[EVENT] Failed to load source: {source.location} — {exc}")

            self.schedules = loaded
            self.folder_map = generate_folder_map(loaded)
            self._save_sources_config()

        if errors:
            logger.warning(f"[EVENT] {len(errors)} source(s) failed to load")
        logger.info(
            f"[EVENT] Loaded {len(loaded)} schedules with "
            f"{sum(len(s.active_events) for s in loaded)} active events"
        )
        return loaded

    def schedules_fingerprint(self) -> frozenset[tuple[str, str, str]]:
        """Return a fingerprint of the current active events for change detection.

        Returns a frozenset of ``(event_id, start_iso, end_iso)`` tuples built
        from :attr:`active_events` across all loaded schedules.  If the
        fingerprint differs between two calls the schedule data has changed and
        an export scan should be triggered.
        """
        result: set[tuple[str, str, str]] = set()
        for schedule in self.schedules:
            for event in schedule.active_events:
                result.add((
                    event.id,
                    event.start.isoformat(),
                    event.end.isoformat(),
                ))
        return frozenset(result)

    def load_source(self, location: str, timeout: float = 15.0) -> Schedule | None:
        """Load a single source by location.

        Returns:
            The loaded Schedule, or None if not found/failed.
        """
        with self._lock:
            for source in self.sources:
                if source.location == location:
                    try:
                        schedule = load_event_source(source, timeout=timeout)
                        # Rebuild the schedule list and folder map
                        self.schedules = [
                            s.schedule for s in self.sources
                            if s.schedule is not None
                        ]
                        self.folder_map = generate_folder_map(self.schedules)
                        return schedule
                    except Exception as exc:
                        logger.error(f"[EVENT] Failed: {location} — {exc}")
                        return None
        logger.warning(f"[EVENT] Source not found: {location}")
        return None

    # ----------------------------------------------------------------
    # Photo sorting
    # ----------------------------------------------------------------

    def annotate(self, source_dict: dict) -> dict[str, str]:
        """Annotate all photos in source_dict with event folder assignments.

        Each photo entry gets ``"event_folder"``, ``"event_id"``, and
        ``"event_name"`` keys added.

        Args:
            source_dict: The main BID source dictionary.

        Returns:
            Summary mapping: ``"folder/photo" → "event_folder_name"``.
        """
        if not self.schedules:
            logger.warning("[EVENT] No schedules loaded — cannot annotate photos")
            return {}
        return annotate_source_dict_with_events(
            source_dict,
            self.schedules,
            local_tz_offset_hours=self.tz_offset,            local_tz=self.local_tz,        )

    def ensure_export_folders(
        self,
        export_folder: str,
        export_profiles: dict,
    ) -> list[str]:
        """Create the event-based subfolder structure under each export profile.

        Args:
            export_folder:   Base export directory.
            export_profiles: Export settings dict.

        Returns:
            List of created directories.
        """
        if not self.folder_map:
            logger.warning("[EVENT] No folder map — call load_all() first")
            return []
        return create_event_folders(export_folder, export_profiles, self.folder_map)

    def get_photo_event_folder(self, photo_meta: dict) -> str:
        """Get the event subfolder for a single photo (from its annotation).

        Falls back to ``"00_undefined"`` if not annotated.
        """
        return photo_meta.get("event_folder", "00_undefined")

    @property
    def has_events(self) -> bool:
        """Whether any schedules are loaded and have active events."""
        return bool(self.schedules) and any(
            len(s.active_events) > 0 for s in self.schedules
        )

    # ----------------------------------------------------------------
    # Persistence
    # ----------------------------------------------------------------

    def _config_path(self) -> Path:
        return self.project_dir / EVENT_SOURCES_FILENAME

    def _load_sources_config(self) -> None:
        """Load source registrations from the project's event_sources.json."""
        path = self._config_path()
        if not path.is_file():
            logger.debug(f"[EVENT] No event sources config at {path}")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            tz = data.get("tz_offset_hours")
            if tz is not None:
                self.tz_offset = float(tz)
            self.sources = [
                EventSource.from_dict(item) for item in data.get("sources", [])
            ]
            logger.info(
                f"[EVENT] Loaded {len(self.sources)} source registrations from {path}"
            )
        except Exception as exc:
            logger.error(f"[EVENT] Failed to load event sources config: {exc}")

    def _save_sources_config(self) -> None:
        """Persist source registrations to event_sources.json."""
        path = self._config_path()
        data = {
            "tz_offset_hours": self.tz_offset,
            "sources": [s.to_dict() for s in self.sources],
            "last_saved": datetime.now(timezone.utc).isoformat(),
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"[EVENT] Saved event sources config to {path}")
        except Exception as exc:
            logger.error(f"[EVENT] Failed to save event sources config: {exc}")
