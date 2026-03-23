## Problem Statement

All features are complete and hardened. The system must now be validated end-to-end,
containerised, and deployed to production infrastructure with monitoring and rollback
capability before the Code Freeze deadline on 2027-02-24.

## Scope

**In scope:**
- End-to-end Playwright test suite covering all critical user journeys
- Load and performance testing (k6) validating the performance baseline from M6
- Docker containerisation of backend and frontend
- Kubernetes production infrastructure configuration
- Health check endpoints and observability stack (OpenTelemetry, Prometheus, Grafana)
- Operations runbook and rollback procedures

**Out of scope:**
- New features
- Production go-live (M13)

## Acceptance Criteria

- [ ] Playwright E2E suite covers login → project → batch processing → results with zero flaky tests
- [ ] p95 API response time < 200 ms under 50 concurrent simulated users (k6)
- [ ] Docker images build and pass smoke tests in CI
- [ ] Kubernetes manifests deploy successfully to staging
- [ ] Rollback procedure tested and documented in runbook
- [ ] All health check endpoints return 200 under normal conditions

## Dependencies

- **Milestone:** M11 — Test/Deploy Readiness (Phase 8)
- **Depends on:** Epic E10 (M10) Release Hardening

## Definition of Done

- [ ] All acceptance criteria checked
- [ ] E2E and load tests pass in CI
- [ ] Runbook committed to `docs/ops/`
- [ ] Production infrastructure provisioned and validated on staging
- [ ] Merged to `main`
