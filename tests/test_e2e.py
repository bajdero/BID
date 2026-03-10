"""
tests/test_e2e.py
Faza 4A: Testy end-to-end — pełny cykl życia projektu.

Weryfikuje kompletne przepływy od tworzenia projektu przez skanowanie,
przetwarzanie, aż do zapisu wyników.
"""
import json
import os
import time
import threading
from pathlib import Path

import pytest
from PIL import Image

from bid.image_processing import process_photo_task
from bid.project_manager import ProjectManager
from bid.source_manager import (
    SourceState,
    check_integrity,
    create_source_dict,
    load_source_dict,
    save_source_dict,
    update_source_dict,
)


# ─────────────────────────────────────────────────────────────────────
# TEST-E2E-001
# ─────────────────────────────────────────────────────────────────────

def test_new_project_full_workflow(tmp_path, log_capture, export_settings_fb):
    """TEST-E2E-001: Stwórz projekt → skanuj → eksportuj → zapisz."""
    # GIVEN: Foldery projektu
    source_dir = tmp_path / "source"
    export_dir = tmp_path / "export"
    project_dir = tmp_path / "projects"
    project_dir.mkdir(parents=True)
    source_dir.mkdir()
    export_dir.mkdir()

    session_dir = source_dir / "session1"
    session_dir.mkdir()

    # Zdjęcia testowe w sesji
    for i in range(3):
        img = Image.new("RGB", (2000, 1500), color=(100 + i * 30, 50, 80))
        exif = img.getexif()
        exif[0x0132] = f"2026:03:09 14:{30 + i}:00"
        img.save(session_dir / f"photo_{i}.jpg", "JPEG", exif=exif.tobytes())

    # Logo
    logo = Image.new("RGBA", (600, 200), color=(255, 255, 255, 200))
    logo.save(session_dir / "logo.png", "PNG")

    # Nadpisujemy ProjectManager.projects_dir dla izolacji testu
    original_projects_dir = ProjectManager.projects_dir
    original_recent_file = ProjectManager.recent_projects_file
    try:
        ProjectManager.projects_dir = project_dir
        ProjectManager.recent_projects_file = tmp_path / "recent.json"

        # WHEN: 1) Stwórz projekt
        created_project_dir = ProjectManager.create_project(
            "TestE2E",
            str(source_dir),
            str(export_dir),
            export_settings_fb,
        )

        # THEN: Weryfikuj strukturę projektu
        assert created_project_dir.exists()
        assert (created_project_dir / "settings.json").exists()
        assert (created_project_dir / "export_option.json").exists()

        # WHEN: 2) Skanuj folder źródłowy
        source_dict = create_source_dict(str(source_dir), str(export_dir), export_settings_fb)

        assert "session1" in source_dict
        assert len(source_dict["session1"]) == 3
        for entry in source_dict["session1"].values():
            assert entry["state"] == SourceState.NEW

        # WHEN: 3) Przetwórz każde zdjęcie
        results = []
        for i in range(3):
            photo_name = f"photo_{i}.jpg"
            entry = source_dict["session1"][photo_name]
            r = process_photo_task(
                photo_path=entry["path"],
                folder_name="session1",
                photo_name=photo_name,
                created_date=entry["created"],
                export_folder=str(export_dir),
                export_settings=export_settings_fb,
                existing_exports={},
            )
            results.append(r)
            if r["success"]:
                source_dict["session1"][photo_name]["state"] = SourceState.OK
                source_dict["session1"][photo_name]["exported"] = r["exported"]

        # Wszystkie eksporty udane
        for i, r in enumerate(results):
            assert r["success"] is True, f"photo_{i} nieudany: {r.get('error_msg')}"
            assert "fb" in r["exported"]
            assert Path(r["exported"]["fb"]).exists()

        # WHEN: 4) Zapisz source_dict
        save_source_dict(source_dict, created_project_dir)

        # THEN: source_dict.json istnieje z wpisami OK
        loaded = load_source_dict(created_project_dir)
        assert loaded is not None
        assert "session1" in loaded
        for entry in loaded["session1"].values():
            assert entry["state"] == SourceState.OK

        # THEN: Sprawdź logi — pełna sekwencja
        log_capture.assert_sequence(
            "Tworzę projekt",
            "Tworzę source_dict",
            "[PROCESS] Start:",
            "[PROCESS] Zakończono:",
        )

    finally:
        ProjectManager.projects_dir = original_projects_dir
        ProjectManager.recent_projects_file = original_recent_file


# ─────────────────────────────────────────────────────────────────────
# TEST-E2E-002
# ─────────────────────────────────────────────────────────────────────

