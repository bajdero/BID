## Problem Statement

After deploying 2.0.0 to production, the smoke test suite must run against the live
environment to confirm that all critical paths work before traffic is formally cut over.

## Scope

**In scope:**
- Run the same Playwright smoke suite used in PoC (M5) against production URL
- Verify login, project selection, batch processing, file browser

**Out of scope:**
- Full E2E suite (already run in CI against staging)

## Acceptance Criteria

- [ ] All smoke tests pass against production URL
- [ ] Test report attached to this issue
- [ ] Zero critical failures before go-live gate is closed

## Dependencies

- **Milestone:** M13 — Web Release 2.0.0 Production Deployment and Final Sign-off
- **Depends on:** REL-01 (production deployment)
- **Parent epic:** [Epic] Final Deployment and Sign-off (Release 2.0.0)

## Definition of Done

- [ ] Smoke tests pass in production
- [ ] Report attached
- [ ] Issue closed
