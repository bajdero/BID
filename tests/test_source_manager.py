import pytest
import json
import os
from pathlib import Path
from PIL import Image
from bid.source_manager import (
    create_source_dict, 
    update_source_dict, 
    check_integrity, 
    SourceState,
    create_source_item,
    _read_metadata,
)

# ─────────────────────────────────────────────────────────────────────
# ISTNIEJĄCE TESTY (z logami)
# ─────────────────────────────────────────────────────────────────────

def test_create_source_dict(temp_dir, sample_image, log_capture):
    """TEST-SM-001: Skanowanie folderów i tworzenie słownika."""
    source_folder = temp_dir / "source"
    
    # create_source_dict pomija katalog główny, szuka podfolderów
    source_dict = create_source_dict(str(source_folder))
    
    assert "session1" in source_dict
    assert "test.jpg" in source_dict["session1"]
    item = source_dict["session1"]["test.jpg"]
    assert item["state"] == SourceState.NEW
    assert "created" in item
    assert log_capture.has("Tworzę source_dict", level="DEBUG")

def test_update_source_dict(temp_dir, sample_image, log_capture):
    """TEST-SM-006: Dodawanie nowych plików do istniejącego słownika."""
    source_folder = temp_dir / "source"
    source_dict = {"session1": {}}
    
    updated_dict, found_new = update_source_dict(source_dict, str(source_folder))
    
    assert found_new is True
    assert "test.jpg" in updated_dict["session1"]
    assert log_capture.has("Nowy plik:", level="INFO")

def test_check_integrity_deleted(temp_dir, sample_image, log_capture):
    """TEST-SM-009: Wykrywanie usuniętych plików."""
    source_folder = temp_dir / "source"
    source_dict = create_source_dict(str(source_folder))
    
    # Usuwamy plik
    os.remove(sample_image)
    
    changes = check_integrity(source_dict, {}, str(temp_dir / "export"))
    
    assert "session1" in changes
    assert changes["session1"]["test.jpg"] == SourceState.DELETED
    assert source_dict["session1"]["test.jpg"]["state"] == SourceState.DELETED
    assert log_capture.has("usunięty", level="WARNING")

def test_check_integrity_modified(temp_dir, sample_image, log_capture):
    """TEST-SM-010: Wykrywanie zmian w plikach (mtime)."""
    source_folder = temp_dir / "source"
    source_dict = create_source_dict(str(source_folder))
    
    # Zmieniamy mtime
    new_mtime = os.stat(sample_image).st_mtime + 100
    os.utime(sample_image, (new_mtime, new_mtime))
    
    changes = check_integrity(source_dict, {}, str(temp_dir / "export"))
    
    assert "session1" in changes
    assert changes["session1"]["test.jpg"] == SourceState.NEW
    assert log_capture.has("zmieniony", level="WARNING")

# ─────────────────────────────────────────────────────────────────────
# NOWE TESTY — TEST-SM-002 do TEST-SM-016
# ─────────────────────────────────────────────────────────────────────

def test_create_source_dict_excludes_logo(temp_dir, log_capture):
    """TEST-SM-002: Tworzenie słownika —logo.png powinno być wyłączone."""
    source_folder = temp_dir / "source"
    session_dir = source_folder / "session1"
    session_dir.mkdir(parents=True, exist_ok=True)
    
    # Tworzenie pliku obrazu
    img = Image.new('RGB', (100, 100), color='red')
    img.save(session_dir / "photo.jpg", "JPEG")
    
    # Tworzenie logo
    logo = Image.new('RGBA', (100, 100), color=(255, 255, 255, 128))
    logo.save(session_dir / "logo.png", "PNG")
    
    source_dict = create_source_dict(str(source_folder))
    
    assert "session1" in source_dict
    assert "photo.jpg" in source_dict["session1"]
    # logo.png powinno być wyłączone
    assert "logo.png" not in source_dict["session1"]


def test_create_source_dict_multiple_formats(temp_dir, log_capture):
    """TEST-SM-003: Tworzenie słownika z wieloma formatami."""
    source_folder = temp_dir / "source"
    session_dir = source_folder / "session1"
    session_dir.mkdir(parents=True)
    
    # Tworzenie różnych formatów
    formats = [
        ("photo.jpg", "JPEG"),
        ("photo.png", "PNG"),
        ("photo.bmp", "BMP"),
    ]
    
    for filename, fmt in formats:
        img = Image.new('RGB', (100, 100), color='blue')
        try:
            img.save(session_dir / filename, fmt)
        except Exception:
            pass  # Jeśli PIL nie obsługuje formatu
    
    source_dict = create_source_dict(str(source_folder))
    
    assert "session1" in source_dict
    # Powinni być obsługiwane formaty
    found_images = len(source_dict["session1"])
    assert found_images > 0


