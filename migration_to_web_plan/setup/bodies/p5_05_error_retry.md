## Problem Statement

When individual files fail, operators need to see the error details and retry
processing without re-submitting the entire batch.

## Scope

**In scope:**
- Error details panel (error message, stack trace excerpt, file path)
- Retry button per failed file
- Retry-all button for batch

**Out of scope:**
- Root cause analysis tooling (out of scope for v2.0.0)

## Acceptance Criteria

- [ ] Error message displayed for each failed file
- [ ] Retry re-queues only the failed files
- [ ] Retry status reflected via WebSocket events

## Dependencies

- **Milestone:** M7 — Processing Dashboard (Phase 5)
- **Depends on:** P5-01
- **Parent epic:** [Epic] Phase 5 — Processing Dashboard

## Definition of Done

- [ ] Code reviewed, tests pass, merged to `main`
