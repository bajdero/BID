"""
tests/test_config.py
Testy jednostkowe dla modułu bid.config — ładowanie i walidacja konfiguracji.

Faza 2B: testy modułu config (load_settings, load_export_options)
"""
import pytest
import json
from pathlib import Path
from bid.config import load_settings, load_export_options
from bid.validators import validate_export_profile


# ─────────────────────────────────────────────────────────────────────
# TEST-CFG-001 do TEST-CFG-009
# ─────────────────────────────────────────────────────────────────────

def test_load_settings_valid(tmp_path, log_capture):
    """TEST-CFG-001: Ładowanie poprawnego settings.json."""
    settings_file = tmp_path / "settings.json"
    settings_data = {
        "source_folder": str(tmp_path / "source"),
        "export_folder": str(tmp_path / "export")
    }
    settings_file.write_text(json.dumps(settings_data), encoding="utf-8")
    
    result = load_settings(settings_file)
    
    assert "source_folder" in result
    assert "export_folder" in result
    assert result["source_folder"] == str(tmp_path / "source")
    assert log_capture.has("Loaded config:", level="DEBUG")


def test_load_settings_missing_file(tmp_path, log_capture):
    """TEST-CFG-002: Ładowanie nieistniejącego pliku → SystemExit."""
    nonexistent = tmp_path / "nonexistent.json"
    
    with pytest.raises(SystemExit) as exc_info:
        load_settings(nonexistent)
    
    assert exc_info.value.code == 1
    assert log_capture.has("Config file not found:", level="CRITICAL")


def test_load_settings_invalid_json(tmp_path, log_capture):
    """TEST-CFG-003: Ładowanie nieprawidłowego JSON → SystemExit."""
    settings_file = tmp_path / "broken.json"
    settings_file.write_text("{ broken json content }", encoding="utf-8")
    
    with pytest.raises(SystemExit) as exc_info:
        load_settings(settings_file)
    
    assert exc_info.value.code == 1
    assert log_capture.has("Invalid JSON in", level="CRITICAL")


def test_load_export_options_valid(tmp_path, log_capture):
    """TEST-CFG-004: Ładowanie poprawnego export_option.json."""
    export_file = tmp_path / "export_option.json"
    export_data = {
        "fb": {
            "size_type": "longer",
            "size": 1200,
            "format": "JPEG",
            "quality": 85,
            "logo": {}
        },
        "insta": {
            "size_type": "width",
            "size": 1080,
            "format": "PNG",
            "quality": 9,
            "logo": {}
        }
    }
    export_file.write_text(json.dumps(export_data), encoding="utf-8")
    
    result = load_export_options(export_file)
    
    assert "fb" in result
    assert "insta" in result
    assert result["fb"]["size_type"] == "longer"
    assert result["insta"]["format"] == "PNG"
    assert log_capture.has("Załadowano", level="INFO")
    assert log_capture.has("profili eksportu", level="INFO")


def test_load_export_options_empty(tmp_path, log_capture):
    """TEST-CFG-005: Pusty export_option.json zwraca pusty dict."""
    export_file = tmp_path / "export_option.json"
    export_file.write_text(json.dumps({}), encoding="utf-8")
    
    result = load_export_options(export_file)
    
    assert isinstance(result, dict)
    assert len(result) == 0
    assert log_capture.has("Załadowano 0 profili", level="INFO")


def test_load_export_options_missing_file(tmp_path, log_capture):
    """TEST-CFG-006: Ładowanie nieistniejącego export_option.json → SystemExit."""
    nonexistent = tmp_path / "no_export.json"
    
    with pytest.raises(SystemExit) as exc_info:
        load_export_options(nonexistent)
    
    assert exc_info.value.code == 1
    assert log_capture.has("Config file not found:", level="CRITICAL")


def test_validate_export_profile_valid(log_capture):
    """TEST-CFG-007: Walidacja poprawnego profilu eksportu."""
    profile = {
        "size_type": "longer",
        "size": 1200,
        "format": "JPEG",
        "quality": 85,
        "logo": {"landscape": {}, "portrait": {}}
    }
    
    errors = validate_export_profile("fb", profile)
    
    assert isinstance(errors, list)
    assert len(errors) == 0


