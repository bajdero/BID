# BID Web Migration — Implementation Plan

## Project Overview

Migrate **BID (Batch Image Delivery)** from a desktop Python/tkinter application to a
modern web application with a REST + WebSocket backend and a browser-based frontend.

- Current release: **1.0.0** (desktop app)
- First web production release: **2.0.0**
- Hard deadline: **2027-03-10**

---

## Phase 1 — Backend API Extraction (due 2026-05-31)

Extract all core business logic from the desktop app into a standalone HTTP API service.

### Deliverables

| # | Title | Type | Area |
|---|-------|------|------|
| 1.1 | Extract image-processing core to service layer | feature | backend |
| 1.2 | Define REST API contract (OpenAPI/Swagger spec) | task | backend |
| 1.3 | Implement FastAPI application scaffold | feature | backend |
| 1.4 | Implement `/jobs` CRUD endpoints (create, list, get, cancel) | feature | backend |
| 1.5 | Implement `/export-profiles` endpoints | feature | backend |
| 1.6 | Implement file-upload endpoint (`/files/upload`) | feature | backend |
| 1.7 | Implement processed-file download endpoint (`/files/download/{id}`) | feature | backend |
| 1.8 | Add API authentication (API-key header) | feature | backend |
| 1.9 | Containerise backend (Dockerfile + docker-compose) | infra | devops |
| 1.10 | Unit tests for all Phase 1 API endpoints | test | backend |

---

## Phase 2 — WebSocket Real-Time Layer (due 2026-06-21)

Add a WebSocket layer so the frontend can receive live processing progress and events.

### Deliverables

| # | Title | Type | Area |
|---|-------|------|------|
| 2.1 | Implement WebSocket server endpoint (`/ws/jobs/{job_id}`) | feature | backend |
| 2.2 | Define event schema (progress, complete, error, cancelled) | task | backend |
| 2.3 | Integrate event broadcasting into image-processing pipeline | feature | backend |
| 2.4 | Implement connection-lifecycle management (connect / disconnect / reconnect) | feature | backend |
| 2.5 | Add WebSocket authentication (token handshake) | feature | backend |
| 2.6 | Integration tests for WebSocket event flow | test | backend |

---

## Phase 3 — Frontend Shell (due 2026-07-19)

Bootstrap the web frontend project and wire it to the backend API.

### Deliverables

| # | Title | Type | Area |
|---|-------|------|------|
| 3.1 | Initialise frontend project (React + TypeScript + Vite) | feature | frontend |
| 3.2 | Configure routing (React Router v6) | feature | frontend |
| 3.3 | Set up global state management (Zustand) | feature | frontend |
| 3.4 | Implement API client layer (axios + generated types from OpenAPI spec) | feature | frontend |
| 3.5 | Implement WebSocket client hook with auto-reconnect | feature | frontend |
| 3.6 | Create base layout: header, sidebar nav, main content area | feature | frontend |
| 3.7 | Implement login / API-key entry screen | feature | frontend |
| 3.8 | CI pipeline for frontend (lint + build + unit tests on PR) | infra | devops |

---

## Phase 4 — Core UI Components (due 2026-09-06)

Build the fundamental UI panels needed for end-to-end basic usage.

### Deliverables

| # | Title | Type | Area |
|---|-------|------|------|
| 4.1 | Settings panel (source folder, export folder, global options) | feature | frontend |
| 4.2 | Export-profile manager (list, create, edit, delete profiles) | feature | frontend |
| 4.3 | Source-folder browser (read-only tree view) | feature | frontend |
| 4.4 | Job-creation wizard (select sources → choose profile → submit) | feature | frontend |
| 4.5 | Job queue panel (list active and recent jobs with status) | feature | frontend |
| 4.6 | Basic image-preview component (thumbnail + metadata) | feature | frontend |
| 4.7 | Component unit tests (React Testing Library) | test | frontend |

---

## Phase 5 — Processing Dashboard (due 2026-11-08)

Build a rich real-time dashboard for monitoring batch-processing progress.

### Deliverables

| # | Title | Type | Area |
|---|-------|------|------|
| 5.1 | Real-time per-job progress bar (via WebSocket) | feature | frontend |
| 5.2 | Per-file status grid (queued / processing / done / error) | feature | frontend |
| 5.3 | Aggregate statistics panel (throughput, ETA, error rate) | feature | frontend |
| 5.4 | Error detail modal with retry / skip actions | feature | frontend |
| 5.5 | Processing history log (paginated, filterable) | feature | frontend |
| 5.6 | Dashboard E2E smoke test (Playwright) | test | qa |

