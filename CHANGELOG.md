# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0-rc1] — 2026-04-30 (PoC)

### Summary

First candidate release of the BID web migration PoC (Phases 1–4).
Delivers a complete FastAPI backend, WebSocket real-time layer, React frontend, and
a single-command Docker Compose stack.

### Added

**Phase 1 — Backend API (P1-01 … P1-06)**
- `src/api/` — FastAPI application with OpenAPI 3.0 spec (`/docs`, `/redoc`)
- REST endpoints: `/auth/login`, `/auth/refresh`, `/api/v1/projects`, `/api/v1/projects/{id}/settings`,
  `/api/v1/projects/{id}/export-profiles`, `/api/v1/projects/{id}/process`,
  `/api/v1/projects/{id}/sources`, `/api/v1/projects/{id}/exports/conflicts`,
  `/api/v1/users`, `/health`, `/version`
- JWT authentication (access + refresh tokens, HS256)
- SQLite persistence via SQLAlchemy ORM (`PhotoRecord`, `AuditLog`, `User`)
- Audit log: per-photo state and metadata change tracking
- ≥ 80 % test coverage on the API layer

**Phase 2 — WebSocket Real-Time Layer (P2-01 … P2-05)**
- `src/api/websocket/` — FastAPI WebSocket endpoint at
  `GET /api/v1/projects/{id}/ws?token=<JWT>`
- `ConnectionManager`: per-project connection registry with `asyncio.Lock`
- Message types: `state_change`, `progress`, `scan_update`, `error`, `ping`, `pong`,
  `queue_metrics`, `server_closing`
- Server-side heartbeat (30 s ping, 10 s pong timeout)
- Auto-reconnect hint via `server_closing` message
- `EventBroadcastService`: polls `bid/events/EventManager` every 5 min, broadcasts `scan_update`
- 35 WebSocket integration tests

**Phase 3 — Frontend Shell (P3-01 … P3-06)**
- `src/frontend/` — React 18 + TypeScript + Vite project
- React Router v6 — client-side routing with protected routes
- Zustand stores: `authStore`, `projectStore`, `processingStore`
- Axios API client with silent JWT refresh and request queuing
- WebSocket client with heartbeat and auto-reconnect (`BidWebSocketClient`)
- Layout: `AppShell`, `Header`, `Sidebar`
- Pages: `LoginPage`, `DashboardPage`, `NotFoundPage`
- shadcn/ui components: `Button`, `Input`, `Label`, `Card`, `Progress`, `Toast`
- GitHub Actions CI: `.github/workflows/frontend.yml` (type-check, lint, build)

**Phase 4 — Core UI Components (P4-01 … P4-06)**
- `ProjectsPage` — list, create, delete projects; select active project (P4-01)
- `ExportsPage` — add/edit/delete export profiles, save via PUT (P4-02)
- `ProcessingPage` — live processing queue via WebSocket, enqueue-all button (P4-03)
- `SourcesPage` — source tree with folder expand/collapse, photo details panel (P4-04 / P4-05)
- `SettingsPage` — account info, FileBrowser link, dark/light/system theme toggle (P4-04 / P4-06)
- `useToast` hook with 5 s auto-dismiss; `Toaster` component (P4-05)
- `src/api/routers/sources.py` — new `GET /sources` and `GET /sources/{folder}/{photo}` endpoints

**PoC Infrastructure (POC-01 … POC-03)**
- `docker-compose.yml` — four-service stack: `nginx`, `api`, `frontend`, `filebrowser`
- `nginx/nginx.conf` — reverse proxy: `/` → frontend, `/api` → backend, `/files` → FileBrowser
- `src/Dockerfile` — multi-stage Python 3.11-slim API image
- `src/frontend/Dockerfile` — multi-stage Node 20 + nginx frontend image
- `.env.example` — documented environment variable template
- `CHANGELOG.md` — this file

### Changed

- `src/api/main.py`: registered `sources.router` under `/api/v1`
- `src/api/routers/` import updated to include `sources`
- `migration_to_web_plan/implementation_plan.md`: Phases 3, 4, and PoC marked ✅ COMPLETE
- `README.md`: added "Quick start (Docker)" section

### Fixed

- `src/frontend/src/lib/apiClient.ts`: `ProjectResponse`, `SourceTree`/`PhotoEntry`, `ExportProfile`,
  `ProcessResponse` types now match actual API schemas exactly
- `src/frontend/src/pages/ExportsPage.tsx`: rewrote to use `profiles: Record<string, ExportProfile>`
  structure (was incorrect array-based schema)
- `src/frontend/src/pages/SourcesPage.tsx`: rewrote to use `SourceTree.folders` tree structure
- `src/frontend/src/pages/ProcessingPage.tsx`: updated `enqueueAll` to call correct API endpoint

---

## [1.x] — Desktop application (Tkinter)

See git history for prior desktop-application releases.
