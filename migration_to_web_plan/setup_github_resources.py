#!/usr/bin/env python3
"""
BID Web Migration — GitHub Setup Script
Creates labels, milestones, and issues via GitHub CLI.
Repository: bajdero/BID
"""

import subprocess
import json
import sys
import time

REPO = "bajdero/BID"

# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------
LABELS = [
    # type labels
    {"name": "type:epic",    "color": "8B00FF", "description": "Epic issue grouping multiple child issues"},
    {"name": "type:feature", "color": "0075CA", "description": "New feature or enhancement"},
    {"name": "type:task",    "color": "E4E669", "description": "Non-code task (docs, config, planning)"},
    {"name": "type:test",    "color": "0E8A16", "description": "Test implementation or test infrastructure"},
    {"name": "type:infra",   "color": "BFD4F2", "description": "Infrastructure, CI/CD, DevOps work"},
    {"name": "type:audit",   "color": "D93F0B", "description": "Audit, review, or investigation"},
    {"name": "type:release", "color": "C2E0C6", "description": "Release governance, gates, sign-off"},
    # priority labels
    {"name": "priority:p0",  "color": "B60205", "description": "Critical — release blocker"},
    {"name": "priority:p1",  "color": "D93F0B", "description": "High — must complete in milestone"},
    {"name": "priority:p2",  "color": "FBCA04", "description": "Medium — important but not blocking"},
    # area labels
    {"name": "area:backend",  "color": "1D76DB", "description": "Backend / API work"},
    {"name": "area:frontend", "color": "0075CA", "description": "Frontend / UI work"},
    {"name": "area:devops",   "color": "5319E7", "description": "DevOps, CI/CD, infrastructure"},
    {"name": "area:qa",       "color": "0E8A16", "description": "Quality assurance, testing"},
]

# ---------------------------------------------------------------------------
# Milestones  (title -> due date ISO)
# ---------------------------------------------------------------------------
MILESTONES = [
    {"title": "M1 - Backend API Extraction (Phase 1)",                            "due": "2026-05-31T00:00:00Z"},
    {"title": "M2 - WebSocket Real-Time Layer (Phase 2)",                          "due": "2026-06-21T00:00:00Z"},
    {"title": "M3 - Frontend Shell (Phase 3)",                                     "due": "2026-07-19T00:00:00Z"},
    {"title": "M4 - Core UI Components (Phase 4)",                                 "due": "2026-09-06T00:00:00Z"},
    {"title": "M5 - PoC Release 2.0.0-rc1",                                        "due": "2026-09-20T00:00:00Z"},
    {"title": "M6 - Architecture and Implementation Audit",                        "due": "2026-10-04T00:00:00Z"},
    {"title": "M7 - Processing Dashboard (Phase 5)",                               "due": "2026-11-08T00:00:00Z"},
    {"title": "M8 - FileBrowser + Vector Search (Phase 6)",                        "due": "2026-12-06T00:00:00Z"},
    {"title": "M9 - Event System UI (Phase 7)",                                    "due": "2027-01-10T00:00:00Z"},
    {"title": "M10 - Feature Freeze",                                              "due": "2027-01-20T00:00:00Z"},
    {"title": "M11 - Test/Deploy Readiness (Phase 8)",                             "due": "2027-02-20T00:00:00Z"},
    {"title": "M12 - Code Freeze",                                                 "due": "2027-02-24T00:00:00Z"},
    {"title": "M13 - Web Release 2.0.0 Production Deployment and Final Sign-off", "due": "2027-03-10T00:00:00Z"},
]

# ---------------------------------------------------------------------------
# Issue definitions
# Each entry: title, milestone_title, labels, body
# ---------------------------------------------------------------------------

def epic_body(problem, in_scope, out_scope, ac_items, deps_milestone, deps_issues=None, dod_extra=None):
    ac = "\n".join(f"- [ ] {i}" for i in ac_items)
    in_s = "\n".join(f"- {i}" for i in in_scope)
    out_s = "\n".join(f"- {i}" for i in out_scope)
    deps = f"- **Milestone:** {deps_milestone}\n"
    if deps_issues:
        deps += "- **Depends on:** " + ", ".join(deps_issues) + "\n"
    dod_lines = [
        "- [ ] All child issues closed",
        "- [ ] Code reviewed and approved",
        "- [ ] Tests written and passing",
        "- [ ] Documentation updated (if applicable)",
        "- [ ] Milestone checklist updated",
    ]
    if dod_extra:
        dod_lines += [f"- [ ] {d}" for d in dod_extra]
    dod = "\n".join(dod_lines)
    return f"""## Problem Statement
{problem}

## Scope
**In scope:**
{in_s}

**Out of scope:**
{out_s}

## Acceptance Criteria
{ac}

## Dependencies
{deps}
## Definition of Done
{dod}
"""


def child_body(problem, in_scope, out_scope, ac_items, deps_milestone, deps_issues=None, dod_extra=None):
    return epic_body(problem, in_scope, out_scope, ac_items, deps_milestone, deps_issues or [], dod_extra)


# -- Phase 1 epic and children -------------------------------------------
P1_EPIC_BODY = epic_body(
    problem="BID is a desktop tkinter app. We need to extract its core logic into a REST API so it can be consumed by a web frontend.",
    in_scope=[
        "Extract image-processing logic to a service layer",
        "Define and implement REST API endpoints (jobs, export-profiles, file upload/download)",
        "Add API-key authentication",
        "Containerise the backend",
        "Write unit tests for all endpoints",
    ],
    out_scope=[
        "Frontend implementation",
        "WebSocket layer (Phase 2)",
        "Vector search (Phase 6)",
    ],
    ac_items=[
        "All Phase 1 child issues are closed",
        "OpenAPI spec published at /docs",
        "Backend runs in Docker with docker-compose up",
        "All unit tests pass in CI",
    ],
    deps_milestone="M1 - Backend API Extraction (Phase 1)",
)

