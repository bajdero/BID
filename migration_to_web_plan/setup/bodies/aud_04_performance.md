## Problem Statement

There is no performance baseline for the web system. Without one, regression detection
during Phase 5–7 development is impossible.

## Scope

**In scope:**
- API response time measurements (p50, p95, p99) under light load
- WebSocket message latency measurement
- Frontend Lighthouse scores (Performance, Accessibility)
- Bottleneck identification

**Out of scope:**
- Load testing under production-level traffic (Phase 8)

## Acceptance Criteria

- [ ] Baseline measurements committed to `docs/audit/performance-baseline.md`
- [ ] p95 API latency documented for all Phase 1 endpoints
- [ ] Lighthouse scores documented for main pages

## Dependencies

- **Milestone:** M6 — Architecture and Implementation Audit
- **Depends on:** AUD-01, AUD-02
- **Parent epic:** [Epic] Post-PoC Architecture and Implementation Audit

## Definition of Done

- [ ] `docs/audit/performance-baseline.md` merged to `main`
- [ ] Issue closed
