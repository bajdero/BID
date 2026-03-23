## Problem Statement

Users must be able to log in to the web application using their credentials.
The auth flow must consume the Phase 1 JWT API and persist the session token securely.

## Scope

**In scope:**
- Login page with email/password form
- JWT token storage in `httpOnly` cookie or memory (no localStorage)
- Logout action that clears session
- Automatic token refresh before expiry

**Out of scope:**
- OAuth2 social login (deferred)
- Multi-user management UI (deferred)

## Acceptance Criteria

- [ ] Successful login redirects to `/`
- [ ] Failed login shows error message without exposing details
- [ ] Logout clears session and redirects to `/login`
- [ ] Token refresh happens silently before 8 h expiry

## Dependencies

- **Milestone:** M3 — Frontend Shell (Phase 3)
- **Depends on:** P3-01, P3-02, P1-04 (auth API)
- **Parent epic:** [Epic] Phase 3 — Frontend Shell

## Definition of Done

- [ ] Code reviewed and approved
- [ ] Tests pass in CI
- [ ] Merged to `main`
