## Problem Statement

The web API is publicly accessible and must be protected. JWT-based authentication
ensures only authorised users can trigger processing jobs or access project data.

## Scope

**In scope:**
- JWT token issuance endpoint (`POST /auth/token`)
- FastAPI dependency that validates the Bearer token on protected routes
- Token refresh endpoint
- User store (initially single-user admin; multi-user deferred)

**Out of scope:**
- OAuth2 social login (deferred)
- Role-based access control beyond admin/user (deferred)

## Acceptance Criteria

- [ ] Protected endpoints return HTTP 401 for missing/invalid tokens
- [ ] Token expires after configurable TTL (default 8 h)
- [ ] Refresh token flow works correctly
- [ ] Auth unit tests pass in CI

## Dependencies

- **Milestone:** M1 — Backend API Extraction (Phase 1)
- **Depends on:** P1-02 (FastAPI service)
- **Parent epic:** [Epic] Phase 1 — Backend API Extraction

## Definition of Done

- [ ] Code reviewed and approved
- [ ] Tests pass in CI
- [ ] Auth documented in `docs/api/auth.md`
- [ ] Merged to `main`
