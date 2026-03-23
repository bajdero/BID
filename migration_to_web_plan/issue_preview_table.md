# BID Web Migration — Issue Preview Table (Step 1)

> **Step 1 output** as specified in the problem statement.  
> After reviewing this table, run `setup_github_resources.py` (Linux/macOS) or `setup_github_resources.ps1` (Windows PowerShell) to create all resources.

---

## Milestone Overview

| # | Milestone | Due Date |
|---|-----------|----------|
| M1 | M1 - Backend API Extraction (Phase 1) | 2026-05-31 |
| M2 | M2 - WebSocket Real-Time Layer (Phase 2) | 2026-06-21 |
| M3 | M3 - Frontend Shell (Phase 3) | 2026-07-19 |
| M4 | M4 - Core UI Components (Phase 4) | 2026-09-06 |
| M5 | M5 - PoC Release 2.0.0-rc1 | 2026-09-20 |
| M6 | M6 - Architecture and Implementation Audit | 2026-10-04 |
| M7 | M7 - Processing Dashboard (Phase 5) | 2026-11-08 |
| M8 | M8 - FileBrowser + Vector Search (Phase 6) | 2026-12-06 |
| M9 | M9 - Event System UI (Phase 7) | 2027-01-10 |
| M10 | M10 - Feature Freeze | 2027-01-20 |
| M11 | M11 - Test/Deploy Readiness (Phase 8) | 2027-02-20 |
| M12 | M12 - Code Freeze | 2027-02-24 |
| M13 | M13 - Web Release 2.0.0 Production Deployment and Final Sign-off | 2027-03-10 |

---

## Full Issue Preview Table