def test_reopen_project_incremental(tmp_path, log_capture, export_settings_fb):
    """TEST-E2E-002: Wczytaj istniejący projekt → dodaj nowe → przetwórz tylko nowe."""
    # GIVEN: Projekt z 3 przetworzonymi zdjęciami
    source_dir = tmp_path / "source"
    export_dir = tmp_path / "export"
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True)
    session_dir = source_dir / "session1"
    session_dir.mkdir(parents=True)
    export_dir.mkdir()

    # Tworzenie pierwszej partii zdjęć
    for i in range(3):
        img = Image.new("RGB", (2000, 1500), color=(100 + i * 30, 50, 80))
        img.save(session_dir / f"photo_{i}.jpg", "JPEG")

    logo = Image.new("RGBA", (600, 200), color=(255, 255, 255, 200))
    logo.save(session_dir / "logo.png", "PNG")

    # Inicjalne skanowanie i przetworzenie
    source_dict = create_source_dict(str(source_dir), str(export_dir), export_settings_fb)

    original_export_paths = {}
    for photo_name, entry in source_dict["session1"].items():
        r = process_photo_task(
            photo_path=entry["path"],
            folder_name="session1",
            photo_name=photo_name,
            created_date=entry["created"],
            export_folder=str(export_dir),
            export_settings=export_settings_fb,
            existing_exports={},
        )
        source_dict["session1"][photo_name]["state"] = SourceState.OK
        source_dict["session1"][photo_name]["exported"] = r["exported"]
        original_export_paths[photo_name] = r["exported"].get("fb")

    save_source_dict(source_dict, project_dir)

    # WHEN: Wczytaj istniejący projekt (symulacja ponownego otwarcia)
    loaded_dict = load_source_dict(project_dir)
    assert loaded_dict is not None

    # Dodaj 2 nowe zdjęcia
    for i in range(3, 5):
        img = Image.new("RGB", (2000, 1500), color=(200, i * 30, 50))
        img.save(session_dir / f"photo_{i}.jpg", "JPEG")

    # Aktualizacja słownika
    updated_dict, found_new = update_source_dict(
        loaded_dict, str(source_dir), str(export_dir), export_settings_fb
    )
    assert found_new is True

    # Przetwórz TYLKO nowe zdjęcia
    new_results = []
    for photo_name, entry in updated_dict["session1"].items():
        if entry["state"] == SourceState.NEW:
            r = process_photo_task(
                photo_path=entry["path"],
                folder_name="session1",
                photo_name=photo_name,
                created_date=entry["created"],
                export_folder=str(export_dir),
                export_settings=export_settings_fb,
                existing_exports={},
            )
            new_results.append(r)
            updated_dict["session1"][photo_name]["state"] = SourceState.OK

    # THEN: Tylko 2 nowe przetworzone
    assert len(new_results) == 2
    for r in new_results:
        assert r["success"] is True

    # THEN: Stare eksporty niezmienione (te same ścieżki)
    for photo_name, old_path in original_export_paths.items():
        if old_path:
            assert Path(old_path).exists(), f"Stary eksport usunięty: {old_path}"

    # THEN: Łącznie 5 wpisów
    assert len(updated_dict["session1"]) == 5

    assert log_capture.has("Nowy plik:")


# ─────────────────────────────────────────────────────────────────────
# TEST-E2E-003
# ─────────────────────────────────────────────────────────────────────

