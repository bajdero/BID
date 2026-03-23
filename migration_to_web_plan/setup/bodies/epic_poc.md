## Problem Statement

Phases 1–4 have delivered a functional but unvalidated system. Before investing in
remaining feature development, stakeholders need to see a working end-to-end demo and
confirm the architecture is fit for purpose. This epic covers integration, smoke testing,
packaging, staging deployment, and the PoC demo for 2.0.0-rc1.

## Scope

**In scope:**
- End-to-end integration of frontend (Phase 3–4) with backend (Phase 1–2)
- Smoke test suite covering the critical user journey
- Release tag `2.0.0-rc1` on GitHub with changelog
- Deployment of `2.0.0-rc1` to staging environment
- PoC stakeholder demo and feedback collection

**Out of scope:**
- Post-PoC feature development (Phase 5–7)
- Architecture audit (M6, which starts after this milestone is complete)
- Production deployment (Phase 8)

## Acceptance Criteria

- [ ] User can log in, select a project, trigger batch processing, and see real-time progress
- [ ] Smoke test suite passes on staging with zero failures
- [ ] Release tag `2.0.0-rc1` exists on GitHub with a CHANGELOG entry
- [ ] Staging deployment URL is accessible and returns HTTP 200 on health check
- [ ] Demo conducted; feedback document filed in `docs/poc-feedback/`

## Dependencies

- **Milestone:** M5 — PoC Release 2.0.0-rc1
- **Depends on:** Epics E1–E4 (M1–M4) all complete

## Definition of Done

- [ ] All acceptance criteria checked
- [ ] `2.0.0-rc1` tag created and pushed
- [ ] Staging environment passing health checks
- [ ] Feedback document committed to repository
- [ ] Merged to `main`
