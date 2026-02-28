import pytest
import json
import os
from pathlib import Path
from bid.source_manager import create_source_dict, update_source_dict, check_integrity, SourceState

def test_create_source_dict(temp_dir, sample_image):
    """Testuje skanowanie folderów i tworzenie słownika."""
    source_folder = temp_dir / "source"
    
    # create_source_dict pomija katalog główny, szuka podfolderów
    source_dict = create_source_dict(str(source_folder))
    
    assert "session1" in source_dict
    assert "test.jpg" in source_dict["session1"]
    item = source_dict["session1"]["test.jpg"]
    assert item["state"] == SourceState.NEW
    assert "created" in item

def test_update_source_dict(temp_dir, sample_image):
    """Testuje dodawanie nowych plików do istniejącego słownika."""
    source_folder = temp_dir / "source"
    source_dict = {"session1": {}}
    
    updated_dict, found_new = update_source_dict(source_dict, str(source_folder))
    
    assert found_new is True
    assert "test.jpg" in updated_dict["session1"]

def test_check_integrity_deleted(temp_dir, sample_image):
    """Testuje wykrywanie usuniętych plików."""
    source_folder = temp_dir / "source"
    source_dict = create_source_dict(str(source_folder))
    
    # Usuwamy plik
    os.remove(sample_image)
    
    changes = check_integrity(source_dict, {}, str(temp_dir / "export"))
    
    assert "session1" in changes
    assert changes["session1"]["test.jpg"] == SourceState.DELETED
    assert source_dict["session1"]["test.jpg"]["state"] == SourceState.DELETED

def test_check_integrity_modified(temp_dir, sample_image):
    """Testuje wykrywanie zmian w plikach (mtime)."""
    source_folder = temp_dir / "source"
    source_dict = create_source_dict(str(source_folder))
    
    # Zmieniamy mtime
    new_mtime = os.stat(sample_image).st_mtime + 100
    os.utime(sample_image, (new_mtime, new_mtime))
    
    changes = check_integrity(source_dict, {}, str(temp_dir / "export"))
    
    assert "session1" in changes
    assert changes["session1"]["test.jpg"] == SourceState.NEW