PHASE1_CHILDREN = [
    {
        "title": "Extract image-processing core to service layer",
        "labels": ["type:feature", "priority:p1", "area:backend"],
        "body": child_body(
            "The image-processing logic is tightly coupled to the tkinter UI. It must be decoupled into an independently testable service module.",
            ["Move PIL/Pillow operations to `bid/service/image_processor.py`", "Remove all tkinter imports from processing code"],
            ["New UI components", "API endpoints"],
            ["Service module callable without UI context", "Existing unit tests still pass", "No tkinter imports in service layer"],
            "M1 - Backend API Extraction (Phase 1)",
        ),
    },
    {
        "title": "Define REST API contract (OpenAPI/Swagger spec)",
        "labels": ["type:task", "priority:p1", "area:backend"],
        "body": child_body(
            "A formal API contract is needed before implementation to ensure frontend/backend alignment.",
            ["Draft OpenAPI 3.0 YAML spec for all Phase 1 endpoints", "Publish spec in repository at `api/openapi.yaml`"],
            ["Implementation of endpoints"],
            ["OpenAPI YAML committed to repository", "Spec reviewed and approved by team", "All endpoint schemas defined (request + response)"],
            "M1 - Backend API Extraction (Phase 1)",
        ),
    },
    {
        "title": "Implement FastAPI application scaffold",
        "labels": ["type:feature", "priority:p1", "area:backend"],
        "body": child_body(
            "We need a runnable FastAPI application as the foundation for all API endpoints.",
            ["Create `backend/` directory with FastAPI app", "Add requirements.txt and pyproject.toml", "Health-check endpoint at `/health`"],
            ["Business-logic endpoints (separate issues)"],
            ["FastAPI app starts without errors", "`GET /health` returns 200", "App included in docker-compose"],
            "M1 - Backend API Extraction (Phase 1)",
        ),
    },
    {
        "title": "Implement /jobs CRUD endpoints",
        "labels": ["type:feature", "priority:p1", "area:backend"],
        "body": child_body(
            "The frontend needs to create, list, retrieve, and cancel processing jobs via the API.",
            ["POST /jobs", "GET /jobs", "GET /jobs/{job_id}", "DELETE /jobs/{job_id} (cancel)"],
            ["WebSocket progress streaming (Phase 2)"],
            ["All four endpoints return correct HTTP status codes", "Job state transitions validated", "Unit tests cover happy path and error cases"],
            "M1 - Backend API Extraction (Phase 1)",
        ),
    },
    {
        "title": "Implement /export-profiles endpoints",
        "labels": ["type:feature", "priority:p1", "area:backend"],
        "body": child_body(
            "Export profiles (fb, insta, etc.) must be manageable through the API, replacing the static JSON file.",
            ["GET /export-profiles", "POST /export-profiles", "PUT /export-profiles/{id}", "DELETE /export-profiles/{id}"],
            ["Profile versioning or history"],
            ["CRUD operations work end-to-end", "Profiles persisted between restarts", "Validation rejects invalid profile configs"],
            "M1 - Backend API Extraction (Phase 1)",
        ),
    },
    {
        "title": "Implement file-upload endpoint (/files/upload)",
        "labels": ["type:feature", "priority:p1", "area:backend"],
        "body": child_body(
            "Users need to upload source images through the web interface rather than specifying a local folder path.",
            ["POST /files/upload — multipart file upload", "Store files in configurable upload directory", "Return file ID and metadata"],
            ["Cloud storage integration", "Streaming large files (post-PoC)"],
            ["Upload endpoint accepts JPEG, PNG, TIFF files up to 100 MB", "Returns file ID used in job creation", "Unit tests pass"],
            "M1 - Backend API Extraction (Phase 1)",
        ),
    },
    {
        "title": "Implement processed-file download endpoint (/files/download/{id})",
        "labels": ["type:feature", "priority:p1", "area:backend"],
        "body": child_body(
            "Users need to download processed output files from the web UI.",
            ["GET /files/download/{file_id}", "Stream file bytes with correct Content-Type", "Return 404 for unknown IDs"],
            ["Bulk ZIP download (future)"],
            ["Endpoint streams file correctly", "Returns appropriate Content-Disposition header", "Returns 404 for missing file", "Unit tests pass"],
            "M1 - Backend API Extraction (Phase 1)",
        ),
    },
    {
        "title": "Add API authentication (API-key header)",
        "labels": ["type:feature", "priority:p1", "area:backend"],
        "body": child_body(
            "The API must be protected to prevent unauthorised access.",
            ["API-key validation via `X-API-Key` request header", "Configurable key via environment variable", "Return 401 for missing/invalid key"],
            ["OAuth2 / OIDC (future)", "Per-user keys"],
            ["All endpoints return 401 without valid key", "Valid key grants access", "Key not logged or exposed in responses"],
            "M1 - Backend API Extraction (Phase 1)",
        ),
    },
    {
        "title": "Containerise backend (Dockerfile + docker-compose)",
        "labels": ["type:infra", "priority:p1", "area:devops"],
        "body": child_body(
            "The backend must run reliably across environments via Docker.",
            ["Multi-stage Dockerfile (build + runtime)", "docker-compose.yml with backend service", "Environment variable configuration"],
            ["Kubernetes manifests (Phase 8)", "Production hardening"],
            ["docker-compose up starts backend successfully", "Health check passes inside container", "Image build succeeds in CI"],
            "M1 - Backend API Extraction (Phase 1)",
        ),
    },
    {
        "title": "Unit tests for all Phase 1 API endpoints",
        "labels": ["type:test", "priority:p1", "area:backend"],
        "body": child_body(
            "Each Phase 1 endpoint needs automated unit tests to prevent regressions.",
            ["pytest + httpx TestClient tests for all endpoints", "Happy path and error cases", "Test coverage ≥ 80%"],
            ["Integration tests (Phase 2+)", "Load tests (Phase 8)"],
            ["All tests pass in CI", "Coverage report shows ≥ 80% for `backend/` package", "Tests run in under 60 seconds"],
            "M1 - Backend API Extraction (Phase 1)",
        ),
    },
]

# -- Phase 2 epic and children -------------------------------------------
P2_EPIC_BODY = epic_body(
    problem="The API supports long-running batch jobs. The frontend needs real-time progress updates without polling.",
    in_scope=["WebSocket server endpoint", "Event schema", "Event broadcasting in pipeline", "Connection lifecycle management", "WebSocket auth"],
    out_scope=["Frontend WebSocket client (Phase 3)", "Persistent event log API (Phase 7)"],
    ac_items=["All Phase 2 child issues closed", "Frontend can receive live progress events", "Reconnect logic tested"],
    deps_milestone="M2 - WebSocket Real-Time Layer (Phase 2)",
    deps_issues=["Phase 1 epic"],
)

PHASE2_CHILDREN = [
    {
        "title": "Implement WebSocket server endpoint (/ws/jobs/{job_id})",
        "labels": ["type:feature", "priority:p1", "area:backend"],
        "body": child_body(
            "Clients need a WebSocket endpoint to subscribe to per-job progress events.",
            ["FastAPI WebSocket route `/ws/jobs/{job_id}`", "Broadcast progress events to all subscribers of a job"],
            ["Global broadcast channel", "Persistent history"],
            ["Client receives events when job progresses", "Multiple clients can subscribe to same job", "Unit tests pass"],
            "M2 - WebSocket Real-Time Layer (Phase 2)",
        ),
    },
    {
        "title": "Define event schema (progress, complete, error, cancelled)",
        "labels": ["type:task", "priority:p1", "area:backend"],
        "body": child_body(
            "A consistent event schema is needed for frontend parsing and future extensibility.",
            ["JSON schema for event types: progress, complete, error, cancelled", "Document schema in `api/ws_events.md`"],
            ["Custom event types beyond the four defined"],
            ["Schema document committed", "All event types have required fields defined", "Backend events conform to schema"],
            "M2 - WebSocket Real-Time Layer (Phase 2)",
        ),
    },
    {
        "title": "Integrate event broadcasting into image-processing pipeline",
        "labels": ["type:feature", "priority:p1", "area:backend"],
        "body": child_body(
            "The processing pipeline must emit WebSocket events at each stage so the frontend can show live progress.",
            ["Emit `progress` events at file-level granularity", "Emit `complete` / `error` / `cancelled` at job level"],
            ["Buffering/persistence of events"],
            ["Processing pipeline emits events observable via WebSocket", "Integration test verifies event sequence", "No processing performance regression > 5%"],
            "M2 - WebSocket Real-Time Layer (Phase 2)",
        ),
    },
    {
        "title": "Implement connection-lifecycle management (connect/disconnect/reconnect)",
        "labels": ["type:feature", "priority:p1", "area:backend"],
        "body": child_body(
            "WebSocket connections can drop; the server must handle this gracefully without leaking resources.",
            ["Clean up subscriptions on disconnect", "Reject connections to unknown job IDs with 4004"],
            ["Server-side reconnect logic (client responsibility)"],
            ["Disconnected clients are cleaned up within 5 s", "No memory leak after 100 connect/disconnect cycles", "Unknown job IDs rejected"],
            "M2 - WebSocket Real-Time Layer (Phase 2)",
        ),
    },
    {
        "title": "Add WebSocket authentication (token handshake)",
        "labels": ["type:feature", "priority:p1", "area:backend"],
        "body": child_body(
            "WebSocket connections must be authenticated to prevent unauthorised job monitoring.",
            ["Accept API key as query param `?token=` on WebSocket upgrade", "Reject unauthenticated connections with 4001"],
            ["Per-user scoping of job visibility"],
            ["Unauthenticated connections are rejected", "Authenticated connections receive events normally", "Token not logged"],
            "M2 - WebSocket Real-Time Layer (Phase 2)",
        ),
    },
    {
        "title": "Integration tests for WebSocket event flow",
        "labels": ["type:test", "priority:p1", "area:backend"],
        "body": child_body(
            "The complete WebSocket flow (connect → process → receive events → disconnect) must be verified by automated tests.",
            ["pytest-asyncio tests covering full job lifecycle via WebSocket", "Test reconnect scenario", "Test auth rejection"],
            ["Browser-level E2E tests (Phase 5)"],
            ["All integration tests pass in CI", "Tests verify correct event ordering", "Runs in under 90 seconds"],
            "M2 - WebSocket Real-Time Layer (Phase 2)",
        ),
    },
]

