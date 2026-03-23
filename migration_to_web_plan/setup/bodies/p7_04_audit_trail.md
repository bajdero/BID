## Problem Statement

Auditors need an immutable record of all significant system actions (job started,
config changed, user logged in/out) presented as a chronological timeline.

## Scope

**In scope:**
- Audit trail timeline page showing actor, action, resource, timestamp
- Read-only (no edit/delete from UI)
- Export to CSV

**Out of scope:**
- Compliance reporting (deferred)

## Acceptance Criteria

- [ ] Timeline entries cannot be edited or deleted from the UI
- [ ] CSV export downloads all visible entries
- [ ] Audit entries sourced from `bid/events/` audit event types

## Dependencies

- **Milestone:** M9 — Event System UI (Phase 7)
- **Depends on:** P7-01
- **Parent epic:** [Epic] Phase 7 — Event System UI

## Definition of Done

- [ ] Code reviewed, tests pass, merged to `main`
