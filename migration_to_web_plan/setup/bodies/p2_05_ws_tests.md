## Problem Statement

The WebSocket layer needs a dedicated integration test suite to guard against regressions
in event ordering, connection management, and reconnect behaviour.

## Scope

**In scope:**
- Integration tests using `pytest-asyncio` and `httpx` WebSocket client
- Test scenarios: connect, receive events, disconnect, reconnect
- Test scenario: concurrent clients both receive events

**Out of scope:**
- Browser-based E2E tests (Phase 8)

## Acceptance Criteria

- [ ] All integration tests pass in CI
- [ ] Flaky test rate = 0 over 5 consecutive CI runs

## Dependencies

- **Milestone:** M2 — WebSocket Real-Time Layer (Phase 2)
- **Depends on:** P2-01, P2-02, P2-03, P2-04
- **Parent epic:** [Epic] Phase 2 — WebSocket Real-Time Layer

## Definition of Done

- [ ] Tests pass in CI with zero flakiness
- [ ] Merged to `main`
