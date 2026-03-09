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

    def test_create_project(self, temp_dir):
        """Testuje tworzenie nowego projektu."""
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

    def test_create_project_duplicate(self, temp_dir):
        """Testuje, czy utworzenie projektu o istniejącej nazwie rzuca FileExistsError."""
        name = "Duplicate Project"
        source = temp_dir / "src"
        export = temp_dir / "exp"
        
        # Pierwsze utworzenie
        ProjectManager.create_project(name, str(source), str(export), {"opt": "val"})
        
        # Próba utworzenia projektu o tej samej nazwie powinna rzucić wyjątek
        with pytest.raises(FileExistsError) as exc:
            ProjectManager.create_project(name, str(source), str(export), {"opt": "val"})
            
        assert f"Projekt o nazwie '{name}' już istnieje." in str(exc.value)

    def test_recent_projects_list(self, temp_dir):
        """Testuje dodawanie i pobieranie ostatnich projektów."""
        p1 = temp_dir / "projects" / "p1"
        p1.mkdir(parents=True)
        
        ProjectManager.add_recent_project(str(p1))
        recent = ProjectManager.get_recent_projects()
        
        assert len(recent) == 1
        assert recent[0] == str(p1)

    def test_prune_recent_projects(self, temp_dir):
        """Testuje usuwanie nieistniejących projektów z listy."""
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

    def test_get_project_details(self, temp_dir):
        """Testuje pobieranie metadanych projektu."""
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
