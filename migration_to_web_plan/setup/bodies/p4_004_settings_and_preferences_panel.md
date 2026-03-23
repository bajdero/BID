## Problem Statement

Users need a settings page to configure source/export directories and application preferences. Replaces `bid/ui/setup_wizard.py`.

## Scope

**In scope:**
- Source folder path, export folder path, log level, source != export validation

**Out of scope:**
- Items explicitly listed as deferred

## Acceptance Criteria

- [ ] Source path and export path cannot be the same (validation error shown)
- [ ] Settings persisted via API
- [ ] Settings panel tests pass

## Dependencies

- **Milestone:** M4 — Core UI Components (Phase 4)
- **Depends on:** P1-03, P3-05
- **Parent epic:** [Epic] Phase 4 — Core UI Components

## Definition of Done

- [ ] Code reviewed and approved
- [ ] Tests pass in CI
- [ ] Merged to `main`
