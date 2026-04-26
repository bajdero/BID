"""
src/api/errors.py
FastAPI exception handlers — maps bid.errors exceptions to HTTP status codes.

Mapping from web_architecture.md §11:
  ConfigError          → 422 Unprocessable Entity
  ImageProcessingError → 500 Internal Server Error
  SourceManagerError   → 500 Internal Server Error
  ProjectError         → 404 Not Found / 409 Conflict (depends on exc.status_hint)
  FileNotFoundError    → 404 Not Found
  PermissionError      → 403 Forbidden
  PathTraversalError   → 400 Bad Request
"""
from __future__ import annotations

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from bid.errors import (
    ConfigError,
    ImageProcessingError,
    ProjectError,
    SourceManagerError,
)
from src.api.services.processing import PathTraversalError

logger = logging.getLogger("BID.api")


def _error_body(detail: str, field: str | None = None) -> dict:
    body: dict = {"detail": detail}
    if field:
        body["field"] = field
    return body


async def handle_config_error(request: Request, exc: ConfigError) -> JSONResponse:
    logger.warning(f"[API] ConfigError on {request.url}: {exc}")
    return JSONResponse(status_code=422, content=_error_body(str(exc)))


async def handle_image_processing_error(
    request: Request, exc: ImageProcessingError
) -> JSONResponse:
    logger.error(f"[API] ImageProcessingError on {request.url}: {exc}")
    return JSONResponse(status_code=500, content=_error_body(str(exc)))


async def handle_source_manager_error(
    request: Request, exc: SourceManagerError
) -> JSONResponse:
    logger.error(f"[API] SourceManagerError on {request.url}: {exc}")
    return JSONResponse(status_code=500, content=_error_body(str(exc)))


async def handle_project_error(request: Request, exc: ProjectError) -> JSONResponse:
    # ProjectError carries an optional hint; map to 409 Conflict for "already exists" cases.
    message = str(exc)
    status = 409 if "already exists" in message.lower() else 404
    logger.warning(f"[API] ProjectError ({status}) on {request.url}: {exc}")
    return JSONResponse(status_code=status, content=_error_body(message))


async def handle_file_not_found(
    request: Request, exc: FileNotFoundError
) -> JSONResponse:
    logger.warning(f"[API] FileNotFoundError on {request.url}: {exc}")
    return JSONResponse(status_code=404, content=_error_body(str(exc)))


async def handle_permission_error(
    request: Request, exc: PermissionError
) -> JSONResponse:
    logger.warning(f"[API] PermissionError on {request.url}: {exc}")
    return JSONResponse(status_code=403, content=_error_body("Access denied."))


async def handle_path_traversal(
    request: Request, exc: PathTraversalError
) -> JSONResponse:
    logger.warning(f"[API] PathTraversalError on {request.url}: {exc}")
    return JSONResponse(status_code=400, content=_error_body(str(exc)))


def register_exception_handlers(app) -> None:  # type: ignore[type-arg]
    """Attach all BID-specific exception handlers to *app*."""
    app.add_exception_handler(ConfigError, handle_config_error)
    app.add_exception_handler(ImageProcessingError, handle_image_processing_error)
    app.add_exception_handler(SourceManagerError, handle_source_manager_error)
    app.add_exception_handler(ProjectError, handle_project_error)
    app.add_exception_handler(FileNotFoundError, handle_file_not_found)
    app.add_exception_handler(PermissionError, handle_permission_error)
    app.add_exception_handler(PathTraversalError, handle_path_traversal)
