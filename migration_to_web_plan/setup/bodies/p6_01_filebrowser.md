## Problem Statement

Users need to browse the source file system from the web UI. The component must handle
large collections (tens of thousands of files) without blocking the browser.

## Scope

**In scope:**
- Lazy-loaded directory tree (expand on demand)
- Virtualised list rendering for directories with > 200 files
- File type icons and colour-coded status (grey = skipped, colour = indexed)
- Keyboard navigation (arrow keys, Enter to expand)

**Out of scope:**
- Image preview (P6-02)
- Vector search (P6-03)

## Acceptance Criteria

- [ ] Tree renders ≥ 10 000 files without noticeable lag (< 200 ms initial render)
- [ ] Keyboard navigation works
- [ ] Status colours match `bid/ui/source_tree.py` behaviour

## Dependencies

- **Milestone:** M8 — FileBrowser + Vector Search (Phase 6)
- **Depends on:** Epic E7 (M7) Processing Dashboard
- **Parent epic:** [Epic] Phase 6 — FileBrowser + Vector Search

## Definition of Done

- [ ] Code reviewed, tests pass, merged to `main`
