## Problem Statement

Users need to select an existing project or create a new one before processing. This component replaces `bid/ui/project_selector.py`.

## Scope

**In scope:**
- Project list fetched from Phase 1 API, session list within a project, create/rename/delete project, loading skeleton

**Out of scope:**
- Items explicitly listed as deferred

## Acceptance Criteria

- [ ] Lists all projects from API
- [ ] User can create, rename, delete a project
- [ ] Selecting a project updates global Zustand store
- [ ] Component tests pass

## Dependencies

- **Milestone:** M4 — Core UI Components (Phase 4)
- **Depends on:** P3-05 (API client), P1-03 (project API)
- **Parent epic:** [Epic] Phase 4 — Core UI Components

## Definition of Done

- [ ] Code reviewed and approved
- [ ] Tests pass in CI
- [ ] Merged to `main`
