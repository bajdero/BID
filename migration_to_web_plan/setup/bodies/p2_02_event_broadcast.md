## Problem Statement

The `bid/events/` subsystem currently writes events to an in-memory queue consumed by
the Tkinter UI. It must be adapted to broadcast events to all connected WebSocket clients.

## Scope

**In scope:**
- Adapter layer between `bid/events/manager.py` and the WebSocket connection manager
- All event types mapped to WebSocket message schema
- Async-safe broadcast without blocking the event loop

**Out of scope:**
- New event types (separate issue)

## Acceptance Criteria

- [ ] All events from `bid/events/models.py` broadcast as WebSocket messages
- [ ] Broadcast does not block the processing thread
- [ ] Integration test confirms events arrive at a test WebSocket client

## Dependencies

- **Milestone:** M2 — WebSocket Real-Time Layer (Phase 2)
- **Depends on:** P2-01
- **Parent epic:** [Epic] Phase 2 — WebSocket Real-Time Layer

## Definition of Done

- [ ] Code reviewed and approved
- [ ] Integration test passes in CI
- [ ] Merged to `main`
