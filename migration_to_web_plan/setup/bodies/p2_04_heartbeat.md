## Problem Statement

Long-lived WebSocket connections can drop silently due to proxies and NAT timeouts.
A heartbeat mechanism keeps connections alive and triggers automatic reconnect on failure.

## Scope

**In scope:**
- Server-side ping every 30 s
- Client-side pong response (handled in Phase 3 frontend)
- Server closes and logs stale connections that miss 3 consecutive pings

**Out of scope:**
- Frontend reconnect logic (Phase 3)

## Acceptance Criteria

- [ ] Server sends ping frames every 30 s
- [ ] Stale connections are closed after 90 s of no pong
- [ ] Behaviour verified by integration test using a mock client

## Dependencies

- **Milestone:** M2 — WebSocket Real-Time Layer (Phase 2)
- **Depends on:** P2-01
- **Parent epic:** [Epic] Phase 2 — WebSocket Real-Time Layer

## Definition of Done

- [ ] Code reviewed and approved
- [ ] Tests pass in CI
- [ ] Merged to `main`
