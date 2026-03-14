"""
bid/events/sorter.py
Determine export subfolder names based on event matching.

Converts the event timeline + match results into deterministic folder names
following the pattern: ``{NN}_{sanitized_event_name}``.

Example output for a schedule:
    01_Kankan
    02_Ustawianie_Grupa_ELORE
    03_Grupa_ELORE
    04_Ustawianie_BABY
    05_BABY
    ...
    00_undefined   (for photos that don't match any event)

The folder numbering is stable for a given set of loaded schedules.
"""
from __future__ import annotations

import logging
import os
import re
import shutil
from typing import Sequence

from bid.events.matcher import build_timeline, match_photo_to_event, EventMatch
from bid.events.models import Event, Schedule

logger = logging.getLogger("BID")

# Default folder name for unmatched photos
UNDEFINED_FOLDER = "00_undefined"


def generate_folder_map(
    schedules: Sequence[Schedule],
) -> dict[str, str]:
    """Build a mapping from event ID to numbered folder name.

    The numbering is sequential starting from ``01``, following the
    chronological order of *active* events across all schedules.

    Args:
        schedules: All loaded schedules.

    Returns:
        Dict mapping ``event.id`` → ``"NN_SafeName"``
        (e.g. ``{"event-26-3": "03_Grupa_ELORE"}``).
        Also includes the special key ``"__undefined__"`` → ``"00_undefined"``.
    """
    timeline = build_timeline(schedules)
    folder_map: dict[str, str] = {"__undefined__": UNDEFINED_FOLDER}

    for idx, (event, _schedule) in enumerate(timeline, start=1):
        number = f"{idx:02d}"
        folder_name = f"{number}_{event.safe_name}"
        folder_map[event.id] = folder_name
        logger.debug(f"[EVENT] Folder map: {event.id} → {folder_name}")

    logger.info(
        f"[EVENT] Generated folder map: {len(folder_map) - 1} event folders + undefined"
    )
    return folder_map


def get_export_subfolder(
    match: EventMatch,
    folder_map: dict[str, str],
) -> str:
    """Determine the export subfolder for a matched photo.

    Args:
        match:      Result from ``match_photo_to_event()``.
        folder_map: Mapping from ``generate_folder_map()``.

    Returns:
        Folder name string (e.g. ``"03_Grupa_ELORE"`` or ``"00_undefined"``).
    """
    if match.matched and match.event is not None:
        folder = folder_map.get(match.event.id, UNDEFINED_FOLDER)
        return folder
    return UNDEFINED_FOLDER


def create_event_folders(
    export_folder: str,
    export_profiles: dict,
    folder_map: dict[str, str],
) -> list[str]:
    """Create the event subfolder structure on disk.

    For each export profile, creates all event subfolders:
        ``{export_folder}/{profile}/{event_folder}/``

    Args:
        export_folder:   Base export directory.
        export_profiles: Export settings dict (keys are profile names).
        folder_map:      From ``generate_folder_map()``.

    Returns:
        List of created directory paths.
    """
    created: list[str] = []
    for profile_name in export_profiles:
        for event_id, folder_name in folder_map.items():
            dir_path = os.path.join(export_folder, profile_name, folder_name)
            os.makedirs(dir_path, exist_ok=True)
            created.append(dir_path)

    logger.info(
        f"[EVENT] Created {len(created)} event subfolders across "
        f"{len(export_profiles)} export profiles"
    )
    return created


