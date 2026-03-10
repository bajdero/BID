"""
tests/test_integrity.py
Faza 3B: Testy integracyjne — integralność systemu plików.

Weryfikuje pełne cykle create/update/check_integrity oraz trwałość danych.
"""
import os
import threading
from pathlib import Path

import pytest
from PIL import Image

from bid.source_manager import (
    SourceState,
    check_integrity,
    create_source_dict,
    load_source_dict,
    save_source_dict,
    update_source_dict,
)


# ─────────────────────────────────────────────────────────────────────
# TEST-INT-001
# ─────────────────────────────────────────────────────────────────────

def test_full_cycle_create_check_update(tmp_path, log_capture):
    """TEST-INT-001: create → dodaj pliki → update → check_integrity."""
    source_dir = tmp_path / "source"
    session_dir = source_dir / "session1"
    session_dir.mkdir(parents=True)

    # Krok 1: 3 zdjęcia + create_source_dict
    for i in range(3):
        img = Image.new("RGB", (100, 100), color=(i * 50, 50, 50))
        img.save(session_dir / f"photo_{i}.jpg", "JPEG")

    source_dict = create_source_dict(str(source_dir))

    assert "session1" in source_dict
    assert len(source_dict["session1"]) == 3
    for entry in source_dict["session1"].values():
        assert entry["state"] == SourceState.NEW

    # Krok 2: Dodaj 2 nowe zdjęcia do folderu
    for i in range(3, 5):
        img = Image.new("RGB", (100, 100), color=(i * 30, 80, 80))
        img.save(session_dir / f"photo_{i}.jpg", "JPEG")

    # Krok 3: update_source_dict
    source_dict, found_new = update_source_dict(source_dict, str(source_dir))

    assert found_new is True
    assert len(source_dict["session1"]) == 5

    # Krok 4: check_integrity (pliki NEW nie mają eksportów do weryfikacji)
    changes = check_integrity(source_dict, {}, str(tmp_path / "export"))
    assert changes == {}

    # Kolejność logów
    log_capture.assert_sequence("Tworzę source_dict", "Nowy plik:")


# ─────────────────────────────────────────────────────────────────────
# TEST-INT-002
# ─────────────────────────────────────────────────────────────────────

def test_delete_then_readd_photo(tmp_path, log_capture):
    """TEST-INT-002: Usuń plik → DELETED → przywróć → dict zachowany."""
    source_dir = tmp_path / "source"
    session_dir = source_dir / "session1"
    session_dir.mkdir(parents=True)

    # Stwórz i zeskanuj plik
    img = Image.new("RGB", (100, 100), color="blue")
    img.save(session_dir / "photo.jpg", "JPEG")

    source_dict = create_source_dict(str(source_dir))
    assert source_dict["session1"]["photo.jpg"]["state"] == SourceState.NEW

    # Symuluj stan OK (plik przetworzony)
    source_dict["session1"]["photo.jpg"]["state"] = SourceState.OK

    # Usuń plik z dysku
    os.remove(session_dir / "photo.jpg")

    # check_integrity → DELETED
    changes = check_integrity(source_dict, {}, str(tmp_path / "export"))

    assert source_dict["session1"]["photo.jpg"]["state"] == SourceState.DELETED
    assert "photo.jpg" in changes.get("session1", {})
    assert log_capture.has("usunięty", level="WARNING")

    # Przywróć plik
    img2 = Image.new("RGB", (100, 100), color="green")
    img2.save(session_dir / "photo.jpg", "JPEG")

    # update_source_dict — plik jest już w dict (jako DELETED), wpis pozostaje
    source_dict2, found_new = update_source_dict(source_dict, str(source_dir))

    # Dict musi być spójny i zawierać wpis photo.jpg
    assert "photo.jpg" in source_dict2["session1"]
    # Plik istnieje fizycznie na dysku
    assert (session_dir / "photo.jpg").exists()


# ─────────────────────────────────────────────────────────────────────
# TEST-INT-003
# ─────────────────────────────────────────────────────────────────────

def test_concurrent_dict_updates_thread_safe(tmp_path, log_capture):
    """TEST-INT-003: 10 wątków modyfikuje dict — brak wyjątków, spójność zachowana."""
    # Przygotuj dict z 100 wpisami
    source_dict = {
        "session1": {
            f"photo_{i:03d}.jpg": {
                "path": str(tmp_path / f"photo_{i:03d}.jpg"),
                "state": SourceState.NEW,
                "exported": {},
                "size": "1.0 MB",
                "created": "2026:03:09 12:00:00",
                "mtime": float(1000 + i),
                "exif": {},
            }
            for i in range(100)
        }
    }

    errors: list[str] = []

    def modify_entries(start: int, end: int) -> None:
        """Modyfikuje entries w zakresie [start, end)."""
        try:
            for i in range(start, end):
                key = f"photo_{i:03d}.jpg"
                if key in source_dict["session1"]:
                    source_dict["session1"][key]["state"] = SourceState.OK
                    source_dict["session1"][key]["exported"] = {"fb": f"/export/fb_{i}.jpg"}
        except Exception as exc:
            errors.append(str(exc))

    # 10 wątków, każdy obsługuje 10 wpisów
    threads = [
        threading.Thread(target=modify_entries, args=(t * 10, (t + 1) * 10))
        for t in range(10)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # Brak wyjątków
    assert errors == [], f"Błędy w wątkach: {errors}"
    # Wszystkie 100 wpisów obecne
    assert len(source_dict["session1"]) == 100
    # Wszystkie wpisy zmienione na OK
    for entry in source_dict["session1"].values():
        assert entry["state"] == SourceState.OK


# ─────────────────────────────────────────────────────────────────────
# TEST-INT-004
# ─────────────────────────────────────────────────────────────────────

def test_save_load_preserves_unicode(tmp_path, log_capture):
    """TEST-INT-004: Polskie znaki w nazwach zachowane po save → load."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    source_dict = {
        "Zdjęcia_ŻŹĆ": {
            "foto_ąę.jpg": {
                "path": str(tmp_path / "Zdjęcia_ŻŹĆ" / "foto_ąę.jpg"),
                "state": SourceState.NEW,
                "exported": {},
                "size": "1.5 MB",
                "created": "2026:01:15 10:00:00",
                "mtime": 1234567890.0,
                "exif": {"Make": "Aparat_ńó"},
            }
        }
    }

    save_source_dict(source_dict, project_dir)
    loaded = load_source_dict(project_dir)

    assert loaded is not None
    assert "Zdjęcia_ŻŹĆ" in loaded
    assert "foto_ąę.jpg" in loaded["Zdjęcia_ŻŹĆ"]
    entry = loaded["Zdjęcia_ŻŹĆ"]["foto_ąę.jpg"]
    assert entry["exif"]["Make"] == "Aparat_ńó"
    assert entry["state"] == SourceState.NEW

    log_capture.assert_sequence("Zapisano source_dict", "Wczytuję istniejący source_dict.json")
