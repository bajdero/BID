## Problem Statement

The system must handle concurrent users without exceeding the performance SLO
established in the M6 baseline. k6 load tests validate this.

## Scope

**In scope:**
- k6 scripts simulating 50 concurrent users for 10 minutes
- Scenarios: API CRUD, batch processing trigger, WebSocket connection
- Pass/fail threshold: p95 API latency < 200 ms

**Out of scope:**
- Stress testing beyond 50 concurrent users (deferred to 2.1.0)

## Acceptance Criteria

- [ ] All k6 scenarios complete without HTTP errors > 1 %
- [ ] p95 API response time < 200 ms under 50 concurrent users
- [ ] Load test report committed to `docs/performance/`

## Dependencies

- **Milestone:** M11 — Test/Deploy Readiness (Phase 8)
- **Depends on:** P8-03 (Docker), P8-04 (infra) for staging environment
- **Parent epic:** [Epic] Phase 8 — Test/Deploy Readiness

## Definition of Done

- [ ] Load test passes thresholds
- [ ] Report committed to `docs/performance/`
- [ ] Merged to `main`