---

## Phase 6 — FileBrowser + Vector Search (due 2026-12-06)

Add an advanced file-browser and image-similarity search to the web UI.

### Deliverables

| # | Title | Type | Area |
|---|-------|------|------|
| 6.1 | Full file-browser component (navigate source and export trees) | feature | frontend |
| 6.2 | Backend: generate and store image embedding vectors | feature | backend |
| 6.3 | Backend: vector-similarity search endpoint (`/search/similar`) | feature | backend |
| 6.4 | Frontend: similarity-search UI (upload query image → show results) | feature | frontend |
| 6.5 | Metadata-filter sidebar (date, profile, author, status) | feature | frontend |
| 6.6 | Integration tests for vector-search endpoint | test | backend |

---

## Phase 7 — Event System UI (due 2027-01-10)

Expose the backend event stream in a structured, actionable UI.

### Deliverables

| # | Title | Type | Area |
|---|-------|------|------|
| 7.1 | Event-log viewer (streaming table, filter by level / job / time) | feature | frontend |
| 7.2 | In-app notification toasts (success / warning / error) | feature | frontend |
| 7.3 | Alert management page (acknowledge, dismiss, history) | feature | frontend |
| 7.4 | System-health indicators (backend uptime, queue depth, error rate) | feature | frontend |
| 7.5 | Backend: structured event log API (`/events`) | feature | backend |
| 7.6 | E2E tests for event-log and notification flows | test | qa |

---

## Phase 8 — Test / Deploy Readiness (due 2027-02-20)

Harden the system for production: comprehensive testing, CI/CD, and operational readiness.

### Deliverables

| # | Title | Type | Area |
|---|-------|------|------|
| 8.1 | Full E2E test suite (Playwright — happy path + edge cases) | test | qa |
| 8.2 | Performance / load tests (k6 — 50 concurrent jobs baseline) | test | qa |
| 8.3 | Security audit — OWASP Top-10 review + dependency scan | audit | qa |
| 8.4 | Production Dockerfile + docker-compose (multi-stage, non-root) | infra | devops |
| 8.5 | GitHub Actions CI/CD pipeline (test → build → push image → deploy) | infra | devops |
| 8.6 | Kubernetes / Compose production deployment manifests | infra | devops |
| 8.7 | Monitoring stack (Prometheus metrics endpoint + Grafana dashboard) | infra | devops |
| 8.8 | Runbook and operations guide | task | devops |

---

## Governance Milestones

### PoC Release Readiness (M5 — 2026-09-20)

Validate that Phases 1–4 produce a releasable proof-of-concept (tag `2.0.0-rc1`).

| # | Title | Type | Area |
|---|-------|------|------|
| G1 | Release candidate build and smoke test (`2.0.0-rc1`) | release | devops |
| G2 | Internal demo and stakeholder sign-off for PoC | task | qa |

### Post-PoC Architecture and Implementation Audit (M6 — 2026-10-04)

Formal audit of the PoC to identify architecture gaps before full development.
*Starts only after M5 (PoC Release) is complete.*

| # | Title | Type | Area |
|---|-------|------|------|
| A1 | Architecture review — backend API design and scalability | audit | backend |
| A2 | Architecture review — frontend state and component model | audit | frontend |
| A3 | Security review — authentication and data flow | audit | backend |
| A4 | Performance baseline — API latency and WebSocket throughput | audit | backend |
| A5 | Audit findings report and remediation plan | task | qa |

### Release Hardening — Feature Freeze to Code Freeze (M10–M12)

| # | Title | Type | Area |
|---|-------|------|------|
| H1 | Feature Freeze Gate — no new features after 2027-01-20 | release | devops |
| H2 | Regression test run against feature-freeze build | test | qa |
| H3 | Code Freeze Gate — only release blockers after 2027-02-24 | release | devops |

### Final Deployment and Sign-off — Release 2.0.0 (M13 — 2027-03-10)

| # | Title | Type | Area |
|---|-------|------|------|
| F1 | Production deployment of release 2.0.0 | release | devops |
| F2 | Go-Live Gate — deployment validation and rollback readiness | release | devops |
| F3 | Final stakeholder sign-off for release 2.0.0 | task | qa |