| Milestone | Due Date | Issue Title | Type Label | Priority | Dependency |
|-----------|----------|-------------|------------|----------|------------|
| M1 | 2026-05-31 | [Epic] Phase 1 — Backend API Extraction | type:epic | priority:p1 | — |
| M1 | 2026-05-31 | Extract image-processing core to service layer | type:feature | priority:p1 | Phase 1 epic |
| M1 | 2026-05-31 | Define REST API contract (OpenAPI/Swagger spec) | type:task | priority:p1 | Phase 1 epic |
| M1 | 2026-05-31 | Implement FastAPI application scaffold | type:feature | priority:p1 | Phase 1 epic |
| M1 | 2026-05-31 | Implement /jobs CRUD endpoints | type:feature | priority:p1 | Phase 1 epic |
| M1 | 2026-05-31 | Implement /export-profiles endpoints | type:feature | priority:p1 | Phase 1 epic |
| M1 | 2026-05-31 | Implement file-upload endpoint (/files/upload) | type:feature | priority:p1 | Phase 1 epic |
| M1 | 2026-05-31 | Implement processed-file download endpoint (/files/download/{id}) | type:feature | priority:p1 | Phase 1 epic |
| M1 | 2026-05-31 | Add API authentication (API-key header) | type:feature | priority:p1 | Phase 1 epic |
| M1 | 2026-05-31 | Containerise backend (Dockerfile + docker-compose) | type:infra | priority:p1 | Phase 1 epic |
| M1 | 2026-05-31 | Unit tests for all Phase 1 API endpoints | type:test | priority:p1 | Phase 1 epic |
| M2 | 2026-06-21 | [Epic] Phase 2 — WebSocket Real-Time Layer | type:epic | priority:p1 | Phase 1 epic |
| M2 | 2026-06-21 | Implement WebSocket server endpoint (/ws/jobs/{job_id}) | type:feature | priority:p1 | Phase 2 epic |
| M2 | 2026-06-21 | Define event schema (progress, complete, error, cancelled) | type:task | priority:p1 | Phase 2 epic |
| M2 | 2026-06-21 | Integrate event broadcasting into image-processing pipeline | type:feature | priority:p1 | Phase 2 epic |
| M2 | 2026-06-21 | Implement connection-lifecycle management (connect/disconnect/reconnect) | type:feature | priority:p1 | Phase 2 epic |
| M2 | 2026-06-21 | Add WebSocket authentication (token handshake) | type:feature | priority:p1 | Phase 2 epic |
| M2 | 2026-06-21 | Integration tests for WebSocket event flow | type:test | priority:p1 | Phase 2 epic |
| M3 | 2026-07-19 | [Epic] Phase 3 — Frontend Shell | type:epic | priority:p1 | Phase 2 epic |
| M3 | 2026-07-19 | Initialise frontend project (React + TypeScript + Vite) | type:feature | priority:p1 | Phase 3 epic |
| M3 | 2026-07-19 | Configure routing (React Router v6) | type:feature | priority:p1 | Phase 3 epic |
| M3 | 2026-07-19 | Set up global state management (Zustand) | type:feature | priority:p1 | Phase 3 epic |
| M3 | 2026-07-19 | Implement API client layer (axios + OpenAPI-generated types) | type:feature | priority:p1 | Phase 3 epic |
| M3 | 2026-07-19 | Implement WebSocket client hook with auto-reconnect | type:feature | priority:p1 | Phase 3 epic |
| M3 | 2026-07-19 | Create base layout: header, sidebar nav, main content area | type:feature | priority:p1 | Phase 3 epic |
| M3 | 2026-07-19 | Implement login / API-key entry screen | type:feature | priority:p1 | Phase 3 epic |
| M3 | 2026-07-19 | CI pipeline for frontend (lint + build + unit tests on PR) | type:infra | priority:p1 | Phase 3 epic |
| M4 | 2026-09-06 | [Epic] Phase 4 — Core UI Components | type:epic | priority:p1 | Phase 3 epic |
| M4 | 2026-09-06 | Settings panel (source folder, export folder, global options) | type:feature | priority:p1 | Phase 4 epic |
| M4 | 2026-09-06 | Export-profile manager (list, create, edit, delete profiles) | type:feature | priority:p1 | Phase 4 epic |
| M4 | 2026-09-06 | Source-folder browser (read-only tree view) | type:feature | priority:p1 | Phase 4 epic |
| M4 | 2026-09-06 | Job-creation wizard (select sources, choose profile, submit) | type:feature | priority:p1 | Phase 4 epic |
| M4 | 2026-09-06 | Job queue panel (list active and recent jobs with status) | type:feature | priority:p1 | Phase 4 epic |
| M4 | 2026-09-06 | Basic image-preview component (thumbnail + metadata) | type:feature | priority:p2 | Phase 4 epic |
| M4 | 2026-09-06 | Component unit tests for Phase 4 (React Testing Library) | type:test | priority:p1 | Phase 4 epic |
| M5 | 2026-09-20 | [Epic] PoC Release Readiness (2.0.0-rc1) | type:epic, type:release | priority:p0 | Phase 4 epic |
| M5 | 2026-09-20 | Release candidate build and smoke test (2.0.0-rc1) | type:release | priority:p0 | PoC epic |
| M5 | 2026-09-20 | Internal demo and stakeholder sign-off for PoC | type:task | priority:p0 | PoC epic |
| M6 | 2026-10-04 | [Epic] Post-PoC Architecture and Implementation Audit | type:epic, type:audit | priority:p1 | **M5 must be COMPLETE** |
| M6 | 2026-10-04 | Architecture review — backend API design and scalability | type:audit | priority:p1 | Audit epic, M5 complete |
| M6 | 2026-10-04 | Architecture review — frontend state and component model | type:audit | priority:p1 | Audit epic, M5 complete |
| M6 | 2026-10-04 | Security review — authentication and data flow | type:audit | priority:p0 | Audit epic, M5 complete |
| M6 | 2026-10-04 | Performance baseline — API latency and WebSocket throughput | type:audit | priority:p1 | Audit epic, M5 complete |
| M6 | 2026-10-04 | Audit findings report and remediation plan | type:task | priority:p1 | All M6 audit issues |
| M7 | 2026-11-08 | [Epic] Phase 5 — Processing Dashboard | type:epic | priority:p1 | Phase 4 epic, Audit epic |
| M7 | 2026-11-08 | Real-time per-job progress bar (via WebSocket) | type:feature | priority:p1 | Phase 5 epic |
| M7 | 2026-11-08 | Per-file status grid (queued / processing / done / error) | type:feature | priority:p1 | Phase 5 epic |
| M7 | 2026-11-08 | Aggregate statistics panel (throughput, ETA, error rate) | type:feature | priority:p2 | Phase 5 epic |
| M7 | 2026-11-08 | Error detail modal with retry / skip actions | type:feature | priority:p1 | Phase 5 epic |
| M7 | 2026-11-08 | Processing history log (paginated, filterable) | type:feature | priority:p2 | Phase 5 epic |
| M7 | 2026-11-08 | Dashboard E2E smoke test (Playwright) | type:test | priority:p1 | Phase 5 epic |
| M8 | 2026-12-06 | [Epic] Phase 6 — FileBrowser + Vector Search | type:epic | priority:p1 | Phase 5 epic |
| M8 | 2026-12-06 | Full file-browser component (navigate source and export trees) | type:feature | priority:p1 | Phase 6 epic |
| M8 | 2026-12-06 | Backend: generate and store image embedding vectors | type:feature | priority:p1 | Phase 6 epic |
| M8 | 2026-12-06 | Backend: vector-similarity search endpoint (/search/similar) | type:feature | priority:p1 | Phase 6 epic |
| M8 | 2026-12-06 | Frontend: similarity-search UI (upload query image, show results) | type:feature | priority:p1 | Phase 6 epic |
| M8 | 2026-12-06 | Metadata-filter sidebar (date, profile, author, status) | type:feature | priority:p2 | Phase 6 epic |
| M8 | 2026-12-06 | Integration tests for vector-search endpoint | type:test | priority:p1 | Phase 6 epic |
| M9 | 2027-01-10 | [Epic] Phase 7 — Event System UI | type:epic | priority:p1 | Phase 6 epic |
| M9 | 2027-01-10 | Event-log viewer (streaming table, filter by level/job/time) | type:feature | priority:p1 | Phase 7 epic |
| M9 | 2027-01-10 | In-app notification toasts (success / warning / error) | type:feature | priority:p1 | Phase 7 epic |
| M9 | 2027-01-10 | Alert management page (acknowledge, dismiss, history) | type:feature | priority:p2 | Phase 7 epic |
| M9 | 2027-01-10 | System-health indicators (backend uptime, queue depth, error rate) | type:feature | priority:p1 | Phase 7 epic |
| M9 | 2027-01-10 | Backend: structured event log API (/events) | type:feature | priority:p1 | Phase 7 epic |
| M9 | 2027-01-10 | E2E tests for event-log and notification flows | type:test | priority:p1 | Phase 7 epic |
| M10 | 2027-01-20 | [Epic] Release Hardening (Feature Freeze to Code Freeze) | type:epic, type:release | priority:p0 | Phase 7 epic |
| M10 | 2027-01-20 | **Feature Freeze Gate** — no new features after 2027-01-20 | type:release | priority:p0 | Hardening epic |
| M10 | 2027-01-20 | Regression test run against feature-freeze build | type:test | priority:p0 | Feature Freeze Gate |
| M11 | 2027-02-20 | [Epic] Phase 8 — Test/Deploy Readiness | type:epic | priority:p0 | Feature Freeze Gate |
| M11 | 2027-02-20 | Full E2E test suite (Playwright — happy path + edge cases) | type:test | priority:p0 | Phase 8 epic |
| M11 | 2027-02-20 | Performance / load tests (k6 — 50 concurrent jobs baseline) | type:test | priority:p0 | Phase 8 epic |
| M11 | 2027-02-20 | Security audit — OWASP Top-10 review and dependency scan | type:audit | priority:p0 | Phase 8 epic |
| M11 | 2027-02-20 | Production Dockerfile + docker-compose (multi-stage, non-root) | type:infra | priority:p0 | Phase 8 epic |
| M11 | 2027-02-20 | GitHub Actions CI/CD pipeline (test, build, push image, deploy) | type:infra | priority:p0 | Phase 8 epic |
| M11 | 2027-02-20 | Kubernetes / Compose production deployment manifests | type:infra | priority:p1 | Phase 8 epic |
| M11 | 2027-02-20 | Monitoring stack (Prometheus metrics + Grafana dashboard) | type:infra | priority:p1 | Phase 8 epic |
| M11 | 2027-02-20 | Runbook and operations guide | type:task | priority:p1 | Phase 8 epic |
| M12 | 2027-02-24 | **Code Freeze Gate** — only release blockers after 2027-02-24 | type:release | priority:p0 | Regression tests pass |
| M13 | 2027-03-10 | [Epic] Final Deployment and Sign-off (Release 2.0.0) | type:epic, type:release | priority:p0 | Phase 8 epic, Code Freeze Gate |
| M13 | 2027-03-10 | Production deployment of release 2.0.0 | type:release | priority:p0 | Final epic |
| M13 | 2027-03-10 | **Go-Live Gate** — deployment validation and rollback readiness | type:release | priority:p0 | 2.0.0 deployed |
| M13 | 2027-03-10 | Final stakeholder sign-off for release 2.0.0 | type:task | priority:p0 | Go-Live Gate |

