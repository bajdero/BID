# BID Web Migration — Implementation Plan

**Project:** BID (Batch Image Delivery) — Desktop-to-Web Migration  
**Target release:** 2.0.0 (production)  
**Hard deadline:** 2027-03-10  
**PoC release:** 2.0.0-rc1 by 2026-09-20

---

## Overview

BID is a Python/Tkinter desktop application for batch image processing: automatic scaling, watermark
overlay, EXIF cleaning, colour-space conversion, and delivery-folder export.  
This plan migrates the application to a web architecture with a FastAPI backend, a WebSocket
real-time layer, and a React TypeScript frontend while preserving all existing functionality.

---

## Phase 1 — Backend API Extraction

**Milestone:** M1 — Backend API Extraction (Phase 1)  
**Due:** 2026-05-31  
**Goal:** Decouple the processing core from the Tkinter UI and expose it as a documented REST API.

### Deliverables

| ID | Title | Labels | Priority |
|----|-------|--------|----------|
| P1-01 | Design and document REST API specification (OpenAPI 3.0) | type:task, area:backend | p1 |
| P1-02 | Extract image processing pipeline to FastAPI service | type:feature, area:backend | p0 |
| P1-03 | Implement project and session management API endpoints | type:feature, area:backend | p0 |
| P1-04 | Add JWT/OAuth2 authentication and authorisation layer | type:feature, area:backend | p1 |
| P1-05 | Create database abstraction layer (SQLite → PostgreSQL) | type:infra, area:backend | p1 |
| P1-06 | Write unit tests for all API endpoints | type:test, area:backend | p1 |

### Acceptance criteria
- All image-processing operations available in `bid/image_processing.py` are accessible via REST.
- Project/session CRUD endpoints replicate `bid/project_manager.py` behaviour.
- OpenAPI spec renders in Swagger UI without errors.
- ≥ 80 % test coverage on API layer.

---

## Phase 2 — WebSocket Real-Time Layer

**Milestone:** M2 — WebSocket Real-Time Layer (Phase 2)  
**Due:** 2026-06-21  
**Goal:** Stream processing progress and system events to connected clients in real time.

### Deliverables

| ID | Title | Labels | Priority |
|----|-------|--------|----------|
| P2-01 | Implement WebSocket server (FastAPI + asyncio) | type:feature, area:backend | p0 |
| P2-02 | Adapt existing event system to broadcast over WebSocket | type:feature, area:backend | p0 |
| P2-03 | Stream per-file and batch processing progress to clients | type:feature, area:backend | p1 |
| P2-04 | Add heartbeat and automatic client reconnect mechanism | type:feature, area:backend | p1 |
| P2-05 | Write WebSocket integration tests | type:test, area:backend | p1 |

### Acceptance criteria
- Clients receive `processing_started`, `progress`, `processing_done`, and `error` events.
- Reconnect succeeds within 5 s after connection loss.
- No message loss during batch processing of ≥ 100 images.

---

## Phase 3 — Frontend Shell

**Milestone:** M3 — Frontend Shell (Phase 3)  
**Due:** 2026-07-19  
**Goal:** Scaffold the React TypeScript web application with routing, auth, and layout.

### Deliverables

| ID | Title | Labels | Priority |
|----|-------|--------|----------|
| P3-01 | Bootstrap React + TypeScript + Vite project | type:infra, area:frontend | p0 |
| P3-02 | Configure client-side routing (React Router v6) | type:feature, area:frontend | p1 |
| P3-03 | Implement authentication flow (login, session, logout) | type:feature, area:frontend | p0 |
| P3-04 | Create base layout components (AppShell, Sidebar, Header) | type:feature, area:frontend | p1 |
| P3-05 | Set up state management (Zustand) and API client layer | type:infra, area:frontend | p1 |
| P3-06 | Configure GitHub Actions CI/CD pipeline for frontend | type:infra, area:devops | p1 |

### Acceptance criteria
- Application builds and passes lint with zero errors.
- Protected routes redirect unauthenticated users to login.
- CI pipeline runs on every pull request.

---

## Phase 4 — Core UI Components

**Milestone:** M4 — Core UI Components (Phase 4)  
**Due:** 2026-09-06  
**Goal:** Implement the primary interactive components that mirror the existing Tkinter panels.

### Deliverables

| ID | Title | Labels | Priority |
|----|-------|--------|----------|
| P4-01 | Project/session selector (replaces `bid/ui/project_selector.py`) | type:feature, area:frontend | p0 |
| P4-02 | Export profile configuration wizard (replaces `bid/ui/export_wizard.py`) | type:feature, area:frontend | p0 |
| P4-03 | Image processing queue display with live status | type:feature, area:frontend | p0 |
| P4-04 | Settings and preferences panel (replaces `bid/ui/setup_wizard.py`) | type:feature, area:frontend | p1 |
| P4-05 | Toast notification system (replaces `bid/ui/toast.py`) | type:feature, area:frontend | p1 |
| P4-06 | Theme provider — dark / light mode | type:feature, area:frontend | p2 |

