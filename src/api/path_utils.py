"""
src/api/path_utils.py
Shared path-traversal guards used by both ProcessingService and SourceService.

Extracted here to avoid a circular import between services/processing.py
(which imports from services/source.py) and services/source.py.
"""
from __future__ import annotations

import re
from pathlib import Path

# Allowed path-component characters.
# Reject anything containing '..' or filesystem separators to prevent traversal.
_SAFE_COMPONENT_RE = re.compile(r'^[^/\\<>:"|?*\x00-\x1f]+$')


class PathTraversalError(ValueError):
    """Raised when a path component contains traversal sequences."""


def validate_path_component(component: str) -> None:
    """
    Raise PathTraversalError if *component* is empty, contains '..' literals,
    or contains characters that could be used for directory traversal.
    """
    if not component:
        raise PathTraversalError("Path component must not be empty.")
    if ".." in component:
        raise PathTraversalError(
            f"Path component contains traversal sequence: {component!r}"
        )
    if not _SAFE_COMPONENT_RE.match(component):
        raise PathTraversalError(
            f"Path component contains forbidden characters: {component!r}"
        )


def resolve_within(base: Path, *parts: str) -> Path:
    """
    Join *parts* under *base*, resolve to an absolute path, and verify the
    result does not escape *base*.  Raise PathTraversalError otherwise.
    """
    candidate = (base.joinpath(*parts)).resolve()
    if not candidate.is_relative_to(base.resolve()):
        raise PathTraversalError(
            f"Resolved path {candidate!r} escapes allowed directory {base!r}."
        )
    return candidate
