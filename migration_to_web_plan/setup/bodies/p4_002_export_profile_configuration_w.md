## Problem Statement

Users configure export profiles (format, quality, logo settings). This replaces `bid/ui/export_wizard.py` with a multi-step web wizard.

## Scope

**In scope:**
- All options from export_option.json: format, quality, logo required/placement/size; create/edit/delete profiles

**Out of scope:**
- Items explicitly listed as deferred

## Acceptance Criteria

- [ ] All export options from export_option.json configurable
- [ ] Validation prevents invalid combinations
- [ ] Profile saved via API
- [ ] Wizard tests pass

## Dependencies

- **Milestone:** M4 — Core UI Components (Phase 4)
- **Depends on:** P1-03 (session/config API), P3-05
- **Parent epic:** [Epic] Phase 4 — Core UI Components

## Definition of Done

- [ ] Code reviewed and approved
- [ ] Tests pass in CI
- [ ] Merged to `main`
