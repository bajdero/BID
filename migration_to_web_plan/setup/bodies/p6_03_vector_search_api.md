## Problem Statement

The desktop application has a vector similarity search capability in `bid/events/`.
A REST API endpoint must expose this so the web UI can query for visually similar images.

## Scope

**In scope:**
- `POST /search/vector` endpoint accepting an image ID or uploaded query image
- Returns top-N similar images with similarity scores
- Image embedding index served from the backend

**Out of scope:**
- Embedding model training / re-indexing pipeline (separate infra)
- Frontend UI (P6-04)

## Acceptance Criteria

- [ ] Endpoint returns results in < 2 s for a 50 000-image index
- [ ] Results include image path and similarity score (0–1)
- [ ] Unit tests cover the endpoint

## Dependencies

- **Milestone:** M8 — FileBrowser + Vector Search (Phase 6)
- **Parent epic:** [Epic] Phase 6 — FileBrowser + Vector Search

## Definition of Done

- [ ] Code reviewed, tests pass, merged to `main`
