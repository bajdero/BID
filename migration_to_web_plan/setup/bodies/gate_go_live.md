## Problem Statement

Before traffic is switched to the new BID 2.0.0 production environment, a formal Go-Live
Gate must be passed. This gate validates that the deployment is healthy, monitoring is
active, and rollback can be executed within the agreed RTO if needed.

## Scope

**In scope:**
- Production deployment health check (all services, endpoints, DB connectivity)
- Rollback readiness verification (procedure tested, team briefed)
- Monitoring and alerting active (Prometheus alerts firing correctly in test)
- Stakeholder and operations team sign-off before traffic cut-over

**Out of scope:**
- Post-go-live monitoring (ongoing operations)
- Feature changes

## Acceptance Criteria

- [ ] All production health check endpoints return HTTP 200
- [ ] Rollback procedure executed successfully in pre-production dry run
- [ ] Prometheus/Grafana dashboards show zero critical alerts
- [ ] Operations team confirms they can execute rollback within 15 minutes
- [ ] Project lead signs off on go-live
- [ ] This gate issue is closed only after traffic cut-over succeeds

## Dependencies

- **Milestone:** M13 — Web Release 2.0.0 Production Deployment and Final Sign-off
- **Depends on:** Gate G2 (Code Freeze), Epic E12 (M13) Final Deployment

## Definition of Done

- [ ] All acceptance criteria checked and signed off
- [ ] Go-live completed without rollback
- [ ] Gate issue closed by project lead
