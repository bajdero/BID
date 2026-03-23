## Problem Statement

Phases 1–4 have been developed in parallel tracks that have never been run together.
End-to-end integration connects the React frontend to the FastAPI backend and WebSocket
layer to produce the first complete working system.

## Scope

**In scope:**
- CORS configuration on the backend for the frontend origin
- Environment configuration (API base URL, WS URL) for staging
- Resolving all integration-breaking issues found during wiring

**Out of scope:**
- New features

## Acceptance Criteria

- [ ] User can log in via the web UI
- [ ] User can select a project and trigger a batch processing job
- [ ] Real-time progress updates appear in the queue display
- [ ] Processing completes and results are viewable

## Dependencies

- **Milestone:** M5 — PoC Release 2.0.0-rc1
- **Depends on:** Epics E1–E4 (M1–M4)
- **Parent epic:** [Epic] PoC Release Readiness (2.0.0-rc1)

## Definition of Done

- [ ] End-to-end user journey works on staging
- [ ] Issues found and filed
- [ ] Merged to `main`
