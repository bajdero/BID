## Problem Statement

The `bid/events/` subsystem (`bid/ui/events_window.py`) provides a rich event log in the
desktop application. The web migration must expose this as a real-time, filterable event
viewer so operators can monitor processing activity, diagnose problems, and maintain an
immutable audit trail.

## Scope

**In scope:**
- Real-time event log viewer powered by the Phase 2 WebSocket layer
- Filtering by event type, severity level, and date range
- In-app and email notification preferences per event type
- Audit trail and activity timeline display (immutable from UI)

**Out of scope:**
- Event schema changes (separate backend task)
- Mobile layout (deferred)

## Acceptance Criteria

- [ ] New events appear in the viewer within 500 ms of occurrence
- [ ] Filters apply without a full page reload
- [ ] Audit trail entries cannot be edited or deleted from the UI
- [ ] Notification preferences persist via the API

## Dependencies

- **Milestone:** M9 — Event System UI (Phase 7)
- **Depends on:** Epic E8 (M8) FileBrowser + Vector Search

## Definition of Done

- [ ] Code reviewed and approved
- [ ] Acceptance criteria checked
- [ ] Tests pass in CI
- [ ] Merged to `main`
