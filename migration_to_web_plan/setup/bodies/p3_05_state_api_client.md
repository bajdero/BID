## Problem Statement

Components need a typed API client and a shared state store to avoid prop drilling and
duplicate fetch logic across the application.

## Scope

**In scope:**
- Zustand store slices: auth, projects, jobs
- Typed API client using `fetch` with interceptors (auth header, error handling)
- React Query (TanStack Query) for server state caching

**Out of scope:**
- WebSocket state integration (Phase 4)

## Acceptance Criteria

- [ ] API client auto-attaches Bearer token to all requests
- [ ] 401 responses trigger logout and redirect
- [ ] Zustand store passes unit tests

## Dependencies

- **Milestone:** M3 — Frontend Shell (Phase 3)
- **Depends on:** P3-01, P3-03
- **Parent epic:** [Epic] Phase 3 — Frontend Shell

## Definition of Done

- [ ] Code reviewed and approved
- [ ] Tests pass in CI
- [ ] Merged to `main`
