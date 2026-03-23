## Problem Statement

Clicking a file in the browser must show a preview and its EXIF metadata, replicating
the desktop `bid/ui/details_panel.py` and `bid/ui/preview.py` behaviour.

## Scope

**In scope:**
- Image preview panel (thumbnail + full resolution toggle)
- EXIF metadata table: size, creation date, state, author, pixel dimensions, aspect ratio
- Matches fields from `bid/ui/details_panel.py` TODO list

**Out of scope:**
- Metadata editing (P6-05)

## Acceptance Criteria

- [ ] Preview loads within 500 ms for images < 10 MB
- [ ] EXIF fields match `get_all_exif()` output
- [ ] Panel accessible by keyboard

## Dependencies

- **Milestone:** M8 — FileBrowser + Vector Search (Phase 6)
- **Depends on:** P6-01
- **Parent epic:** [Epic] Phase 6 — FileBrowser + Vector Search

## Definition of Done

- [ ] Code reviewed, tests pass, merged to `main`
