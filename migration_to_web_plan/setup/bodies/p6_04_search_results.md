## Problem Statement

Search results from the vector search API must be displayed in an intuitive grid
with similarity scores, allowing users to quickly identify and select similar images.

## Scope

**In scope:**
- Search input (upload image or enter image ID)
- Results grid with thumbnails and similarity percentage
- Pagination (20 results/page)
- Click to open in file browser / preview panel

**Out of scope:**
- Text search (separate feature)

## Acceptance Criteria

- [ ] Search results appear within 3 s of query submission
- [ ] Similarity score shown as percentage on each thumbnail
- [ ] Clicking a result opens the file in the browser

## Dependencies

- **Milestone:** M8 — FileBrowser + Vector Search (Phase 6)
- **Depends on:** P6-03
- **Parent epic:** [Epic] Phase 6 — FileBrowser + Vector Search

## Definition of Done

- [ ] Code reviewed, tests pass, merged to `main`
