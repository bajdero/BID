"""
bid/events/cli.py
Standalone command-line interface for the event-based photo sorting system.

Can be run independently of the BID GUI:
    python -m bid.events.cli --help

Examples:
    # Add a remote JSON source
    python -m bid.events.cli add-source "https://www.yapa.art.pl/2026/obsuwa/json2.php?idKoncertu=26" --label "Saturday Competition"

    # Add a local JSON file
    python -m bid.events.cli add-source "./schedule_day1.json" --label "Day 1"

    # List registered sources
    python -m bid.events.cli list-sources

    # Load all sources and show the event timeline
    python -m bid.events.cli show-timeline

    # Annotate source_dict and show sorting assignments
    python -m bid.events.cli sort --dry-run

    # Create event folders and annotate photos
    python -m bid.events.cli sort
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from bid.events.manager import EventManager
from bid.events.models import SourceType
from bid.events.source_loader import detect_source_type


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s : %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def _load_settings(project_dir: Path) -> dict:
    settings_path = project_dir / "settings.json"
    if not settings_path.is_file():
        print(f"ERROR: settings.json not found in {project_dir}", file=sys.stderr)
        sys.exit(1)
    with open(settings_path, "r", encoding="utf-8") as f:
        return json.load(f)


def cmd_add_source(args: argparse.Namespace) -> None:
    """Add a new event JSON source."""
    mgr = EventManager(args.project)
    try:
        source = mgr.add_source(
            location=args.location,
            label=args.label or "",
        )
        print(f"Added source: {source.location} (type={source.source_type.value})")
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_remove_source(args: argparse.Namespace) -> None:
    """Remove a registered event source."""
    mgr = EventManager(args.project)
    if mgr.remove_source(args.location):
        print(f"Removed: {args.location}")
    else:
        print(f"Source not found: {args.location}", file=sys.stderr)
        sys.exit(1)


def cmd_list_sources(args: argparse.Namespace) -> None:
    """List all registered event sources."""
    mgr = EventManager(args.project)
    sources = mgr.list_sources()
    if not sources:
        print("No event sources registered.")
        return
    for s in sources:
        status = "enabled" if s["enabled"] else "DISABLED"
        error = f" [ERROR: {s['error']}]" if s.get("error") else ""
        print(f"  [{status}] {s['source_type']:4s} | {s['location']}{error}")
        if s.get("label"):
            print(f"           Label: {s['label']}")


def cmd_show_timeline(args: argparse.Namespace) -> None:
    """Load all sources and display the merged event timeline."""
    mgr = EventManager(args.project)
    schedules = mgr.load_all()

    if not schedules:
        print("No schedules loaded.")
        return

    for schedule in schedules:
        print(f"\n{'='*60}")
        print(f"Schedule: {schedule.title}")
        print(f"Source:   {schedule.source_url}")
        print(f"Updated:  {schedule.last_update}")
        print(f"{'='*60}")

        active = schedule.active_events
        all_events = schedule.events
        print(f"Total events: {len(all_events)}, Active (status=was): {len(active)}")
        print()

        for i, event in enumerate(all_events):
            marker = "*" if event.status.value == "was" else " "
            folder = mgr.folder_map.get(event.id, "(skipped)")
            print(
                f"  {marker} {event.time_display:15s} | "
                f"{event.name:40s} | status={event.status.value:4s} | "
                f"folder={folder}"
            )

    print(f"\nFolder map ({len(mgr.folder_map)} entries):")
    for eid, fname in sorted(mgr.folder_map.items(), key=lambda x: x[1]):
        print(f"  {fname:30s} ← {eid}")


def cmd_sort(args: argparse.Namespace) -> None:
    """Annotate source_dict with event assignments and optionally create folders."""
    from bid.source_manager import load_source_dict, save_source_dict

    project_dir = Path(args.project)
    settings = _load_settings(project_dir)

    mgr = EventManager(project_dir)
    schedules = mgr.load_all()

    if not schedules:
        print("No schedules loaded. Add sources first.", file=sys.stderr)
        sys.exit(1)

    # Load source_dict
    source_dict = load_source_dict(project_dir)
    if source_dict is None:
        print("ERROR: No source_dict.json found. Run BID first to index photos.", file=sys.stderr)
        sys.exit(1)

    # Annotate
    summary = mgr.annotate(source_dict)

    # Print summary
    from collections import Counter
    folder_counts = Counter(summary.values())
    print(f"\nEvent Sorting Summary ({len(summary)} photos):")
    print("-" * 50)
    for folder, count in sorted(folder_counts.items()):
        print(f"  {folder:35s} : {count:4d} photos")

    if args.dry_run:
        print("\n(Dry run — no files modified)")
        return

    # Save annotated source_dict
    save_source_dict(source_dict, project_dir)
    print(f"\nSaved annotated source_dict to {project_dir / 'source_dict.json'}")

    # Create export folders
    export_folder = settings["export_folder"]
    export_options_path = project_dir / "export_option.json"
    if export_options_path.is_file():
        with open(export_options_path, "r", encoding="utf-8") as f:
            export_settings = json.load(f)
        created = mgr.ensure_export_folders(export_folder, export_settings)
        print(f"Created {len(created)} event subfolders.")
    else:
        print("WARNING: No export_option.json found — skipping folder creation.")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="bid-events",
        description="BID Event-Based Photo Sorting System",
    )
    parser.add_argument(
        "--project", "-p",
        type=str,
        default=".",
        help="Path to BID project directory (default: current dir)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # add-source
    p_add = subparsers.add_parser("add-source", help="Register a new event JSON source")
    p_add.add_argument("location", help="URL or file path to JSON")
    p_add.add_argument("--label", "-l", default="", help="Human-readable label")
    p_add.set_defaults(func=cmd_add_source)

    # remove-source
    p_rm = subparsers.add_parser("remove-source", help="Remove a registered event source")
    p_rm.add_argument("location", help="URL or file path to remove")
    p_rm.set_defaults(func=cmd_remove_source)

    # list-sources
    p_ls = subparsers.add_parser("list-sources", help="List registered event sources")
    p_ls.set_defaults(func=cmd_list_sources)

    # show-timeline
    p_tl = subparsers.add_parser("show-timeline", help="Load and display event timeline")
    p_tl.set_defaults(func=cmd_show_timeline)

    # sort
    p_sort = subparsers.add_parser("sort", help="Annotate photos with event assignments")
    p_sort.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Show what would be done without modifying files",
    )
    p_sort.set_defaults(func=cmd_sort)

    args = parser.parse_args()
    _setup_logging(args.verbose)
    args.func(args)


if __name__ == "__main__":
    main()