# -- Phase 3 epic and children -------------------------------------------
P3_EPIC_BODY = epic_body(
    problem="There is no web frontend. We need a complete project scaffold wired to the backend API.",
    in_scope=["React+TypeScript+Vite scaffold", "Routing", "State management", "API client", "WebSocket hook", "Base layout", "Login screen", "CI pipeline"],
    out_scope=["Business-logic UI panels (Phase 4+)"],
    ac_items=["All Phase 3 child issues closed", "App builds and deploys to staging", "Login flow works end-to-end"],
    deps_milestone="M3 - Frontend Shell (Phase 3)",
    deps_issues=["Phase 2 epic"],
)

PHASE3_CHILDREN = [
    {
        "title": "Initialise frontend project (React + TypeScript + Vite)",
        "labels": ["type:feature", "priority:p1", "area:frontend"],
        "body": child_body(
            "No frontend project exists. A properly configured React/TypeScript/Vite project is the foundation for all frontend work.",
            ["Create `frontend/` directory with Vite scaffold", "ESLint + Prettier configuration", "Vitest for unit tests"],
            ["Component library selection (separate issue)"],
            ["npm run dev starts dev server", "npm run build produces production bundle", "npm run test runs Vitest", "Lint passes with zero warnings"],
            "M3 - Frontend Shell (Phase 3)",
        ),
    },
    {
        "title": "Configure routing (React Router v6)",
        "labels": ["type:feature", "priority:p1", "area:frontend"],
        "body": child_body(
            "The app needs client-side routing to support multiple pages/views without full page reloads.",
            ["Install React Router v6", "Define route structure: /, /jobs, /jobs/:id, /settings, /profiles", "Protected routes (redirect to login if unauthenticated)"],
            ["Server-side rendering"],
            ["Navigating between routes works", "Unauthenticated users are redirected to login", "404 page shown for unknown routes"],
            "M3 - Frontend Shell (Phase 3)",
        ),
    },
    {
        "title": "Set up global state management (Zustand)",
        "labels": ["type:feature", "priority:p1", "area:frontend"],
        "body": child_body(
            "Shared state (auth token, active job, settings) needs a predictable management solution.",
            ["Install and configure Zustand", "Auth store (token, login/logout actions)", "Jobs store skeleton"],
            ["Server-state caching (React Query — separate issue if needed)"],
            ["Auth store persists token across page reloads (localStorage)", "Stores have TypeScript types", "Unit tests for stores pass"],
            "M3 - Frontend Shell (Phase 3)",
        ),
    },
    {
        "title": "Implement API client layer (axios + OpenAPI-generated types)",
        "labels": ["type:feature", "priority:p1", "area:frontend"],
        "body": child_body(
            "Frontend components need a typed, consistent way to call the backend REST API.",
            ["axios instance with base URL and auth header injection", "Generate TypeScript types from `api/openapi.yaml`", "Error handling wrapper"],
            ["Caching layer", "Retry logic (beyond simple error handling)"],
            ["API calls include X-API-Key header automatically", "TypeScript types match OpenAPI spec", "401 responses trigger logout"],
            "M3 - Frontend Shell (Phase 3)",
        ),
    },
    {
        "title": "Implement WebSocket client hook with auto-reconnect",
        "labels": ["type:feature", "priority:p1", "area:frontend"],
        "body": child_body(
            "Components need a reusable React hook to subscribe to job WebSocket events with automatic reconnection.",
            ["useJobWebSocket(jobId) hook", "Exponential backoff reconnect logic (max 5 retries)", "Typed event payloads"],
            ["Global WebSocket connection pooling (future optimisation)"],
            ["Hook reconnects after server restart", "Events typed per ws_events schema", "Hook unit tests pass"],
            "M3 - Frontend Shell (Phase 3)",
        ),
    },
    {
        "title": "Create base layout: header, sidebar nav, main content area",
        "labels": ["type:feature", "priority:p1", "area:frontend"],
        "body": child_body(
            "A consistent shell layout is needed as the container for all page content.",
            ["Top header with app title and user/logout", "Left sidebar with nav links", "Main content area with routing outlet", "Responsive breakpoints (min 1024 px wide)"],
            ["Mobile-first / full responsive redesign (future)"],
            ["Layout renders correctly at 1024, 1440, 1920 px", "Nav highlights active route", "Vitest snapshot test passes"],
            "M3 - Frontend Shell (Phase 3)",
        ),
    },
    {
        "title": "Implement login / API-key entry screen",
        "labels": ["type:feature", "priority:p1", "area:frontend"],
        "body": child_body(
            "Users must enter their API key to authenticate before accessing the app.",
            ["Login page with API-key input", "Validate key against backend `/health` with key", "Store token in auth store on success"],
            ["SSO / OIDC (future)", "Remember-me persistence beyond sessionStorage"],
            ["Successful login navigates to dashboard", "Invalid key shows error message", "Token stored securely"],
            "M3 - Frontend Shell (Phase 3)",
        ),
    },
    {
        "title": "CI pipeline for frontend (lint + build + unit tests on PR)",
        "labels": ["type:infra", "priority:p1", "area:devops"],
        "body": child_body(
            "All frontend PRs must pass automated lint, build, and test checks before merge.",
            ["GitHub Actions workflow: lint → build → vitest on every PR", "Fail fast on lint errors", "Cache node_modules"],
            ["E2E tests in CI (Phase 8)"],
            ["Workflow runs on every PR targeting main", "Build artifact uploaded", "All steps pass on clean scaffold"],
            "M3 - Frontend Shell (Phase 3)",
        ),
    },
]

# -- Phase 4 epic and children -------------------------------------------
P4_EPIC_BODY = epic_body(
    problem="The frontend shell exists but has no domain-specific UI. Core panels are needed for basic end-to-end usage.",
    in_scope=["Settings panel", "Export-profile manager", "Source-folder browser", "Job-creation wizard", "Job queue panel", "Image preview", "Component tests"],
    out_scope=["Real-time processing dashboard (Phase 5)", "Advanced file browser (Phase 6)"],
    ac_items=["All Phase 4 child issues closed", "User can create and monitor a job end-to-end via the UI", "Component tests pass in CI"],
    deps_milestone="M4 - Core UI Components (Phase 4)",
    deps_issues=["Phase 3 epic"],
)

PHASE4_CHILDREN = [
    {
        "title": "Settings panel (source folder, export folder, global options)",
        "labels": ["type:feature", "priority:p1", "area:frontend"],
        "body": child_body(
            "Users need to configure application-wide settings through the UI instead of editing JSON files.",
            ["Form to set source and export folder paths", "Save settings via API", "Reload settings on app start"],
            ["Per-user settings (single-user app for PoC)"],
            ["Settings save persists across refresh", "Validation prevents empty paths", "Unit test covers form submission"],
            "M4 - Core UI Components (Phase 4)",
        ),
    },
    {
        "title": "Export-profile manager (list, create, edit, delete profiles)",
        "labels": ["type:feature", "priority:p1", "area:frontend"],
        "body": child_body(
            "Users need a UI to manage export profiles instead of editing export_option.json directly.",
            ["List all profiles", "Create / edit profile form (all fields from export_option.json schema)", "Delete with confirmation"],
            ["Profile import/export as JSON (future)"],
            ["CRUD operations reflected immediately in list", "Invalid values prevented by form validation", "Unit tests for form pass"],
            "M4 - Core UI Components (Phase 4)",
        ),
    },
    {
        "title": "Source-folder browser (read-only tree view)",
        "labels": ["type:feature", "priority:p1", "area:frontend"],
        "body": child_body(
            "Users need to see the source folder structure to select session folders for processing.",
            ["Tree view of source folder (API-backed)", "Expand/collapse nodes", "Show file counts per folder"],
            ["File editing or deletion", "Uploading directly through tree (Phase 1 upload endpoint used separately)"],
            ["Tree renders source folder structure correctly", "Expand/collapse works", "Unit test with mocked API passes"],
            "M4 - Core UI Components (Phase 4)",
        ),
    },
    {
        "title": "Job-creation wizard (select sources → choose profile → submit)",
        "labels": ["type:feature", "priority:p1", "area:frontend"],
        "body": child_body(
            "Users need a guided multi-step flow to create a processing job.",
            ["Step 1: Select source folder(s)", "Step 2: Choose export profile", "Step 3: Review and submit (POST /jobs)"],
            ["Advanced scheduling or delayed start"],
            ["Job created successfully in 3 steps", "Wizard validates each step before proceeding", "On success navigates to job detail page"],
            "M4 - Core UI Components (Phase 4)",
        ),
    },
    {
        "title": "Job queue panel (list active and recent jobs with status)",
        "labels": ["type:feature", "priority:p1", "area:frontend"],
        "body": child_body(
            "Users need visibility into all their jobs: running, completed, and failed.",
            ["Table of jobs with status badges", "Polling or WebSocket refresh every 5 s", "Cancel button for active jobs", "Link to job detail page"],
            ["Pagination beyond 50 jobs (PoC scope)"],
            ["Jobs list updates without full page reload", "Cancel action calls DELETE /jobs/{id}", "Unit test with mock data passes"],
            "M4 - Core UI Components (Phase 4)",
        ),
    },
    {
        "title": "Basic image-preview component (thumbnail + metadata)",
        "labels": ["type:feature", "priority:p2", "area:frontend"],
        "body": child_body(
            "Users need a quick preview of processed images without downloading the full file.",
            ["Thumbnail image rendered from /files/download/{id}", "Show metadata: filename, size, dimensions, profile"],
            ["Full lightbox viewer (future)", "Side-by-side before/after (future)"],
            ["Thumbnail loads within 2 s on LAN", "Metadata displayed correctly", "Shows placeholder on load error"],
            "M4 - Core UI Components (Phase 4)",
        ),
    },
    {
        "title": "Component unit tests (React Testing Library)",
        "labels": ["type:test", "priority:p1", "area:frontend"],
        "body": child_body(
            "All Phase 4 components need automated unit tests to prevent UI regressions.",
            ["React Testing Library tests for each Phase 4 component", "Mock API calls with msw", "Coverage ≥ 75% for Phase 4 components"],
            ["Visual regression tests (future)"],
            ["All tests pass in CI", "Coverage threshold enforced in CI", "No skipped tests without justification"],
            "M4 - Core UI Components (Phase 4)",
        ),
    },
]

