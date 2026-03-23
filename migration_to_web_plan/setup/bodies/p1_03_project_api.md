## Problem Statement

Project and session management currently lives in `bid/project_manager.py` with no
network interface. REST endpoints are needed so web clients can create, read, update,
and delete projects and sessions.

## Scope

**In scope:**
- CRUD endpoints for projects and sessions
- Source folder and export folder association
- Project state persistence (replacing JSON file storage with DB)

**Out of scope:**
- Source tree file browsing (Phase 6)

## Acceptance Criteria

- [ ] `GET/POST/PATCH/DELETE /projects` and `/projects/{id}/sessions` work correctly
- [ ] Project state round-trips correctly through the API
- [ ] Unit tests cover all endpoints

## Dependencies

- **Milestone:** M1 — Backend API Extraction (Phase 1)
- **Depends on:** P1-02 (FastAPI service), P1-05 (DB layer)
- **Parent epic:** [Epic] Phase 1 — Backend API Extraction

## Definition of Done

- [ ] Code reviewed and approved
- [ ] Tests pass in CI
- [ ] Merged to `main`
