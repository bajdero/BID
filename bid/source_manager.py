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

from bid.image_processing import exif_clean_from_tiff, get_all_exif

logger = logging.getLogger("Yapa_CM")


class SourceState:
    """Możliwe stany zdjęcia w kolejce przetwarzania."""
    NEW        = "new"
    PROCESSING = "processing"
    OK         = "ok"
    OK_OLD     = "ok_old"    # znaleziono istniejące eksporty (np. po odbudowie bazy)
    ERROR      = "error"
    DELETED    = "deleted"   # plik źródłowy usunięty z dysku
    SKIP       = "skip"      # użytkownik ręcznie pominął plik


# ---------------------------------------------------------------------------
# Ścieżka pliku persystencji (obok katalogu projektu)
# ---------------------------------------------------------------------------

def _source_dict_path(project_dir: Path) -> Path:
    return project_dir / "source_dict.json"


# ---------------------------------------------------------------------------
# Tworzenie/aktualizacja słownika
# ---------------------------------------------------------------------------

def _read_metadata(
    file_path: str,
    folder_name: str,
    file: str,
    stats: os.stat_result,
) -> tuple[str, dict]:
    """Próbuje odczytać datę i wszystkie tagi z EXIF; fallback na czas modyfikacji pliku.

    Args:
        file_path:   Pełna ścieżka do pliku.
        folder_name: Nazwa folderu (do logowania).
        file:        Nazwa pliku (do logowania).
        stats:       Wynik os.stat (do fallbacku).

    Returns:
        Krotka (data_str, exif_dict).
    """
    default_date = datetime.datetime.fromtimestamp(
        int(stats.st_mtime), datetime.timezone.utc
    ).strftime("%Y:%m:%d %H:%M:%S")
    
    try:
        with Image.open(file_path) as img:
            exif = img.getexif()
            full_exif = get_all_exif(img)
            
            created = None
            if exif:
                # Próba odczytu DateTimeOriginal (0x9003) z korzenia lub bloku IFD
                for getter in (
                    lambda e: e[0x9003],
                    lambda e: e.get_ifd(34665)[0x9003],
                ):
                    try:
                        created = getter(exif)
                        break
                    except (KeyError, Exception):
                        pass
            
            return created or default_date, full_exif
            
    except Exception as exc:
        logger.error(f"Cannot open image for EXIF: {folder_name}/{file} — {exc}")
        return default_date, {}


def create_source_item(
    root: str, 
    folder_name: str, 
    file: str,
    export_folder: str | None = None,
    export_settings: dict | None = None,
) -> dict:
    """Tworzy wpis słownika dla jednego zdjęcia.

    Args:
        root:        Pełna ścieżka do katalogu zawierającego plik.
        folder_name: Nazwa folderu (= nazwa autora/sesji).
        file:        Nazwa pliku.
        export_folder:   Główny folder eksportów (do sprawdzania istniejących).
        export_settings: Konfiguracja exportu.

    Returns:
        Słownik z kluczami: path, state, exported, size, created.
    """
    file_path = os.path.normpath(os.path.join(root, file))
    stats = os.stat(file_path)
    size_str = f"{stats.st_size / 1_024_000:.2f} MB"

    created, exif_dict = _read_metadata(file_path, folder_name, file, stats)
    
    # Domyślny stan
    state = SourceState.NEW
    exported_data = {}

    # Jeśli odbudowujemy bazę — sprawdź czy eksporty już są
    if export_folder and export_settings:
        all_match = True
        temp_exported = {}
        
        created_tag = created.replace(" ", "_").replace(":", "-")
        orig_stem = os.path.splitext(file)[0]
        folder_tag = folder_name.replace(" ", "_")
        export_base_name = f"YAPA{created_tag}_{folder_tag}_{orig_stem}"
        
        # Otwieramy obraz tylko jeśli musimy sprawdzić ratio (bo jakieś eksporty brakuje)
        img_for_ratio = None
        try:
            for deliver, d_cfg in export_settings.items():
                ext = ".jpg" if d_cfg["format"] == "JPEG" else ".png"
                exp_path = os.path.normpath(os.path.join(export_folder, deliver, export_base_name + ext))
                if os.path.isfile(exp_path):
                    temp_exported[deliver] = exp_path
                else:
                    # Sprawdź czy ten wariant w ogóle powinien istnieć (ratio)
                    ratios = d_cfg.get("ratio")
                    if ratios:
                        if img_for_ratio is None:
                            img_for_ratio = Image.open(file_path)
                        
                        w, h = img_for_ratio.size
                        ratio = round(w / h, 2)
                        
                        match = False
                        for r_min, r_max in ratios:
                            if r_min <= ratio <= r_max:
                                match = True
                                break
                        if not match:
                            continue
                    
                    all_match = False
            
        except Exception as exc:
            logger.error(f"Błąd sprawdzania OK_OLD dla {folder_name}/{file}: {exc}")
        finally:
            if img_for_ratio:
                img_for_ratio.close()
        
        exported_data = temp_exported
        if all_match and temp_exported:
            state = SourceState.OK_OLD

    return {
        "path":     file_path,
        "state":    state,
        "exported": exported_data,
        "size":     size_str,
        "created":  created,
        "mtime":    stats.st_mtime,
        "exif":     exif_dict,
    }


def create_source_dict(
    source_folder: str,
    export_folder: str | None = None,
    export_settings: dict | None = None,
) -> dict:
    """Skanuje folder źródłowy i buduje słownik zdjęć.

    Args:
        source_folder: Ścieżka do głównego folderu z podfolderami sesji.
        export_folder:   Opcjonalna ścieżka do eksportów (wykrywanie OK_OLD).
        export_settings: Opcjonalne ustawienia eksportów.

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
            output[folder_name][file] = create_source_item(
                root, folder_name, file, export_folder, export_settings
            )
    return output


def update_source_dict(
    source_dict: dict, 
    source_folder: str,
    export_folder: str | None = None,
    export_settings: dict | None = None,
) -> tuple[dict, bool]:
    """Aktualizuje istniejący słownik o nowe foldery i pliki.

    Args:
        source_dict:    Aktualny słownik zdjęć.
        source_folder:  Ścieżka do głównego folderu źródłowego.
        export_folder:  Opcjonalna ścieżka do eksportów.
        export_settings: Opcjonalne ustawienia eksportów.

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
                    root, folder_name, file, export_folder, export_settings
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
            if state in (SourceState.PROCESSING, SourceState.DELETED, SourceState.OK_OLD):
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

    Obsługuje błędy formatu JSON (korupcja pliku).

    Args:
        project_dir: Katalog projektu.

    Returns:
        Słownik zdjęć lub ``None``, gdy plik nie istnieje lub jest uszkodzony.
    """
    path = _source_dict_path(project_dir)
    if not path.is_file():
        return None

    logger.info("Wczytuję istniejący source_dict.json")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        logger.error(f"Plik source_dict.json jest uszkodzony (JSON error): {exc}")
        logger.error("Baza zostanie odbudowana na podstawie skanowania dysku.")
        return None
    except Exception as exc:
        logger.error(f"Błąd krytyczny podczas wczytywania source_dict.json: {exc}")
        return None
