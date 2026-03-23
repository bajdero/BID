## Problem Statement

The desktop source tree (`bid/ui/source_tree.py`) must be replicated as a web file browser.
In addition, the vector similarity search capability in `bid/events/` must be exposed through
a searchable UI, allowing users to find visually similar images across their entire library.

## Scope

**In scope:**
- File browser component with lazy-loaded directory tree (virtualised for large collections)
- Image preview panel with full EXIF metadata display (replicating `bid/ui/details_panel.py`)
- Backend vector search API endpoint using image embeddings
- Search results grid with similarity score and pagination
- Inline metadata editor (author, date, custom EXIF fields)

**Out of scope:**
- Vector index training / re-indexing pipeline (separate infra task)
- Mobile-responsive layout (deferred)

## Acceptance Criteria

- [ ] Directory tree handles ≥ 10 000 files without noticeable lag (< 200 ms render)
- [ ] Vector search returns results in < 2 s for a 50 000-image index
- [ ] Metadata edits persist via the Phase 1 API
- [ ] EXIF fields displayed match those in `bid/image_processing.py` `get_all_exif()`

## Dependencies

- **Milestone:** M8 — FileBrowser + Vector Search (Phase 6)
- **Depends on:** Epic E7 (M7) Processing Dashboard

## Definition of Done

- [ ] Code reviewed and approved
- [ ] Acceptance criteria checked
- [ ] Tests pass in CI
- [ ] Merged to `main`
