"""
tests/test_api_projects.py
Integration tests for project and settings endpoints (P1-03).
"""
from __future__ import annotations

from fastapi.testclient import TestClient


def _projects_url() -> str:
    return "/api/v1/projects"


def _project_url(project_id: str) -> str:
    return f"/api/v1/projects/{project_id}"


def _settings_url(project_id: str) -> str:
    return f"/api/v1/projects/{project_id}/settings"


def _profiles_url(project_id: str) -> str:
    return f"/api/v1/projects/{project_id}/export-profiles"


def _validate_profile_url(project_id: str) -> str:
    return f"/api/v1/projects/{project_id}/export-profiles/validate"


def _audit_url(project_id: str) -> str:
    return f"/api/v1/projects/{project_id}/audit/logs"


class TestProjectsApi:
    def test_list_projects_contains_fixture_project(self, api_test_app, sample_api_project):
        with TestClient(api_test_app) as client:
            r = client.get(_projects_url())
        assert r.status_code == 200
        ids = {p["id"] for p in r.json()}
        assert sample_api_project.name in ids

    def test_get_project_details(self, api_test_app, sample_api_project):
        with TestClient(api_test_app) as client:
            r = client.get(_project_url(sample_api_project.name))
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == sample_api_project.name
        assert body["path"].endswith(sample_api_project.name)

    def test_create_project(self, api_test_app):
        payload = {
            "name": "New API Project",
            "source_folder": "D:/tmp/source",
            "export_folder": "D:/tmp/export",
            "export_profiles": {
                "web": {
                    "size_type": "longer",
                    "size": 800,
                    "format": "JPEG",
                    "quality": 80,
                    "logo": {},
                    "logo_required": False,
                }
            },
        }
        with TestClient(api_test_app) as client:
            r = client.post(_projects_url(), json=payload)
        assert r.status_code == 201
        assert r.json()["id"] == "New_API_Project"

    def test_get_and_update_settings(self, api_test_app, sample_api_project):
        pid = sample_api_project.name
        with TestClient(api_test_app) as client:
            current = client.get(_settings_url(pid))
            assert current.status_code == 200
            body = current.json()

            body["source_folder"] = body["source_folder"] + "_updated"
            updated = client.put(_settings_url(pid), json=body)

        assert updated.status_code == 200
        assert updated.json()["source_folder"].endswith("_updated")

    def test_get_and_update_export_profiles(self, api_test_app, sample_api_project):
        pid = sample_api_project.name
        with TestClient(api_test_app) as client:
            current = client.get(_profiles_url(pid))
            assert current.status_code == 200
            profiles = current.json()["profiles"]

            profiles["print"] = {
                "size_type": "width",
                "size": 1200,
                "format": "JPEG",
                "quality": 90,
                "logo": {},
                "logo_required": False,
            }
            updated = client.put(_profiles_url(pid), json=profiles)

        assert updated.status_code == 200
        assert "print" in updated.json()["profiles"]

    def test_validate_export_profile(self, api_test_app, sample_api_project):
        pid = sample_api_project.name
        payload = {
            "name": "bad",
            "profile": {
                "size_type": "wrong",
                "size": 800,
                "format": "JPEG",
                "quality": 80,
                "logo": {},
            },
        }
        with TestClient(api_test_app) as client:
            r = client.post(_validate_profile_url(pid), json=payload)
        assert r.status_code == 200
        body = r.json()
        assert body["valid"] is False
        assert len(body["errors"]) > 0

    def test_audit_logs_endpoint(self, api_test_app, sample_api_project):
        with TestClient(api_test_app) as client:
            r = client.get(_audit_url(sample_api_project.name))
        assert r.status_code == 200
        assert isinstance(r.json(), list)
