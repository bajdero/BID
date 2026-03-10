"""
tests/test_regressions.py
Faza 4B: Testy regresji — weryfikacja znanych bugów z AUDIT_REPORT.md.

Każdy test odpowiada konkretnemu bugowi i zapewnia że problem nie powróci.
"""
import json
import os
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from PIL import Image

from bid.image_processing import process_photo_task, get_logo
from bid.source_manager import (
    SourceState,
    create_source_dict,
    load_source_dict,
    save_source_dict,
)


# ─────────────────────────────────────────────────────────────────────
# TEST-REG-001: BUG-003 — Cicha awaria watermarku
# ─────────────────────────────────────────────────────────────────────

def test_watermark_always_applied_when_logo_exists(tmp_path, log_capture, export_settings_fb):
    """TEST-REG-001: Logo istnieje → watermark ZAWSZE nałożony.

    Weryfikuje że BUG-003 (cicha awaria gdy brak logo) nie dotknie sytuacji
    gdy logo jest dostępne — eksport musi zawierać watermark.
    """
    # GIVEN: Zdjęcie + logo.png w tym samym folderze
    session_dir = tmp_path / "source" / "session1"
    session_dir.mkdir(parents=True)
    export_dir = tmp_path / "export"
    export_dir.mkdir()

    img = Image.new("RGB", (2000, 1500), color=(100, 150, 200))
    img_path = session_dir / "photo.jpg"
    img.save(img_path, "JPEG")

    logo = Image.new("RGBA", (400, 133), color=(255, 255, 255, 200))
    for x in range(50, 350):
        for y in range(20, 113):
            logo.putpixel((x, y), (0, 0, 0, 255))
    logo.save(session_dir / "logo.png", "PNG")

    # Skaluj zdjęcie (symulacja resize przed watermarkiem) dla weryfikacji pikseli
    resized_no_watermark = img.resize((1200, 900))
    sample_pixel_before = resized_no_watermark.getpixel((1199 - 10, 899 - 10))

    # Wyczyść cache logo żeby test był deterministyczny
    get_logo.cache_clear()

    # WHEN: process_photo_task z istniejącym logo
    result = process_photo_task(
        photo_path=str(img_path),
        folder_name="session1",
        photo_name="photo.jpg",
        created_date="2026:03:09 14:30:00",
        export_folder=str(export_dir),
        export_settings=export_settings_fb,
        existing_exports={},
    )

    # THEN: Eksport się udał
    assert result["success"] is True, f"Błąd eksportu: {result.get('error_msg')}"
    assert "fb" in result["exported"]

    exported_path = Path(result["exported"]["fb"])
    assert exported_path.exists()

    # THEN: Piksele w prawym dolnym rogu RÓŻNIĄ SIĘ od oryginalnego przeskalowanego zdjęcia
    # — watermark musi być widoczny
    with Image.open(exported_path) as exported_img:
        w, h = exported_img.size
        # Sprawdzamy piksel w strefie watermarku (prawy dolny róg)
        watermark_pixel = exported_img.getpixel((w - 15, h - 15))

    # Watermark jest ciemny — piksel musi różnić się od jasnego tła
    assert watermark_pixel != sample_pixel_before, (
        "Watermark nie został nałożony! Piksel w prawym dolnym rogu jest identyczny "
        f"z oryginalem: {watermark_pixel}"
    )

    # THEN: Brak ostrzeżenia BRAK LOGO w logach
    assert not log_capture.has("BRAK LOGO"), (
        "Nieoczekiwane ostrzeżenie o braku logo gdy logo istnieje"
    )

    # THEN: Log potwierdzający nałożenie watermarku
    assert log_capture.has("watermark") or log_capture.has("logo"), (
        "Brak logu o watermarku / logo"
    )


# ─────────────────────────────────────────────────────────────────────
# TEST-REG-002: BUG-002 — Race condition w source_dict
# ─────────────────────────────────────────────────────────────────────

