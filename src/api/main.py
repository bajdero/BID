"""
src/api/main.py
FastAPI application factory for the BID backend API.

Run locally:
    uvicorn src.api.main:app --reload --port 8000

Swagger UI (OpenAPI spec):
    http://localhost:8000/docs

Redoc:
    http://localhost:8000/redoc

Static spec export:
    python -m src.api.export_spec
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.config import settings
from src.api.deps import require_authenticated_user
from src.api.errors import register_exception_handlers
from src.api.models.database import init_db
from src.api.routers import auth, exports, processing, projects, system, users
from src.api.services.events import EventBroadcastService, set_event_service, get_event_service
from src.api.services.processing import ProcessingService, set_service, get_service
from src.api.websocket import router as ws_router
from src.api.websocket.manager import ConnectionManager, set_manager

logger = logging.getLogger("BID.api")

# ---------------------------------------------------------------------------
# OpenAPI tag metadata — drives the tag section in Swagger UI / Redoc
# ---------------------------------------------------------------------------

OPENAPI_TAGS: list[dict] = [
    {
        "name": "system",
        "description": (
            "Liveness and version probes, and queue-level operational metrics.  "
            "These endpoints require no authentication and are intended for "
            "load-balancer health checks and monitoring dashboards."
        ),
    },
    {
        "name": "processing",
        "description": (
            "Image-processing pipeline control for a single project.  "
            "Enqueue selected or all *new* photos, reset photos to *new* state, "
            "and query the real-time processing-queue snapshot.  "
            "Processing is non-blocking: the enqueue call returns immediately "
            "while work proceeds in background threads."
        ),
    },
    {
        "name": "exports",
        "description": (
            "Export-conflict management.  "
            "Lists photos whose expected output file is missing or zero-byte "
            "(*blocked exports*) and provides a bulk-resolve action to either "
            "re-queue (`replace`) or permanently skip (`skip`) conflicting entries."
        ),
    },
    {
        "name": "projects",
        "description": (
            "Project directory CRUD, settings management, and export-profile "
            "configuration.  "
            "Projects are on-disk directories under `PROJECTS_DIR`; each contains "
            "`settings.json` (source/export folder paths) and `export_option.json` "
            "(profile definitions).  "
            "Also exposes the immutable per-project audit-log stream."
        ),
    },
    {
        "name": "auth",
        "description": (
            "JWT-based authentication.  "
            "POST `/auth/login` with username + password to receive an access token "
            "(30 min, default) and a refresh token (7 days, default).  "
            "Pass the access token as `Authorization: Bearer <token>`."
        ),
    },
    {
        "name": "users",
        "description": (
            "User account management — **admin role required**.  "
            "Supports create, list, update (role/state/email), and delete operations."
        ),
    },
    {
        "name": "websocket",
        "description": (
            "WebSocket real-time event streaming (Phase 2).  "
            "Connect to `GET /api/v1/projects/{project_id}/ws?token=<access_token>` "
            "to receive `state_change`, `progress`, `scan_update`, `queue_metrics`, "
            "and `error` frames as processing progresses.  "
            "Send `{\"type\":\"subscribe\",\"folders\":[...]}` to filter by sub-folder.  "
            "The server sends periodic `ping` frames; reply with `pong` to keep the "
            "connection alive."
        ),
    },
]

# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown actions
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise DB and processing service on startup; clean up on shutdown."""
    logger.info("[API] Starting up — initialising database and processing service.")
    init_db()

    ws_manager = ConnectionManager()
    set_manager(ws_manager)
    logger.info("[API] ConnectionManager ready.")

    svc = ProcessingService(max_workers=settings.MAX_CONCURRENT_TASKS)
    svc.set_ws_manager(ws_manager)
    set_service(svc)
    logger.info(
        f"[API] ProcessingService ready (max_workers={settings.MAX_CONCURRENT_TASKS})."
    )

    event_svc = EventBroadcastService()
    set_event_service(event_svc)
    logger.info("[API] EventBroadcastService ready.")

    yield  # ← application runs here

    logger.info("[API] Shutting down — stopping services.")
    # Notify all connected WebSocket clients before closing
    try:
        from src.api.websocket.schemas import ServerClosingMessage
        ws_manager = get_manager()
        import asyncio
        asyncio.create_task(
            ws_manager.broadcast_all(ServerClosingMessage().model_dump())
        )
    except Exception:
        pass  # WS manager may not be available in all test scenarios
    get_event_service().stop_all()
    get_service().shutdown()


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Build and configure the FastAPI application instance."""
    app = FastAPI(
        title="BID — Batch Image Delivery API",
        description=(
            "REST API for the **BID** (*Batch Image Delivery*) image-processing pipeline.\n\n"
            "BID automates batch photo processing: automatic scaling, watermark overlay, "
            "EXIF cleaning, colour-space conversion, and delivery-folder export.  "
            "This API exposes the processing core as an OpenAPI 3.0-compliant service, "
            "decoupled from the legacy Tkinter UI.\n\n"
            "## Road-map\n"
            "| Phase | Milestone | Status |\n"
            "|-------|-----------|--------|\n"
            "| 1 | Backend API Extraction | **Done** |\n"
            "| 2 | WebSocket real-time layer | **In progress** |\n"
            "| 3 | React/TypeScript frontend | Planned |\n"
            "| 4 | Event system | Planned |\n\n"
            "## Auth\n"
            "Protected endpoints require `Authorization: Bearer <access_token>`.  "
            "Obtain tokens via `POST /api/v1/auth/login`.  "
            "Admin-only endpoints additionally require the `admin` role.\n\n"
            "## Errors\n"
            "All error responses use the `ErrorResponse` schema: "
            "`{ \"detail\": \"...\", \"field\": \"...\" }`."
        ),
        version=settings.API_VERSION,
        contact={
            "name": "BID project",
            "url": "https://github.com/bajdero/BID",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
        openapi_tags=OPENAPI_TAGS,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ---- CORS ----------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["Authorization", "Content-Type"],
        max_age=3600,
    )

    # ---- Exception handlers --------------------------------------------------
    register_exception_handlers(app)

    # ---- Routers (all under /api/v1) ----------------------------------------
    prefix = "/api/v1"
    app.include_router(system.router, prefix=prefix)
    app.include_router(auth.router, prefix=prefix)
    app.include_router(users.router, prefix=prefix)
    app.include_router(
        processing.router,
        prefix=prefix,
        dependencies=[Depends(require_authenticated_user)],
    )
    app.include_router(
        exports.router,
        prefix=prefix,
        dependencies=[Depends(require_authenticated_user)],
    )
    app.include_router(
        projects.router,
        prefix=prefix,
        dependencies=[Depends(require_authenticated_user)],
    )
    # WebSocket endpoint — auth is handled inside the route handler
    # (query-param JWT, no Bearer header support in browser WS API)
    app.include_router(ws_router, prefix=prefix)

    return app


# Module-level application instance used by uvicorn.
app = create_app()
