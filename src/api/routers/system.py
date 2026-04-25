"""
src/api/routers/system.py
Liveness, version, and metrics endpoints — no auth required.

GET /health        → liveness probe
GET /version       → API and BID version strings
GET /metrics/queue → queue-level operational metrics
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.config import settings
from src.api.deps import get_processing_service
from src.api.schemas.common import HealthResponse, QueueMetricsResponse, VersionResponse
from src.api.services.processing import ProcessingService

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
async def health() -> HealthResponse:
    """Return HTTP 200 with body ``{"status": "ok"}`` when the service is alive."""
    return HealthResponse(status="ok")


@router.get("/version", response_model=VersionResponse, summary="API and BID version")
async def version() -> VersionResponse:
    """Return the current API and BID product version strings."""
    return VersionResponse(
        api_version=settings.API_VERSION,
        bid_version=settings.BID_VERSION,
    )


@router.get(
    "/metrics/queue",
    response_model=QueueMetricsResponse,
    summary="Processing-queue operational metrics",
)
async def queue_metrics(
    svc: ProcessingService = Depends(get_processing_service),
) -> QueueMetricsResponse:
    """
    Return aggregate queue metrics across all projects:

    - **queue_length** — tasks waiting to start.
    - **active_workers** — tasks currently executing.
    - **max_workers** — concurrency ceiling (configured via `MAX_CONCURRENT_TASKS`).
    - **completed_total** / **failed_total** — counters since last process restart.
    - **utilization_pct** — `active_workers / max_workers × 100`.

    Suitable for monitoring dashboards and alerting rules.
    """
    raw = svc.get_global_metrics()
    active = raw["active_workers"]
    maximum = raw["max_workers"]
    utilization = round(active / maximum * 100, 1) if maximum else 0.0
    return QueueMetricsResponse(
        queue_length=raw["queue_length"],
        active_workers=active,
        max_workers=maximum,
        completed_total=raw["completed_total"],
        failed_total=raw["failed_total"],
        utilization_pct=utilization,
    )