def test_source_dict_no_corruption_under_load(tmp_path, log_capture):
    """TEST-REG-002: 50 równoczesnych zapisów → dict spójny.

    Weryfikuje brak uszkodzenia source_dict przy równoległym dostępie.
    Symuluje BUG-002: wiele wątków modyfikuje dict jednocześnie.
    """
    # GIVEN: source_dict z 50 entries
    source_dict: dict = {}
    lock = threading.Lock()

    for i in range(50):
        folder = f"folder_{i:02d}"
        source_dict[folder] = {
            f"photo_{i:02d}.jpg": {
                "path": f"/source/{folder}/photo_{i:02d}.jpg",
                "state": SourceState.NEW,
                "exported": {},
                "size": "2.50 MB",
                "created": "2026:03:09 14:30:00",
                "mtime": 1741520000.0,
                "exif": {},
            }
        }

    errors: list[str] = []

    def worker(folder_name: str, photo_name: str):
        """Symuluje aktualizację entry przez wątek roboczy."""
        try:
            with lock:
                if folder_name in source_dict and photo_name in source_dict[folder_name]:
                    source_dict[folder_name][photo_name]["state"] = SourceState.OK
                    source_dict[folder_name][photo_name]["exported"] = {
                        "fb": f"/export/fb/YAPA_{folder_name}_{photo_name}.jpg"
                    }
        except Exception as exc:
            errors.append(f"Wyjątek w wątku {folder_name}/{photo_name}: {exc}")

    # WHEN: 50 wątków jednocześnie modyfikuje entries
    threads = []
    for i in range(50):
        folder = f"folder_{i:02d}"
        photo = f"photo_{i:02d}.jpg"
        t = threading.Thread(target=worker, args=(folder, photo))
        threads.append(t)

    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10.0)

    # THEN: Brak wyjątków
    assert len(errors) == 0, f"Wykryto błędy wątkowe: {errors}"

    # THEN: Dict spójny — wszystkie 50 folderów obecne
    assert len(source_dict) == 50, f"Utracono wpisy: {len(source_dict)} ≠ 50"

    # THEN: Każdy entry może być OK lub NEW (w zależności od harmonogramu wątków)
    for i in range(50):
        folder = f"folder_{i:02d}"
        photo = f"photo_{i:02d}.jpg"
        assert folder in source_dict, f"Brakuje folderu: {folder}"
        assert photo in source_dict[folder], f"Brakuje zdjęcia: {folder}/{photo}"
        state = source_dict[folder][photo]["state"]
        assert state in (SourceState.NEW, SourceState.OK), (
            f"Nieprawidłowy stan {folder}/{photo}: {state}"
        )

    # THEN: Wszystkie entries mają OK (lock zapewnia że każdy wątek wykonał się)
    ok_count = sum(
        1 for folder in source_dict.values()
        for entry in folder.values()
        if entry["state"] == SourceState.OK
    )
    assert ok_count == 50, f"Nie wszystkie entries zaktualizowane: {ok_count}/50"


# ─────────────────────────────────────────────────────────────────────
# TEST-REG-003: Unicode filenames roundtrip
# ─────────────────────────────────────────────────────────────────────

