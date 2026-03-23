## Problem Statement

Users need to see the real-time processing queue: which files are pending, active, done, or failed.

## Scope

**In scope:**
- Queue list with per-file status icons, progress bar for active file, refresh via WebSocket events

**Out of scope:**
- Items explicitly listed as deferred

## Acceptance Criteria

- [ ] Status updates without manual refresh
- [ ] States pending/processing/done/error displayed with distinct icons
- [ ] Clicking a failed item shows error details
- [ ] Component tests pass

## Dependencies

- **Milestone:** M4 — Core UI Components (Phase 4)
- **Depends on:** P2-03 (progress stream), P3-05
- **Parent epic:** [Epic] Phase 4 — Core UI Components

## Definition of Done

- [ ] Code reviewed and approved
- [ ] Tests pass in CI
- [ ] Merged to `main`
