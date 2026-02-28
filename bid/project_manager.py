"""
bid/project_manager.py
Logika zarządzania projektami: wczytywanie, zapisywanie, lista ostatnich projektów.
"""
import json
import logging
import os
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("Yapa_CM")

class ProjectManager:
    projects_dir = Path(__file__).parent.parent / "projects"
    recent_projects_file = Path(__file__).parent.parent / "recent_projects.json"
    @classmethod
    def get_recent_projects(cls) -> list[str]:
        """Zwraca listę ścieżek do ostatnio otwartych projektów."""
        if not cls.recent_projects_file.exists():
            return []
        try:
            with open(cls.recent_projects_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return [str(p) for p in data if isinstance(p, str) and os.path.isdir(p)]
                return []
        except Exception as e:
            logger.error(f"Błąd odczytu ostatnich projektów: {e}")
            return []

    @classmethod
    def add_recent_project(cls, project_path: str):
        """Dodaje projekt do listy ostatnich."""
        recent = cls.get_recent_projects()
        project_path = os.path.abspath(project_path)
        
        if project_path in recent:
            recent.remove(project_path)
        recent.insert(0, project_path)
        
        # Limit to 10
        recent = list(recent[:10])
        
        try:
            with cls.recent_projects_file.open("w", encoding="utf-8") as f:
                json.dump(recent, f, indent=4)
            logger.debug(f"Zaktualizowano listę ostatnich projektów → {cls.recent_projects_file}")
        except Exception as e:
            logger.error(f"Błąd zapisu ostatnich projektów: {e}")

    @classmethod
    def create_project(cls, name: str, source_folder: str, export_folder: str, export_settings: dict) -> Path:
        """Tworzy nowy folder projektu i pliki konfiguracyjne."""
        p_dir = cls.projects_dir / name.replace(" ", "_")
        os.makedirs(p_dir, exist_ok=True)
        
        settings = {
            "source_folder": os.path.abspath(source_folder),
            "export_folder": os.path.abspath(export_folder)
        }
        
        settings_path = p_dir / "settings.json"
        with settings_path.open("w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
        logger.debug(f"Zapisano ustawienia projektu → {settings_path}")
            
        export_path = p_dir / "export_option.json"
        with export_path.open("w", encoding="utf-8") as f:
            json.dump(export_settings, f, indent=4)
        logger.debug(f"Zapisano opcje eksportu projektu → {export_path}")
            
        # source_dict.json will be created on first start
        
        cls.add_recent_project(str(p_dir))
        return p_dir

    @classmethod
    def get_last_project(cls) -> str | None:
        """Zwraca ścieżkę do ostatniego projektu."""
        recent = cls.get_recent_projects()
        return recent[0] if recent else None

    @staticmethod
    def get_project_details(project_path: str) -> dict:
        """Pobiera metadane projektu (data edycji, liczba zdjęć)."""
        path = Path(project_path)
        source_dict_path = path / "source_dict.json"
        
        details = {
            "path": project_path,
            "name": path.name.replace("_", " "),
            "last_modified": "Nieznana",
            "photo_count": 0
        }
        
        try:
            if source_dict_path.exists():
                mtime = source_dict_path.stat().st_mtime
                details["last_modified"] = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                
                with source_dict_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    count = 0
                    if isinstance(data, dict):
                        for folder in data:
                            if isinstance(data[folder], dict):
                                count += len(data[folder])
                    details["photo_count"] = count
            else:
                # Jeśli brak source_dict, sprawdź settings.json dla samej daty
                settings_path = path / "settings.json"
                if settings_path.exists():
                    mtime = settings_path.stat().st_mtime
                    details["last_modified"] = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        except Exception as e:
            logger.error(f"Error reading metadata for {project_path}: {e}")
            
        return details

    @classmethod
    def prune_recent_projects(cls) -> None:
        """Usuwa z listy projekty, które już nie istnieją na dysku."""
        recent = cls.get_recent_projects()
        # Use str(p) comparison but also check existence
        valid = [p for p in recent if Path(p).exists()]
        
        if len(valid) != len(recent):
            try:
                with cls.recent_projects_file.open("w", encoding="utf-8") as f:
                    json.dump(valid, f, indent=4)
                logger.debug(f"Przeczyszczono listę ostatnich projektów → {cls.recent_projects_file}")
            except Exception as e:
                logger.error(f"Error pruning recent projects: {e}")
