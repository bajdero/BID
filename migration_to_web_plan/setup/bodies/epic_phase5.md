## Problem Statement

Users need a dedicated dashboard to control and monitor batch image processing jobs.
The existing desktop queue view must be replicated in the web UI with real-time updates
delivered over the Phase 2 WebSocket layer, plus history, metrics, and error recovery.

## Scope

**In scope:**
- Batch processing status view (start, pause, cancel actions)
- Real-time progress visualisation consuming WebSocket events
- Processing history log viewer with search and filter
- Metrics and statistics dashboard (throughput, error rate, processing time)
- Error details panel with per-item retry action

**Out of scope:**
- FileBrowser (Phase 6)
- Event system audit trail (Phase 7)

## Acceptance Criteria

- [ ] Dashboard updates without page refresh during an active batch
- [ ] History log is searchable by filename, date range, and status
- [ ] Retry action re-queues only the failed items
- [ ] Metrics update in real time via WebSocket
- [ ] Component tests pass in CI

## Dependencies

- **Milestone:** M7 — Processing Dashboard (Phase 5)
- **Depends on:** Epic E6 (M6) audit remediation P0 items closed

## Definition of Done

- [ ] Code reviewed and approved
- [ ] Acceptance criteria checked
- [ ] Component and integration tests pass in CI
- [ ] Merged to `main`
