import pytest
import os
import shutil
from pathlib import Path
from PIL import Image

@pytest.fixture
def temp_dir(tmp_path):
    """Zwraca tymczasowy katalog roboczy."""
    return tmp_path

@pytest.fixture
def sample_project(temp_dir):
    """Tworzy strukturę testowego projektu."""
    proj_path = temp_dir / "test_project"
    proj_path.mkdir()
    
    settings = {
        "source_folder": str(temp_dir / "source"),
        "export_folder": str(temp_dir / "export")
    }
    import json
    with (proj_path / "settings.json").open("w", encoding="utf-8") as f:
        json.dump(settings, f)
        
    (temp_dir / "source").mkdir()
    (temp_dir / "export").mkdir()
    
    return proj_path

@pytest.fixture
def sample_image(temp_dir):
    """Tworzy przykładowy obrazek JPEG."""
    img_path = temp_dir / "source" / "session1" / "test.jpg"
    img_path.parent.mkdir(parents=True, exist_ok=True)
    
    img = Image.new('RGB', (100, 100), color = 'red')
    img.save(img_path, "JPEG")
    
    return img_path
