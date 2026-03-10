"""
tests/test_workflows.py
Faza 3A: Testy integracyjne — pełny workflow przetwarzania zdjęć.

Weryfikuje interakcję między modułami: image_processing + source_manager + konfiguracja.
"""
import os
from pathlib import Path

import pytest
from PIL import Image
from PIL.ExifTags import IFD

from bid.image_processing import process_photo_task, get_logo


# ─────────────────────────────────────────────────────────────────────
# TEST-WF-001
# ─────────────────────────────────────────────────────────────────────

def test_single_photo_full_export(full_test_project, log_capture, export_settings_fb):
    """TEST-WF-001: 1 zdjęcie → 1 profil → plik na dysku."""
    project = full_test_project
    photo_path = str(project["session_dir"] / "photo_0.jpg")

    result = process_photo_task(
        photo_path=photo_path,
        folder_name="session1",
        photo_name="photo_0.jpg",
        created_date="2026:03:09 14:30:00",
        export_folder=str(project["export_dir"]),
        export_settings=export_settings_fb,
        existing_exports={},
    )

    assert result["success"] is True
    assert "fb" in result["exported"]

    exported_path = Path(result["exported"]["fb"])
    assert exported_path.exists()

    # Dłuższa krawędź eksportu = 1200 px
    with Image.open(exported_path) as img:
        assert max(img.width, img.height) == 1200

    # Kolejność logów: Start → Zakończono
    log_capture.assert_sequence("[PROCESS] Start:", "[PROCESS] Zakończono:")


# ─────────────────────────────────────────────────────────────────────
# TEST-WF-002
# ─────────────────────────────────────────────────────────────────────

def test_batch_3_photos_single_profile(full_test_project, log_capture, export_settings_fb):
    """TEST-WF-002: 3 zdjęcia → 3 eksporty w jednym profilu."""
    project = full_test_project
    session_dir = project["session_dir"]
    export_dir = str(project["export_dir"])

    results = []
    for i in range(3):
        r = process_photo_task(
            photo_path=str(session_dir / f"photo_{i}.jpg"),
            folder_name="session1",
            photo_name=f"photo_{i}.jpg",
            created_date=f"2026:03:09 14:{30 + i}:00",
            export_folder=export_dir,
            export_settings=export_settings_fb,
            existing_exports={},
        )
        results.append(r)

    for i, r in enumerate(results):
        assert r["success"] is True, f"photo_{i} nieudany: {r.get('error_msg')}"
        assert "fb" in r["exported"]
        assert Path(r["exported"]["fb"]).exists()
        assert isinstance(r["duration"], float)
        assert r["duration"] > 0

    # 3 pliki w katalogu fb/
    fb_dir = project["export_dir"] / "fb"
    assert fb_dir.is_dir()
    assert len(list(fb_dir.iterdir())) == 3


# ─────────────────────────────────────────────────────────────────────
# TEST-WF-003
# ─────────────────────────────────────────────────────────────────────

def test_batch_multi_profile(full_test_project, log_capture, export_settings_multi):
    """TEST-WF-003: 1 zdjęcie → 2 profile (fb + insta) → 2 pliki."""
    project = full_test_project
    photo_path = str(project["session_dir"] / "photo_0.jpg")

    result = process_photo_task(
        photo_path=photo_path,
        folder_name="session1",
        photo_name="photo_0.jpg",
        created_date="2026:03:09 14:30:00",
        export_folder=str(project["export_dir"]),
        export_settings=export_settings_multi,
        existing_exports={},
    )

    assert result["success"] is True
    assert "fb" in result["exported"]
    assert "insta" in result["exported"]

    fb_path = Path(result["exported"]["fb"])
    insta_path = Path(result["exported"]["insta"])
    assert fb_path.exists()
    assert insta_path.exists()

    # fb = JPEG (.jpg), insta = PNG (.png)
    assert fb_path.suffix == ".jpg"
    assert insta_path.suffix == ".png"


# ─────────────────────────────────────────────────────────────────────
# TEST-WF-004
# ─────────────────────────────────────────────────────────────────────

