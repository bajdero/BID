## Problem Statement

All authenticated pages need a consistent chrome: header with user info, collapsible
sidebar navigation, and a main content area. This must be responsive and accessible.

## Scope

**In scope:**
- `AppShell` layout component wrapping all authenticated pages
- `Header` with app title, user avatar, logout button
- `Sidebar` with navigation links (Projects, Dashboard, Files, Events, Settings)
- Responsive collapse on < 768 px viewport

**Out of scope:**
- Individual page content

## Acceptance Criteria

- [ ] Layout renders correctly on 768 px, 1280 px, and 1920 px viewports
- [ ] Sidebar collapses to icons on < 768 px
- [ ] Keyboard navigation works (tab order, focus ring)

## Dependencies

- **Milestone:** M3 — Frontend Shell (Phase 3)
- **Depends on:** P3-01
- **Parent epic:** [Epic] Phase 3 — Frontend Shell

## Definition of Done

- [ ] Code reviewed and approved
- [ ] Tests pass in CI
- [ ] Merged to `main`
