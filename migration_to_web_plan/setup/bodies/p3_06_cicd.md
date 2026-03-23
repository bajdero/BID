## Problem Statement

Without automated CI, frontend regressions go undetected. A GitHub Actions pipeline
must run lint, type-check, unit tests, and build on every pull request.

## Scope

**In scope:**
- GitHub Actions workflow: lint → type-check → unit tests → build
- Caching of `node_modules` between runs
- Status check required before merge

**Out of scope:**
- E2E pipeline (Phase 8)
- Deployment pipeline (Phase 8)

## Acceptance Criteria

- [ ] Workflow runs on every PR targeting `main`
- [ ] Workflow fails if any step fails
- [ ] Build artefact uploaded for review

## Dependencies

- **Milestone:** M3 — Frontend Shell (Phase 3)
- **Depends on:** P3-01
- **Parent epic:** [Epic] Phase 3 — Frontend Shell

## Definition of Done

- [ ] CI workflow committed to `.github/workflows/frontend.yml`
- [ ] CI passes on `main`
- [ ] Merged to `main`
