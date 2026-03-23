# BID Web Migration - GitHub Milestones and Issues Plan

Version: 1.1  
Date: 2026-03-23

## Goal

Create a practical GitHub milestones + issues rollout plan based on the migration phases, with:
- PoC release included
- Architecture + implementation audit immediately after PoC
- Feature freeze + code freeze explicitly scheduled
- Full deployment and test completion by 2027-03-10
- Existing release lineage respected: current release is 1.0.0, first web production release is 2.0.0

## Scheduling Assumptions

- Project start: 2026-03-24
- Hard deadline: 2027-03-10 (deployment + final validation complete)
- Dates below are target due dates for milestones
- 7-14 day buffer is preserved near release for stabilization

## Proposed Milestones

| Order | Milestone | Due Date | Scope |
|---|---|---|---|
| 1 | M1 - Backend API Extraction (Phase 1) | 2026-05-31 | FastAPI layer, models, routers, auth baseline, API tests start |
| 2 | M2 - WebSocket Real-Time Layer (Phase 2) | 2026-06-21 | WS manager, project channels, processing and monitor broadcasts |
| 3 | M3 - Frontend Shell (Phase 3) | 2026-07-19 | Next.js scaffold, auth flow, dashboard skeleton, API client |
| 4 | M4 - Core UI Components (Phase 4) | 2026-09-06 | Source tree, details panel, preview, source page integration |
| 5 | M5 - PoC Release 2.0.0-rc1 | 2026-09-20 | End-to-end demo path: login -> project -> sources -> process |
| 6 | M6 - Architecture and Implementation Audit | 2026-10-04 | Post-PoC technical audit, findings, risk register, corrective backlog |
| 7 | M7 - Processing Dashboard (Phase 5) | 2026-11-08 | Processing control center, export profiles UI, toasts, live progress |
| 8 | M8 - FileBrowser + Vector Search (Phase 6) | 2026-12-06 | FileBrowser proxy auth, iframe integration, vector service wiring |
| 9 | M9 - Event System UI (Phase 7) | 2027-01-10 | Sources, timeline, annotation flow, assignment and folder map |
| 10 | M10 - Feature Freeze | 2027-01-20 | No new features; only bug fixes and hardening |
| 11 | M11 - Test/Deploy Readiness (Phase 8) | 2027-02-20 | API + E2E coverage, CI/CD, Docker prod config, docs |
| 12 | M12 - Code Freeze | 2027-02-24 | Only release-blocker fixes allowed |
| 13 | M13 - Web Release 2.0.0 Production Deployment and Final Sign-off | 2027-03-10 | Deployment complete, verification complete, release 2.0.0 signed off |

## Recommended Issue Structure

Use one epic issue per phase and child issues per deliverable group.

### Epics

- Epic: Phase 1 - Backend API Extraction
- Epic: Phase 2 - WebSocket Real-Time Layer
- Epic: Phase 3 - Frontend Shell
- Epic: Phase 4 - Core UI Components
- Epic: Phase 5 - Processing Dashboard
- Epic: Phase 6 - FileBrowser + Vector Search
- Epic: Phase 7 - Event System UI
- Epic: Phase 8 - Testing and Deployment
- Epic: PoC Release Readiness
- Epic: Post-PoC Architecture and Implementation Audit
- Epic: Release Hardening (Feature Freeze to Code Freeze)
- Epic: Final Deployment and Sign-off (Release 2.0.0)

### Labels

- type:epic
- type:feature
- type:task
- type:test
- type:infra
- type:audit
- type:release
- priority:p0
- priority:p1
- priority:p2
- area:backend
- area:frontend
- area:devops
- area:qa

### Priority Rules

- P0: blockers for PoC, freeze gates, or final deployment
- P1: planned scope for current milestone
- P2: deferred improvements or non-blocking refactors

## Freeze Policy

### Feature Freeze (2027-01-20)

- No new scope merged after this date without explicit waiver
- Allowed: bug fixes, test stabilization, performance tuning, security patches
- Any exception must reference release-risk analysis

### Code Freeze (2027-02-24)

- Default: no code changes
- Allowed only for release blockers (severity critical/high)
- Every exception requires:
  - linked incident/defect issue
  - rollback plan
  - targeted regression test evidence

## PoC and Audit Gate

### PoC Release Criteria (target 2026-09-20)

- Demo path works on clean environment
- No critical auth, data-loss, or processing crash bugs
- Baseline telemetry/logging enabled
- Tag candidate prepared as 2.0.0-rc1

### Audit Scope (2026-09-21 to 2026-10-04)

- Architecture review: boundaries, scalability, failure modes
- Implementation review: correctness, security, maintainability
- Test and deployment posture review
- Output artifacts:
  - audit report
  - ranked findings
  - mandatory remediation issues mapped to milestones

## Copilot Pro Usage Budget (Target ~50% Monthly)

Because exact Copilot quota telemetry is user-plan and UI dependent, use a staged workflow to keep usage near half of monthly budget.

Monthly reset day: 1st day of each month.

### Usage-Control Strategy

1. Session A (Planning, ~20-25%):
   - Ask Copilot to produce milestone + issue draft only (no retries, no iterative expansion)
   - Review and accept once

2. Session B (Execution, ~20-25%):
   - Ask Copilot to generate deterministic `gh` commands for milestones/issues
   - Run once, then only minimal correction pass

3. Reserve (~5-10%):
   - Keep headroom for post-creation fixes (dates, labels, assignments)

### Month-Split Execution Plan (reset on day 1)

1. Window A (days 1-10):
   - Milestones M1-M4 and related epics/issues
   - Target Copilot usage: 20-25% of monthly quota

2. Window B (days 11-20):
   - Milestones M5-M9 and related epics/issues
   - Target Copilot usage: 20-25% of monthly quota

3. Window C (days 21-end):
   - Milestones M10-M13, freeze gates, release 2.0.0 governance issues
   - Target Copilot usage: 5-10% of monthly quota

### Practical Limits

- Keep prompts under 1 large instruction block plus 1 refinement
- Request table or JSON output first, then command output second
- Avoid repeated "regenerate all" loops
- Batch issue creation by milestone (not all phases at once)

## Creation Order in Repository

1. Create milestones M1-M13 with due dates.
2. Create epic issues and attach each to the correct milestone.
3. Create child issues from deliverables in `implementation_plan.md`.
4. Link each child issue to its parent epic and acceptance criteria.
5. Add freeze gate checklist issues:
   - Feature freeze gate
   - Code freeze gate
   - Final go/no-go
6. Prepare final release milestone and checklist under release version 2.0.0.

## Suggested Gate Issues

- Release Gate: PoC go/no-go checklist
- Audit Gate: architecture + implementation review completion
- Feature Freeze Gate: open P0/P1 defect threshold check
- Code Freeze Gate: release candidate validation
- Production Go-Live Gate: deployment validation, rollback readiness, sign-off
