"""
src/api/schemas/auth.py
Pydantic schemas for authentication and user management (P1-04).
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------------
# Auth — login / token refresh
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

    model_config = ConfigDict(
        json_schema_extra={"example": {"username": "admin", "password": "s3cr3t"}}
    )


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access-token lifetime in seconds.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
            }
        }
    )


class RefreshRequest(BaseModel):
    refresh_token: str


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=128, pattern=r"^[a-zA-Z0-9_\-]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, description="Plain-text password (hashed server-side).")
    role: Literal["admin", "editor", "viewer"] = "editor"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "photo_editor",
                "email": "editor@example.com",
                "password": "Str0ng!Pass",
                "role": "editor",
            }
        }
    )


class UserUpdate(BaseModel):
    """Partial update — only provided fields are changed."""

    role: Literal["admin", "editor", "viewer"] | None = None
    is_active: bool | None = None
    email: EmailStr | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"role": "viewer", "is_active": True}
        }
    )


class UserResponse(BaseModel):
    """Public representation of a user record (no password)."""

    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: str
    last_login: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "username": "admin",
                "email": "admin@example.com",
                "role": "admin",
                "is_active": True,
                "created_at": "2026-03-23T12:00:00",
                "last_login": "2026-03-23T15:00:00",
            }
        }
    )
