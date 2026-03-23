## Problem Statement

The application should support dark and light themes, respecting the OS preference and allowing manual override.

## Scope

**In scope:**
- CSS variables for theme tokens, toggle in header, preference persisted to localStorage

**Out of scope:**
- Items explicitly listed as deferred

## Acceptance Criteria

- [ ] Default matches OS preference
- [ ] Toggle persists across page reloads
- [ ] All existing components render correctly in both themes

## Dependencies

- **Milestone:** M4 — Core UI Components (Phase 4)
- **Depends on:** P3-04 (layout)
- **Parent epic:** [Epic] Phase 4 — Core UI Components

## Definition of Done

- [ ] Code reviewed and approved
- [ ] Tests pass in CI
- [ ] Merged to `main`
