# BID Web Migration — GitHub Milestones and Issues Plan

## Milestone Schedule

| # | Milestone Title | Due Date | Phases / Purpose |
|---|----------------|----------|-----------------|
| M1 | M1 - Backend API Extraction (Phase 1) | 2026-05-31 | Phase 1 deliverables |
| M2 | M2 - WebSocket Real-Time Layer (Phase 2) | 2026-06-21 | Phase 2 deliverables |
| M3 | M3 - Frontend Shell (Phase 3) | 2026-07-19 | Phase 3 deliverables |
| M4 | M4 - Core UI Components (Phase 4) | 2026-09-06 | Phase 4 deliverables |
| M5 | M5 - PoC Release 2.0.0-rc1 | 2026-09-20 | PoC governance |
| M6 | M6 - Architecture and Implementation Audit | 2026-10-04 | Post-PoC audit (starts after M5) |
| M7 | M7 - Processing Dashboard (Phase 5) | 2026-11-08 | Phase 5 deliverables |
| M8 | M8 - FileBrowser + Vector Search (Phase 6) | 2026-12-06 | Phase 6 deliverables |
| M9 | M9 - Event System UI (Phase 7) | 2027-01-10 | Phase 7 deliverables |
| M10 | M10 - Feature Freeze | 2027-01-20 | Freeze gate |
| M11 | M11 - Test/Deploy Readiness (Phase 8) | 2027-02-20 | Phase 8 deliverables |
| M12 | M12 - Code Freeze | 2027-02-24 | Freeze gate |
| M13 | M13 - Web Release 2.0.0 Production Deployment and Final Sign-off | 2027-03-10 | Final release (hard deadline) |

---

## Labels

### Type labels

| Label | Color | Description |
|-------|-------|-------------|
| `type:epic` | #8B00FF | Epic issue grouping multiple child issues |
| `type:feature` | #0075CA | New feature or enhancement |
| `type:task` | #E4E669 | Non-code task (docs, config, planning) |
| `type:test` | #0E8A16 | Test implementation or test infrastructure |
| `type:infra` | #BFD4F2 | Infrastructure, CI/CD, DevOps work |
| `type:audit` | #D93F0B | Audit, review, or investigation |
| `type:release` | #C2E0C6 | Release governance, gates, sign-off |

### Priority labels

| Label | Color | Description |
|-------|-------|-------------|
| `priority:p0` | #B60205 | Critical — release blocker |
| `priority:p1` | #D93F0B | High — must complete in milestone |
| `priority:p2` | #FBCA04 | Medium — important but not blocking |

### Area labels

| Label | Color | Description |
|-------|-------|-------------|
| `area:backend` | #1D76DB | Backend / API work |
| `area:frontend` | #0075CA | Frontend / UI work |
| `area:devops` | #5319E7 | DevOps, CI/CD, infrastructure |
| `area:qa` | #0E8A16 | Quality assurance, testing |

---

## Epic Issues

| Epic Title | Milestone | Labels |
|------------|-----------|--------|
| [Epic] Phase 1 — Backend API Extraction | M1 | type:epic, priority:p1, area:backend |
| [Epic] Phase 2 — WebSocket Real-Time Layer | M2 | type:epic, priority:p1, area:backend |
| [Epic] Phase 3 — Frontend Shell | M3 | type:epic, priority:p1, area:frontend |
| [Epic] Phase 4 — Core UI Components | M4 | type:epic, priority:p1, area:frontend |
| [Epic] PoC Release Readiness (2.0.0-rc1) | M5 | type:epic, type:release, priority:p0, area:devops |
| [Epic] Post-PoC Architecture and Implementation Audit | M6 | type:epic, type:audit, priority:p1, area:backend |
| [Epic] Phase 5 — Processing Dashboard | M7 | type:epic, priority:p1, area:frontend |
| [Epic] Phase 6 — FileBrowser + Vector Search | M8 | type:epic, priority:p1, area:frontend |
| [Epic] Phase 7 — Event System UI | M9 | type:epic, priority:p1, area:frontend |
| [Epic] Release Hardening (Feature Freeze → Code Freeze) | M10 | type:epic, type:release, priority:p0, area:devops |
| [Epic] Phase 8 — Test/Deploy Readiness | M11 | type:epic, priority:p0, area:qa |
| [Epic] Final Deployment and Sign-off (Release 2.0.0) | M13 | type:epic, type:release, priority:p0, area:devops |

---

## Issue Template

Every issue (epic and child) must contain the following sections:

```markdown
## Problem Statement
<What problem does this issue solve?>

## Scope
**In scope:**
- <item>

**Out of scope:**
- <item>

## Acceptance Criteria
- [ ] <criterion 1>
- [ ] <criterion 2>

## Dependencies
- **Milestone:** <Mx>
- **Depends on:** #<issue number> <!-- list blocking issues -->
- **Blocks:** #<issue number>

## Definition of Done
- [ ] Code reviewed and approved
- [ ] Tests written and passing
- [ ] Documentation updated (if applicable)
- [ ] Milestone checklist updated
```

---

## Freeze Gates

| Gate Issue Title | Milestone | Labels |
|-----------------|-----------|--------|
| Feature Freeze Gate — no new features after 2027-01-20 | M10 | type:release, priority:p0, area:devops |
| Code Freeze Gate — only release blockers after 2027-02-24 | M12 | type:release, priority:p0, area:devops |
| Go-Live Gate — deployment validation and rollback readiness | M13 | type:release, priority:p0, area:devops |

---

## Sequence Constraints

1. **M6 (Architecture Audit)** must not start until **M5 (PoC Release 2.0.0-rc1)** is closed.
   - All M6 issues carry the note: *"Depends on: M5 - PoC Release 2.0.0-rc1 being complete."*

2. **M13 final release issues** must explicitly reference version **2.0.0** in their title or body.

3. Freeze gates are blocking issues:
   - Feature Freeze Gate blocks all new feature issues created after 2027-01-20.
   - Code Freeze Gate blocks any non-release-blocker merges after 2027-02-24.

---

## Copilot Usage Batching

| Batch | Days of Month | Milestones |
|-------|--------------|------------|
| A | 1–10 | M1–M4 |
| B | 11–20 | M5–M9 |
| C | 21–end | M10–M13 |

Max two refinement passes total per batch.
