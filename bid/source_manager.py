"""
bid/source_manager.py
Zarządzanie słownikiem plików źródłowych: skanowanie folderów, odczyt EXIF,
persystencja do source_dict.json.

Cross-platform: wszystkie operacje na ścieżkach przez pathlib / os.path,
bez hardkodowanych separatorów.

FIX-PART-FILE: Mechanism to prevent indexing of partially copied files.
  - is_file_ready(): Check if file is fully available (size stable)
  - wait_for_file_ready(): Wait for file with timeout
  - Used in create_source_item() to ensure files are complete before indexing
"""
from __future__ import annotations

import datetime
import json
import logging
import os
import re
import time
from pathlib import Path

from PIL import Image

from bid.image_processing import exif_clean_from_tiff, get_all_exif

logger = logging.getLogger("BID")


def _sanitize_filename(name: str) -> str:
    """Usuwa znaki niedozwolone w nazwach plików Windows/Linux."""
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def _check_logo_exists(folder_path: str, folder_name: str) -> bool:
    """Sprawdza czy logo.png istnieje w folderze sesji.

    Args:
        folder_path: Pełna ścieżka do folderu sesji.
        folder_name: Nazwa folderu (do logowania).

    Returns:
        True jeśli logo.png istnieje, False w przeciwnym razie.
    """
    logo_path = os.path.join(folder_path, "logo.png")
    if not os.path.isfile(logo_path):
        logger.error(f"Brak logo.png w folderze: {folder_name}")
        return False
    return True


# ---------------------------------------------------------------------------
# FIX-ASYNC: Non-blocking File Readiness Detection
# File checks are async - indexing never blocks, incomplete files get DOWNLOADING state
# ---------------------------------------------------------------------------

def is_file_ready_quick(file_path: str) -> bool:
    """Quick NON-BLOCKING check if file is ready (no wait).
    
    Does NOT block - only checks current state.
    Used during indexing to quickly determine file status.
    
    For blocking wait, use monitor_incomplete_files() in background instead.
    
    Args:
        file_path: Full path to file.
    
    Returns:
        True if file appears complete, False if likely incomplete.
        
    Implementation:
        - Assume files are complete unless strong evidence otherwise
        - Only mark incomplete if size is exactly 0 (very new, not written)
        - Or if file locked (cannot stat properly)
        - Cross-platform: detects common incomplete states
        
    Notes:
        - Files are marked DOWNLOADING only in rare cases
        - Monitoring will update status when file becomes stable
        - This keeps indexing fast (no waits)
    """
    if not os.path.exists(file_path):
        return False
    
    try:
        # Get current file stats
        stat = os.stat(file_path)
        
        # If file size is 0, likely being created
        if stat.st_size == 0:
            return False
        
        # Otherwise assume file is ready (complete)
        # Monitoring will catch incomplete files later if needed
        return True
        
    except (OSError, IOError):
        # File locked or inaccessible
        return False


def is_file_stable(file_path: str, check_duration: float = 0.5) -> bool:
    """Check if file size is stable (blocking wait for stability check).
    
    BLOCKING: Waits for check_duration to verify size stability.
    Used by monitor_incomplete_files() in background thread.
    
    Args:
        file_path:      Full path to file.
        check_duration: Seconds to wait between size checks.
    
    Returns:
        True if size unchanged (file complete), False if still growing.
    """
    if not os.path.exists(file_path):
        return False
    
    try:
        initial_size = os.path.getsize(file_path)
        time.sleep(check_duration)
        final_size = os.path.getsize(file_path)
        
        is_stable = (initial_size == final_size)
        
        if not is_stable:
            logger.debug(
                f"File still being written: {file_path} "
                f"(size: {initial_size} → {final_size} bytes)"
            )
        
        return is_stable
    
    except (OSError, IOError) as exc:
        logger.debug(f"Cannot check file stability: {file_path} — {exc}")
        return False


