"""bid/validators.py — Walidacja danych wejściowych."""
from __future__ import annotations
import os
from typing import Any

VALID_SIZE_TYPES = ("longer", "width", "height", "shorter")
VALID_FORMATS = ("JPEG", "PNG")
VALID_PLACEMENTS = ("top-left", "top-right", "bottom-left", "bottom-right")

def validate_export_profile(name: str, profile: dict) -> list[str]:
    """Sprawdza kompletność i poprawność profilu eksportu.
    
    Returns:
        Lista błędów (pusta = profil poprawny).
    """
    errors = []
    required = ["size_type", "size", "format", "quality", "logo"]
    for key in required:
        if key not in profile:
            errors.append(f"Profil '{name}': brak klucza '{key}'")
    
    if "size_type" in profile and profile["size_type"] not in VALID_SIZE_TYPES:
        errors.append(f"Profil '{name}': nieprawidłowy size_type '{profile['size_type']}'")
    
    if "format" in profile and profile["format"] not in VALID_FORMATS:
        errors.append(f"Profil '{name}': nieprawidłowy format '{profile['format']}'")
    
    if "ratio" in profile:
        ratio = profile["ratio"]
        if not isinstance(ratio, list) or not all(isinstance(r, (int, float)) for r in ratio):
            errors.append(f"Profil '{name}': ratio musi być listą liczb (np. [0.8, 1.25])")
    
    if "logo_required" in profile and not isinstance(profile["logo_required"], bool):
        errors.append(f"Profil '{name}': logo_required musi być wartością logiczną (true/false)")
    
    if "logo" in profile and isinstance(profile["logo"], dict):
        for orientation in ("landscape", "portrait"):
            if orientation in profile["logo"]:
                logo_cfg = profile["logo"][orientation]
                if "placement" in logo_cfg and logo_cfg["placement"] not in VALID_PLACEMENTS:
                    errors.append(
                        f"Profil '{name}': nieprawidłowe logo.{orientation}.placement "
                        f"'{logo_cfg['placement']}'"
                    )
    
    return errors


def validate_path_exists(path: str, label: str) -> str | None:
    """Sprawdza czy ścieżka istnieje. Zwraca komunikat błędu lub None."""
    if not os.path.exists(path):
        return f"{label}: ścieżka nie istnieje: {path}"
    return None


def validate_source_export_different(source: str, export: str) -> str | None:
    """Sprawdza czy foldery source i export są różne."""
    if os.path.normpath(source) == os.path.normpath(export):
        return "Folder źródłowy i eksportowy nie mogą być identyczne"
    return None