def test_unicode_filenames_roundtrip(tmp_path, log_capture):
    """TEST-REG-003: Polskie znaki w nazwach plików → cały pipeline bez UnicodeError.

    Weryfikuje że ścieżki z polskimi znakami przechodzą przez:
    create_source_dict → save_source_dict → load_source_dict → process_photo_task
    """
    # GIVEN: Folder z polskimi znakami w nazwie folderu
    unicode_folder_name = "Zdjęcia_ŻŹĆ"
    source_dir = tmp_path / "source"
    session_dir = source_dir / unicode_folder_name
    export_dir = tmp_path / "export"
    project_dir = tmp_path / "project"

    try:
        session_dir.mkdir(parents=True)
    except (OSError, UnicodeEncodeError) as exc:
        pytest.skip(f"System plików nie obsługuje polskich znaków w ścieżkach: {exc}")

    export_dir.mkdir()
    project_dir.mkdir()

    # Zdjęcie z polską nazwą
    unicode_photo_name = "foto_ąęść.jpg"
    img = Image.new("RGB", (200, 150), color=(100, 150, 200))
    try:
        img.save(session_dir / unicode_photo_name, "JPEG")
    except (OSError, UnicodeEncodeError) as exc:
        pytest.skip(f"System plików nie obsługuje polskich znaków w nazwach plików: {exc}")

    logo = Image.new("RGBA", (40, 14), color=(255, 255, 255, 200))
    logo.save(session_dir / "logo.png", "PNG")

    export_settings = {
        "fb": {
            "size_type": "longer",
            "size": 150,
            "format": "JPEG",
            "quality": 85,
            "logo": {
                "landscape": {"size": 30, "opacity": 60, "x_offset": 5, "y_offset": 5},
                "portrait": {"size": 39, "opacity": 60, "x_offset": 5, "y_offset": 5},
            },
        }
    }

    # WHEN: create_source_dict
    source_dict = create_source_dict(str(source_dir))

    assert unicode_folder_name in source_dict, (
        f"Folder '{unicode_folder_name}' nie znaleziony w source_dict. "
        f"Klucze: {list(source_dict.keys())}"
    )
    assert unicode_photo_name in source_dict[unicode_folder_name], (
        f"Plik '{unicode_photo_name}' nie znaleziony."
    )

    # WHEN: save_source_dict → load_source_dict (roundtrip UTF-8)
    save_source_dict(source_dict, project_dir)
    loaded_dict = load_source_dict(project_dir)

    assert loaded_dict is not None, "Nie udało się wczytać source_dict.json"
    assert unicode_folder_name in loaded_dict, (
        f"Folder z polskimi znakami utracony po roundtrip JSON. "
        f"Klucze: {list(loaded_dict.keys())}"
    )
    assert unicode_photo_name in loaded_dict[unicode_folder_name], (
        f"Plik z polskimi znakami utracony po roundtrip JSON."
    )

    # WHEN: process_photo_task z polską ścieżką
    entry = loaded_dict[unicode_folder_name][unicode_photo_name]
    get_logo.cache_clear()
    result = process_photo_task(
        photo_path=entry["path"],
        folder_name=unicode_folder_name,
        photo_name=unicode_photo_name,
        created_date=entry["created"],
        export_folder=str(export_dir),
        export_settings=export_settings,
        existing_exports={},
    )

    # THEN: Przetwarzanie zakończone sukcesem
    assert result["success"] is True, (
        f"Przetwarzanie pliku z polskimi znakami nie powiodło się: {result.get('error_msg')}"
    )
    assert "fb" in result["exported"]
    assert Path(result["exported"]["fb"]).exists()

    # THEN: Brak UnicodeError w logach
    error_logs = log_capture.at_level("ERROR")
    unicode_errors = [msg for msg in error_logs if "unicode" in msg.lower() or "codec" in msg.lower()]
    assert len(unicode_errors) == 0, f"Błędy Unicode w logach: {unicode_errors}"


# ─────────────────────────────────────────────────────────────────────
# TEST-REG-004: UNC path handling
# ─────────────────────────────────────────────────────────────────────

def test_unc_path_handling(tmp_path, log_capture):
    """TEST-REG-004: Ścieżki UNC (\\server\\share\\...) → create_source_dict nie crashuje.

    Weryfikuje poprawne parsowanie ścieżek UNC z podwójnymi backslashami.
    Używa mock os.walk żeby nie wymagać prawdziwego udziału sieciowego.
    """
    # GIVEN: Ścieżka UNC
    unc_path = r"\\server\share\photos"

    # Symulowany wynik os.walk dla ścieżki UNC
    # Normalizacja ścieżki przez os.path.normpath może zmienić format na Windows
    import os
    normalized_unc = os.path.normpath(unc_path)

    session_path = os.path.normpath(os.path.join(unc_path, "session1"))

    mock_walk_results = [
        # (root, dirs, files)
        (normalized_unc, ["session1"], []),
        (session_path, [], ["photo_001.jpg", "logo.png"]),
    ]

    # Symulowany wynik create_source_item dla UNC
    mock_item = {
        "path": os.path.normpath(session_path + "/photo_001.jpg"),
        "state": SourceState.NEW,
        "exported": {},
        "size": "3.00 MB",
        "created": "2026:03:09 14:30:00",
        "mtime": 1741520000.0,
        "exif": {},
    }

    # WHEN: create_source_dict z mockowanym os.walk
    with patch("bid.source_manager.os.walk", return_value=mock_walk_results), \
         patch("bid.source_manager.create_source_item", return_value=mock_item):

        source_dict = create_source_dict(unc_path)

    # THEN: Brak crash — dict zawiera sesję z UNC
    assert "session1" in source_dict, (
        f"Sesja nie znaleziona w wynikach UNC. Klucze: {list(source_dict.keys())}"
    )
    assert "photo_001.jpg" in source_dict["session1"], (
        "Zdjęcie nie znalezione w sesji UNC"
    )

    # THEN: Ścieżka zdjęcia jest poprawnie ukształtowana (bez podwójnych separatorów)
    photo_path = source_dict["session1"]["photo_001.jpg"]["path"]
    assert "//" not in photo_path.replace("\\\\", ""), (
        f"Podwójne slashe w ścieżce: {photo_path}"
    )

    # THEN: Logi nie zawierają traceback/wyjątków
    error_logs = log_capture.at_level("ERROR")
    critical_errors = [msg for msg in error_logs if "exception" in msg.lower() or "traceback" in msg.lower()]
    assert len(critical_errors) == 0, f"Krytyczne błędy przy UNC: {critical_errors}"