# -- PoC Release Readiness epic and children -------------------------------------------
POC_EPIC_BODY = epic_body(
    problem="Phases 1–4 are complete but have not been validated as a shippable proof-of-concept. We need a release candidate build and stakeholder sign-off before continuing to Phase 5.",
    in_scope=["Build and tag 2.0.0-rc1", "Smoke testing", "Stakeholder demo"],
    out_scope=["Full regression suite (Phase 8)", "Performance testing"],
    ac_items=["Release candidate tagged as 2.0.0-rc1", "Smoke tests pass", "Stakeholders sign off"],
    deps_milestone="M5 - PoC Release 2.0.0-rc1",
    deps_issues=["Phase 4 epic"],
)

POC_CHILDREN = [
    {
        "title": "Release candidate build and smoke test (2.0.0-rc1)",
        "labels": ["type:release", "priority:p0", "area:devops"],
        "body": child_body(
            "We need to tag and build the first release candidate to validate that Phases 1–4 are production-ready enough for a PoC.",
            ["Tag commit as 2.0.0-rc1", "Build Docker images", "Run smoke test checklist against staging"],
            ["Full regression suite"],
            ["Git tag 2.0.0-rc1 exists", "Docker images build without errors", "All smoke test items pass", "Deployment to staging successful"],
            "M5 - PoC Release 2.0.0-rc1",
        ),
    },
    {
        "title": "Internal demo and stakeholder sign-off for PoC",
        "labels": ["type:task", "priority:p0", "area:qa"],
        "body": child_body(
            "Stakeholders need to validate the PoC before committing to full development (Phases 5–8).",
            ["Prepare demo script covering core flows", "Conduct demo session", "Collect and document feedback", "Obtain written sign-off"],
            ["External user testing"],
            ["Demo conducted with all stakeholders present", "Feedback documented in issue comments", "Sign-off recorded", "Go/no-go decision made for Phases 5–8"],
            "M5 - PoC Release 2.0.0-rc1",
        ),
    },
]

# -- Architecture Audit epic and children -------------------------------------------
AUDIT_EPIC_BODY = epic_body(
    problem="The PoC revealed the overall approach but may have introduced architectural shortcuts. A formal audit is needed before full development to avoid costly rework later.",
    in_scope=["Backend API design review", "Frontend architecture review", "Security review", "Performance baseline"],
    out_scope=["Implementing fixes (tracked as separate issues in Phase 5+)", "External security penetration test"],
    ac_items=["All audit child issues closed", "Audit findings report published", "Remediation plan created and prioritised"],
    deps_milestone="M6 - Architecture and Implementation Audit",
    deps_issues=["PoC Release Readiness epic — M5 must be complete before this milestone begins"],
    dod_extra=["Remediation items added to relevant phase backlogs"],
)

AUDIT_CHILDREN = [
    {
        "title": "Architecture review — backend API design and scalability",
        "labels": ["type:audit", "priority:p1", "area:backend"],
        "body": child_body(
            "The PoC backend was built for speed. A formal review is needed to assess scalability and maintainability before Phase 5.",
            ["Review API design against REST best practices", "Assess concurrency model for batch jobs", "Review database/storage strategy"],
            ["Implementing changes (separate issues)"],
            ["Review findings documented", "At least one severity-rated finding per category", "Remediation recommendations included"],
            "M6 - Architecture and Implementation Audit",
            ["PoC Release Readiness epic — M5 must be complete before this milestone begins"],
        ),
    },
    {
        "title": "Architecture review — frontend state and component model",
        "labels": ["type:audit", "priority:p1", "area:frontend"],
        "body": child_body(
            "The frontend state management and component architecture need formal review before building more complex UI in Phases 5–7.",
            ["Review Zustand store design", "Review component hierarchy and prop drilling", "Assess API client and WebSocket hook patterns"],
            ["Implementing changes (separate issues)"],
            ["Review findings documented", "Component dependency graph produced", "Recommendations for Phase 5+ accepted"],
            "M6 - Architecture and Implementation Audit",
            ["PoC Release Readiness epic — M5 must be complete before this milestone begins"],
        ),
    },
    {
        "title": "Security review — authentication and data flow",
        "labels": ["type:audit", "priority:p0", "area:backend"],
        "body": child_body(
            "The PoC uses a simple API-key auth. A security review is needed to identify gaps before handling real user data.",
            ["Review API-key storage and transmission", "Review WebSocket auth token handling", "Review file upload/download access control", "OWASP Top-10 checklist for PoC scope"],
            ["Full penetration test (Phase 8)"],
            ["OWASP Top-10 checklist completed", "All P0 security findings have remediation issues created", "Review report published"],
            "M6 - Architecture and Implementation Audit",
            ["PoC Release Readiness epic — M5 must be complete before this milestone begins"],
        ),
    },
    {
        "title": "Performance baseline — API latency and WebSocket throughput",
        "labels": ["type:audit", "priority:p1", "area:backend"],
        "body": child_body(
            "We need baseline performance numbers to set targets for Phase 8 load testing.",
            ["Measure P50/P95/P99 latency for core endpoints", "Measure WebSocket event throughput for 10 concurrent jobs", "Document results as baseline"],
            ["Optimisation work (post-audit if needed)"],
            ["Baseline numbers documented", "Results committed to `docs/performance_baseline.md`", "Comparison targets defined for Phase 8"],
            "M6 - Architecture and Implementation Audit",
            ["PoC Release Readiness epic — M5 must be complete before this milestone begins"],
        ),
    },
    {
        "title": "Audit findings report and remediation plan",
        "labels": ["type:task", "priority:p1", "area:qa"],
        "body": child_body(
            "All audit findings need to be consolidated into a single report with a prioritised remediation plan.",
            ["Aggregate findings from all M6 audit issues", "Severity-rate each finding (P0–P2)", "Create GitHub issues for each P0/P1 finding in relevant phase backlogs"],
            ["External publication of report"],
            ["Report published as `docs/audit_report_m6.md`", "All P0 findings have remediation issues created", "Remediation plan accepted by team"],
            "M6 - Architecture and Implementation Audit",
            ["PoC Release Readiness epic — M5 must be complete before this milestone begins"],
        ),
    },
]

