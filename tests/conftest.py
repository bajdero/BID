import pytest
import json
import os
import shutil
from pathlib import Path
from PIL import Image
import logging

LOGGER_NAME = "BID"

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


# ─── NOWE FIXTURES (Faza 1) ───


class LogCaptureHelper:
    """Helper do weryfikacji logów w testach."""
    
    def __init__(self, caplog):
        self._caplog = caplog
    
    @property
    def records(self):
        return self._caplog.records
    
    @property
    def messages(self):
        return [r.message for r in self._caplog.records]
    
    def has(self, substring: str, level: str = None) -> bool:
        """Czy jest log zawierający substring (opcjonalnie na danym poziomie)."""
        for r in self._caplog.records:
            if substring in r.message:
                if level is None or r.levelname == level:
                    return True
        return False
    
    def count(self, substring: str) -> int:
        """Ile logów zawiera substring."""
        return sum(1 for r in self._caplog.records if substring in r.message)
    
    def at_level(self, level: str) -> list[str]:
        """Wszystkie wiadomości na danym poziomie."""
        return [r.message for r in self._caplog.records if r.levelname == level]
    
    def assert_sequence(self, *substrings: str):
        """Sprawdź czy logi zawierają podane substringi W KOLEJNOŚCI."""
        msgs = self.messages
        pos = 0
        for sub in substrings:
            found = False
            for i in range(pos, len(msgs)):
                if sub in msgs[i]:
                    pos = i + 1
                    found = True
                    break
            assert found, f"Brak '{sub}' w logach po pozycji {pos}. Logi: {msgs}"


@pytest.fixture
def log_capture(caplog):
    """Przechwytuje logi Yapa_CM na poziomie DEBUG.
    
    Użycie w teście:
        def test_x(log_capture):
            do_something()
            assert log_capture.has("Skanowanie", level="INFO")
    """
    with caplog.at_level(logging.DEBUG, logger=LOGGER_NAME):
        yield LogCaptureHelper(caplog)


@pytest.fixture
def export_settings_fb():
    """Pojedynczy profil eksportu 'fb' do testów."""
    return {
        "fb": {
            "size_type": "longer",
            "size": 1200,
            "format": "JPEG",
            "quality": 85,
            "logo": {
                "landscape": {"size": 240, "opacity": 60, "x_offset": 10, "y_offset": 10},
                "portrait": {"size": 312, "opacity": 60, "x_offset": 10, "y_offset": 10}
            }
        }
    }


@pytest.fixture
def export_settings_multi():
    """Wieloprofilowy export settings (fb + insta)."""
    return {
        "fb": {
            "size_type": "longer",
            "size": 1200,
            "format": "JPEG",
            "quality": 85,
            "logo": {
                "landscape": {"size": 240, "opacity": 60, "x_offset": 10, "y_offset": 10},
                "portrait": {"size": 312, "opacity": 60, "x_offset": 10, "y_offset": 10}
            }
        },
        "insta": {
            "size_type": "width",
            "size": 1080,
            "format": "PNG",
            "quality": 9,
            "logo": {
                "landscape": {"size": 228, "opacity": 60, "x_offset": 10, "y_offset": 10},
                "portrait": {"size": 296, "opacity": 60, "x_offset": 10, "y_offset": 10}
            }
        }
    }


@pytest.fixture
def sample_image_with_exif(tmp_path):
    """Tworzy JPEG z podstawowymi tagami EXIF."""
    from PIL.ExifTags import IFD
    img = Image.new("RGB", (2000, 1500), color="blue")
    exif = img.getexif()
    exif[0x010F] = "TestCamera"          # Make
    exif[0x0110] = "TestModel"           # Model
    exif[0x0132] = "2026:03:09 14:30:00" # DateTime
    ifd = exif.get_ifd(IFD.Exif)
    ifd[0x9003] = "2026:03:09 14:30:00"  # DateTimeOriginal
    ifd[0x9004] = "2026:03:09 14:30:00"  # DateTimeDigitized
    
    session_dir = tmp_path / "source" / "session1"
    session_dir.mkdir(parents=True)
    img_path = session_dir / "test_exif.jpg"
    img.save(img_path, "JPEG", exif=exif.tobytes())
    return img_path


@pytest.fixture
def sample_logo(tmp_path):
    """Tworzy logo.png w folderze źródłowym."""
    logo = Image.new("RGBA", (600, 200), color=(255, 255, 255, 128))
    # Dodaj jakiś wzór
    for x in range(100, 500):
        for y in range(50, 150):
            logo.putpixel((x, y), (0, 0, 0, 200))
    session_dir = tmp_path / "source" / "session1"
    session_dir.mkdir(parents=True, exist_ok=True)
    logo_path = session_dir / "logo.png"
    logo.save(logo_path, "PNG")
    return logo_path


