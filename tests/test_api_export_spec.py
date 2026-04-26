"""
tests/test_api_export_spec.py
Unit tests for OpenAPI static export helper.
"""
from __future__ import annotations

from pathlib import Path

from src.api import export_spec


def test_export_spec_main_writes_file(tmp_path, monkeypatch):
    out = tmp_path / "openapi.json"
    monkeypatch.setattr("sys.argv", ["export_spec", "--out", str(out)])

    export_spec.main()

    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert '"openapi"' in content
    assert '"paths"' in content
