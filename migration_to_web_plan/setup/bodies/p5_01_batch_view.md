## Problem Statement

Operators need a control centre to start, pause, and cancel batch processing jobs
and monitor their progress in real time.

## Scope

**In scope:**
- Batch job list with start/pause/cancel actions
- Per-job status: queued, running, paused, done, failed
- Confirmation dialog before cancel

**Out of scope:**
- History log (P5-03)

## Acceptance Criteria

- [ ] Start/pause/cancel actions call correct API endpoints
- [ ] Status reflects real-time WebSocket events
- [ ] Cancel confirmation prevents accidental job termination

## Dependencies

- **Milestone:** M7 — Processing Dashboard (Phase 5)
- **Depends on:** P2-03 (progress stream), Epic E6 (M6) audit P0 items resolved
- **Parent epic:** [Epic] Phase 5 — Processing Dashboard

## Definition of Done

- [ ] Code reviewed, tests pass, merged to `main`
