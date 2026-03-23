## Problem Statement

The BID desktop application contains a tightly coupled processing core that cannot be accessed
from a web browser. This epic tracks the full extraction of that core into a documented,
tested REST API, unblocking all subsequent frontend and integration work.

## Scope

**In scope:**
- FastAPI service wrapping `bid/image_processing.py`, `bid/source_manager.py`, and `bid/project_manager.py`
- REST endpoints for all image-processing operations
- JWT/OAuth2 authentication and authorisation middleware
- Database abstraction layer (SQLite for development, PostgreSQL for production)
- OpenAPI 3.0 specification rendered in Swagger UI
- Unit tests with ≥ 80 % coverage on the API layer

**Out of scope:**
- Frontend UI (Phase 3–4)
- WebSocket real-time layer (Phase 2)
- Production deployment (Phase 8)

## Acceptance Criteria

- [ ] All operations in `bid/image_processing.py` are callable via REST endpoints
- [ ] Project and session CRUD maps to `bid/project_manager.py` behaviour
- [ ] OpenAPI spec renders without errors in Swagger UI at `/docs`
- [ ] JWT authentication rejects unauthenticated requests with HTTP 401
- [ ] API unit tests pass in CI with ≥ 80 % line coverage
- [ ] Database migrations managed by Alembic

## Dependencies

- **Milestone:** M1 — Backend API Extraction (Phase 1)
- **Depends on:** No prior issues (first phase)

## Definition of Done

- [ ] Code reviewed and approved by at least one peer
- [ ] All acceptance criteria checked
- [ ] CI pipeline green (lint + tests)
- [ ] OpenAPI spec committed to `docs/api/`
- [ ] Merged to `main`
