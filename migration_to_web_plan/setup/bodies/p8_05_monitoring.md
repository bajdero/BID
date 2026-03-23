## Problem Statement

Without observability, production incidents are hard to detect and diagnose.
Health checks and telemetry must be in place before go-live.

## Scope

**In scope:**
- `GET /health` and `GET /ready` endpoints returning structured JSON
- OpenTelemetry traces and metrics exported to Prometheus
- Grafana dashboard for API latency, error rate, job throughput
- Alerting rules for p95 > 500 ms and error rate > 5 %

**Out of scope:**
- Log aggregation (deferred to 2.0.x)

## Acceptance Criteria

- [ ] Health endpoints return `{"status":"ok"}` under normal conditions
- [ ] Prometheus scrapes metrics every 15 s
- [ ] Grafana dashboard committed to `deploy/grafana/`
- [ ] Alerting rules fire in a test simulation

## Dependencies

- **Milestone:** M11 — Test/Deploy Readiness (Phase 8)
- **Depends on:** P8-04 (k8s infra)
- **Parent epic:** [Epic] Phase 8 — Test/Deploy Readiness

## Definition of Done

- [ ] Health endpoints deployed
- [ ] Grafana dashboard committed
- [ ] Alerting rules tested
- [ ] Merged to `main`
