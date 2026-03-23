## Problem Statement

As of 2027-02-24 the BID 2.0.0 codebase must be frozen. Only release-blocker fixes
(P0 severity) may be merged to `main` after this date. This gate issue enforces
that policy and confirms readiness for production deployment.

## Scope

**In scope:**
- Enforcing the code freeze from 2027-02-24 onwards
- Reviewing and approving any exception request (release-blocker only)
- Confirming all E2E and load tests pass on the frozen codebase
- Confirming the release candidate build is signed off

**Out of scope:**
- New features (blocked since Feature Freeze 2027-01-20)
- Non-blocker bug fixes (deferred to 2.0.x maintenance)

## Acceptance Criteria

- [ ] All non-blocker open issues are moved to milestone `2.0.x` or closed
- [ ] E2E test suite passes on the frozen `main` branch
- [ ] Load tests validate performance SLO (p95 < 200 ms under 50 users)
- [ ] Release build artefact signed and stored
- [ ] This gate issue is closed on or after 2027-02-24 by the project lead

## Dependencies

- **Milestone:** M12 — Code Freeze
- **Depends on:** Epic E11 (M11) — Test/Deploy Readiness complete

## Definition of Done

- [ ] No non-blocker PRs merged after 2027-02-24
- [ ] Release build artefact produced and verified
- [ ] Gate issue closed by project lead