# -- Phase 5 epic and children -------------------------------------------
P5_EPIC_BODY = epic_body(
    problem="Users have no real-time visibility into running jobs beyond the basic queue panel from Phase 4.",
    in_scope=["Real-time progress bars", "Per-file status grid", "Aggregate statistics", "Error detail modal", "Processing history log", "E2E smoke test"],
    out_scope=["Advanced analytics / reporting (future)", "Mobile notifications"],
    ac_items=["All Phase 5 child issues closed", "User can monitor a running job in real-time", "E2E smoke test passes"],
    deps_milestone="M7 - Processing Dashboard (Phase 5)",
    deps_issues=["Phase 4 epic", "Post-PoC Architecture and Implementation Audit epic"],
)

PHASE5_CHILDREN = [
    {
        "title": "Real-time per-job progress bar (via WebSocket)",
        "labels": ["type:feature", "priority:p1", "area:frontend"],
        "body": child_body(
            "Users need to see live job progress without polling.",
            ["Progress bar component driven by useJobWebSocket hook", "Show percentage and current file name", "Smooth animation"],
            ["ETA calculation (separate issue if needed)"],
            ["Progress updates received in < 1 s of backend event", "Progress bar animates smoothly", "Unit test with mock WebSocket passes"],
            "M7 - Processing Dashboard (Phase 5)",
        ),
    },
    {
        "title": "Per-file status grid (queued / processing / done / error)",
        "labels": ["type:feature", "priority:p1", "area:frontend"],
        "body": child_body(
            "Users need file-level visibility into the processing state of each image in a job.",
            ["Grid/table showing each file with status badge", "Real-time updates via WebSocket events", "Click row to open image preview"],
            ["Virtual scrolling for > 1000 files (future)"],
            ["Grid updates in real-time as files are processed", "Status badges use consistent colour coding", "Unit test passes"],
            "M7 - Processing Dashboard (Phase 5)",
        ),
    },
    {
        "title": "Aggregate statistics panel (throughput, ETA, error rate)",
        "labels": ["type:feature", "priority:p2", "area:frontend"],
        "body": child_body(
            "Users want at-a-glance metrics for a running job.",
            ["Show: files/min throughput, estimated completion time, error count/rate"],
            ["Historical analytics charts (future)"],
            ["Statistics update at least every 5 s", "ETA calculation within 20% accuracy", "Panel renders without errors"],
            "M7 - Processing Dashboard (Phase 5)",
        ),
    },
    {
        "title": "Error detail modal with retry / skip actions",
        "labels": ["type:feature", "priority:p1", "area:frontend"],
        "body": child_body(
            "When a file fails processing, users need to understand why and take action.",
            ["Modal showing error message, stack trace (dev mode), affected file", "Retry button (calls POST /jobs/{id}/retry-file)", "Skip button (calls POST /jobs/{id}/skip-file)"],
            ["Bulk retry (future)"],
            ["Modal opens from error row in file grid", "Retry/skip actions call correct API endpoints", "Modal closes on success", "Unit test passes"],
            "M7 - Processing Dashboard (Phase 5)",
        ),
    },
    {
        "title": "Processing history log (paginated, filterable)",
        "labels": ["type:feature", "priority:p2", "area:frontend"],
        "body": child_body(
            "Users need to review past jobs and their outcomes.",
            ["Paginated list of completed/cancelled jobs", "Filter by status, date range, profile", "Link to job detail"],
            ["Full audit trail / event sourcing (future)"],
            ["History loads from GET /jobs with filters", "Pagination works correctly", "Filters apply without page reload"],
            "M7 - Processing Dashboard (Phase 5)",
        ),
    },
    {
        "title": "Dashboard E2E smoke test (Playwright)",
        "labels": ["type:test", "priority:p1", "area:qa"],
        "body": child_body(
            "The Phase 5 dashboard needs an automated E2E test to verify the full real-time flow.",
            ["Playwright test: login → create job → watch progress → verify completion", "Run against staging environment"],
            ["Full regression suite (Phase 8)"],
            ["E2E test passes in CI against staging", "Test completes in < 5 minutes", "Test is flake-free over 3 consecutive runs"],
            "M7 - Processing Dashboard (Phase 5)",
        ),
    },
]

# -- Phase 6 epic and children -------------------------------------------
P6_EPIC_BODY = epic_body(
    problem="Users lack an advanced file browser and cannot search for similar images by visual similarity.",
    in_scope=["Full file-browser component", "Vector embedding generation", "Similarity search endpoint", "Similarity search UI", "Metadata filter sidebar", "Integration tests"],
    out_scope=["Multi-modal search (text + image)", "Cloud storage backends"],
    ac_items=["All Phase 6 child issues closed", "User can browse files and find similar images", "Integration tests pass"],
    deps_milestone="M8 - FileBrowser + Vector Search (Phase 6)",
    deps_issues=["Phase 5 epic"],
)

PHASE6_CHILDREN = [
    {
        "title": "Full file-browser component (navigate source and export trees)",
        "labels": ["type:feature", "priority:p1", "area:frontend"],
        "body": child_body(
            "The read-only tree from Phase 4 needs to be extended into a full file browser for both source and export directories.",
            ["Dual-pane layout (source | export)", "Breadcrumb navigation", "File info panel on selection", "Thumbnail strip for image files"],
            ["File editing or deletion through browser"],
            ["Both trees navigate correctly", "Thumbnail renders for images", "Breadcrumb updates on navigation", "Unit tests pass"],
            "M8 - FileBrowser + Vector Search (Phase 6)",
        ),
    },
    {
        "title": "Backend: generate and store image embedding vectors",
        "labels": ["type:feature", "priority:p1", "area:backend"],
        "body": child_body(
            "Similarity search requires pre-computed vector embeddings for each processed image.",
            ["Generate embeddings after each file is processed (CLIP or similar lightweight model)", "Store embeddings in local vector store (e.g., Chroma or Faiss)"],
            ["Real-time embedding during processing (async background task)"],
            ["Embeddings generated for all test images", "Storage persists across container restarts", "Embedding generation adds < 20% overhead to processing time"],
            "M8 - FileBrowser + Vector Search (Phase 6)",
        ),
    },
    {
        "title": "Backend: vector-similarity search endpoint (/search/similar)",
        "labels": ["type:feature", "priority:p1", "area:backend"],
        "body": child_body(
            "The frontend needs a backend endpoint to query for visually similar images.",
            ["POST /search/similar — accepts image file or file ID, returns top-N similar images", "Configurable N (default 10)", "Return file IDs and similarity scores"],
            ["Approximate nearest-neighbour tuning (future)"],
            ["Endpoint returns relevant results for test images", "Response time < 2 s for corpus of 1000 images", "Integration tests pass"],
            "M8 - FileBrowser + Vector Search (Phase 6)",
        ),
    },
    {
        "title": "Frontend: similarity-search UI (upload query image → show results)",
        "labels": ["type:feature", "priority:p1", "area:frontend"],
        "body": child_body(
            "Users need a UI to find images visually similar to a query image.",
            ["Upload or select query image", "Call /search/similar", "Display results as image grid with similarity scores"],
            ["Saved search history"],
            ["Search returns and displays results within 3 s", "Results grid shows thumbnails and scores", "Unit test with mock API passes"],
            "M8 - FileBrowser + Vector Search (Phase 6)",
        ),
    },
    {
        "title": "Metadata-filter sidebar (date, profile, author, status)",
        "labels": ["type:feature", "priority:p2", "area:frontend"],
        "body": child_body(
            "Users need to filter the file browser by metadata to find specific images quickly.",
            ["Filter sidebar with date range, export profile, author (source folder), and job status", "Filters apply to file list without page reload"],
            ["Saved filter presets (future)"],
            ["Filters reduce file list correctly", "Multiple filters combine with AND logic", "Clear-all button resets filters"],
            "M8 - FileBrowser + Vector Search (Phase 6)",
        ),
    },
    {
        "title": "Integration tests for vector-search endpoint",
        "labels": ["type:test", "priority:p1", "area:backend"],
        "body": child_body(
            "The vector search flow needs automated integration tests with real image data.",
            ["pytest tests: upload images → process → search → verify results", "Test empty corpus case", "Test invalid query image"],
            ["Accuracy benchmarking (Phase 8 audit scope)"],
            ["All integration tests pass in CI", "Tests use reproducible test image set", "Runs in < 3 minutes"],
            "M8 - FileBrowser + Vector Search (Phase 6)",
        ),
    },
]

