## Problem Statement

Users need fine-grained progress: which file is being processed, what percentage is done,
and estimated time remaining. This requires streaming per-file events from the processing
pipeline over WebSocket.

## Scope

**In scope:**
- `processing_started`, `progress` (0–100 %), `processing_done`, `error` events per file
- Batch-level summary events (started, completed, failed counts)
- Integration with the job queue from P1-02

**Out of scope:**
- Dashboard UI (Phase 5)

## Acceptance Criteria

- [ ] Progress events fire for each file at minimum at start and end
- [ ] Batch summary event sent when all files complete
- [ ] Tests simulate a 10-file batch and verify all events received

## Dependencies

- **Milestone:** M2 — WebSocket Real-Time Layer (Phase 2)
- **Depends on:** P2-02
- **Parent epic:** [Epic] Phase 2 — WebSocket Real-Time Layer

## Definition of Done

- [ ] Code reviewed and approved
- [ ] Tests pass in CI
- [ ] Merged to `main`
