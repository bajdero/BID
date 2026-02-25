"""
bid/source_manager.py
Zarządzanie słownikiem plików źródłowych: skanowanie folderów, odczyt EXIF,
persystencja do source_dict.json.

Cross-platform: wszystkie operacje na ścieżkach przez pathlib / os.path,
bez hardkodowanych separatorów.
"""
from __future__ import annotations

import datetime
import json
import logging
import os
from pathlib import Path

from PIL import Image

from bid.image_processing import exif_clean_from_tiff

logger = logging.getLogger("Yapa_CM")


class SourceState:
    """Możliwe stany zdjęcia w kolejce przetwarzania."""
    NEW        = "new"
    PROCESSING = "processing"
    OK         = "ok"
    ERROR      = "error"
    DELETED    = "deleted"   # plik źródłowy usunięty z dysku


# ---------------------------------------------------------------------------
# Ścieżka pliku persystencji (obok katalogu projektu)
# ---------------------------------------------------------------------------

def _source_dict_path(project_dir: Path) -> Path:
    return project_dir / "source_dict.json"


# ---------------------------------------------------------------------------
# Tworzenie/aktualizacja słownika
# ---------------------------------------------------------------------------

def create_source_item(root: str, folder_name: str, file: str) -> dict:
    """Tworzy wpis słownika dla jednego zdjęcia.

    Odczytuje EXIF w trybie leniwym (bez dekodowania pikseli).

    Args:
        root:        Pełna ścieżka do katalogu zawierającego plik.
        folder_name: Nazwa folderu (= nazwa autora/sesji).
        file:        Nazwa pliku.

    Returns:
        Słownik z kluczami: path, state, exported, size, created.
    """
    file_path = os.path.normpath(os.path.join(root, file))
    stats = os.stat(file_path)
    size_str = f"{stats.st_size / 1_024_000:.2f} MB"

    created = _read_created_date(file_path, folder_name, file, stats)

    return {
        "path":     file_path,
        "state":    SourceState.NEW,
        "exported": {},
        "size":     size_str,
        "created":  created,
        "mtime":    stats.st_mtime,   # czas modyfikacji — do wykrywania zmian
    }


def _read_created_date(
    file_path: str,
    folder_name: str,
    file: str,
    stats: os.stat_result,
) -> str:
    """Próbuje odczytać datę z EXIF; fallback na czas modyfikacji pliku.

    Args:
        file_path:   Pełna ścieżka do pliku.
        folder_name: Nazwa folderu (do logowania).
        file:        Nazwa pliku (do logowania).
        stats:       Wynik os.stat (do fallbacku).

    Returns:
        Data jako string w formacie ``'YYYY:MM:DD HH:MM:SS'``.
    """
    try:
        with Image.open(file_path) as img:
            exif = img.getexif()
    except Exception as exc:
        logger.error(f"Cannot open image for EXIF: {folder_name}/{file} — {exc}")
        return datetime.datetime.fromtimestamp(
            int(stats.st_mtime), datetime.timezone.utc
        ).strftime("%Y:%m:%d %H:%M:%S")

    if exif:
        # Próba odczytu DateTimeOriginal (0x9003) z korzenia lub bloku IFD
        for getter in (
            lambda e: e[0x9003],
            lambda e: e.get_ifd(34665)[0x9003],
        ):
            try:
                return getter(exif)
            except (KeyError, Exception):
                pass
        logger.warning(f"No DateTimeOriginal in EXIF: {folder_name}/{file}")

    return datetime.datetime.fromtimestamp(
        int(stats.st_mtime), datetime.timezone.utc
    ).strftime("%Y:%m:%d %H:%M:%S")


def create_source_dict(source_folder: str) -> dict:
    """Skanuje folder źródłowy i buduje słownik zdjęć.

    Args:
        source_folder: Ścieżka do głównego folderu z podfolderami sesji.

    Returns:
        Słownik: {folder_name: {file_name: source_item}}.
    """
    logger.debug("Tworzę source_dict")
    output: dict = {}
    for root, _dirs, files in os.walk(source_folder):
        root = os.path.normpath(root)  # unify separators before any join
        if root == os.path.normpath(source_folder):
            continue  # Pomijamy katalog główny
        folder_name = Path(root).name  # Cross-platform: bez split('\\')
        output[folder_name] = {}
        if "logo.png" not in files:
            logger.error(f"Brak logo.png w folderze: {folder_name}")
        for file in files:
            if file == "logo.png":
                continue
            output[folder_name][file] = create_source_item(root, folder_name, file)
    return output