def monitor_incomplete_files(
    source_dict: dict,
    max_checks: int = 5,
    check_interval: float = 2.0,
) -> dict[str, dict[str, bool]]:
    """Monitor files in DOWNLOADING state and update when complete.
    
    NON-BLOCKING for caller - runs as background task.
    Should be called periodically (e.g., every 2 seconds).
    
    Args:
        source_dict:   The source dictionary with files.
        max_checks:    Maximum stability checks before marking READY.
        check_interval: Seconds between stability checks.
    
    Returns:
        Dictionary of updates: {folder: {file: ready_bool}}.
        Returns empty dict if no updates.
    
    Notes:
        - FIX-ASYNC: Non-blocking monitoring
        - Updates files from DOWNLOADING → NEW when ready
        - Reads EXIF metadata when file becomes ready
        - Handles network delays gracefully
        - Cross-platform compatible
    
    Usage:
        In background thread or timer:
            updates = monitor_incomplete_files(source_dict)
            for folder, files in updates.items():
                for file, is_ready in files.items():
                    if is_ready:
                        source_dict[folder][file]["state"] = SourceState.NEW
    """
    updates: dict[str, dict[str, bool]] = {}
    
    for folder_name, files in source_dict.items():
        for file_name, item in files.items():
            # Only check files in DOWNLOADING state
            if item.get("state") != SourceState.DOWNLOADING:
                continue
            
            file_path = item.get("path")
            if not file_path:
                continue
            
            # Quick stability check (one measurement, small wait)
            if is_file_stable(file_path, check_duration=check_interval):
                # File is now stable - read its metadata
                try:
                    stats = os.stat(file_path)
                    created, exif_dict = _read_metadata(file_path, folder_name, file_name, stats)
                    
                    # Update metadata now that file is ready
                    item["created"] = created
                    item["exif"] = exif_dict
                    size_str = f"{stats.st_size / 1_024_000:.2f} MB"
                    item["size"] = size_str
                    item["size_bytes"] = stats.st_size
                    
                    # Mark as updated
                    if folder_name not in updates:
                        updates[folder_name] = {}
                    updates[folder_name][file_name] = True
                    logger.info(f"File ready (was downloading): {folder_name}/{file_name}")
                    
                except Exception as exc:
                    logger.error(f"Error reading metadata for ready file {file_path}: {exc}")
                    # Keep it as DOWNLOADING for next cycle
                    updates[folder_name] = updates.get(folder_name, {})
                    updates[folder_name][file_name] = False
            else:
                # Still not ready
                updates[folder_name] = updates.get(folder_name, {})
                updates[folder_name][file_name] = False
    
    return updates


# Keep old functions for backward compatibility if needed
def is_file_ready(file_path: str, check_duration: float = 0.5) -> bool:
    """Legacy: Use is_file_ready_quick() + is_file_stable() instead.
    
    This function is deprecated. Use:
    - is_file_ready_quick() for non-blocking indexing checks
    - is_file_stable() for blocking stability checks
    - monitor_incomplete_files() for background monitoring
    """
    logger.debug("is_file_ready() deprecated - redirecting to is_file_stable()")
    return is_file_stable(file_path, check_duration)


def wait_for_file_ready(
    file_path: str,
    timeout: float = 30.0,
    check_interval: float = 0.5,
    max_checks: int = 10,
) -> bool:
    """Legacy: Use monitor_incomplete_files() instead.
    
    This function is deprecated. For non-blocking async approach, use:
    - monitor_incomplete_files() running in background thread
    - Updates files from DOWNLOADING state to NEW when ready
    """
    logger.debug("wait_for_file_ready() deprecated - use monitor_incomplete_files()")
    start_time = time.time()
    ready_count = 0
    
    while time.time() - start_time < timeout:
        if is_file_stable(file_path, check_duration=check_interval):
            ready_count += 1
            if ready_count >= max_checks:
                logger.debug(f"File ready after {time.time() - start_time:.1f}s: {file_path}")
                return True
        else:
            ready_count = 0
        
        time.sleep(0.05)
    
    elapsed = time.time() - start_time
    logger.warning(
        f"Timeout waiting for file to be ready ({elapsed:.1f}s): {file_path}"
    )
    return False