def test_export_preserves_exif_after_resize(full_test_project, log_capture, export_settings_fb):
    """TEST-WF-004: EXIF round-trip — Make i Model zachowane po skalowaniu."""
    project = full_test_project
    session_dir = project["session_dir"]

    # Zdjęcie z tagami Make, Model, DateTime
    photo_path_obj = session_dir / "exif_photo.jpg"
    img = Image.new("RGB", (2000, 1500), color=(80, 120, 160))
    exif = img.getexif()
    exif[0x010F] = "TestMake"            # Make
    exif[0x0110] = "TestModel"           # Model
    exif[0x0132] = "2026:03:09 12:00:00" # DateTime
    ifd = exif.get_ifd(IFD.Exif)
    ifd[0x9003] = "2026:03:09 12:00:00"  # DateTimeOriginal
    img.save(photo_path_obj, "JPEG", exif=exif.tobytes())

    result = process_photo_task(
        photo_path=str(photo_path_obj),
        folder_name="session1",
        photo_name="exif_photo.jpg",
        created_date="2026:03:09 12:00:00",
        export_folder=str(project["export_dir"]),
        export_settings=export_settings_fb,
        existing_exports={},
    )

    assert result["success"] is True
    exported_path = Path(result["exported"]["fb"])
    assert exported_path.exists()

    # Make (0x010F) i Model (0x0110) zachowane w eksporcie
    with Image.open(exported_path) as exported_img:
        exported_exif = exported_img.getexif()
        assert 0x010F in exported_exif, "Make powinien być zachowany w EXIF eksportu"
        assert 0x0110 in exported_exif, "Model powinien być zachowany w EXIF eksportu"

    log_capture.assert_sequence("[PROCESS] Start:", "[PROCESS] Zakończono:")


# ─────────────────────────────────────────────────────────────────────
# TEST-WF-005
# ─────────────────────────────────────────────────────────────────────

def test_export_creates_subfolder(full_test_project, log_capture, export_settings_fb):
    """TEST-WF-005: Brakujący podkatalog eksportu jest automatycznie tworzony."""
    project = full_test_project
    export_dir = project["export_dir"]

    # Upewnij się, że fb/ jeszcze nie istnieje
    assert not (export_dir / "fb").exists()

    result = process_photo_task(
        photo_path=str(project["session_dir"] / "photo_0.jpg"),
        folder_name="session1",
        photo_name="photo_0.jpg",
        created_date="2026:03:09 14:30:00",
        export_folder=str(export_dir),
        export_settings=export_settings_fb,
        existing_exports={},
    )

    assert result["success"] is True
    # Podkatalog fb/ powinien zostać automatycznie utworzony
    assert (export_dir / "fb").is_dir()
    assert log_capture.has("[PROCESS] Start:", level="INFO")


# ─────────────────────────────────────────────────────────────────────
# TEST-WF-006
# ─────────────────────────────────────────────────────────────────────

def test_export_skip_existing(full_test_project, log_capture, export_settings_fb):
    """TEST-WF-006: Istniejący plik eksportu nie jest nadpisywany."""
    project = full_test_project
    export_dir = project["export_dir"]

    # Przygotuj istniejący plik eksportu
    fb_dir = export_dir / "fb"
    fb_dir.mkdir(parents=True, exist_ok=True)
    existing_file = fb_dir / "existing_export.jpg"
    existing_file.write_bytes(b"FAKE_JPEG_CONTENT_ORIGINAL")
    original_mtime = existing_file.stat().st_mtime
    original_content = existing_file.read_bytes()

    result = process_photo_task(
        photo_path=str(project["session_dir"] / "photo_0.jpg"),
        folder_name="session1",
        photo_name="photo_0.jpg",
        created_date="2026:03:09 14:30:00",
        export_folder=str(export_dir),
        export_settings=export_settings_fb,
        existing_exports={"fb": str(existing_file)},
    )

    assert result["success"] is True
    # Istniejący plik nie został nadpisany
    assert existing_file.stat().st_mtime == original_mtime
    assert existing_file.read_bytes() == original_content
    # Wynik wskazuje na istniejącą ścieżkę
    assert result["exported"].get("fb") == str(existing_file)
    assert log_capture.has("Pomijam istniejący eksport", level="DEBUG")