# -- Phase 7 epic and children -------------------------------------------
P7_EPIC_BODY = epic_body(
    problem="System events (errors, warnings, completions) are only visible in processing dashboard. A dedicated event/notification system is needed for operational awareness.",
    in_scope=["Event-log viewer", "Notification toasts", "Alert management page", "System-health indicators", "Structured event log API", "E2E tests"],
    out_scope=["External alerting integrations (Slack, PagerDuty — future)", "Log aggregation (ELK/Loki — Phase 8 monitoring)"],
    ac_items=["All Phase 7 child issues closed", "Operators can see all system events and acknowledge alerts", "E2E tests pass"],
    deps_milestone="M9 - Event System UI (Phase 7)",
    deps_issues=["Phase 6 epic"],
)

PHASE7_CHILDREN = [
    {
        "title": "Event-log viewer (streaming table, filter by level/job/time)",
        "labels": ["type:feature", "priority:p1", "area:frontend"],
        "body": child_body(
            "Operators need a live view of all system events for debugging and monitoring.",
            ["Streaming table of events via GET /events (SSE or polling)", "Filter by log level (INFO/WARN/ERROR), job ID, and time range", "Auto-scroll with pause-on-hover"],
            ["Full log aggregation backend (Phase 8 monitoring)"],
            ["Log viewer shows events within 2 s of occurrence", "Filters work correctly", "Auto-scroll pauses on hover", "Unit test passes"],
            "M9 - Event System UI (Phase 7)",
        ),
    },
    {
        "title": "In-app notification toasts (success / warning / error)",
        "labels": ["type:feature", "priority:p1", "area:frontend"],
        "body": child_body(
            "Users need immediate visual feedback for important events without watching the event log.",
            ["Toast notifications for: job complete, job error, system warning", "Auto-dismiss after 5 s (errors require manual dismiss)", "Max 3 toasts visible simultaneously"],
            ["Email or push notifications (future)"],
            ["Toasts appear for all three event types", "Error toasts require manual dismiss", "Toasts don't overlap or cause layout shift", "Unit test passes"],
            "M9 - Event System UI (Phase 7)",
        ),
    },
    {
        "title": "Alert management page (acknowledge, dismiss, history)",
        "labels": ["type:feature", "priority:p2", "area:frontend"],
        "body": child_body(
            "Persistent alerts (system errors, failed jobs) need a dedicated page for lifecycle management.",
            ["List active and historical alerts", "Acknowledge and dismiss actions", "Filter by severity and status"],
            ["Alert routing rules (future)", "SLA tracking"],
            ["Acknowledge/dismiss persists via API", "Historical alerts accessible", "Unit test passes"],
            "M9 - Event System UI (Phase 7)",
        ),
    },
    {
        "title": "System-health indicators (backend uptime, queue depth, error rate)",
        "labels": ["type:feature", "priority:p1", "area:frontend"],
        "body": child_body(
            "Operators need at-a-glance system health visibility in the UI.",
            ["Header or dashboard widget: backend status (green/red), job queue depth, rolling 1-h error rate"],
            ["Historical health charts (Phase 8 Grafana dashboard)"],
            ["Indicators update every 30 s", "Red indicator when backend is unreachable", "Unit test with mock health endpoint passes"],
            "M9 - Event System UI (Phase 7)",
        ),
    },
    {
        "title": "Backend: structured event log API (/events)",
        "labels": ["type:feature", "priority:p1", "area:backend"],
        "body": child_body(
            "The frontend event viewer and alert system need a backend API to query structured events.",
            ["GET /events with pagination and filters (level, job_id, since)", "POST /events/acknowledge/{id}", "Events persisted in database (SQLite for PoC)"],
            ["Event streaming via SSE (optimisation if needed)", "Long-term log archiving"],
            ["Endpoint returns paginated events", "Acknowledge endpoint updates event status", "Integration test passes"],
            "M9 - Event System UI (Phase 7)",
        ),
    },
    {
        "title": "E2E tests for event-log and notification flows",
        "labels": ["type:test", "priority:p1", "area:qa"],
        "body": child_body(
            "Phase 7 features need automated E2E tests to verify the event system works end-to-end.",
            ["Playwright tests: trigger job error → verify toast → verify event log entry → acknowledge alert"],
            ["Performance testing (Phase 8)"],
            ["E2E tests pass in CI against staging", "Tests are flake-free over 3 runs", "Completes in < 5 minutes"],
            "M9 - Event System UI (Phase 7)",
        ),
    },
]

# -- Release Hardening epic and children -------------------------------------------
HARDENING_EPIC_BODY = epic_body(
    problem="Development is complete. The system must be hardened for production: no new features, regressions fixed, and code frozen before final deployment.",
    in_scope=["Feature freeze enforcement", "Regression test run", "Code freeze enforcement"],
    out_scope=["New features (frozen)", "Non-critical improvements"],
    ac_items=["Feature Freeze Gate closed", "Regression tests pass", "Code Freeze Gate closed"],
    deps_milestone="M10 - Feature Freeze",
    deps_issues=["Phase 7 epic"],
)

HARDENING_CHILDREN = [
    {
        "title": "Feature Freeze Gate — no new features after 2027-01-20",
        "labels": ["type:release", "priority:p0", "area:devops"],
        "body": child_body(
            "After 2027-01-20, no new feature PRs may be merged. Only bug fixes, test improvements, and release blockers are permitted.",
            ["Document feature freeze policy in CONTRIBUTING.md", "Add PR label check (CI blocks `type:feature` PRs after freeze date)", "Notify all contributors"],
            ["Retroactive feature additions", "Performance improvements (allowed if non-functional-change)"],
            ["CONTRIBUTING.md updated with freeze policy", "CI check in place and tested", "All contributors notified via issue comment", "No open `type:feature` PRs without freeze exception approval"],
            "M10 - Feature Freeze",
        ),
    },
    {
        "title": "Regression test run against feature-freeze build",
        "labels": ["type:test", "priority:p0", "area:qa"],
        "body": child_body(
            "A full regression test run is needed after feature freeze to establish the quality baseline for the release.",
            ["Run full test suite (unit + integration + E2E)", "Document results", "Create issues for all failures"],
            ["New test development (only fixing failures)"],
            ["Full test suite passes with zero failures", "Test results documented in `docs/regression_freeze_2027-01-20.md`", "All failures resolved before Code Freeze"],
            "M10 - Feature Freeze",
        ),
    },
    {
        "title": "Code Freeze Gate — only release blockers after 2027-02-24",
        "labels": ["type:release", "priority:p0", "area:devops"],
        "body": child_body(
            "After 2027-02-24, only P0 release blocker fixes may be merged. All other changes are deferred to post-2.0.0.",
            ["Update CONTRIBUTING.md with code freeze policy", "CI check blocks non-P0 PRs after code freeze date"],
            ["Hotfixes with explicit release-blocker label exception"],
            ["CONTRIBUTING.md updated", "CI check tested and verified", "No non-P0 PRs merged after 2027-02-24 without exception"],
            "M12 - Code Freeze",
        ),
    },
]

# -- Phase 8 epic and children -------------------------------------------
P8_EPIC_BODY = epic_body(
    problem="The application is feature-complete but not production-hardened. We need comprehensive testing, CI/CD, and operational infrastructure before the 2.0.0 release.",
    in_scope=["Full E2E suite", "Load tests", "Security audit", "Production Docker", "CI/CD pipeline", "K8s/Compose manifests", "Monitoring", "Runbook"],
    out_scope=["Feature development (frozen)", "Multi-region deployment (future)"],
    ac_items=["All Phase 8 child issues closed", "CI/CD pipeline deploys to production", "Monitoring operational", "Runbook reviewed"],
    deps_milestone="M11 - Test/Deploy Readiness (Phase 8)",
    deps_issues=["Release Hardening epic (Feature Freeze Gate must be closed)"],
)

