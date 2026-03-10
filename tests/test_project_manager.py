import pytest
import os
import json
from pathlib import Path
from bid.project_manager import ProjectManager

class TestProjectManager:
    @pytest.fixture(autouse=True)
    def setup_paths(self, temp_dir):
        """Mockuje ścieżki ProjectManager przed każdym testem."""
        self.old_proj_dir = ProjectManager.projects_dir
        self.old_recent_file = ProjectManager.recent_projects_file
        
        ProjectManager.projects_dir = temp_dir / "projects"
        ProjectManager.projects_dir.mkdir(exist_ok=True)
        ProjectManager.recent_projects_file = temp_dir / "recent_projects.json"
        
        yield
        
        ProjectManager.projects_dir = self.old_proj_dir
        ProjectManager.recent_projects_file = self.old_recent_file

    def test_create_project(self, temp_dir, log_capture):
        """TEST-PM-001: Testuje tworzenie nowego projektu."""
        name = "Test Project"
        source = temp_dir / "src"
        export = temp_dir / "exp"
        source.mkdir()
        export.mkdir()
        
        p_path = ProjectManager.create_project(name, str(source), str(export), {"opt": "val"})
        
        assert p_path.exists()
        assert (p_path / "settings.json").exists()
        assert (p_path / "export_option.json").exists()
        
        with (p_path / "settings.json").open("r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["source_folder"] == str(source)
            assert data["export_folder"] == str(export)
        
        assert log_capture.has("Tworzę projekt", level="INFO")
        assert log_capture.has("Zapisano ustawienia projektu", level="DEBUG")

    def test_create_project_duplicate(self, temp_dir, log_capture):
        """TEST-PM-002: tworzenie projektu o istniejącej nazwie rzuca FileExistsError."""
        name = "Duplicate Project"
        source = temp_dir / "src"
        export = temp_dir / "exp"
        
        # Pierwsze utworzenie
        ProjectManager.create_project(name, str(source), str(export), {"opt": "val"})
        
        # Próba utworzenia projektu o tej samej nazwie powinna rzucić wyjątek
        with pytest.raises(FileExistsError) as exc:
            ProjectManager.create_project(name, str(source), str(export), {"opt": "val"})
            
        assert f"Projekt o nazwie '{name}' już istnieje." in str(exc.value)

    def test_recent_projects_list(self, temp_dir, log_capture):
        """TEST-PM-003: Testuje dodawanie i pobieranie ostatnich projektów."""
        p1 = temp_dir / "projects" / "p1"
        p1.mkdir(parents=True)
        
        ProjectManager.add_recent_project(str(p1))
        recent = ProjectManager.get_recent_projects()
        
        assert len(recent) == 1
        assert recent[0] == str(p1)
        assert log_capture.has("Zaktualizowano listę ostatnich projektów", level="DEBUG")

    def test_prune_recent_projects(self, temp_dir, log_capture):
        """TEST-PM-004: Testuje usuwanie nieistniejących projektów z listy."""
        p1 = temp_dir / "projects" / "p1"
        p1.mkdir(parents=True)
        p2 = temp_dir / "projects" / "p2"
        # p2 nie istnieje fizycznie
        
        # Ręcznie wpisujemy p2 do pliku, bo add_recent_project używa os.path.isdir
        with ProjectManager.recent_projects_file.open("w", encoding="utf-8") as f:
            json.dump([str(p1), str(p2)], f)
            
        ProjectManager.prune_recent_projects()
        recent = ProjectManager.get_recent_projects()
        
        assert str(p1) in recent
        assert str(p2) not in recent
        assert len(recent) == 1

    def test_get_project_details(self, temp_dir, log_capture):
        """TEST-PM-005: Testuje pobieranie metadanych projektu."""
        p1 = temp_dir / "projects" / "p1"
        p1.mkdir(parents=True)
        
        # Tworzymy fake source_dict.json
        source_dict = {
            "folder1": {
                "file1.jpg": {"state": "ok"},
                "file2.jpg": {"state": "ok"}
            }
        }
        with (p1 / "source_dict.json").open("w", encoding="utf-8") as f:
            json.dump(source_dict, f)
            
        details = ProjectManager.get_project_details(str(p1))
        
        assert details["name"] == "p1"
        assert details["photo_count"] == 2
        assert details["last_modified"] != "Nieznana"

    # ─────────────────────────────────────────────────────────────────────
    # NOWE TESTY — TEST-PM-006 do TEST-PM-008
    # ─────────────────────────────────────────────────────────────────────

    def test_get_project_details_with_source_dict(self, temp_dir, log_capture):
        """TEST-PM-005: get_project_details z source_dict.json."""
        p1 = temp_dir / "projects" / "p1"
        p1.mkdir(parents=True)
        
        # Tworzenie source_dict z 5 zdjęciami
        source_dict = {
            "session1": {
                f"photo_{i}.jpg": {"state": "ok"} for i in range(5)
            }
        }
        with (p1 / "source_dict.json").open("w", encoding="utf-8") as f:
            json.dump(source_dict, f)
            
        details = ProjectManager.get_project_details(str(p1))
        
        assert details["photo_count"] == 5
        assert details["last_modified"] != "Nieznana"

    def test_get_project_details_no_source_dict(self, temp_dir, log_capture):
        """TEST-PM-006: get_project_details bez source_dict.json."""
        p1 = temp_dir / "projects" / "p1"
        p1.mkdir(parents=True)
        
        # Brak source_dict.json
        details = ProjectManager.get_project_details(str(p1))
        
        assert details["photo_count"] == 0
        assert details["name"] == "p1"

    def test_recent_projects_max_10(self, temp_dir, log_capture):
        """TEST-PM-007: Limit ostatnich projektów do 10."""
        # Tworzenie 15 projektów
        for i in range(15):
            p = temp_dir / "projects" / f"p{i}"
            p.mkdir(parents=True)
            ProjectManager.add_recent_project(str(p))
        
        recent = ProjectManager.get_recent_projects()
        
        assert len(recent) <= 10
        # Najnowszy powinien być na pozycji [0]
        latest = Path(recent[0]).name
        assert latest == "p14"

    def test_create_project_spaces_in_name(self, temp_dir, log_capture):
        """TEST-PM-008: Tworzenie projektu ze spacjami w nazwie."""
        name = "Projekt Z Odstępami"
        source = temp_dir / "src"
        export = temp_dir / "exp"
        source.mkdir()
        export.mkdir()
        
        p_path = ProjectManager.create_project(name, str(source), str(export), {"opt": "val"})
        
        # Folder powinien mieć podkreślniki zamiast spacji
        assert "Projekt_Z_Odstępami" in str(p_path)
        assert (p_path / "settings.json").exists()
        assert (p_path / "export_option.json").exists()

    def test_get_last_project(self, temp_dir, log_capture):
        """Pobieranie ostatniego projektu."""
        p1 = temp_dir / "projects" / "p1"
        p1.mkdir(parents=True)
        
        ProjectManager.add_recent_project(str(p1))
        
        last = ProjectManager.get_last_project()
        assert last == str(p1)

    def test_get_recent_projects_empty(self, temp_dir, log_capture):
        """Pobieranie ostatnich projektów z pustą listą."""
        recent = ProjectManager.get_recent_projects()
        
        assert isinstance(recent, list)
        assert len(recent) == 0

    def test_add_recent_project_duplicate_moves_to_front(self, temp_dir, log_capture):
        """Dodanie projektu który już istnieje przesuwa go na początek."""
        p1 = temp_dir / "projects" / "p1"
        p2 = temp_dir / "projects" / "p2"
        p1.mkdir(parents=True)
        p2.mkdir(parents=True)
        
        ProjectManager.add_recent_project(str(p1))
        ProjectManager.add_recent_project(str(p2))
        
        # p1 był pierwszy, teraz p2 powinien być pierwszy
        recent = ProjectManager.get_recent_projects()
        assert recent[0] == str(p2)
        assert recent[1] == str(p1)
        
        # Dodajemy p1 ponownie
        ProjectManager.add_recent_project(str(p1))
        recent = ProjectManager.get_recent_projects()
        
        # p1 powinien być znowu na początku
        assert recent[0] == str(p1)
        assert recent[1] == str(p2)

    def test_get_project_details_empty_source_dict(self, temp_dir, log_capture):
        """get_project_details z pustym source_dict.json."""
        p1 = temp_dir / "projects" / "p1"
        p1.mkdir(parents=True)
        
        # Pusty source_dict
        with (p1 / "source_dict.json").open("w", encoding="utf-8") as f:
            json.dump({}, f)
            
        details = ProjectManager.get_project_details(str(p1))
        
        assert details["photo_count"] == 0
