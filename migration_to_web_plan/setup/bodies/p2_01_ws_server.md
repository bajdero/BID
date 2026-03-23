## Problem Statement

Processing jobs can run for minutes. The REST API only supports polling, which wastes
bandwidth and adds latency. A WebSocket server endpoint delivers live updates efficiently.

## Scope

**In scope:**
- FastAPI WebSocket endpoint at `ws://.../ws`
- Connection manager tracking active clients
- Message schema: `{type, job_id, data, timestamp}`

**Out of scope:**
- Frontend consumer (Phase 3–4)

## Acceptance Criteria

- [ ] Clients can connect and receive JSON messages
- [ ] Multiple concurrent clients each receive their own event stream
- [ ] Server-side errors are reported as `type:error` messages before close

## Dependencies

- **Milestone:** M2 — WebSocket Real-Time Layer (Phase 2)
- **Depends on:** P1-02 (FastAPI service)
- **Parent epic:** [Epic] Phase 2 — WebSocket Real-Time Layer

## Definition of Done

- [ ] Code reviewed and approved
- [ ] Tests pass in CI
- [ ] Merged to `main`
