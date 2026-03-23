## Problem Statement

Operators occasionally need to correct or enrich EXIF metadata (author, date) directly
from the web UI without opening a separate tool.

## Scope

**In scope:**
- Editable fields: author, creation date, custom tags
- Save via PATCH API endpoint
- Confirmation dialog before overwrite

**Out of scope:**
- Bulk metadata edit (deferred to 2.1.0)

## Acceptance Criteria

- [ ] Author and date fields editable inline
- [ ] Saved changes reflected in subsequent EXIF display
- [ ] Confirmation shown before overwriting existing metadata

## Dependencies

- **Milestone:** M8 — FileBrowser + Vector Search (Phase 6)
- **Depends on:** P6-02, P1-02 (API)
- **Parent epic:** [Epic] Phase 6 — FileBrowser + Vector Search

## Definition of Done

- [ ] Code reviewed, tests pass, merged to `main`
