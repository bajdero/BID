"""
bid/events — Event-based photo sorting system.

Automatically sorts photos into folders based on event metadata
obtained from JSON sources (remote URLs or local files).

Architecture:
  models.py        — Data classes (Event, Schedule, EventSource, EventMatch)
  source_loader.py — JSON fetching/parsing (URL & file)
  matcher.py       — Timestamp-based photo↔event matching
  sorter.py        — Folder name generation & source_dict annotation
  manager.py       — High-level orchestrator (EventManager)
  cli.py           — Standalone command-line interface

Quick start:
    from bid.events import EventManager

    mgr = EventManager(project_dir="./my_project")
    mgr.add_source("https://example.com/schedule.json", label="Day 1")
    mgr.load_all()
    mgr.annotate(source_dict)
    mgr.ensure_export_folders(export_folder, export_settings)
"""
from bid.events.models import (
    Event,
    EventMatch,
    EventSource,
    EventStatus,
    Schedule,
    SourceType,
)
from bid.events.manager import EventManager

__all__ = [
    "Event",
    "EventMatch",
    "EventManager",
    "EventSource",
    "EventStatus",
    "Schedule",
    "SourceType",
]