def annotate_source_dict_with_events(
    source_dict: dict,
    schedules: Sequence[Schedule],
    local_tz_offset_hours: float = 0.0,
    local_tz=None,
) -> dict[str, str]:
    """Annotate every photo in source_dict with its event folder.

    Adds an ``"event_folder"`` key to each photo entry and an
    ``"event_id"`` key for cross-referencing.

    Args:
        source_dict:           The main source dictionary.
        schedules:             All loaded schedules.
        local_tz_offset_hours: Fixed TZ offset in hours for EXIF timestamps.
                               Ignored when *local_tz* is provided.
        local_tz:              A ``datetime.tzinfo`` / ``ZoneInfo`` object.
                               When given, it takes priority over
                               ``local_tz_offset_hours`` and handles DST
                               transitions automatically.

    Returns:
        Summary dict: ``{folder/photo: event_folder_name}``.
    """
    from bid.events.matcher import parse_photo_timestamp

    folder_map = generate_folder_map(schedules)
    summary: dict[str, str] = {}
    matched_count = 0
    unmatched_count = 0

    for folder_name, photos in source_dict.items():
        for photo_name, meta in photos.items():
            ts = parse_photo_timestamp(
                created_str=meta.get("created"),
                file_mtime=meta.get("mtime"),
                local_tz_offset_hours=local_tz_offset_hours,
                local_tz=local_tz,
            )
            if ts is not None:
                match = match_photo_to_event(ts, schedules)
                subfolder = get_export_subfolder(match, folder_map)
                meta["event_folder"] = subfolder
                meta["event_id"] = match.event.id if match.event else None
                meta["event_name"] = match.event.name if match.event else None
            else:
                meta["event_folder"] = UNDEFINED_FOLDER
                meta["event_id"] = None
                meta["event_name"] = None
                subfolder = UNDEFINED_FOLDER

            key = f"{folder_name}/{photo_name}"
            summary[key] = subfolder

            if subfolder != UNDEFINED_FOLDER:
                matched_count += 1
            else:
                unmatched_count += 1

    logger.info(
        f"[EVENT] Annotated source_dict: {matched_count} matched, "
        f"{unmatched_count} unmatched ({matched_count + unmatched_count} total)"
    )
    return summary


def move_exported_files_on_reassignment(
    source_dict: dict,
    export_folder: str,
) -> tuple[int, int]:
    """Move already-exported files into their current event subfolders.

    Call this after ``annotate_source_dict_with_events()`` has updated
    ``meta["event_folder"]``.  For every profile export whose file is not
    already in the expected directory the file is physically moved and
    ``meta["exported"][profile]`` is updated to the new path.

    Returns
    -------
    (moved_count, error_count)
    """
    moved = 0
    errors = 0

    for folder_name, photos in source_dict.items():
        for photo_name, meta in photos.items():
            event_subfolder: str | None = meta.get("event_folder")
            exported: dict = meta.get("exported", {})
            if not exported:
                continue

            for profile, current_path in list(exported.items()):
                if not current_path or not os.path.isfile(current_path):
                    continue

                if event_subfolder:
                    expected_dir = os.path.abspath(
                        os.path.join(export_folder, profile, event_subfolder)
                    )
                else:
                    expected_dir = os.path.abspath(
                        os.path.join(export_folder, profile)
                    )

                current_abs = os.path.abspath(current_path)
                current_dir = os.path.dirname(current_abs)

                if os.path.normcase(current_dir) == os.path.normcase(expected_dir):
                    continue  # already in the right place

                # Warn if the file is already inside *some* event subfolder
                # (re-assignment scenario).
                profile_root = os.path.normcase(
                    os.path.abspath(os.path.join(export_folder, profile))
                )
                if os.path.normcase(os.path.dirname(current_dir)) != profile_root:
                    logger.warning(
                        "[EVENT] Re-moving %s/%s (%s): %s \u2192 %s",
                        folder_name, photo_name, profile, current_abs, expected_dir,
                    )

                try:
                    os.makedirs(expected_dir, exist_ok=True)
                    dest = os.path.join(expected_dir, os.path.basename(current_abs))
                    shutil.move(current_abs, dest)
                    meta["exported"][profile] = dest
                    moved += 1
                    logger.info(
                        "[EVENT] Moved %s/%s (%s) \u2192 %s",
                        folder_name, photo_name, profile, dest,
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.error("[EVENT] Failed to move %s: %s", current_abs, exc)
                    errors += 1

    logger.info("[EVENT] move_exported_files: %d moved, %d errors", moved, errors)
    return moved, errors