### Acceptance criteria
- All export profile options available in `export_option.json` are configurable from the UI.
- Queue displays per-file state: pending, processing, done, error.
- Toast messages disappear after 5 s.

---

## PoC Release Readiness

**Milestone:** M5 — PoC Release 2.0.0-rc1  
**Due:** 2026-09-20  
**Goal:** Deliver a working end-to-end PoC of the web application for stakeholder validation.

### Deliverables

| ID | Title | Labels | Priority |
|----|-------|--------|----------|
| POC-01 | End-to-end integration: connect frontend Phase 3–4 to Phase 1–2 backend | type:task, area:backend | p0 |
| POC-02 | PoC smoke test suite covering the critical user journey | type:test, area:qa | p0 |
| POC-03 | Tag and publish release package 2.0.0-rc1 | type:release | p0 |
| POC-04 | Deploy 2.0.0-rc1 to staging environment | type:infra, area:devops | p0 |
| POC-05 | Conduct PoC stakeholder demo and collect feedback | type:task | p1 |

### Acceptance criteria
- User can log in, select a project, trigger batch processing, and see real-time progress.
- Release tag `2.0.0-rc1` exists on GitHub with changelog.
- Staging deployment passes smoke tests.

---

## Post-PoC Architecture and Implementation Audit

**Milestone:** M6 — Architecture and Implementation Audit  
**Due:** 2026-10-04  
**Prerequisite:** M5 — PoC Release 2.0.0-rc1 must be complete.  
**Goal:** Identify and remediate architectural, security, and quality gaps before feature build-out.

### Deliverables

| ID | Title | Labels | Priority |
|----|-------|--------|----------|
| AUD-01 | Backend API code-quality and architecture review | type:audit, area:backend | p0 |
| AUD-02 | Frontend architecture and component-design review | type:audit, area:frontend | p0 |
| AUD-03 | Security audit — OWASP Top 10 analysis | type:audit, area:backend | p0 |
| AUD-04 | Performance baseline measurement and bottleneck report | type:audit | p1 |
| AUD-05 | Document audit findings and publish remediation plan | type:audit | p0 |

### Acceptance criteria
- All P0 findings from AUD-03 (OWASP critical/high) have an assigned remediation issue.
- Performance baseline document is merged to `main`.
- Remediation plan is reviewed and approved.

---

## Phase 5 — Processing Dashboard

**Milestone:** M7 — Processing Dashboard (Phase 5)  
**Due:** 2026-11-08  
**Goal:** Build a full-featured batch-processing control centre with real-time feedback.

### Deliverables

| ID | Title | Labels | Priority |
|----|-------|--------|----------|
| P5-01 | Batch processing status view (start, pause, cancel) | type:feature, area:frontend | p0 |
| P5-02 | Real-time progress visualisation using WebSocket events | type:feature, area:frontend | p0 |
| P5-03 | Processing history log viewer with search and filter | type:feature, area:frontend | p1 |
| P5-04 | Metrics and statistics dashboard (throughput, error rate) | type:feature, area:frontend | p1 |
| P5-05 | Error details panel with retry action | type:feature, area:frontend | p1 |

### Acceptance criteria
- Dashboard updates without page refresh during active batch.
- History log is searchable by filename, date, and status.
- Retry on failed items re-queues only those items.

---

## Phase 6 — FileBrowser + Vector Search

**Milestone:** M8 — FileBrowser + Vector Search (Phase 6)  
**Due:** 2026-12-06  
**Goal:** Reproduce the desktop source-tree and add vector-similarity image search.

### Deliverables

| ID | Title | Labels | Priority |
|----|-------|--------|----------|
| P6-01 | File browser component with lazy-loaded directory tree | type:feature, area:frontend | p0 |
| P6-02 | Image preview panel with full EXIF metadata display | type:feature, area:frontend | p1 |
| P6-03 | Backend vector search API endpoint (image embeddings) | type:feature, area:backend | p1 |
| P6-04 | Search results grid/list with similarity score | type:feature, area:frontend | p1 |
| P6-05 | Inline metadata editor (author, date, custom EXIF fields) | type:feature, area:frontend | p2 |

### Acceptance criteria
- Directory tree supports ≥ 10 000 files without performance degradation.
- Vector search returns results in < 2 s for a 50 000-image index.
- Metadata edits persist to the backend.

---