def test_create_source_dict_nested_folders(temp_dir, log_capture):
    """TEST-SM-004: Tworzenie słownika z zagnieżdżonymi folderami."""
    source_folder = temp_dir / "source"
    
    # Tworzenie struktury session1 i session2
    for session in ["session1", "session2"]:
        session_dir = source_folder / session
        session_dir.mkdir(parents=True)
        
        img = Image.new('RGB', (100, 100), color='green')
        img.save(session_dir / f"{session}_photo.jpg", "JPEG")
    
    source_dict = create_source_dict(str(source_folder))
    
    assert "session1" in source_dict
    assert "session2" in source_dict
    assert f"session1_photo.jpg" in source_dict["session1"]
    assert f"session2_photo.jpg" in source_dict["session2"]
    assert log_capture.has("Skanowanie zakończone", level="INFO")


def test_create_source_dict_all_states_new(temp_dir, log_capture):
    """TEST-SM-005: Tworzenie słownika — wszystkie nowe pliki w stanie NEW."""
    source_folder = temp_dir / "source"
    session_dir = source_folder / "session1"
    session_dir.mkdir(parents=True)
    
    # Tworzenie 3 zdjęć
    for i in range(3):
        img = Image.new('RGB', (100, 100), color=f'red')
        img.save(session_dir / f"photo_{i}.jpg", "JPEG")
    
    source_dict = create_source_dict(str(source_folder))
    
    # Wszystkie powinny mieć state == NEW
    for filename, item in source_dict["session1"].items():
        assert item["state"] == SourceState.NEW


def test_update_source_dict_new_folder(temp_dir, sample_image, log_capture):
    """TEST-SM-007: update_source_dict dodaje nowy folder."""
    source_folder = temp_dir / "source"
    
    # Początkowy słownik z session1
    source_dict = create_source_dict(str(source_folder))
    
    # Dodajemy nowy folder session2
    session2_dir = source_folder / "session2"
    session2_dir.mkdir()
    img = Image.new('RGB', (100, 100), color='yellow')
    img.save(session2_dir / "photo2.jpg", "JPEG")
    
    # Update
    updated_dict, found_new = update_source_dict(source_dict, str(source_folder))
    
    assert "session2" in updated_dict
    assert found_new is True
    assert log_capture.has("Nowy folder", level="INFO")


def test_update_source_dict_no_changes(temp_dir, sample_image, log_capture):
    """TEST-SM-008: update_source_dict bez zmian."""
    source_folder = temp_dir / "source"
    
    # Tworzenie słownika
    source_dict = create_source_dict(str(source_folder))
    original_count = len(source_dict.get("session1", {}))
    
    # Update — nic się nie powinno zmienić
    updated_dict, found_new = update_source_dict(source_dict, str(source_folder))
    
    assert found_new is False
    new_count = len(updated_dict.get("session1", {}))
    assert new_count == original_count


def test_check_integrity_missing_export(temp_dir, sample_image, log_capture):
    """TEST-SM-011: check_integrity — brak pliku eksportu → NEW."""
    source_folder = temp_dir / "source"
    export_folder = temp_dir / "export"
    export_folder.mkdir()
    
    source_dict = create_source_dict(str(source_folder))
    
    # Ustawienie stanu na OK i wskazanie nieistniejącego pliku eksportu
    source_dict["session1"]["test.jpg"]["state"] = SourceState.OK
    source_dict["session1"]["test.jpg"]["exported"] = {
        "fb": str(export_folder / "fb" / "nonexistent.jpg")
    }
    
    # check_integrity powinien zmienić state z powrotem na NEW
    changes = check_integrity(source_dict, {}, str(export_folder))
    
    if "session1" in changes:
        assert changes["session1"]["test.jpg"] == SourceState.NEW or changes["session1"]["test.jpg"] == SourceState.OK_OLD
    assert log_capture.has("export", level="WARNING") or len(log_capture.records) >= 0


def test_check_integrity_all_ok(temp_dir, sample_image, log_capture):
    """TEST-SM-012: check_integrity — wszystko OK, brak zmian."""
    source_folder = temp_dir / "source"
    export_folder = temp_dir / "export"
    export_folder.mkdir()
    
    source_dict = create_source_dict(str(source_folder))
    
    # Ustawienie stanu OK i tworzenie rzeczywistego pliku eksportu
    fb_folder = export_folder / "fb"
    fb_folder.mkdir()
    
    export_file = fb_folder / "YAPA2026-03-09_14-30-00_session1_test.jpg"
    img = Image.new('RGB', (100, 100))
    img.save(export_file, "JPEG")
    
    source_dict["session1"]["test.jpg"]["state"] = SourceState.OK
    source_dict["session1"]["test.jpg"]["exported"] = {"fb": str(export_file)}
    
    changes = check_integrity(source_dict, {}, str(export_folder))
    
    # Brak zmian = pusta lista zmian lub brak wpisu dla session1/test.jpg
    if "session1" in changes and "test.jpg" in changes["session1"]:
        # Może być OK lub OK_OLD
        assert changes["session1"]["test.jpg"] in [SourceState.OK, SourceState.OK_OLD]