def test_validate_export_profile_missing_size(log_capture):
    """TEST-CFG-008: Walidacja profilu bez klucza 'size'."""
    profile = {
        "size_type": "longer",
        # "size" brakuje
        "format": "JPEG",
        "quality": 85,
        "logo": {}
    }
    
    errors = validate_export_profile("fb", profile)
    
    assert isinstance(errors, list)
    assert len(errors) > 0
    assert any("size" in err for err in errors)


def test_validate_export_profile_missing_format(log_capture):
    """Walidacja profilu bez formatu."""
    profile = {
        "size_type": "longer",
        "size": 1200,
        # "format" brakuje
        "quality": 85,
        "logo": {}
    }
    
    errors = validate_export_profile("fb", profile)
    
    assert len(errors) > 0
    assert any("format" in err for err in errors)


def test_validate_export_profile_invalid_size_type(log_capture):
    """Walidacja profilu z nieprawidłowym size_type."""
    profile = {
        "size_type": "invalid_type",  # powinno być: longer, width, height
        "size": 1200,
        "format": "JPEG",
        "quality": 85,
        "logo": {}
    }
    
    errors = validate_export_profile("fb", profile)
    
    assert len(errors) > 0
    assert any("size_type" in err for err in errors)


def test_validate_export_profile_invalid_format(log_capture):
    """Walidacja profilu z nieprawidłowym formatem."""
    profile = {
        "size_type": "longer",
        "size": 1200,
        "format": "GIF",  # powinno być JPEG lub PNG
        "quality": 85,
        "logo": {}
    }
    
    errors = validate_export_profile("fb", profile)
    
    assert len(errors) > 0
    assert any("format" in err for err in errors)


def test_validate_export_profile_invalid_ratio(log_capture):
    """TEST-CFG-009: Walidacja profilu z nieprawidłowym ratio."""
    profile = {
        "size_type": "longer",
        "size": 1200,
        "format": "JPEG",
        "quality": 85,
        "logo": {},
        "ratio": "not_a_list"  # powinno być listą
    }
    
    errors = validate_export_profile("fb", profile)
    
    assert len(errors) > 0
    assert any("ratio" in err for err in errors)


def test_validate_export_profile_valid_ratio(log_capture):
    """Walidacja profilu z poprawnym ratio."""
    profile = {
        "size_type": "longer",
        "size": 1200,
        "format": "JPEG",
        "quality": 85,
        "logo": {},
        "ratio": [[1.33, 1.78], [0.75, 1.25]]  # poprawny format
    }
    
    errors = validate_export_profile("fb", profile)
    
    # ratio powinien być akceptowalny
    # (może być inne walidacje, ale ratio powinno być OK)
    assert not any("ratio" in err for err in errors)


def test_load_settings_with_custom_path(tmp_path, log_capture):
    """Ładowanie settings z niestandardowej ścieżki."""
    custom_settings = tmp_path / "custom" / "settings.json"
    custom_settings.parent.mkdir(parents=True)
    custom_settings.write_text(json.dumps({"test": "data"}), encoding="utf-8")
    
    result = load_settings(custom_settings)
    
    assert result["test"] == "data"
    assert log_capture.has("Loaded config:", level="DEBUG")


def test_load_export_options_multiple_profiles(tmp_path, log_capture):
    """Ładowanie export_option z wieloma profilami."""
    export_file = tmp_path / "export_option.json"
    export_data = {
        "fb": {"size": 1200, "format": "JPEG", "size_type": "longer", "quality": 85, "logo": {}},
        "insta": {"size": 1080, "format": "PNG", "size_type": "width", "quality": 9, "logo": {}},
        "tiktok": {"size": 1080, "format": "JPEG", "size_type": "height", "quality": 90, "logo": {}},
    }
    export_file.write_text(json.dumps(export_data), encoding="utf-8")
    
    result = load_export_options(export_file)
    
    assert len(result) == 3
    assert "tiktok" in result
    assert log_capture.has("Załadowano 3 profili", level="INFO")
