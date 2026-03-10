"""
tests/test_config_processing.py
Faza 3C: Testy integracyjne — interakcja konfiguracji z przetwarzaniem obrazów.

Weryfikuje że ustawienia w export_settings są poprawnie stosowane przez process_photo_task.
"""
from pathlib import Path

import pytest
from PIL import Image

from bid.image_processing import process_photo_task, get_logo


# ─────────────────────────────────────────────────────────────────────
# Helpery
# ─────────────────────────────────────────────────────────────────────

def _make_photo(session_dir: Path, name: str, width: int = 2000, height: int = 1500) -> Path:
    img = Image.new("RGB", (width, height), color=(100, 150, 200))
    path = session_dir / name
    img.save(path, "JPEG")
    return path


def _make_logo(session_dir: Path) -> Path:
    logo = Image.new("RGBA", (400, 133), color=(255, 255, 255, 200))
    path = session_dir / "logo.png"
    logo.save(path, "PNG")
    return path


def _basic_profile(size: int, fmt: str = "JPEG", size_type: str = "longer", extra: dict | None = None) -> dict:
    quality = 85 if fmt == "JPEG" else 6
    profile = {
        "size_type": size_type,
        "size": size,
        "format": fmt,
        "quality": quality,
        "logo": {
            "landscape": {"size": size // 5, "opacity": 60, "x_offset": 10, "y_offset": 10},
            "portrait": {"size": int(size / 3.85), "opacity": 60, "x_offset": 10, "y_offset": 10},
        },
    }
    if extra:
        profile.update(extra)
    return profile


# ─────────────────────────────────────────────────────────────────────
# TEST-CP-001
# ─────────────────────────────────────────────────────────────────────

def test_config_drives_export_size(tmp_path, log_capture):
    """TEST-CP-001: Rozmiar eksportu pochodzi z konfiguracji (longer=800)."""
    session_dir = tmp_path / "source" / "session1"
    session_dir.mkdir(parents=True)
    export_dir = tmp_path / "export"
    export_dir.mkdir()

    photo_path = _make_photo(session_dir, "photo.jpg", 2000, 1500)
    _make_logo(session_dir)

    export_settings = {"fb": _basic_profile(size=800, size_type="longer")}

    result = process_photo_task(
        photo_path=str(photo_path),
        folder_name="session1",
        photo_name="photo.jpg",
        created_date="2026:03:09 14:00:00",
        export_folder=str(export_dir),
        export_settings=export_settings,
        existing_exports={},
    )

    assert result["success"] is True
    exported_path = Path(result["exported"]["fb"])
    assert exported_path.exists()

    with Image.open(exported_path) as img:
        assert max(img.width, img.height) == 800

    assert log_capture.has("[PROCESS] Zakończono:", level="INFO")


# ─────────────────────────────────────────────────────────────────────
# TEST-CP-002
# ─────────────────────────────────────────────────────────────────────

def test_config_jpeg_vs_png_format(tmp_path, log_capture):
    """TEST-CP-002: format JPEG → .jpg, format PNG → .png."""
    session_dir = tmp_path / "source" / "session1"
    session_dir.mkdir(parents=True)
    export_dir = tmp_path / "export"
    export_dir.mkdir()

    photo_path = _make_photo(session_dir, "photo.jpg")
    _make_logo(session_dir)

    export_settings = {
        "fb": _basic_profile(size=600, fmt="JPEG"),
        "insta": _basic_profile(size=600, fmt="PNG", size_type="width"),
    }

    result = process_photo_task(
        photo_path=str(photo_path),
        folder_name="session1",
        photo_name="photo.jpg",
        created_date="2026:03:09 14:00:00",
        export_folder=str(export_dir),
        export_settings=export_settings,
        existing_exports={},
    )

    assert result["success"] is True
    assert "fb" in result["exported"]
    assert "insta" in result["exported"]

    fb_path = Path(result["exported"]["fb"])
    insta_path = Path(result["exported"]["insta"])
    assert fb_path.exists()
    assert insta_path.exists()

    assert fb_path.suffix == ".jpg"
    assert insta_path.suffix == ".png"

    with Image.open(fb_path) as fb_img:
        assert fb_img.format == "JPEG"
    with Image.open(insta_path) as insta_img:
        assert insta_img.format == "PNG"


# ─────────────────────────────────────────────────────────────────────
# TEST-CP-003
# ─────────────────────────────────────────────────────────────────────

def test_config_with_ratio_filter(tmp_path, log_capture):
    """TEST-CP-003: Filtr ratio — ultra-panoramiczne zdjęcie jest pomijane."""
    session_dir = tmp_path / "source" / "session1"
    session_dir.mkdir(parents=True)
    export_dir = tmp_path / "export"
    export_dir.mkdir()

    # Zdjęcie panoramiczne: 3000x1000, ratio = round(3000/1000, 2) = 3.0
    photo_path = _make_photo(session_dir, "panoramic.jpg", 3000, 1000)
    _make_logo(session_dir)

    # Profil akceptuje tylko ratio 0.8 i 1.25 (whitelist) — 3.0 nie pasuje
    profile_with_ratio = _basic_profile(size=800, extra={"ratio": [0.8, 1.25]})
    export_settings = {"fb": profile_with_ratio}

    result = process_photo_task(
        photo_path=str(photo_path),
        folder_name="session1",
        photo_name="panoramic.jpg",
        created_date="2026:03:09 14:00:00",
        export_folder=str(export_dir),
        export_settings=export_settings,
        existing_exports={},
    )

    # Przetwarzanie zakończone bez błędu, ale profil fb pominięty
    assert result["success"] is True
    assert "fb" not in result["exported"]

    # Katalog fb/ nie istnieje lub jest pusty
    fb_dir = export_dir / "fb"
    assert not fb_dir.exists() or len(list(fb_dir.iterdir())) == 0

    assert log_capture.has("Pomijam", level="DEBUG")


# ─────────────────────────────────────────────────────────────────────
# TEST-CP-004
# ─────────────────────────────────────────────────────────────────────

def test_missing_logo_exports_without_watermark(tmp_path, log_capture):
    """TEST-CP-004: Brak logo.png → eksport pomyślny, ale bez watermarku."""
    session_dir = tmp_path / "source" / "session1"
    session_dir.mkdir(parents=True)
    export_dir = tmp_path / "export"
    export_dir.mkdir()

    # Zdjęcie BEZ logo.png w tym samym folderze
    photo_path = _make_photo(session_dir, "photo.jpg")
    assert not (session_dir / "logo.png").exists()

    export_settings = {"fb": _basic_profile(size=800)}

    result = process_photo_task(
        photo_path=str(photo_path),
        folder_name="session1",
        photo_name="photo.jpg",
        created_date="2026:03:09 14:00:00",
        export_folder=str(export_dir),
        export_settings=export_settings,
        existing_exports={},
    )

    # Eksport powinien się udać pomimo braku logo
    assert result["success"] is True
    assert "fb" in result["exported"]
    assert Path(result["exported"]["fb"]).exists()

    # Ostrzeżenie o brakującym logo
    assert log_capture.has("BRAK LOGO", level="WARNING")
