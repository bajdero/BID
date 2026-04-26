"""
tests/test_auth_service.py
Unit tests for AuthService and JWT helpers (P1-04).
"""
from __future__ import annotations

import pytest
from jose import JWTError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.models.database import Base
from src.api.schemas.auth import UserCreate
from src.api.services.auth import AuthService, create_access_token, decode_token


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


class TestAuthService:
    def test_create_user_and_authenticate(self, db_session):
        svc = AuthService()
        created = svc.create_user(
            db_session,
            body=UserCreate(
                username="admin",
                email="admin@example.com",
                password="StrongPass1",
                role="admin",
            ),
        )
        assert created.username == "admin"

        token_pair = svc.login(db_session, "admin", "StrongPass1")
        assert token_pair is not None
        assert token_pair.access_token

    def test_login_fails_for_bad_password(self, db_session):
        svc = AuthService()
        svc.create_user(
            db_session,
            body=UserCreate(
                username="editor",
                email="editor@example.com",
                password="CorrectPass1",
                role="editor",
            ),
        )

        assert svc.login(db_session, "editor", "wrong") is None

    def test_decode_access_token_payload(self):
        token = create_access_token("u1", "admin")
        payload = decode_token(token)
        assert payload["sub"] == "u1"
        assert payload["role"] == "admin"
        assert payload["type"] == "access"

    def test_decode_invalid_token_raises(self):
        with pytest.raises(JWTError):
            decode_token("not-a-jwt")