def test_error_recovery_workflow(tmp_path, log_capture, export_settings_fb):
    """TEST-E2E-003: 5 zdjęć, 1 uszkodzone → 4 OK + 1 ERROR."""
    # GIVEN: Projekt z 5 zdjęciami, z czego 1 uszkodzone
    source_dir = tmp_path / "source"
    export_dir = tmp_path / "export"
    session_dir = source_dir / "session1"
    session_dir.mkdir(parents=True)
    export_dir.mkdir()

    # 4 poprawne zdjęcia
    for i in range(4):
        img = Image.new("RGB", (1000, 750), color=(100 + i * 30, 80, 60))
        img.save(session_dir / f"photo_{i}.jpg", "JPEG")

    # 1 uszkodzone zdjęcie (plik z nieprawidłowymi danymi)
    corrupted_path = session_dir / "photo_corrupted.jpg"
    corrupted_path.write_bytes(b"FAKE_JPEG_DATA_NOT_VALID" * 10)

    logo = Image.new("RGBA", (600, 200), color=(255, 255, 255, 200))
    logo.save(session_dir / "logo.png", "PNG")

    photos = [
        f"photo_{i}.jpg" for i in range(4)
    ] + ["photo_corrupted.jpg"]

    # WHEN: Przetwórz wszystkie zdjęcia
    results = {}
    for photo_name in photos:
        photo_path = str(session_dir / photo_name)
        r = process_photo_task(
            photo_path=photo_path,
            folder_name="session1",
            photo_name=photo_name,
            created_date="2026:03:09 14:30:00",
            export_folder=str(export_dir),
            export_settings=export_settings_fb,
            existing_exports={},
        )
        results[photo_name] = r

    # THEN: 4 success, 1 failure
    successes = [r for r in results.values() if r["success"] is True]
    failures = [r for r in results.values() if r["success"] is False]

    assert len(successes) == 4, f"Oczekiwano 4 sukcesów, got {len(successes)}"
    assert len(failures) == 1, f"Oczekiwano 1 błędu, got {len(failures)}"

    # Uszkodzone zdjęcie ma error_msg
    corrupted_result = results["photo_corrupted.jpg"]
    assert corrupted_result["success"] is False
    assert corrupted_result["error_msg"] is not None

    # THEN: 4 eksporty na dysku
    fb_dir = export_dir / "fb"
    assert fb_dir.is_dir()
    fb_files = list(fb_dir.iterdir())
    assert len(fb_files) == 4

    # THEN: Logi zawierają sukcesy i błąd
    assert log_capture.count("[PROCESS] Zakończono:") == 4
    assert log_capture.has("[PROCESS] Błąd")


# ─────────────────────────────────────────────────────────────────────
# TEST-E2E-004
# ─────────────────────────────────────────────────────────────────────

def test_performance_100_images(tmp_path, log_capture, export_settings_fb):
    """TEST-E2E-004: 100 syntetycznych zdjęć 200x150 → wszystkie przetworzone."""
    # GIVEN: 100 małych zdjęć (szybkie przetwarzanie)
    source_dir = tmp_path / "source"
    export_dir = tmp_path / "export"
    session_dir = source_dir / "perf_session"
    session_dir.mkdir(parents=True)
    export_dir.mkdir()

    num_images = 100
    for i in range(num_images):
        img = Image.new("RGB", (200, 150), color=(i % 256, (i * 3) % 256, (i * 7) % 256))
        img.save(session_dir / f"photo_{i:03d}.jpg", "JPEG")

    logo = Image.new("RGBA", (40, 15), color=(255, 255, 255, 200))
    logo.save(session_dir / "logo.png", "PNG")

    # Użyj małego profilu eksportu dla szybkości
    small_export_settings = {
        "fb": {
            "size_type": "longer",
            "size": 100,  # bardzo małe eksporty dla szybkości w testach
            "format": "JPEG",
            "quality": 85,
            "logo": {
                "landscape": {"size": 20, "opacity": 60, "x_offset": 5, "y_offset": 5},
                "portrait": {"size": 26, "opacity": 60, "x_offset": 5, "y_offset": 5},
            },
        }
    }

    # WHEN: Przetwórz wszystkie 100 zdjęć sekwencyjnie
    start_time = time.perf_counter()
    success_count = 0
    error_count = 0

    for i in range(num_images):
        photo_name = f"photo_{i:03d}.jpg"
        r = process_photo_task(
            photo_path=str(session_dir / photo_name),
            folder_name="perf_session",
            photo_name=photo_name,
            created_date="2026:03:09 14:30:00",
            export_folder=str(export_dir),
            export_settings=small_export_settings,
            existing_exports={},
        )
        if r["success"]:
            success_count += 1
        else:
            error_count += 1

    elapsed = time.perf_counter() - start_time

    # THEN: Wszystkie przetworzone poprawnie
    assert success_count == num_images, f"Oczekiwano {num_images} sukcesów, got {success_count} (errors: {error_count})"
    assert error_count == 0

    # THEN: Czas < 60s (benchmark)
    assert elapsed < 60.0, f"Przetwarzanie trwało zbyt długo: {elapsed:.1f}s"

    # THEN: 100 plików w katalogu eksportu
    fb_dir = export_dir / "fb"
    assert fb_dir.is_dir()
    exported_files = list(fb_dir.iterdir())
    assert len(exported_files) == num_images

    # THEN: Logi zawierają 100 zakończonych eksportów, brak ERROR
    assert log_capture.count("[PROCESS] Zakończono:") == num_images
    error_logs = log_capture.at_level("ERROR")
    assert len(error_logs) == 0, f"Nieoczekiwane błędy: {error_logs}"
