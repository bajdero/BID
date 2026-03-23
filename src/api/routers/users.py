"""
src/api/routers/users.py
User management endpoints — admin only (P1-04).

GET    /users          — list all users
POST   /users          — create a new user
PUT    /users/{id}     — update user role / state / email
DELETE /users/{id}     — permanently delete a user
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.deps import get_auth_service, get_db, require_admin
from src.api.models.user import UserRecord
from src.api.schemas.auth import UserCreate, UserResponse, UserUpdate
from src.api.schemas.common import ErrorResponse
from src.api.services.auth import AuthService

_ERR = {
    400: {"model": ErrorResponse, "description": "Validation error."},
    401: {"model": ErrorResponse, "description": "Authentication required."},
    403: {"model": ErrorResponse, "description": "Admin role required."},
    404: {"model": ErrorResponse, "description": "User not found."},
    409: {"model": ErrorResponse, "description": "Username or email already in use."},
}

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "",
    response_model=list[UserResponse],
    summary="List all users (admin only)",
    responses=_ERR,
)
def list_users(
    db: Session = Depends(get_db),
    svc: AuthService = Depends(get_auth_service),
    _admin: UserRecord = Depends(require_admin),
) -> list[UserResponse]:
    """Return all user records ordered by creation date. Requires admin role."""
    return svc.list_users(db)


@router.post(
    "",
    response_model=UserResponse,
    status_code=201,
    summary="Create a new user (admin only)",
    responses=_ERR,
)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    svc: AuthService = Depends(get_auth_service),
    _admin: UserRecord = Depends(require_admin),
) -> UserResponse:
    """
    Create a new user account.  Returns **409 Conflict** if *username* or
    *email* is already taken.
    """
    try:
        return svc.create_user(db, body)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user role / state / email (admin only)",
    responses=_ERR,
)
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    svc: AuthService = Depends(get_auth_service),
    _admin: UserRecord = Depends(require_admin),
) -> UserResponse:
    """Partially update a user's *role*, *is_active*, or *email*."""
    try:
        return svc.update_user(
            db, user_id,
            role=body.role,
            is_active=body.is_active,
            email=str(body.email) if body.email else None,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete(
    "/{user_id}",
    status_code=204,
    summary="Delete a user (admin only)",
    responses=_ERR,
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    svc: AuthService = Depends(get_auth_service),
    _admin: UserRecord = Depends(require_admin),
) -> None:
    """Permanently remove a user account."""
    try:
        svc.delete_user(db, user_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