PHASE8_CHILDREN = [
    {
        "title": "Full E2E test suite (Playwright — happy path + edge cases)",
        "labels": ["type:test", "priority:p0", "area:qa"],
        "body": child_body(
            "A comprehensive E2E suite is needed to validate all user-facing flows before the 2.0.0 production release.",
            ["Happy path: login → create job → monitor → download", "Edge cases: network error, invalid file, cancel mid-job", "Run in CI on every PR to main"],
            ["Accessibility testing (future)"],
            ["All E2E tests pass in CI", "Zero flaky tests over 5 consecutive runs", "Suite completes in < 15 minutes"],
            "M11 - Test/Deploy Readiness (Phase 8)",
        ),
    },
    {
        "title": "Performance / load tests (k6 — 50 concurrent jobs baseline)",
        "labels": ["type:test", "priority:p0", "area:qa"],
        "body": child_body(
            "We need to verify the system meets performance targets under realistic load before production.",
            ["k6 load test: 50 concurrent jobs, 500 images each", "Measure P95 API latency and WebSocket event delay", "Compare against M6 baseline"],
            ["Sustained soak testing (future)", "CDN/edge performance"],
            ["P95 API latency < 500 ms under 50 concurrent jobs", "WebSocket event delay < 2 s", "Zero 5xx errors under load test", "Results documented"],
            "M11 - Test/Deploy Readiness (Phase 8)",
        ),
    },
    {
        "title": "Security audit — OWASP Top-10 review + dependency scan",
        "labels": ["type:audit", "priority:p0", "area:qa"],
        "body": child_body(
            "Final security audit is required before the 2.0.0 production release.",
            ["OWASP Top-10 checklist for full application", "Dependency vulnerability scan (Trivy or Safety)", "Remediate all P0 findings"],
            ["External penetration test (post-2.0.0 roadmap)"],
            ["OWASP Top-10 checklist complete with no open P0 items", "Dependency scan shows zero critical CVEs", "Audit report published as `docs/security_audit_2.0.0.md`"],
            "M11 - Test/Deploy Readiness (Phase 8)",
        ),
    },
    {
        "title": "Production Dockerfile + docker-compose (multi-stage, non-root)",
        "labels": ["type:infra", "priority:p0", "area:devops"],
        "body": child_body(
            "The development Dockerfiles need to be hardened for production: multi-stage builds, non-root user, minimal image size.",
            ["Multi-stage Dockerfile for backend and frontend", "Non-root user in runtime stage", "Production docker-compose with resource limits and restart policies"],
            ["Kubernetes Helm chart (separate issue)"],
            ["Images build without errors", "Containers run as non-root", "Image sizes < 500 MB (backend) and < 100 MB (frontend)", "Health checks pass"],
            "M11 - Test/Deploy Readiness (Phase 8)",
        ),
    },
    {
        "title": "GitHub Actions CI/CD pipeline (test → build → push image → deploy)",
        "labels": ["type:infra", "priority:p0", "area:devops"],
        "body": child_body(
            "A full CI/CD pipeline is required to automate testing, image building, and deployment for the 2.0.0 release.",
            ["On PR: lint + unit + integration tests", "On merge to main: build images + push to registry + deploy to staging", "On release tag: deploy to production"],
            ["Canary deployments (future)", "Blue/green deployments (future)"],
            ["Pipeline runs end-to-end without manual intervention", "Staging deployed on every merge to main", "Production deployed on release tag", "Rollback procedure documented"],
            "M11 - Test/Deploy Readiness (Phase 8)",
        ),
    },
    {
        "title": "Kubernetes / Compose production deployment manifests",
        "labels": ["type:infra", "priority:p1", "area:devops"],
        "body": child_body(
            "Production deployment needs declarative manifests for reproducible, version-controlled deployments.",
            ["Kubernetes manifests (Deployment, Service, Ingress, ConfigMap, Secret) OR docker-compose production override", "Resource requests/limits defined", "Liveness and readiness probes"],
            ["Helm chart packaging (future)", "Multi-region (future)"],
            ["Manifests deploy successfully to staging cluster", "All resource limits set", "Probes configured and passing"],
            "M11 - Test/Deploy Readiness (Phase 8)",
        ),
    },
    {
        "title": "Monitoring stack (Prometheus metrics + Grafana dashboard)",
        "labels": ["type:infra", "priority:p1", "area:devops"],
        "body": child_body(
            "Production operations require observability: metrics collection and dashboarding.",
            ["Backend Prometheus `/metrics` endpoint (job count, processing rate, error rate, latency histograms)", "Grafana dashboard with key panels", "Alert rules for error rate > 5% and P95 latency > 1 s"],
            ["Log aggregation (Loki/ELK — future)", "APM tracing (future)"],
            ["Metrics endpoint accessible and scraped by Prometheus", "Grafana dashboard operational in staging", "Alert rules fire correctly in test"],
            "M11 - Test/Deploy Readiness (Phase 8)",
        ),
    },
    {
        "title": "Runbook and operations guide",
        "labels": ["type:task", "priority:p1", "area:devops"],
        "body": child_body(
            "Operations team needs a runbook covering deployment, common failure scenarios, and rollback procedures.",
            ["Deployment procedure (step-by-step)", "Rollback procedure", "Common failure scenarios and remediation", "Monitoring dashboard guide", "Contact escalation list"],
            ["Automated runbook testing"],
            ["Runbook committed as `docs/runbook.md`", "Reviewed by at least one ops team member", "All commands tested successfully"],
            "M11 - Test/Deploy Readiness (Phase 8)",
        ),
    },
]

# -- Final Deployment epic and children -------------------------------------------
FINAL_EPIC_BODY = epic_body(
    problem="The 2.0.0 release is ready. We need to deploy to production, validate the deployment, and obtain final sign-off.",
    in_scope=["Production deployment of 2.0.0", "Go-Live Gate validation", "Final stakeholder sign-off"],
    out_scope=["Post-2.0.0 features (tracked separately)"],
    ac_items=["Release 2.0.0 deployed to production", "Go-Live Gate passed", "Final sign-off obtained"],
    deps_milestone="M13 - Web Release 2.0.0 Production Deployment and Final Sign-off",
    deps_issues=["Phase 8 epic (all issues closed)", "Code Freeze Gate closed"],
    dod_extra=["Git tag 2.0.0 created and pushed", "Release notes published"],
)

