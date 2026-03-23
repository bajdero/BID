# Prompt for GitHub Copilot - Create Milestones and Issues

Copy this prompt into GitHub Copilot Chat (in the repository root), then run the generated commands.

---

You are helping me set up GitHub milestones and issues for the BID web migration project.

## Inputs

- Use plan file: migration_to_web_plan/implementation_plan.md
- Use schedule file: migration_to_web_plan/github_milestones_and_issues_plan.md
- Hard deadline: 2027-03-10 (deployment and final validation complete)
- Existing release is 1.0.0; first web production release must be 2.0.0
- Language: English only

## Required outcomes

1. Create milestones with exact names and due dates:
   - M1 - Backend API Extraction (Phase 1) -> 2026-05-31
   - M2 - WebSocket Real-Time Layer (Phase 2) -> 2026-06-21
   - M3 - Frontend Shell (Phase 3) -> 2026-07-19
   - M4 - Core UI Components (Phase 4) -> 2026-09-06
   - M5 - PoC Release 2.0.0-rc1 -> 2026-09-20
   - M6 - Architecture and Implementation Audit -> 2026-10-04
   - M7 - Processing Dashboard (Phase 5) -> 2026-11-08
   - M8 - FileBrowser + Vector Search (Phase 6) -> 2026-12-06
   - M9 - Event System UI (Phase 7) -> 2027-01-10
   - M10 - Feature Freeze -> 2027-01-20
   - M11 - Test/Deploy Readiness (Phase 8) -> 2027-02-20
   - M12 - Code Freeze -> 2027-02-24
   - M13 - Web Release 2.0.0 Production Deployment and Final Sign-off -> 2027-03-10

2. Create one epic issue per phase plus release governance epics:
   - Phase 1 through Phase 8 epics
   - PoC Release Readiness epic
   - Post-PoC Architecture and Implementation Audit epic
   - Release Hardening epic (feature freeze to code freeze)
   - Final Deployment and Sign-off (Release 2.0.0) epic

3. For each epic, create child issues from deliverables in implementation_plan.md.

4. Ensure freeze gates are explicit issues:
   - Feature Freeze Gate (no new features after 2027-01-20)
   - Code Freeze Gate (only release blockers after 2027-02-24)
   - Go-Live Gate (deployment validation and rollback readiness)

5. Enforce sequence rule:
   - Architecture and implementation audit milestone/issues must start only after PoC release milestone is complete.
   - Final release issues must explicitly reference version 2.0.0

## Labels to apply

Create missing labels if needed and apply consistently:
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

## Issue template requirements

Each created issue must include:
- Problem statement
- Scope (in/out)
- Acceptance criteria (checklist)
- Dependencies (milestone + related issues)
- Definition of done

## Output format and execution steps

Step 1: First print a markdown table preview only:
- milestone
- due date
- issue title
- type label
- priority label
- dependency

Stop and wait for confirmation.

Step 2: After confirmation, print deterministic GitHub CLI commands only:
- `gh label create ...` for missing labels
- `gh api repos/:owner/:repo/milestones ...` or equivalent `gh` commands for milestones
- `gh issue create ...` commands for epics and child issues

Commands must be safe to run on Windows PowerShell.

Step 3: After command generation, print a short verification checklist:
- confirm milestone count = 13
- confirm freeze milestones exist
- confirm audit is after PoC
- confirm final milestone due date = 2027-03-10

## Copilot usage budget constraint (important)

Optimize for approximately 50% of monthly Copilot Pro usage:
- Keep output concise and deterministic
- No repeated full regenerations
- Monthly reset day is the 1st; batch execution as:
   - Batch A (day 1-10): M1-M4
   - Batch B (day 11-20): M5-M9
   - Batch C (day 21-end): M10-M13
- Max two refinement passes total

If any required repository detail is missing, ask focused questions before generating commands.

---

## Optional follow-up prompt (after preview)

Use this if you want Copilot to continue from Step 1:

Proceed with Step 2 and generate the PowerShell-safe `gh` commands now. Use the previously approved preview exactly; do not add extra issues.
