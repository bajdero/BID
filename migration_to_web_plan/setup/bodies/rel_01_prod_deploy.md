## Problem Statement

All validation is complete. Release 2.0.0 must be deployed to production.

## Scope

**In scope:**
- Execute production deployment using runbook from P8-06
- Apply Kubernetes manifests to production cluster
- Database migration `alembic upgrade head` in production

**Out of scope:**
- Post-release monitoring setup (already in place from M11)

## Acceptance Criteria

- [ ] Production deployment completes without rollback
- [ ] All pods healthy (`kubectl get pods` shows Running)
- [ ] `GET /health` returns `{"status":"ok"}` in production
- [ ] Database migration completes without errors

## Dependencies

- **Milestone:** M13 — Web Release 2.0.0 Production Deployment and Final Sign-off
- **Depends on:** Gate G2 (Code Freeze), Epic E11 (M11) complete
- **Parent epic:** [Epic] Final Deployment and Sign-off (Release 2.0.0)

## Definition of Done

- [ ] Production deployment confirmed healthy
- [ ] Release 2.0.0 tag exists on GitHub
- [ ] Issue closed