FINAL_CHILDREN = [
    {
        "title": "Production deployment of release 2.0.0",
        "labels": ["type:release", "priority:p0", "area:devops"],
        "body": child_body(
            "Execute the production deployment of BID web version 2.0.0.",
            ["Tag commit as 2.0.0", "Trigger CI/CD production deploy workflow", "Verify deployment health"],
            ["Rollback (separate Go-Live Gate issue covers rollback readiness)"],
            ["Git tag 2.0.0 exists", "Production deployment succeeds via CI/CD pipeline", "Health checks pass post-deployment", "Monitoring shows green status"],
            "M13 - Web Release 2.0.0 Production Deployment and Final Sign-off",
            ["Phase 8 epic — all issues must be closed", "Code Freeze Gate must be closed"],
        ),
    },
    {
        "title": "Go-Live Gate — deployment validation and rollback readiness",
        "labels": ["type:release", "priority:p0", "area:devops"],
        "body": child_body(
            "Before declaring 2.0.0 live, we must validate the production deployment and confirm rollback capability.",
            ["Execute smoke test checklist against production", "Verify rollback procedure works (test in staging)", "Confirm monitoring alerts are active"],
            ["Full regression in production (pre-deployment E2E covers this)"],
            ["All production smoke tests pass", "Rollback tested successfully in staging within 5 minutes", "Monitoring and alerting confirmed active in production", "Go/no-go sign-off recorded"],
            "M13 - Web Release 2.0.0 Production Deployment and Final Sign-off",
            ["Production deployment of release 2.0.0 must be complete"],
        ),
    },
    {
        "title": "Final stakeholder sign-off for release 2.0.0",
        "labels": ["type:task", "priority:p0", "area:qa"],
        "body": child_body(
            "Release 2.0.0 requires formal stakeholder acceptance before the project can be closed.",
            ["Conduct final demo/walkthrough with stakeholders", "Collect written sign-off", "Publish release notes for 2.0.0"],
            ["Ongoing post-release support (tracked separately)"],
            ["Sign-off obtained from all required stakeholders", "Release notes published on GitHub Releases", "Project retrospective scheduled"],
            "M13 - Web Release 2.0.0 Production Deployment and Final Sign-off",
            ["Go-Live Gate must be passed"],
        ),
    },
]

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def run(cmd, check=True):
    """Run a shell command and return stdout."""
    print(f"  CMD: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"  STDERR: {result.stderr.strip()}", file=sys.stderr)
        # Don't exit — log and continue so we can finish as much as possible
    return result.stdout.strip()


def gh(*args):
    return run(["gh"] + list(args))


def create_label(label):
    name = label["name"]
    color = label["color"]
    description = label["description"]
    print(f"  Creating label: {name}")
    result = subprocess.run(
        ["gh", "label", "create", name, "--color", color, "--description", description, "--repo", REPO],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        if "already exists" in result.stderr or "422" in result.stderr:
            # Update existing label
            subprocess.run(
                ["gh", "label", "edit", name, "--color", color, "--description", description, "--repo", REPO],
                capture_output=True, text=True
            )
            print(f"    (updated existing label)")
        else:
            print(f"    WARNING: {result.stderr.strip()}", file=sys.stderr)


def create_milestone(milestone):
    title = milestone["title"]
    due = milestone["due"]
    print(f"  Creating milestone: {title}")
    result = subprocess.run(
        ["gh", "api", f"repos/{REPO}/milestones",
         "--method", "POST",
         "-f", f"title={title}",
         "-f", f"due_on={due}",
         "-f", "state=open"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"    WARNING creating milestone '{title}': {result.stderr.strip()}", file=sys.stderr)
        return None
    data = json.loads(result.stdout)
    print(f"    -> milestone number: {data['number']}")
    return data["number"]


def get_milestone_number(title):
    result = subprocess.run(
        ["gh", "api", f"repos/{REPO}/milestones", "--paginate"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    milestones = json.loads(result.stdout)
    for m in milestones:
        if m["title"] == title:
            return m["number"]
    return None


def create_issue(title, labels, body, milestone_number):
    print(f"  Creating issue: {title}")
    label_args = []
    for lbl in labels:
        label_args += ["--label", lbl]
    cmd = (
        ["gh", "issue", "create",
         "--repo", REPO,
         "--title", title,
         "--body", body,
         "--milestone", str(milestone_number)]
        + label_args
    )
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    WARNING creating issue '{title}': {result.stderr.strip()}", file=sys.stderr)
        return None
    url = result.stdout.strip()
    number = url.rstrip("/").split("/")[-1]
    print(f"    -> #{number} {url}")
    return int(number)


# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("BID Web Migration — GitHub Setup Script")
    print(f"Repository: {REPO}")
    print("=" * 60)

    # 1. Create labels
    print("\n[1/3] Creating labels...")
    for label in LABELS:
        create_label(label)
        time.sleep(0.2)

    # 2. Create milestones
    print("\n[2/3] Creating milestones...")
    milestone_map = {}  # title -> number
    for ms in MILESTONES:
        num = create_milestone(ms)
        if num:
            milestone_map[ms["title"]] = num
        else:
            # Maybe it already exists — try to fetch
            num = get_milestone_number(ms["title"])
            if num:
                milestone_map[ms["title"]] = num
                print(f"    (found existing milestone #{num})")
        time.sleep(0.3)

    print(f"\n  Milestone map: {milestone_map}")

    # 3. Create issues
    print("\n[3/3] Creating issues...")

    issue_groups = [
        # (epic_title, epic_labels, epic_body, milestone_title, children)
        (
            "[Epic] Phase 1 — Backend API Extraction",
            ["type:epic", "priority:p1", "area:backend"],
            P1_EPIC_BODY,
            "M1 - Backend API Extraction (Phase 1)",
            PHASE1_CHILDREN,
        ),
        (
            "[Epic] Phase 2 — WebSocket Real-Time Layer",
            ["type:epic", "priority:p1", "area:backend"],
            P2_EPIC_BODY,
            "M2 - WebSocket Real-Time Layer (Phase 2)",
            PHASE2_CHILDREN,
        ),
        (
            "[Epic] Phase 3 — Frontend Shell",
            ["type:epic", "priority:p1", "area:frontend"],
            P3_EPIC_BODY,
            "M3 - Frontend Shell (Phase 3)",
            PHASE3_CHILDREN,
        ),
        (
            "[Epic] Phase 4 — Core UI Components",
            ["type:epic", "priority:p1", "area:frontend"],
            P4_EPIC_BODY,
            "M4 - Core UI Components (Phase 4)",
            PHASE4_CHILDREN,
        ),
        (
            "[Epic] PoC Release Readiness (2.0.0-rc1)",
            ["type:epic", "type:release", "priority:p0", "area:devops"],
            POC_EPIC_BODY,
            "M5 - PoC Release 2.0.0-rc1",
            POC_CHILDREN,
        ),
        (
            "[Epic] Post-PoC Architecture and Implementation Audit",
            ["type:epic", "type:audit", "priority:p1", "area:backend"],
            AUDIT_EPIC_BODY,
            "M6 - Architecture and Implementation Audit",
            AUDIT_CHILDREN,
        ),
        (
            "[Epic] Phase 5 — Processing Dashboard",
            ["type:epic", "priority:p1", "area:frontend"],
            P5_EPIC_BODY,
            "M7 - Processing Dashboard (Phase 5)",
            PHASE5_CHILDREN,
        ),
        (
            "[Epic] Phase 6 — FileBrowser + Vector Search",
            ["type:epic", "priority:p1", "area:frontend"],
            P6_EPIC_BODY,
            "M8 - FileBrowser + Vector Search (Phase 6)",
            PHASE6_CHILDREN,
        ),
        (
            "[Epic] Phase 7 — Event System UI",
            ["type:epic", "priority:p1", "area:frontend"],
            P7_EPIC_BODY,
            "M9 - Event System UI (Phase 7)",
            PHASE7_CHILDREN,
        ),
        (
            "[Epic] Release Hardening (Feature Freeze → Code Freeze)",
            ["type:epic", "type:release", "priority:p0", "area:devops"],
            HARDENING_EPIC_BODY,
            "M10 - Feature Freeze",
            HARDENING_CHILDREN,
        ),
        (
            "[Epic] Phase 8 — Test/Deploy Readiness",
            ["type:epic", "priority:p0", "area:qa"],
            P8_EPIC_BODY,
            "M11 - Test/Deploy Readiness (Phase 8)",
            PHASE8_CHILDREN,
        ),
        (
            "[Epic] Final Deployment and Sign-off (Release 2.0.0)",
            ["type:epic", "type:release", "priority:p0", "area:devops"],
            FINAL_EPIC_BODY,
            "M13 - Web Release 2.0.0 Production Deployment and Final Sign-off",
            FINAL_CHILDREN,
        ),
    ]

    for epic_title, epic_labels, epic_body_text, ms_title, children in issue_groups:
        ms_num = milestone_map.get(ms_title)
        if not ms_num:
            print(f"  WARNING: milestone '{ms_title}' not found, skipping epic '{epic_title}'")
            continue

        print(f"\n  --- Epic: {epic_title} ---")
        epic_num = create_issue(epic_title, epic_labels, epic_body_text, ms_num)
        time.sleep(0.5)

        for child in children:
            child_labels = child["labels"]
            child_body_text = child["body"]
            # Append epic reference to child body
            if epic_num:
                child_body_text += f"\n\n---\n_Part of epic #{epic_num}: {epic_title}_\n"
            create_issue(child["title"], child_labels, child_body_text, ms_num)
            time.sleep(0.5)

    print("\n" + "=" * 60)
    print("Setup complete!")
    print("\nVerification checklist:")
    print(f"  Milestones created: {len(milestone_map)} (expected 13)")
    freeze_milestones = [t for t in milestone_map if "Freeze" in t]
    print(f"  Freeze milestones: {freeze_milestones}")
    audit_ms = [t for t in milestone_map if "Audit" in t]
    poc_ms = [t for t in milestone_map if "PoC" in t]
    print(f"  Audit milestone: {audit_ms} (should be M6, after PoC M5: {poc_ms})")
    final_ms = {t: milestone_map[t] for t in milestone_map if "2.0.0 Production" in t}
    print(f"  Final milestone (2027-03-10): {final_ms}")
    print("=" * 60)


if __name__ == "__main__":
    main()
