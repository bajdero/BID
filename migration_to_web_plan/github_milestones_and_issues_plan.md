# BID Web Migration — GitHub Milestones and Issues Plan

**Project:** BID 2.0.0 Web Migration  
**Planning date:** 2026-03-23  
**Hard deadline:** 2027-03-10

---

## Milestone Summary (13 milestones)

| # | Milestone | Due Date | Description |
|---|-----------|----------|-------------|
| M1 | Backend API Extraction (Phase 1) | 2026-05-31 | REST API extraction from Python desktop core |
| M2 | WebSocket Real-Time Layer (Phase 2) | 2026-06-21 | Real-time event streaming over WebSocket |
| M3 | Frontend Shell (Phase 3) | 2026-07-19 | React/TS scaffold with routing, auth, layout |
| M4 | Core UI Components (Phase 4) | 2026-09-06 | Primary interactive panels and wizards |
| M5 | PoC Release 2.0.0-rc1 | 2026-09-20 | End-to-end PoC — stakeholder validation |
| M6 | Architecture and Implementation Audit | 2026-10-04 | Post-PoC audit (starts after M5 is complete) |
| M7 | Processing Dashboard (Phase 5) | 2026-11-08 | Batch processing control centre |
| M8 | FileBrowser + Vector Search (Phase 6) | 2026-12-06 | Web file browser and vector image search |
| M9 | Event System UI (Phase 7) | 2027-01-10 | Web UI for the BID event subsystem |
| M10 | Feature Freeze | 2027-01-20 | **Gate: no new features after this date** |
| M11 | Test/Deploy Readiness (Phase 8) | 2027-02-20 | E2E tests, containerisation, prod infra |
| M12 | Code Freeze | 2027-02-24 | **Gate: only release blockers after this date** |
| M13 | Web Release 2.0.0 Production Deployment and Final Sign-off | 2027-03-10 | Production go-live and 2.0.0 release |

---

## Issue Inventory

### Epics (12 epic issues)

| Epic # | Title | Milestone | Labels | Priority |
|--------|-------|-----------|--------|----------|
| E1 | [Epic] Phase 1 — Backend API Extraction | M1 | type:epic, area:backend | p0 |
| E2 | [Epic] Phase 2 — WebSocket Real-Time Layer | M2 | type:epic, area:backend | p0 |
| E3 | [Epic] Phase 3 — Frontend Shell | M3 | type:epic, area:frontend | p0 |
| E4 | [Epic] Phase 4 — Core UI Components | M4 | type:epic, area:frontend | p0 |
| E5 | [Epic] PoC Release Readiness (2.0.0-rc1) | M5 | type:epic, type:release | p0 |
| E6 | [Epic] Post-PoC Architecture and Implementation Audit | M6 | type:epic, type:audit | p0 |
| E7 | [Epic] Phase 5 — Processing Dashboard | M7 | type:epic, area:frontend | p0 |
| E8 | [Epic] Phase 6 — FileBrowser + Vector Search | M8 | type:epic, area:frontend | p0 |
| E9 | [Epic] Phase 7 — Event System UI | M9 | type:epic, area:frontend | p0 |
| E10 | [Epic] Release Hardening (Feature Freeze → Code Freeze) | M10 | type:epic, type:release | p0 |
| E11 | [Epic] Phase 8 — Test/Deploy Readiness | M11 | type:epic, area:qa | p0 |
| E12 | [Epic] Final Deployment and Sign-off (Release 2.0.0) | M13 | type:epic, type:release | p0 |

### Freeze Gate Issues (3 gate issues)

| Gate | Title | Milestone | Labels | Priority |
|------|-------|-----------|--------|----------|
| G1 | Feature Freeze Gate — no new features after 2027-01-20 | M10 | type:release, priority:p0 | p0 |
| G2 | Code Freeze Gate — only release blockers after 2027-02-24 | M12 | type:release, priority:p0 | p0 |
| G3 | Go-Live Gate — deployment validation and rollback readiness | M13 | type:release, priority:p0 | p0 |

### Child Issues per Phase

#### Phase 1 — Backend API Extraction (M1)