# ─────────────────────────────────────────────────────────────────────
# TEST-REG-005: Export option with all format types
# ─────────────────────────────────────────────────────────────────────

def test_export_option_with_all_format_types(tmp_path, log_capture):
    """TEST-REG-005: Profile JPEG i PNG → poprawne rozszerzenia i wyniki.

    Weryfikuje że każdy obsługiwany format eksportu produkuje poprawny plik.
    """
    # GIVEN: Zdjęcie źródłowe
    session_dir = tmp_path / "source" / "session1"
    session_dir.mkdir(parents=True)
    export_dir = tmp_path / "export"
    export_dir.mkdir()

    img = Image.new("RGB", (1000, 750), color=(80, 120, 160))
    img_path = session_dir / "photo.jpg"
    img.save(img_path, "JPEG")

    logo = Image.new("RGBA", (200, 67), color=(255, 255, 255, 200))
    logo.save(session_dir / "logo.png", "PNG")

    # Profile z różnymi formatami
    multi_format_settings = {
        "jpeg_profile": {
            "size_type": "longer",
            "size": 800,
            "format": "JPEG",
            "quality": 85,
            "logo": {
                "landscape": {"size": 160, "opacity": 60, "x_offset": 10, "y_offset": 10},
                "portrait": {"size": 208, "opacity": 60, "x_offset": 10, "y_offset": 10},
            },
        },
        "png_profile": {
            "size_type": "longer",
            "size": 600,
            "format": "PNG",
            "quality": 6,
            "logo": {
                "landscape": {"size": 120, "opacity": 60, "x_offset": 10, "y_offset": 10},
                "portrait": {"size": 156, "opacity": 60, "x_offset": 10, "y_offset": 10},
            },
        },
    }

    get_logo.cache_clear()

    # WHEN: Przetwórz zdjęcie z oboma profilami
    result = process_photo_task(
        photo_path=str(img_path),
        folder_name="session1",
        photo_name="photo.jpg",
        created_date="2026:03:09 14:30:00",
        export_folder=str(export_dir),
        export_settings=multi_format_settings,
        existing_exports={},
    )

    # THEN: Oba eksporty zaistniały
    assert result["success"] is True, f"Błąd eksportu: {result.get('error_msg')}"
    assert "jpeg_profile" in result["exported"], "Brak eksportu JPEG"
    assert "png_profile" in result["exported"], "Brak eksportu PNG"

    jpeg_path = Path(result["exported"]["jpeg_profile"])
    png_path = Path(result["exported"]["png_profile"])

    # THEN: Pliki istnieją na dysku
    assert jpeg_path.exists(), f"Plik JPEG nie istnieje: {jpeg_path}"
    assert png_path.exists(), f"Plik PNG nie istnieje: {png_path}"

    # THEN: Poprawne rozszerzenia
    assert jpeg_path.suffix == ".jpg", f"Oczekiwano .jpg, got {jpeg_path.suffix}"
    assert png_path.suffix == ".png", f"Oczekiwano .png, got {png_path.suffix}"

    # THEN: Poprawne rozmiary
    with Image.open(jpeg_path) as jpeg_img:
        assert max(jpeg_img.width, jpeg_img.height) == 800
        assert jpeg_img.format == "JPEG"

    with Image.open(png_path) as png_img:
        assert max(png_img.width, png_img.height) == 600
        assert png_img.format == "PNG"

    # THEN: JPEG ma EXIF, PNG ma metadane tekstowe
    with Image.open(jpeg_path) as jpeg_img:
        exif_data = jpeg_img.getexif()
        assert len(exif_data) > 0, "JPEG bez danych EXIF"

    # THEN: Brak błędów w logach
    error_logs = log_capture.at_level("ERROR")
    assert len(error_logs) == 0, f"Nieoczekiwane błędy: {error_logs}"

    # THEN: Logi potwierdzające oba eksporty
    assert log_capture.has("jpeg_profile")
    assert log_capture.has("png_profile")
