## Problem Statement

The API must be verifiably correct. A comprehensive unit test suite ensures that
regressions are caught early and the ≥ 80 % coverage target for Phase 1 is met.

## Scope

**In scope:**
- pytest unit tests for all Phase 1 API endpoints using `httpx.AsyncClient`
- Coverage report published in CI (GitHub Actions)
- Edge cases: invalid input, missing files, DB errors

**Out of scope:**
- End-to-end tests (Phase 8)
- Performance/load tests (Phase 8)

## Acceptance Criteria

- [ ] `pytest` passes with zero failures in CI
- [ ] Line coverage ≥ 80 % on the API module
- [ ] Coverage report uploaded as CI artefact

## Dependencies

- **Milestone:** M1 — Backend API Extraction (Phase 1)
- **Depends on:** P1-02, P1-03, P1-04, P1-05
- **Parent epic:** [Epic] Phase 1 — Backend API Extraction

## Definition of Done

- [ ] All tests pass in CI
- [ ] Coverage ≥ 80 % confirmed
- [ ] Merged to `main`