@pytest.fixture
def full_test_project(tmp_path, export_settings_fb):
    """Kompletny projekt testowy z ustawieniami, zdjęciami i logo."""
    project_dir = tmp_path / "projects" / "TestProject"
    source_dir = tmp_path / "source"
    export_dir = tmp_path / "export"
    
    for d in [project_dir, source_dir, export_dir]:
        d.mkdir(parents=True)
    
    # Settings
    settings = {"source_folder": str(source_dir), "export_folder": str(export_dir)}
    (project_dir / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
    (project_dir / "export_option.json").write_text(
        json.dumps(export_settings_fb), encoding="utf-8"
    )
    
    # Zdjęcia testowe
    session_dir = source_dir / "session1"
    session_dir.mkdir()
    
    for i in range(3):
        img = Image.new("RGB", (2000, 1500), color=(100 + i * 50, 50, 50))
        exif = img.getexif()
        exif[0x0132] = f"2026:03:09 14:{30+i}:00"
        img.save(session_dir / f"photo_{i}.jpg", "JPEG", exif=exif.tobytes())
    
    # Logo
    logo = Image.new("RGBA", (600, 200), color=(255, 255, 255, 128))
    logo.save(session_dir / "logo.png", "PNG")
    
    return {
        "project_dir": project_dir,
        "source_dir": source_dir,
        "export_dir": export_dir,
        "session_dir": session_dir,
        "settings": settings,
        "export_settings": export_settings_fb,
    }


# ---------------------------------------------------------------------------
# Fixtures for FastAPI API tests (P1-02)
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_api_project(tmp_path):
    """
    Create a minimal on-disk project directory for API integration tests.

    Structure:
        <tmp>/projects/api_test/
            settings.json       ← source/export folder paths
            export_option.json  ← single 'web' profile (no logo required)
    """
    import json as _json

    projects_root = tmp_path / "projects"
    source_dir = tmp_path / "api_source"
    export_dir = tmp_path / "api_export"

    for d in (projects_root, source_dir, export_dir):
        d.mkdir(parents=True, exist_ok=True)

    proj = projects_root / "api_test"
    proj.mkdir()

    settings_data = {
        "source_folder": str(source_dir),
        "export_folder": str(export_dir),
    }
    (proj / "settings.json").write_text(_json.dumps(settings_data), encoding="utf-8")

    export_opts = {
        "web": {
            "size_type": "longer",
            "size": 800,
            "format": "JPEG",
            "quality": 80,
            "logo": {
                "landscape": {"size": 200, "opacity": 60, "x_offset": 10, "y_offset": 10},
                "portrait": {"size": 260, "opacity": 60, "x_offset": 10, "y_offset": 10},
            },
            "logo_required": False,
        }
    }
    (proj / "export_option.json").write_text(_json.dumps(export_opts), encoding="utf-8")

    return proj


@pytest.fixture()
def api_source_photo(sample_api_project):
    """
    Create a minimal JPEG in the project's source folder and return (folder, filename).
    """
    import json as _json

    settings_data = _json.loads((sample_api_project / "settings.json").read_text())
    source_folder = Path(settings_data["source_folder"])
    session_dir = source_folder / "Session1"
    session_dir.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", (400, 300), color="green")
    img_path = session_dir / "sample.jpg"
    img.save(img_path, "JPEG")

    return "Session1", "sample.jpg"


@pytest.fixture()
def api_test_app(tmp_path, sample_api_project):
    """
    Build a FastAPI test application instance wired to:
      - An in-memory SQLite database (isolated per test).
      - The sample_api_project directory via PROJECTS_DIR override.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from src.api.config import settings as app_settings
    from src.api.deps import get_db, get_processing_service, get_project_path
    from src.api.main import create_app
    from src.api.models.database import Base
    from src.api.services.processing import ProcessingService

    import src.api.models.database as _db_mod

    # ── In-memory DB ──────────────────────────────────────────────────────────
    # StaticPool ensures all connections share one in-memory SQLite database,
    # so tables created by init_db() are visible to request-handler sessions.
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(test_engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # Patch module-level engine/SessionLocal so lifespan's init_db() uses the
    # in-memory DB instead of the real file path.
    _orig_engine = _db_mod.engine
    _orig_session = _db_mod.SessionLocal
    _db_mod.engine = test_engine
    _db_mod.SessionLocal = TestSessionLocal

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # ── Processing service (real, but process_photo_task is mocked in tests) ─
    test_svc = ProcessingService(max_workers=1)

    def override_get_processing_service():
        return test_svc

    # ── Project path resolver pointing at tmp projects root ──────────────────
    import re as _re
    _SAFE_RE = _re.compile(r"^[a-zA-Z0-9_\-.]+$")

    def override_get_project_path(project_id: str):
        from fastapi import HTTPException
        if not _SAFE_RE.match(project_id):
            raise HTTPException(status_code=400, detail="Invalid project id")
        p = sample_api_project.parent / project_id
        if not p.exists():
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
        return p

    # ── Build app wired to the test in-memory database ────────────────────────
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_processing_service] = override_get_processing_service
    app.dependency_overrides[get_project_path] = override_get_project_path

    yield app

    test_svc.shutdown()
    Base.metadata.drop_all(test_engine)
    test_engine.dispose()
    # Restore original module-level DB objects
    _db_mod.engine = _orig_engine
    _db_mod.SessionLocal = _orig_session