| ID | Title | Labels | Priority |
|----|-------|--------|----------|
| P1-01 | Design REST API specification (OpenAPI 3.0) for BID operations | type:task, area:backend | p1 |
| P1-02 | Extract image processing pipeline to FastAPI service | type:feature, area:backend | p0 |
| P1-03 | Implement project and session management API endpoints | type:feature, area:backend | p0 |
| P1-04 | Add JWT authentication and authorisation middleware | type:feature, area:backend | p1 |
| P1-05 | Create database abstraction layer (SQLite → PostgreSQL) | type:infra, area:backend | p1 |
| P1-06 | Write unit tests for all API endpoints (≥ 80% coverage) | type:test, area:backend | p1 |

#### Phase 2 — WebSocket Real-Time Layer (M2)

| ID | Title | Labels | Priority |
|----|-------|--------|----------|
| P2-01 | Implement WebSocket server (FastAPI + asyncio) | type:feature, area:backend | p0 |
| P2-02 | Adapt bid/events system to broadcast over WebSocket | type:feature, area:backend | p0 |
| P2-03 | Stream per-file and batch processing progress to clients | type:feature, area:backend | p1 |
| P2-04 | Add heartbeat and automatic client reconnect mechanism | type:feature, area:backend | p1 |
| P2-05 | Write WebSocket integration tests | type:test, area:backend | p1 |

#### Phase 3 — Frontend Shell (M3)

| ID | Title | Labels | Priority |
|----|-------|--------|----------|
| P3-01 | Bootstrap React + TypeScript + Vite project | type:infra, area:frontend | p0 |
| P3-02 | Configure client-side routing (React Router v6) | type:feature, area:frontend | p1 |
| P3-03 | Implement authentication flow (login, session, logout) | type:feature, area:frontend | p0 |
| P3-04 | Create base layout components (AppShell, Sidebar, Header) | type:feature, area:frontend | p1 |
| P3-05 | Set up state management (Zustand) and API client (fetch/axios) | type:infra, area:frontend | p1 |
| P3-06 | Configure GitHub Actions CI/CD pipeline for frontend | type:infra, area:devops | p1 |

#### Phase 4 — Core UI Components (M4)

| ID | Title | Labels | Priority |
|----|-------|--------|----------|
| P4-01 | Project/session selector component | type:feature, area:frontend | p0 |
| P4-02 | Export profile configuration wizard | type:feature, area:frontend | p0 |
| P4-03 | Image processing queue display with live status | type:feature, area:frontend | p0 |
| P4-04 | Settings and preferences panel | type:feature, area:frontend | p1 |
| P4-05 | Toast notification system | type:feature, area:frontend | p1 |
| P4-06 | Theme provider (dark / light mode) | type:feature, area:frontend | p2 |

#### PoC Release (M5)

| ID | Title | Labels | Priority |
|----|-------|--------|----------|
| POC-01 | End-to-end integration: frontend ↔ backend API | type:task, area:backend | p0 |
| POC-02 | PoC smoke test suite — critical user journey | type:test, area:qa | p0 |
| POC-03 | Tag and publish release package 2.0.0-rc1 | type:release | p0 |
| POC-04 | Deploy 2.0.0-rc1 to staging environment | type:infra, area:devops | p0 |
| POC-05 | Conduct PoC stakeholder demo and collect feedback | type:task | p1 |

#### Post-PoC Audit (M6)

| ID | Title | Labels | Priority |
|----|-------|--------|----------|
| AUD-01 | Backend API code-quality and architecture review | type:audit, area:backend | p0 |
| AUD-02 | Frontend architecture and component-design review | type:audit, area:frontend | p0 |
| AUD-03 | Security audit — OWASP Top 10 analysis | type:audit, area:backend | p0 |
| AUD-04 | Performance baseline measurement and bottleneck report | type:audit | p1 |
| AUD-05 | Document audit findings and publish remediation plan | type:audit | p0 |

#### Phase 5 — Processing Dashboard (M7)

| ID | Title | Labels | Priority |
|----|-------|--------|----------|
| P5-01 | Batch processing status view (start, pause, cancel) | type:feature, area:frontend | p0 |
| P5-02 | Real-time progress visualisation via WebSocket | type:feature, area:frontend | p0 |
| P5-03 | Processing history log viewer with search and filter | type:feature, area:frontend | p1 |
| P5-04 | Metrics and statistics dashboard | type:feature, area:frontend | p1 |
| P5-05 | Error details panel with retry action | type:feature, area:frontend | p1 |

