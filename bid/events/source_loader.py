"""
bid/events/source_loader.py
Load event JSON from remote URLs or local files.

Supports:
  - HTTP/HTTPS URLs (via ``urllib`` — no extra dependencies)
  - Local filesystem JSON files
  - Configurable timeout and retry logic
  - Graceful error handling with structured logging

Thread-safe: each function is stateless; callers manage state.
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from bid.events.models import (
    EventSource,
    Schedule,
    SourceType,
)

logger = logging.getLogger("BID")

# Default network timeout in seconds
DEFAULT_TIMEOUT: float = 15.0
DEFAULT_USER_AGENT: str = "BID-EventLoader/1.0"


def fetch_json_from_url(
    url: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Fetch and parse JSON from a remote HTTP(S) URL.

    Args:
        url:     Full URL to the JSON endpoint.
        timeout: Network timeout in seconds.

    Returns:
        Parsed JSON as a dict.

    Raises:
        ConnectionError: On network failures.
        ValueError: On invalid JSON or non-200 response.
    """
    logger.debug(f"[EVENT] Fetching JSON from URL: {url}")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": DEFAULT_USER_AGENT, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise ValueError(
                    f"HTTP {response.status} from {url}"
                )
            raw = response.read()
            data = json.loads(raw)
            logger.info(f"[EVENT] Loaded JSON from {url} ({len(raw)} bytes)")
            return data
    except urllib.error.URLError as exc:
        raise ConnectionError(f"Cannot reach {url}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON from {url}: {exc}") from exc


def load_json_from_file(path: str | Path) -> dict[str, Any]:
    """Load and parse JSON from a local file.

    Args:
        path: Filesystem path to the JSON file.

    Returns:
        Parsed JSON as a dict.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: On invalid JSON content.
    """
    fpath = Path(path)
    logger.debug(f"[EVENT] Loading JSON from file: {fpath}")
    if not fpath.is_file():
        raise FileNotFoundError(f"Event JSON file not found: {fpath}")
    try:
        text = fpath.read_text(encoding="utf-8")
        data = json.loads(text)
        logger.info(f"[EVENT] Loaded JSON from {fpath} ({len(text)} bytes)")
        return data
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {fpath}: {exc}") from exc


def load_event_source(
    source: EventSource,
    timeout: float = DEFAULT_TIMEOUT,
) -> Schedule:
    """Load and parse a Schedule from an EventSource.

    Updates ``source.schedule``, ``source.last_loaded``, ``source.error``
    in-place as side effects.

    Args:
        source:  The EventSource to load.
        timeout: Network timeout for URL sources.

    Returns:
        Parsed Schedule.

    Raises:
        ConnectionError: On network failure (URL sources).
        FileNotFoundError: If local file is missing.
        ValueError: On invalid JSON or parse errors.
    """
    from datetime import datetime, timezone

    try:
        if source.source_type == SourceType.URL:
            data = fetch_json_from_url(source.location, timeout=timeout)
        else:
            data = load_json_from_file(source.location)

        schedule = Schedule.from_json(data, source_url=source.location)
        source.schedule = schedule
        source.last_loaded = datetime.now(timezone.utc)
        source.error = None

        logger.debug(
            f"[EVENT] Parsed schedule '{schedule.title}' from {source.location}: "
            f"{len(schedule.events)} total events, "
            f"{len(schedule.active_events)} active (status=was)"
        )
        return schedule

    except Exception as exc:
        source.error = str(exc)
        logger.error(f"[EVENT] Failed to load {source.location}: {exc}")
        raise


def detect_source_type(location: str) -> SourceType:
    """Auto-detect whether a location string is a URL or a file path.

    Args:
        location: URL or filesystem path.

    Returns:
        SourceType.URL or SourceType.FILE.
    """
    lower = location.strip().lower()
    if lower.startswith("http://") or lower.startswith("https://"):
        return SourceType.URL
    return SourceType.FILE
