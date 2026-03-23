## Problem Statement

There is no web frontend for BID. This epic scaffolds the React TypeScript application
with routing, authentication, and base layout so that all subsequent UI epics have a
consistent foundation to build on.

## Scope

**In scope:**
- React 18 + TypeScript 5 + Vite project scaffold
- React Router v6 routing with protected routes
- Login / session / logout authentication flow (consuming Phase 1 JWT API)
- AppShell, Sidebar, and Header layout components
- Zustand state management store and typed API client
- GitHub Actions CI/CD pipeline (lint, type-check, unit tests, build)

**Out of scope:**
- Specific feature panels (Phase 4+)
- Production deployment (Phase 8)

## Acceptance Criteria

- [ ] `npm run build` completes without errors
- [ ] `npm run lint` passes with zero warnings
- [ ] Protected routes redirect unauthenticated users to `/login`
- [ ] CI pipeline runs on every pull request and passes
- [ ] Base layout renders correctly on 1280×800 and 1920×1080 viewports

## Dependencies

- **Milestone:** M3 — Frontend Shell (Phase 3)
- **Depends on:** Epic E1 (M1) for auth API endpoints

## Definition of Done

- [ ] Code reviewed and approved
- [ ] Acceptance criteria checked
- [ ] CI pipeline green
- [ ] `README.md` updated with frontend setup instructions
- [ ] Merged to `main`
