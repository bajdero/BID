## Problem Statement

The frontend shell provides structure but no actual functionality. This epic delivers the
primary interactive components that mirror the existing Tkinter panels, giving users
feature parity with the desktop application for project selection, export configuration,
queue monitoring, and settings management.

## Scope

**In scope:**
- Project/session selector component (replaces `bid/ui/project_selector.py`)
- Export profile configuration wizard (replaces `bid/ui/export_wizard.py`)
- Image processing queue display with live per-file status
- Settings and preferences panel (replaces `bid/ui/setup_wizard.py`)
- Toast notification system (replaces `bid/ui/toast.py`)
- Dark / light theme provider

**Out of scope:**
- FileBrowser and vector search (Phase 6)
- Event system UI (Phase 7)
- Processing Dashboard (Phase 5)

## Acceptance Criteria

- [ ] All export profile options from `export_option.json` are configurable in the wizard
- [ ] Queue shows per-file state: pending, processing, done, error
- [ ] Toast messages auto-dismiss after 5 s
- [ ] Settings changes persist via the Phase 1 API
- [ ] Components pass unit tests with React Testing Library

## Dependencies

- **Milestone:** M4 — Core UI Components (Phase 4)
- **Depends on:** Epic E3 (M3) Frontend Shell, Epic E1 (M1) API

## Definition of Done

- [ ] Code reviewed and approved
- [ ] Acceptance criteria checked
- [ ] Component unit tests pass in CI
- [ ] Storybook stories (or equivalent) for each component
- [ ] Merged to `main`
