"""
bid/config.py
Ładowanie i walidacja konfiguracji (settings.json, export_option.json).
Ścieżki resolwowane względem katalogu projektu (nie cwd),
dzięki czemu działa zarówno na Windows jak i na Linuxie.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger("Yapa_CM")

# Katalog projektu = katalog nadrzędny względem tego pliku (bid/)
PROJECT_DIR: Path = Path(__file__).parent.parent


def _load_json(path: Path, label: str) -> dict:
    """Otwiera i parsuje plik JSON.

    Args:
        path:  Ścieżka do pliku JSON.
        label: Opis pliku (do logowania błędów).

    Returns:
        Sparsowany słownik.

    Raises:
        SystemExit: jeśli plik nie istnieje lub zawiera błędny JSON.
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        logger.debug(f"Loaded config: {path}")
        return data
    except FileNotFoundError:
        logger.critical(f"Config file not found: {path} ({label})")
        raise SystemExit(1)
    except json.JSONDecodeError as exc:
        logger.critical(f"Invalid JSON in {path} ({label}): {exc}")
        raise SystemExit(1)


def load_settings(path: Path | None = None) -> dict:
    """Wczytuje settings.json.

    Args:
        path: Opcjonalna niestandardowa ścieżka. Domyślnie PROJECT_DIR/settings.json.

    Returns:
        Słownik z ustawieniami.
    """
    if path is None:
        path = PROJECT_DIR / "settings.json"
    return _load_json(path, "settings")


def load_export_options(path: Path | None = None) -> dict:
    """Wczytuje export_option.json.

    Args:
        path: Opcjonalna niestandardowa ścieżka. Domyślnie PROJECT_DIR/export_option.json.

    Returns:
        Słownik z opcjami eksportu.
    """
    if path is None:
        path = PROJECT_DIR / "export_option.json"
    return _load_json(path, "export_options")
