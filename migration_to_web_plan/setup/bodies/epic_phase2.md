## Problem Statement

The REST API delivers responses on request, but batch image processing can take minutes.
Clients need live progress updates without polling. This epic delivers the WebSocket
real-time layer that streams processing events to all connected browsers.

## Scope

**In scope:**
- FastAPI WebSocket server endpoint
- Adaptation of `bid/events/` subsystem to publish events over WebSocket
- Per-file and batch-level progress streaming
- Heartbeat and automatic client reconnect mechanism
- WebSocket integration test suite

**Out of scope:**
- Frontend WebSocket consumer (Phase 3–4)
- Authentication over WebSocket (relies on JWT from Phase 1)

## Acceptance Criteria

- [ ] WebSocket endpoint available at `ws://.../ws`
- [ ] Clients receive `processing_started`, `progress`, `processing_done`, and `error` events
- [ ] Heartbeat sent every 30 s; client auto-reconnects within 5 s of connection loss
- [ ] No message loss during batch processing of ≥ 100 images
- [ ] Integration tests pass in CI

## Dependencies

- **Milestone:** M2 — WebSocket Real-Time Layer (Phase 2)
- **Depends on:** Epic E1 — Phase 1 Backend API Extraction (M1 must be complete)

## Definition of Done

- [ ] Code reviewed and approved
- [ ] Acceptance criteria checked
- [ ] CI pipeline green
- [ ] WebSocket event schema documented in `docs/api/websocket.md`
- [ ] Merged to `main`
