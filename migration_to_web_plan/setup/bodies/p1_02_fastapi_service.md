## Problem Statement

The image processing logic in `bid/image_processing.py` is tightly coupled to the Tkinter UI.
It must be extracted into a FastAPI service so that web clients can trigger processing jobs.

## Scope

**In scope:**
- FastAPI application wrapping all functions in `bid/image_processing.py`
- Endpoints: resize, convert colour space, apply watermark/logo, clean EXIF
- Background task queue for long-running batch operations
- Structured JSON logging (reusing `bid/logging_config.py`)

**Out of scope:**
- WebSocket progress streaming (Phase 2)
- Frontend integration

## Acceptance Criteria

- [ ] All public functions in `bid/image_processing.py` callable via REST
- [ ] Long-running jobs accepted with HTTP 202 and a job ID for polling
- [ ] Errors return RFC 7807 Problem Details JSON
- [ ] Unit tests cover all endpoints (≥ 80 % coverage)

## Dependencies

- **Milestone:** M1 — Backend API Extraction (Phase 1)
- **Depends on:** P1-01 (API spec)
- **Parent epic:** [Epic] Phase 1 — Backend API Extraction

## Definition of Done

- [ ] Code reviewed and approved
- [ ] Tests pass in CI with ≥ 80 % coverage
- [ ] Merged to `main`
