## Problem Statement

Users need non-blocking feedback for operations (success, warning, error). Replaces `bid/ui/toast.py`.

## Scope

**In scope:**
- Toast component with auto-dismiss (5 s), max 3 simultaneous toasts, types: info/success/warning/error

**Out of scope:**
- Items explicitly listed as deferred

## Acceptance Criteria

- [ ] Toast auto-dismisses after 5 s
- [ ] At most 3 toasts visible simultaneously
- [ ] Accessible (role=alert)
- [ ] Component tests pass

## Dependencies

- **Milestone:** M4 — Core UI Components (Phase 4)
- **Depends on:** P3-01
- **Parent epic:** [Epic] Phase 4 — Core UI Components

## Definition of Done

- [ ] Code reviewed and approved
- [ ] Tests pass in CI
- [ ] Merged to `main`