## Phase 7 — Event System UI

**Milestone:** M9 — Event System UI (Phase 7)  
**Due:** 2027-01-10  
**Goal:** Expose the existing `bid/events/` subsystem through a rich web interface.

### Deliverables

| ID | Title | Labels | Priority |
|----|-------|--------|----------|
| P7-01 | Real-time event log viewer (WebSocket-powered) | type:feature, area:frontend | p0 |
| P7-02 | Event filtering by type, severity, and date range | type:feature, area:frontend | p1 |
| P7-03 | Event notification preferences (email / in-app) | type:feature, area:frontend | p2 |
| P7-04 | Audit trail and activity timeline display | type:feature, area:frontend | p1 |

### Acceptance criteria
- Event viewer shows new events within 500 ms of occurrence.
- Filters apply without full page reload.
- Audit trail entries are immutable from the UI.

---

## Feature Freeze Gate

**Milestone:** M10 — Feature Freeze  
**Due:** 2027-01-20  
**No new features may be merged after this date.**

---

## Phase 8 — Test / Deploy Readiness

**Milestone:** M11 — Test/Deploy Readiness (Phase 8)  
**Due:** 2027-02-20  
**Goal:** Validate the full system, containerise, and certify it for production deployment.

### Deliverables

| ID | Title | Labels | Priority |
|----|-------|--------|----------|
| P8-01 | End-to-end test suite (Playwright) covering all critical paths | type:test, area:qa | p0 |
| P8-02 | Load and performance testing (k6) — validate baseline | type:test, area:qa | p0 |
| P8-03 | Docker containerisation and docker-compose for local dev | type:infra, area:devops | p0 |
| P8-04 | Kubernetes / production infrastructure configuration | type:infra, area:devops | p0 |
| P8-05 | Health check endpoints and observability (metrics + tracing) | type:infra, area:devops | p1 |
| P8-06 | Rollback procedures and operations runbook | type:task, area:devops | p0 |

### Acceptance criteria
- E2E suite covers login → project select → batch processing → results with zero flaky tests.
- p95 API response time < 200 ms under 50 concurrent users.
- Rollback procedure tested and documented.

---

## Code Freeze Gate

**Milestone:** M12 — Code Freeze  
**Due:** 2027-02-24  
**Only release-blocker fixes may be merged after this date.**

---

## Final Deployment and Sign-off (Release 2.0.0)

**Milestone:** M13 — Web Release 2.0.0 Production Deployment and Final Sign-off  
**Due:** 2027-03-10  
**Goal:** Deploy version 2.0.0 to production and obtain formal sign-off.

### Deliverables

| ID | Title | Labels | Priority |
|----|-------|--------|----------|
| REL-01 | Execute production deployment of release 2.0.0 | type:release, area:devops | p0 |
| REL-02 | Go-Live Gate — deployment validation and rollback readiness | type:release, area:devops | p0 |
| REL-03 | Post-deployment smoke testing in production | type:test, area:qa | p0 |
| REL-04 | Final stakeholder sign-off sign document | type:task | p0 |
| REL-05 | Create and publish GitHub release 2.0.0 with full changelog | type:release | p0 |

### Acceptance criteria
- Production smoke tests pass without rollback.
- Release tag `2.0.0` exists on GitHub with complete changelog.
- Sign-off document signed by all stakeholders.
- Hard deadline 2027-03-10 met.

---

## Dependency Graph

```
M1 (Backend API)
  └─► M2 (WebSocket)
        └─► M3 (Frontend Shell)
              └─► M4 (Core UI)
                    └─► M5 (PoC rc1)
                          └─► M6 (Audit)  ← starts ONLY after M5 is complete
                                └─► M7 (Dashboard)
                                      └─► M8 (FileBrowser+Search)
                                            └─► M9 (Event System UI)
                                                  └─► M10 (Feature Freeze)
                                                        └─► M11 (Test/Deploy)
                                                              └─► M12 (Code Freeze)
                                                                    └─► M13 (Release 2.0.0)
```

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend API | Python 3.12, FastAPI, Pydantic v2, Uvicorn |
| Real-time | WebSocket (FastAPI), asyncio |
| Database | SQLAlchemy 2.0, Alembic (SQLite dev / PostgreSQL prod) |
| Frontend | React 18, TypeScript 5, Vite, Zustand, React Router v6 |
| UI Library | Mantine or shadcn/ui |
| Testing — backend | pytest, pytest-asyncio, httpx |
| Testing — frontend | Vitest, React Testing Library, Playwright |
| Load testing | k6 |
| Containerisation | Docker, docker-compose |
| CI/CD | GitHub Actions |
| Observability | OpenTelemetry, Prometheus, Grafana |
