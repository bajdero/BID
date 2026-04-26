"""
src/api/services/auth.py
JWT token generation/validation and password hashing utilities (P1-04).

Security design:
- Passwords are hashed with passlib PBKDF2-SHA256 (never stored or logged in plain-text).
- JWTs are signed with HMAC-SHA256 using the app SECRET_KEY.
- Access tokens are short-lived (default 30 min); refresh tokens long-lived (7 days).
- Token payloads carry only `sub` (username), `role`, and `type` ("access"/"refresh").
- Tokens with type != "access" are rejected by get_current_user.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.api.config import settings
from src.api.models.user import UserRecord
from src.api.schemas.auth import TokenResponse, UserCreate, UserResponse

logger = logging.getLogger("BID.api")

# One shared password-hashing context for the entire process.
# PBKDF2-SHA256 is selected for broad platform compatibility.
_pwd_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------


def hash_password(plain: str) -> str:
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------


def _create_token(data: dict[str, Any], expire_seconds: int) -> str:
    """Sign a JWT that expires in *expire_seconds* from now (UTC)."""
    payload = data.copy()
    exp = datetime.now(timezone.utc) + timedelta(seconds=expire_seconds)
    payload["exp"] = exp
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(username: str, role: str) -> str:
    return _create_token(
        {"sub": username, "role": role, "type": "access"},
        settings.ACCESS_TOKEN_EXPIRE_SECONDS,
    )


def create_refresh_token(username: str, role: str) -> str:
    return _create_token(
        {"sub": username, "role": role, "type": "refresh"},
        settings.REFRESH_TOKEN_EXPIRE_SECONDS,
    )


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and verify a JWT.  Raises JWTError on invalid/expired tokens.
    Does NOT check token type — callers must verify ``payload["type"]``.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


# ---------------------------------------------------------------------------
# AuthService
# ---------------------------------------------------------------------------


class AuthService:
    """
    Stateless service for user authentication and management.
    A new instance is safe to create per-request.
    """

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def authenticate(self, db: Session, username: str, password: str) -> UserRecord | None:
        """
        Return the UserRecord if *username* + *password* are valid and the account
        is active; otherwise return None.
        """
        user = db.query(UserRecord).filter_by(username=username).first()
        if user is None or not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        # Record login time.
        user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        return user

    def login(self, db: Session, username: str, password: str) -> TokenResponse | None:
        """Return a TokenResponse on success; None if credentials are invalid."""
        user = self.authenticate(db, username, password)
        if user is None:
            return None
        return TokenResponse(
            access_token=create_access_token(user.username, user.role),
            refresh_token=create_refresh_token(user.username, user.role),
            expires_in=settings.ACCESS_TOKEN_EXPIRE_SECONDS,
        )

    def refresh(self, db: Session, refresh_token: str) -> TokenResponse | None:
        """
        Validate a refresh token and issue a new access+refresh pair.
        Returns None if the token is invalid or the user account is deactivated.
        """
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            return None

        if payload.get("type") != "refresh":
            return None

        username: str = payload.get("sub", "")
        user = db.query(UserRecord).filter_by(username=username).first()
        if user is None or not user.is_active:
            return None

        return TokenResponse(
            access_token=create_access_token(user.username, user.role),
            refresh_token=create_refresh_token(user.username, user.role),
            expires_in=settings.ACCESS_TOKEN_EXPIRE_SECONDS,
        )

    # ------------------------------------------------------------------
    # User management (admin operations)
    # ------------------------------------------------------------------

    def list_users(self, db: Session) -> list[UserResponse]:
        users = db.query(UserRecord).order_by(UserRecord.id).all()
        return [self._to_response(u) for u in users]

    def create_user(self, db: Session, body: UserCreate) -> UserResponse:
        """
        Create a new user.  Raises ValueError if username or email is already taken.
        """
        if db.query(UserRecord).filter_by(username=body.username).first():
            raise ValueError(f"Username '{body.username}' is already taken.")
        if db.query(UserRecord).filter_by(email=body.email).first():
            raise ValueError(f"Email '{body.email}' is already registered.")

        user = UserRecord(
            username=body.username,
            email=body.email,
            hashed_password=hash_password(body.password),
            role=body.role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"[AUTH] Created user '{body.username}' role={body.role!r}")
        return self._to_response(user)

    def update_user(
        self,
        db: Session,
        user_id: int,
        *,
        role: str | None = None,
        is_active: bool | None = None,
        email: str | None = None,
    ) -> UserResponse:
        """Update mutable fields on a user.  Returns the updated record."""
        user = db.query(UserRecord).filter_by(id=user_id).first()
        if user is None:
            raise LookupError(f"User {user_id} not found.")
        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active
        if email is not None:
            # Check email uniqueness.
            conflict = (
                db.query(UserRecord)
                .filter(UserRecord.email == email, UserRecord.id != user_id)
                .first()
            )
            if conflict:
                raise ValueError(f"Email '{email}' is already registered.")
            user.email = email
        db.commit()
        db.refresh(user)
        return self._to_response(user)

    def delete_user(self, db: Session, user_id: int) -> None:
        """Permanently delete a user record.  Raises LookupError if not found."""
        user = db.query(UserRecord).filter_by(id=user_id).first()
        if user is None:
            raise LookupError(f"User {user_id} not found.")
        db.delete(user)
        db.commit()
        logger.info(f"[AUTH] Deleted user id={user_id}")

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _to_response(user: UserRecord) -> UserResponse:
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else "",
            last_login=user.last_login.isoformat() if user.last_login else None,
        )
