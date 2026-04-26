"""
tests/test_api_auth_users.py
Integration tests for auth and users endpoints (P1-04/P1-06).
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.deps import require_admin, require_authenticated_user
from src.api.models.user import UserRecord
from src.api.services.auth import hash_password


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _seed_user(*, username: str, email: str, password: str, role: str, is_active: bool = True):
    # SessionLocal is monkeypatched by the api_test_app fixture; import lazily
    # from the module each time to get the patched in-memory session factory.
    from src.api.models import database as db_mod

    with db_mod.SessionLocal() as db:
        user = UserRecord(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            role=role,
            is_active=is_active,
        )
        db.add(user)
        db.commit()


def _strict_client(api_test_app):
    # Remove auth bypass overrides used by non-auth integration tests.
    api_test_app.dependency_overrides.pop(require_authenticated_user, None)
    api_test_app.dependency_overrides.pop(require_admin, None)
    return TestClient(api_test_app)


class TestAuthAndUsers:
    def test_login_success_and_refresh(self, api_test_app):
        _seed_user(
            username="admin",
            email="admin@example.com",
            password="StrongPass1",
            role="admin",
        )
        with _strict_client(api_test_app) as client:
            login = client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": "StrongPass1"},
            )
            assert login.status_code == 200
            tokens = login.json()
            assert tokens["token_type"] == "bearer"
            assert tokens["access_token"]
            assert tokens["refresh_token"]

            refreshed = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": tokens["refresh_token"]},
            )
            assert refreshed.status_code == 200
            assert refreshed.json()["access_token"]

    def test_login_rejects_invalid_credentials(self, api_test_app):
        _seed_user(
            username="editor",
            email="editor@example.com",
            password="CorrectPass1",
            role="editor",
        )
        with _strict_client(api_test_app) as client:
            bad = client.post(
                "/api/v1/auth/login",
                json={"username": "editor", "password": "wrong"},
            )
        assert bad.status_code == 401

    def test_users_requires_auth(self, api_test_app):
        with _strict_client(api_test_app) as client:
            r = client.get("/api/v1/users")
        assert r.status_code == 401

    def test_users_crud_with_admin_token(self, api_test_app):
        _seed_user(
            username="superadmin",
            email="superadmin@example.com",
            password="StrongPass1",
            role="admin",
        )
        with _strict_client(api_test_app) as client:
            login = client.post(
                "/api/v1/auth/login",
                json={"username": "superadmin", "password": "StrongPass1"},
            )
            token = login.json()["access_token"]

            created = client.post(
                "/api/v1/users",
                headers=_auth_header(token),
                json={
                    "username": "viewer1",
                    "email": "viewer1@example.com",
                    "password": "ViewerPass1",
                    "role": "viewer",
                },
            )
            assert created.status_code == 201
            uid = created.json()["id"]

            listed = client.get("/api/v1/users", headers=_auth_header(token))
            assert listed.status_code == 200
            assert any(u["username"] == "viewer1" for u in listed.json())

            updated = client.put(
                f"/api/v1/users/{uid}",
                headers=_auth_header(token),
                json={"role": "editor", "is_active": True},
            )
            assert updated.status_code == 200
            assert updated.json()["role"] == "editor"

            deleted = client.delete(f"/api/v1/users/{uid}", headers=_auth_header(token))
            assert deleted.status_code == 204

    def test_users_forbidden_for_non_admin(self, api_test_app):
        _seed_user(
            username="editor2",
            email="editor2@example.com",
            password="EditorPass1",
            role="editor",
        )
        with _strict_client(api_test_app) as client:
            login = client.post(
                "/api/v1/auth/login",
                json={"username": "editor2", "password": "EditorPass1"},
            )
            token = login.json()["access_token"]

            denied = client.get("/api/v1/users", headers=_auth_header(token))
            assert denied.status_code == 403
