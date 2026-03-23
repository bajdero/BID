## Problem Statement

Unit and integration tests do not catch cross-layer regressions. A Playwright E2E
suite validates the complete user journey from browser to database.

## Scope

**In scope:**
- Playwright tests for: login, project CRUD, batch processing, file browser, event log
- Tests run against the staging environment in CI
- Zero-flakiness requirement

**Out of scope:**
- Performance testing (P8-02)

## Acceptance Criteria

- [ ] E2E suite covers all critical paths defined in the smoke test plan
- [ ] Suite runs in < 15 minutes in CI
- [ ] Flakiness rate = 0 over 5 consecutive CI runs
- [ ] Tests run as a required CI gate before merge to `main`

## Dependencies

- **Milestone:** M11 — Test/Deploy Readiness (Phase 8)
- **Depends on:** Epic E10 (M10) Release Hardening
- **Parent epic:** [Epic] Phase 8 — Test/Deploy Readiness

## Definition of Done

- [ ] E2E suite committed to `tests/e2e/`
- [ ] CI gate configured
- [ ] Zero flaky tests confirmed
- [ ] Merged to `main`
