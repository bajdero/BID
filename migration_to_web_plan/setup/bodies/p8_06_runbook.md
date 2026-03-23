## Problem Statement

The operations team needs a runbook to deploy, monitor, and roll back the application
in production without requiring engineering involvement for routine operations.

## Scope

**In scope:**
- Deployment procedure (step-by-step with commands)
- Rollback procedure (tested in pre-production)
- Common failure scenarios and remediation steps
- Escalation contacts

**Out of scope:**
- Auto-remediation scripts (deferred)

## Acceptance Criteria

- [ ] Runbook committed to `docs/ops/runbook.md`
- [ ] Rollback procedure executed successfully in a staging dry run
- [ ] Reviewed by at least one operations team member

## Dependencies

- **Milestone:** M11 — Test/Deploy Readiness (Phase 8)
- **Depends on:** P8-04, P8-05
- **Parent epic:** [Epic] Phase 8 — Test/Deploy Readiness

## Definition of Done

- [ ] Runbook merged to `main`
- [ ] Rollback dry run documented
- [ ] Issue closed
