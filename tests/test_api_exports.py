"""
tests/test_api_exports.py
Integration tests for the export-conflict endpoints.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(api_test_app):
    with TestClient(api_test_app) as c:
        yield c


@pytest.fixture()
def project_id(sample_api_project):
    return sample_api_project.name


# ---------------------------------------------------------------------------
# GET /exports/conflicts
# ---------------------------------------------------------------------------


class TestListConflicts:
    def test_empty_returns_200(self, client, project_id):
        r = client.get(f"/api/v1/projects/{project_id}/exports/conflicts")
        assert r.status_code == 200

    def test_returns_list(self, client, project_id):
        data = client.get(f"/api/v1/projects/{project_id}/exports/conflicts").json()
        assert isinstance(data, list)

    def test_unknown_project_returns_404(self, client):
        r = client.get("/api/v1/projects/no_such_project/exports/conflicts")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# POST /exports/conflicts/resolve — validation
# ---------------------------------------------------------------------------


class TestResolveConflicts:
    def test_missing_body_rejected(self, client, project_id):
        r = client.post(
            f"/api/v1/projects/{project_id}/exports/conflicts/resolve"
        )
        assert r.status_code == 422

    def test_invalid_mode_rejected(self, client, project_id):
        r = client.post(
            f"/api/v1/projects/{project_id}/exports/conflicts/resolve",
            json={"mode": "bogus", "action": "replace"},
        )
        assert r.status_code == 422

    def test_invalid_action_rejected(self, client, project_id):
        r = client.post(
            f"/api/v1/projects/{project_id}/exports/conflicts/resolve",
            json={"mode": "all", "action": "delete"},
        )
        assert r.status_code == 422

    def test_resolve_all_replace_empty_project(self, client, project_id):
        r = client.post(
            f"/api/v1/projects/{project_id}/exports/conflicts/resolve",
            json={"mode": "all", "action": "replace"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["resolved"] == 0
        assert data["action"] == "replace"

    def test_resolve_all_skip(self, client, project_id):
        r = client.post(
            f"/api/v1/projects/{project_id}/exports/conflicts/resolve",
            json={"mode": "all", "action": "skip"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["action"] == "skip"

    def test_resolve_selection_with_items(self, client, project_id):
        r = client.post(
            f"/api/v1/projects/{project_id}/exports/conflicts/resolve",
            json={
                "mode": "selection",
                "action": "replace",
                "items": [["Session1", "IMG_001.jpg"]],
            },
        )
        # session1/IMG_001.jpg doesn't exist in DB → resolved=0 but still 200
        assert r.status_code == 200
        assert r.json()["resolved"] == 0

    def test_unknown_project_returns_404(self, client):
        r = client.post(
            "/api/v1/projects/no_such_project/exports/conflicts/resolve",
            json={"mode": "all", "action": "skip"},
        )
        assert r.status_code == 404
