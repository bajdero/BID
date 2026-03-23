## Problem Statement

The PoC must be deployed to a staging environment accessible to stakeholders for review.

## Scope

**In scope:**
- Deploy backend FastAPI service and frontend React app to staging
- Configure staging environment variables
- Health check endpoint returning HTTP 200

**Out of scope:**
- Production deployment (M13)
- Kubernetes setup (Phase 8)

## Acceptance Criteria

- [ ] Staging URL accessible and returns HTTP 200 on health check
- [ ] Deployed version matches tag `2.0.0-rc1`

## Dependencies

- **Milestone:** M5 — PoC Release 2.0.0-rc1
- **Depends on:** POC-01
- **Parent epic:** [Epic] PoC Release Readiness (2.0.0-rc1)

## Definition of Done

- [ ] Staging deploy confirmed healthy
- [ ] URL shared with stakeholders
- [ ] Issue closed
