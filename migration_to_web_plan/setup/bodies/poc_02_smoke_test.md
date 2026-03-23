## Problem Statement

Before tagging the PoC release, a smoke test suite must confirm the critical user
journey works end-to-end on the staging environment.

## Scope

**In scope:**
- Playwright smoke tests: login → project select → start batch → verify progress → verify output
- Run against staging deployment

**Out of scope:**
- Full E2E suite (Phase 8)

## Acceptance Criteria

- [ ] Smoke suite passes with zero failures on staging
- [ ] Suite runs in < 5 minutes
- [ ] Results reported in CI artefacts

## Dependencies

- **Milestone:** M5 — PoC Release 2.0.0-rc1
- **Depends on:** POC-01 (integration), POC-04 (staging deploy)
- **Parent epic:** [Epic] PoC Release Readiness (2.0.0-rc1)

## Definition of Done

- [ ] Smoke tests pass on staging
- [ ] Test report committed to CI artefacts
- [ ] Issue closed