---

## Counts

| Category | Count |
|----------|-------|
| Milestones | **13** |
| Epic issues | **12** |
| Child issues (deliverables) | **66** |
| Freeze gate issues | **3** (Feature Freeze, Code Freeze, Go-Live Gate) |
| **Total issues** | **81** |

---

## Verification Checklist (Step 3)

- [x] Milestone count = 13 ✓
- [x] Freeze milestones exist: M10 (Feature Freeze), M12 (Code Freeze) ✓
- [x] Go-Live Gate exists in M13 ✓
- [x] Architecture audit (M6) is after PoC release (M5): M6 due 2026-10-04 > M5 due 2026-09-20 ✓
- [x] Audit issues carry explicit dependency note: "M5 must be COMPLETE before this milestone begins" ✓
- [x] Final milestone due date = 2027-03-10 ✓
- [x] Final release issues reference version 2.0.0 ✓

---

## Sequence Constraints Summary

```
M5 (PoC 2.0.0-rc1) ──► M6 (Architecture Audit) — audit STARTS only after M5 closed
M7–M9 (Phases 5–7)  ──► M10 (Feature Freeze) ──► M11 (Phase 8) ──► M12 (Code Freeze) ──► M13 (2.0.0 Production)
                                                                                              Hard deadline: 2027-03-10
```
