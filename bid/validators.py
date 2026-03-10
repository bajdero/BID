"""bid/validators.py — Walidacja danych wejściowych."""
from __future__ import annotations
import os
from typing import Any

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
    
    if "size_type" in profile and profile["size_type"] not in ("longer", "width", "height"):
        errors.append(f"Profil '{name}': nieprawidłowy size_type '{profile['size_type']}'")
    
    if "format" in profile and profile["format"] not in ("JPEG", "PNG"):
        errors.append(f"Profil '{name}': nieprawidłowy format '{profile['format']}'")
    
    if "ratio" in profile:
        ratio = profile["ratio"]
        if not isinstance(ratio, list):
            errors.append(f"Profil '{name}': ratio musi być listą")
    
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