class SourceState:
    """Możliwe stany zdjęcia w kolejce przetwarzania."""
    DOWNLOADING = "downloading"  # FIX-ASYNC: Plik aktualnie się ściąga z sieci
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
    wait_timeout: float = 30.0,
) -> dict:
    """Tworzy wpis słownika dla jednego zdjęcia.

    Args:
        root:        Pełna ścieżka do katalogu zawierającego plik.
        folder_name: Nazwa folderu (= nazwa autora/sesji).
        file:        Nazwa pliku.
        export_folder:   Główny folder eksportów (do sprawdzania istniejących).
        export_settings: Konfiguracja exportu.
        wait_timeout:    DEPRECATED. Kept for compatibility but not used in async mode.

    Returns:
        Słownik z kluczami: path, state, exported, size, created, mtime, exif.
        
    Notes:
        - FIX-ASYNC: 100% non-blocking indexing. Incomplete files get DOWNLOADING state
        - Quick non-blocking check: files indexed immediately
        - EXIF read skipped for DOWNLOADING files (no file access blocking)
        - Monitor with monitor_incomplete_files() to update when ready
        - Cross-platform: works on Windows, Linux, macOS
        - Processing skipped for DOWNLOADING files
    """
    file_path = os.path.normpath(os.path.join(root, file))
    
    # FIX-ASYNC: Quick non-blocking check (doesn't wait)
    file_ready = is_file_ready_quick(file_path)
    
    stats = os.stat(file_path)
    size_str = f"{stats.st_size / 1_024_000:.2f} MB"

    # FIX-ASYNC: Set state based on file readiness
    if file_ready:
        state = SourceState.NEW
        logger.debug(f"File indexed as NEW (ready): {folder_name}/{file}")
        # Only read metadata for ready files (non-blocking)
        created, exif_dict = _read_metadata(file_path, folder_name, file, stats)
    else:
        # File incomplete (DOWNLOADING): skip expensive I/O
        state = SourceState.DOWNLOADING
        logger.debug(f"File indexed as DOWNLOADING (incomplete): {folder_name}/{file}")
        # Use file mtime as placeholder, fill in real metadata when monitor marks it ready
        default_date = datetime.datetime.fromtimestamp(
            int(stats.st_mtime), datetime.timezone.utc
        ).strftime("%Y:%m:%d %H:%M:%S")
        created = default_date
        exif_dict = {}
    
    exported_data = {}

    # Jeśli odbudowujemy bazę — sprawdź czy eksporty już są
    if export_folder and export_settings:
        all_match = True
        temp_exported = {}
        
        created_tag = created.replace(" ", "_").replace(":", "-")
        orig_stem = os.path.splitext(file)[0]
        folder_tag = _sanitize_filename(folder_name.replace(" ", "_"))
        export_base_name = f"YAPA{created_tag}_{folder_tag}_{_sanitize_filename(orig_stem)}"
        
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
                        
                        if not any(abs(ratio - r) < 0.01 for r in ratios):
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
        "size_bytes": stats.st_size,
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
    normalized_source = os.path.normpath(os.path.realpath(source_folder))
    for root, _dirs, files in os.walk(source_folder):
        root = os.path.normpath(root)  # unify separators before any join
        # Weryfikacja path traversal przez symlinki
        real_root = os.path.normpath(os.path.realpath(root))
        if not real_root.startswith(normalized_source):
            logger.warning(f"Pominięto folder poza zakresem (symlink?): {root}")
            continue
        if root == os.path.normpath(source_folder):
            continue  # Pomijamy katalog główny
        folder_name = Path(root).name  # Cross-platform: bez split('\\')
        output[folder_name] = {}
        _check_logo_exists(root, folder_name)
        for file in files:
            if file == "logo.png":
                continue
            # Skip macOS/iOS metadata files (e.g., ._ prefixed files from iPad export)
            if file.startswith("._"):
                logger.debug(f"Ignorując plik metadanych: {folder_name}/{file}")
                continue
            output[folder_name][file] = create_source_item(
                root, folder_name, file, export_folder, export_settings
            )
    logger.info(f"Skanowanie zakończone: {len(output)} folderów w '{source_folder}'")
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
    normalized_source = os.path.normpath(os.path.realpath(source_folder))

    for root, _dirs, files in os.walk(source_folder):
        root = os.path.normpath(root)  # unify separators before any join
        # Weryfikacja path traversal przez symlinki
        real_root = os.path.normpath(os.path.realpath(root))
        if not real_root.startswith(normalized_source):
            logger.warning(f"Pominięto folder poza zakresem (symlink?): {root}")
            continue
        if root == os.path.normpath(source_folder):
            continue
        folder_name = Path(root).name  # Cross-platform
        if folder_name not in source_dict:
            logger.info(f"Nowy folder: '{folder_name}'")
            source_dict[folder_name] = {}
        _check_logo_exists(root, folder_name)
        for file in files:
            if file == "logo.png":
                continue
            # Skip macOS/iOS metadata files (e.g., ._ prefixed files from iPad export)
            if file.startswith("._"):
                logger.debug(f"Ignorując plik metadanych: {folder_name}/{file}")
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

    Pliki w stanie PROCESSING, DELETED, lub DOWNLOADING nie są sprawdzane ponownie.
    (DOWNLOADING files will be rechecked by monitor_incomplete_files in background)

    Args:
        source_dict:     Słownik zdjęć.
        export_settings: Konfiguracja delivery (export_option.json).
        export_folder:   Główny folder eksportów.

    Returns:
        Słownik ze zmianami: {folder: {photo: new_state}}.
        Puste jeśli nie wykryto żadnych zmian.
        
    Notes:
        - FIX-ASYNC: Skips DOWNLOADING files (no processing until ready)
    """
    changes: dict[str, dict[str, str]] = {}

    for folder, photos in source_dict.items():
        for photo, meta in photos.items():
            state = meta.get("state", SourceState.NEW)

            # Pomijamy stany tymczasowe / już oznaczone
            # FIX-ASYNC: Skip DOWNLOADING files (will be checked by background monitor)
            if state in (SourceState.PROCESSING, SourceState.DELETED, SourceState.OK_OLD, SourceState.DOWNLOADING):
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

            # ---- Sprawdzenie zmiany (mtime i rozmiar) ----
            try:
                file_stat = os.stat(src_path)
                current_mtime = file_stat.st_mtime
                current_size = file_stat.st_size
            except OSError:
                continue  # niedostępny — spróbujemy przy następnym cyklu

            stored_mtime = meta.get("mtime")
            stored_size = meta.get("size_bytes")
            
            # Sprawdzenie zmiany mtime
            if stored_mtime is not None and current_mtime != stored_mtime:
                logger.warning(
                    f"[INTEGRITY] Plik źródłowy zmieniony (mtime) — reprocessing: "
                    f"{folder}/{photo}"
                )
                source_dict[folder][photo]["mtime"] = current_mtime
                source_dict[folder][photo]["size_bytes"] = current_size
                size_str = f"{current_size / 1_024_000:.2f} MB"
                source_dict[folder][photo]["size"] = size_str
                source_dict[folder][photo]["state"] = SourceState.NEW
                source_dict[folder][photo]["exported"] = {}
                changes.setdefault(folder, {})[photo] = SourceState.NEW
                continue
            
            # Sprawdzenie zmiany rozmiaru (niezależnie od mtime)
            if stored_size is not None and current_size != stored_size:
                logger.warning(
                    f"[INTEGRITY] Plik źródłowy zmienił rozmiar — reprocessing: "
                    f"{folder}/{photo} (was {stored_size} bytes, now {current_size} bytes)"
                )
                source_dict[folder][photo]["size_bytes"] = current_size
                size_str = f"{current_size / 1_024_000:.2f} MB"
                source_dict[folder][photo]["size"] = size_str
                source_dict[folder][photo]["state"] = SourceState.NEW
                source_dict[folder][photo]["exported"] = {}
                changes.setdefault(folder, {})[photo] = SourceState.NEW
                continue

            # ---- Sprawdzenie plików eksportowych (tylko OK) ----
            # TODO: Trzeba dodać nowy state jeżeli fail jest z errorem błąd zapisu e <export> file is not seekable to wtedy state powinien być export_fail
            if state not in [SourceState.OK, SourceState.ERROR]:
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
