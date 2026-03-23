## Problem Statement

Operators need to monitor system events in real time. The desktop `bid/ui/events_window.py`
must be reproduced as a live-updating web component powered by WebSocket.

## Scope

**In scope:**
- Real-time event log list showing type, severity, timestamp, message
- New events prepended at top without page reload
- Event severity colour-coding (info, warning, error)

**Out of scope:**
- Filtering (P7-02)

## Acceptance Criteria

- [ ] New events appear within 500 ms of occurrence
- [ ] Severity colour matches `bid/events/models.py` level values
- [ ] Log virtualized to handle > 1000 events without lag

## Dependencies

- **Milestone:** M9 — Event System UI (Phase 7)
- **Depends on:** P2-02 (event broadcast)
- **Parent epic:** [Epic] Phase 7 — Event System UI

## Definition of Done

- [ ] Code reviewed, tests pass, merged to `main`
