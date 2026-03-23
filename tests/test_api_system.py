"""
tests/test_api_system.py
Integration tests for the /health and /version system endpoints.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.config import settings


@pytest.fixture()
def client(api_test_app):
    """Synchronous TestClient wrapping the test application."""
    with TestClient(api_test_app) as c:
        yield c


class TestHealth:
    def test_returns_200(self, client):
        r = client.get("/api/v1/health")
        assert r.status_code == 200

    def test_body(self, client):
        r = client.get("/api/v1/health")
        assert r.json() == {"status": "ok"}

    def test_content_type_json(self, client):
        r = client.get("/api/v1/health")
        assert "application/json" in r.headers["content-type"]


class TestVersion:
    def test_returns_200(self, client):
        r = client.get("/api/v1/version")
        assert r.status_code == 200

    def test_body_contains_versions(self, client):
        data = client.get("/api/v1/version").json()
        assert "api_version" in data
        assert "bid_version" in data

    def test_api_version_matches_settings(self, client):
        data = client.get("/api/v1/version").json()
        assert data["api_version"] == settings.API_VERSION
