## Problem Statement

The frontend needs client-side routing so users can navigate between pages without
full reloads, and so protected routes redirect unauthenticated users to login.

## Scope

**In scope:**
- React Router v6 with `createBrowserRouter`
- Route definitions: `/login`, `/`, `/projects`, `/projects/:id`, `/settings`
- `ProtectedRoute` wrapper that redirects to `/login` if no valid session

**Out of scope:**
- Page content (other child issues)

## Acceptance Criteria

- [ ] Unauthenticated users accessing any protected route are redirected to `/login`
- [ ] Deep links work after page refresh (requires server 404 → `index.html` config)
- [ ] Route configuration unit-tested

## Dependencies

- **Milestone:** M3 — Frontend Shell (Phase 3)
- **Depends on:** P3-01
- **Parent epic:** [Epic] Phase 3 — Frontend Shell

## Definition of Done

- [ ] Code reviewed and approved
- [ ] Tests pass in CI
- [ ] Merged to `main`
