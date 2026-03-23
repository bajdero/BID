## Problem Statement

Before writing any code, the complete REST API contract for BID must be specified.
A documented OpenAPI 3.0 spec prevents integration mismatches between backend and frontend
and serves as the single source of truth throughout the project.

## Scope

**In scope:**
- OpenAPI 3.0 specification for all BID operations (image processing, project/session CRUD, config)
- Request/response schemas using Pydantic v2 models
- Error response formats (RFC 7807 Problem Details)
- Swagger UI accessible at `/docs`

**Out of scope:**
- WebSocket API (covered in Phase 2)
- Implementation code

## Acceptance Criteria

- [ ] OpenAPI spec covers all endpoints planned for Phase 1
- [ ] Spec renders in Swagger UI at `/docs` without validation errors
- [ ] All schemas have descriptions and example values
- [ ] Spec committed to `docs/api/openapi.yaml`

## Dependencies

- **Milestone:** M1 — Backend API Extraction (Phase 1)
- **Parent epic:** [Epic] Phase 1 — Backend API Extraction

## Definition of Done

- [ ] Spec reviewed and approved by tech lead
- [ ] Committed to `docs/api/openapi.yaml`
- [ ] Issue closed
