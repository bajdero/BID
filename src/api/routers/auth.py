"""
src/api/routers/auth.py
Authentication endpoints (P1-04).

POST /auth/login    — issue access + refresh tokens
POST /auth/refresh  — rotate tokens using a valid refresh token
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.deps import get_auth_service, get_db
from src.api.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from src.api.schemas.common import ErrorResponse
from src.api.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

_ERR = {
    401: {"model": ErrorResponse, "description": "Invalid credentials or expired token."},
}


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive JWT tokens",
    responses={400: {"model": ErrorResponse}, **_ERR},
)
def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
    svc: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Authenticate with *username* and *password*.

    On success returns an **access token** (short-lived) and a **refresh token**
    (long-lived).  Pass the access token as `Authorization: Bearer <token>` on
    protected endpoints.
    """
    result = svc.login(db, body.username, body.password)
    if result is None:
        raise HTTPException(
            status_code=401, detail="Incorrect username or password."
        )
    return result


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    responses=_ERR,
)
def refresh(
    body: RefreshRequest,
    db: Session = Depends(get_db),
    svc: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Exchange a valid *refresh_token* for a new access + refresh token pair.

    Previously issued refresh tokens remain valid until they expire according to
    the server's token lifetime settings; clients should discard old refresh
    tokens once a new pair is obtained.

    # TODO(security): implement refresh-token rotation — store JTIs in a DB
    # revocation table and invalidate the previous token on re-issue.
    # See: https://github.com/bajdero/BID/pull/26#discussion (C4)
    """
    result = svc.refresh(db, body.refresh_token)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token.")
    return result