#### Phase 6 — FileBrowser + Vector Search (M8)

| ID | Title | Labels | Priority |
|----|-------|--------|----------|
| P6-01 | File browser component with lazy-loaded directory tree | type:feature, area:frontend | p0 |
| P6-02 | Image preview panel with EXIF metadata display | type:feature, area:frontend | p1 |
| P6-03 | Backend vector search API endpoint (image embeddings) | type:feature, area:backend | p1 |
| P6-04 | Search results grid with similarity score | type:feature, area:frontend | p1 |
| P6-05 | Inline metadata editor (author, date, custom EXIF fields) | type:feature, area:frontend | p2 |

#### Phase 7 — Event System UI (M9)

| ID | Title | Labels | Priority |
|----|-------|--------|----------|
| P7-01 | Real-time event log viewer (WebSocket-powered) | type:feature, area:frontend | p0 |
| P7-02 | Event filtering by type, severity, and date range | type:feature, area:frontend | p1 |
| P7-03 | Event notification preferences (email / in-app) | type:feature, area:frontend | p2 |
| P7-04 | Audit trail and activity timeline display | type:feature, area:frontend | p1 |

#### Phase 8 — Test/Deploy Readiness (M11)

| ID | Title | Labels | Priority |
|----|-------|--------|----------|
| P8-01 | End-to-end test suite (Playwright) — critical paths | type:test, area:qa | p0 |
| P8-02 | Load and performance testing (k6) against baseline | type:test, area:qa | p0 |
| P8-03 | Docker containerisation and docker-compose for dev | type:infra, area:devops | p0 |
| P8-04 | Kubernetes / production infrastructure configuration | type:infra, area:devops | p0 |
| P8-05 | Health check endpoints and observability (metrics + tracing) | type:infra, area:devops | p1 |
| P8-06 | Rollback procedures and operations runbook | type:task, area:devops | p0 |

#### Final Release (M13)

| ID | Title | Labels | Priority |
|----|-------|--------|----------|
| REL-01 | Execute production deployment of release 2.0.0 | type:release, area:devops | p0 |
| REL-03 | Post-deployment smoke testing in production | type:test, area:qa | p0 |
| REL-04 | Final stakeholder sign-off | type:task | p0 |
| REL-05 | Create and publish GitHub release 2.0.0 with full changelog | type:release | p0 |

---

## Labels Required

| Label | Colour | Description |
|-------|--------|-------------|
| type:epic | #0052CC | Epic — parent issue tracking a full phase or feature area |
| type:feature | #0075CA | New user-facing functionality |
| type:task | #E4E669 | Non-coding task (docs, planning, coordination) |
| type:test | #0E8A16 | Test implementation or test infrastructure |
| type:infra | #F9D0C4 | Infrastructure, CI/CD, DevOps configuration |
| type:audit | #D93F0B | Code review, security or quality audit |
| type:release | #6F42C1 | Release preparation, tagging, deployment |
| priority:p0 | #B60205 | Critical — blocks release |
| priority:p1 | #E4E669 | High — required for milestone |
| priority:p2 | #0075CA | Medium — nice to have |
| area:backend | #1D76DB | Backend API and server-side code |
| area:frontend | #0075CA | React/TS frontend code |
| area:devops | #F9D0C4 | Infrastructure, containers, pipelines |
| area:qa | #0E8A16 | Quality assurance and testing |

---

## Execution Batches (Copilot usage budget)

| Batch | Day range | Milestones |
|-------|-----------|------------|
| A | 1–10 | M1, M2, M3, M4 |
| B | 11–20 | M5, M6, M7, M8, M9 |
| C | 21–end | M10, M11, M12, M13 |

---

## Verification Checklist

- [ ] Total milestones = 13
- [ ] Feature Freeze milestone (M10) exists with due date 2027-01-20
- [ ] Code Freeze milestone (M12) exists with due date 2027-02-24
- [ ] M6 (Audit) depends on M5 (PoC) completion
- [ ] Final milestone due date = 2027-03-10
- [ ] Release 2.0.0 referenced explicitly in M13 issues
- [ ] All 14 labels created
- [ ] All 12 epics created
- [ ] All 3 freeze gates created
- [ ] Child issues created for all phases