def update_source_dict(source_dict: dict, source_folder: str) -> tuple[dict, bool]:
    """Aktualizuje istniejący słownik o nowe foldery i pliki.

    Args:
        source_dict:    Aktualny słownik zdjęć.
        source_folder:  Ścieżka do głównego folderu źródłowego.

    Returns:
        Krotka (zaktualizowany słownik, flaga czy znaleziono nowe pliki).
    """
    logger.debug("Aktualizuję source_dict")
    found_new = False

    for root, _dirs, files in os.walk(source_folder):
        root = os.path.normpath(root)  # unify separators before any join
        if root == os.path.normpath(source_folder):
            continue
        folder_name = Path(root).name  # Cross-platform
        if folder_name not in source_dict:
            logger.info(f"Nowy folder: '{folder_name}'")
            source_dict[folder_name] = {}
        if "logo.png" not in files:
            logger.error(f"Brak logo.png w folderze: {folder_name}")
        for file in files:
            if file == "logo.png":
                continue
            if file not in source_dict[folder_name]:
                logger.info(f"Nowy plik: '{folder_name}/{file}'")
                found_new = True
                source_dict[folder_name][file] = create_source_item(
                    root, folder_name, file
                )

    return source_dict, found_new


# ---------------------------------------------------------------------------
# Sprawdzanie integralności plików
# ---------------------------------------------------------------------------

IntegrityResult = dict  # alias dla czytelności


def check_integrity(
    source_dict: dict,
    export_settings: dict,
    export_folder: str,
) -> IntegrityResult:
    """Sprawdza integralność plików źródłowych i eksportów.

    Dla każdego zdjęcia w słowniku:
    - Plik źródłowy usunięty     → state = DELETED (logowane)
    - Plik źródłowy zmieniony    → state = NEW (reprocessing, logowane)
    - Brak któregoś pliku export → state = NEW (reprocessing, logowane)

    Pliki w stanie PROCESSING lub DELETED nie są sprawdzane ponownie.

    Args:
        source_dict:     Słownik zdjęć.
        export_settings: Konfiguracja delivery (export_option.json).
        export_folder:   Główny folder eksportów.

    Returns:
        Słownik ze zmianami: {folder: {photo: new_state}}.
        Puste jeśli nie wykryto żadnych zmian.
    """
    changes: dict[str, dict[str, str]] = {}

    for folder, photos in source_dict.items():
        for photo, meta in photos.items():
            state = meta.get("state", SourceState.NEW)

            # Pomijamy stany tymczasowe / już oznaczone
            if state in (SourceState.PROCESSING, SourceState.DELETED):
                continue

            src_path = meta.get("path", "")

            # ---- Sprawdzenie pliku źródłowego ----
            if not os.path.isfile(src_path):
                logger.warning(
                    f"[INTEGRITY] Plik źródłowy usunięty: {folder}/{photo}"
                )
                source_dict[folder][photo]["state"] = SourceState.DELETED
                changes.setdefault(folder, {})[photo] = SourceState.DELETED
                continue

            # ---- Sprawdzenie zmiany (mtime) ----
            try:
                current_mtime = os.stat(src_path).st_mtime
            except OSError:
                continue  # niedostępny — spróbujemy przy następnym cyklu

            stored_mtime = meta.get("mtime")
            if stored_mtime is not None and current_mtime != stored_mtime:
                logger.warning(
                    f"[INTEGRITY] Plik źródłowy zmieniony — reprocessing: "
                    f"{folder}/{photo}"
                )
                source_dict[folder][photo]["mtime"] = current_mtime
                source_dict[folder][photo]["state"] = SourceState.NEW
                source_dict[folder][photo]["exported"] = {}
                changes.setdefault(folder, {})[photo] = SourceState.NEW
                continue

            # ---- Sprawdzenie plików eksportowych (tylko OK) ----
            if state != SourceState.OK:
                continue

            exported: dict = meta.get("exported", {})
            for deliver in export_settings:
                export_path = exported.get(deliver, "")
                if export_path and not os.path.isfile(export_path):
                    logger.warning(
                    f"[INTEGRITY] Brak pliku eksportu '{deliver}' — "
                    f"reprocessing: {folder}/{photo}"
                    )
                    source_dict[folder][photo]["state"] = SourceState.NEW
                    # Nie usuwamy całego 'exported', aby app mógł pominąć istniejące pliki
                    changes.setdefault(folder, {})[photo] = SourceState.NEW
                    break  # wystarczy jeden brakujący, żeby wymusić reprocessing

    return changes


def save_source_dict(source_dict: dict, project_dir: Path) -> None:
    """Zapisuje słownik zdjęć do pliku JSON.

    Args:
        source_dict:  Słownik zdjęć do zapisania.
        project_dir:  Katalog projektu (tam ląduje source_dict.json).
    """
    path = _source_dict_path(project_dir)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(source_dict, fh, indent=4, ensure_ascii=False)
    logger.debug(f"Zapisano source_dict → {path}")


def load_source_dict(project_dir: Path) -> dict | None:
    """Wczytuje słownik z pliku JSON, jeśli istnieje.

    Args:
        project_dir: Katalog projektu.

    Returns:
        Słownik zdjęć lub ``None``, gdy plik nie istnieje.
    """
    path = _source_dict_path(project_dir)
    if path.is_file():
        logger.info("Wczytuję istniejący source_dict.json")
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return None