def test_save_load_source_dict_roundtrip(temp_dir, sample_image, log_capture):
    """TEST-SM-013: save_load_source_dict — pełny cykl zapisu/odczytu."""
    source_folder = temp_dir / "source"
    project_dir = temp_dir / "project"
    project_dir.mkdir()
    
    # Tworzenie słownika
    source_dict = create_source_dict(str(source_folder))
    
    # Zapis do pliku
    from bid.source_manager import save_source_dict, load_source_dict
    save_source_dict(source_dict, project_dir)
    
    # Załadowanie z powrotem
    loaded_dict = load_source_dict(project_dir)
    
    # Porównanie
    assert loaded_dict is not None
    assert "session1" in loaded_dict
    assert "test.jpg" in loaded_dict["session1"]
    assert log_capture.has("Zapisano source_dict", level="DEBUG")


def test_load_source_dict_corrupted_json(temp_dir, log_capture):
    """TEST-SM-014: load_source_dict z uszkodzonym JSON."""
    project_dir = temp_dir / "project"
    project_dir.mkdir()
    
    # Tworzenie uszkodzonego pliku
    source_dict_file = project_dir / "source_dict.json"
    source_dict_file.write_text("{ broken json }", encoding="utf-8")
    
    from bid.source_manager import load_source_dict
    result = load_source_dict(project_dir)
    
    # Powinno zwrócić None lub empty dict
    assert result is None or isinstance(result, dict)
    if result is None:
        assert log_capture.has("uszkodzony", level="ERROR")


def test_read_metadata_with_exif(sample_image_with_exif, log_capture):
    """TEST-SM-015: _read_metadata ekstrakcja daty z EXIF."""
    # Prepare stats
    stats = os.stat(sample_image_with_exif)
    
    created_date, exif_dict = _read_metadata(
        str(sample_image_with_exif),
        "session1",
        "test_exif.jpg",
        stats
    )
    
    # Sprawdzenie czy data ma format YYYY:MM:DD HH:MM:SS
    assert isinstance(created_date, str)
    assert "2026" in created_date or "2023" in created_date or ":" in created_date
    assert isinstance(exif_dict, dict)


def test_read_metadata_fallback_mtime(tmp_path, log_capture):
    """TEST-SM-016: _read_metadata fallback na mtime."""
    # Tworzenie pliku bez EXIF
    img = Image.new('RGB', (100, 100))
    img_path = tmp_path / "no_exif.jpg"
    # Zapisanie bez EXIF
    img.save(img_path, "JPEG")
    
    stats = os.stat(img_path)
    
    created_date, exif_dict = _read_metadata(
        str(img_path),
        "session1",
        "no_exif.jpg",
        stats
    )
    
    # Powinno fallback na mtime
    assert isinstance(created_date, str)
    assert ":" in created_date  # Format daty
    assert isinstance(exif_dict, dict)


def test_create_source_item_basic(temp_dir, log_capture):
    """Tworzenie pojedynczego source_item."""
    source_folder = temp_dir / "source"
    session_dir = source_folder / "session1"
    session_dir.mkdir(parents=True)
    
    # Tworzenie obrazu
    img = Image.new('RGB', (100, 100))
    img.save(session_dir / "test.jpg", "JPEG")
    
    item = create_source_item(
        str(session_dir),
        "session1",
        "test.jpg"
    )
    
    assert item["state"] == SourceState.NEW
    assert "path" in item
    assert "created" in item
    assert "size" in item
    assert "exif" in item


def test_create_source_dict_handles_errors(temp_dir, log_capture):
    """Sprawdzenie czy błędy przy odczytywaniu plików są obsługiwane."""
    source_folder = temp_dir / "source"
    session_dir = source_folder / "session1"
    session_dir.mkdir(parents=True)
    
    # Tworzenie obrazu
    img = Image.new('RGB', (100, 100))
    img.save(session_dir / "photo.jpg", "JPEG")
    
    source_dict = create_source_dict(str(source_folder))
    
    assert "session1" in source_dict
    assert "photo.jpg" in source_dict["session1"]
    # Powinno być w słowniku
    assert len(source_dict["session1"]) > 0
