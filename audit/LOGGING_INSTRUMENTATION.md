# INSTRUMENTACJA LOGÓW — YAPA/BID

**Cel:** Dodanie precyzyjnych logów umożliwiających weryfikację zachowania w testach automatycznych.  
**Zasada:** Każda istotna operacja loguje: START + SUKCES/BŁĄD + kontekst (plik, rozmiar, profil, czas).  
**Logger:** `logging.getLogger("Yapa_CM")` — ten sam we wszystkich modułach.

---

## SPIS TREŚCI

1. [Nowy moduł: bid/logging_config.py](#1-nowy-moduł-bidlogging_configpy)
2. [Zmiany w main.py](#2-zmiany-w-mainpy)
3. [Zmiany w bid/image_processing.py](#3-zmiany-w-bidimage_processingpy)
4. [Zmiany w bid/source_manager.py](#4-zmiany-w-bidsource_managerpy)
5. [Zmiany w bid/config.py](#5-zmiany-w-bidconfigpy)
6. [Zmiany w bid/app.py](#6-zmiany-w-bidapppy)
7. [Zmiany w bid/project_manager.py](#7-zmiany-w-bidproject_managerpy)
8. [Zmiany w bid/ui/](#8-zmiany-w-bidui)
9. [Podsumowanie dodanych logów](#9-podsumowanie-dodanych-logów)

---

## 1. NOWY MODUŁ: bid/logging_config.py

Wydzielenie konfiguracji loggera z `main.py` do osobnego modułu — umożliwia testom override bez modyfikacji `main.py`.

```python
"""
bid/logging_config.py
Centralna konfiguracja loggera Yapa_CM.
Testy mogą importować setup_logger() aby skonfigurować logger bez uruchamiania main.py.
"""
from __future__ import annotations

import datetime
import logging
from pathlib import Path

LOGGER_NAME = "Yapa_CM"

def setup_logger(
    level: int = logging.INFO,
    log_dir: Path | None = None,
    console: bool = True,
    file: bool = True,
) -> logging.Logger:
    """Konfiguruje i zwraca loggera Yapa_CM.
    
    Args:
        level: Poziom logowania.
        log_dir: Katalog na pliki logów. None = logs/ obok main.py.
        console: Czy dodać handler konsoli.
        file: Czy dodać handler pliku.
    
    Returns:
        Skonfigurowany logger.
    """
    logger = logging.getLogger(LOGGER_NAME)
    
    # Nie konfiguruj ponownie jeśli handlery już istnieją
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    
    if console:
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(fmt)
        logger.addHandler(ch)
    
    if file:
        if log_dir is None:
            log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        log_name = datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S") + ".log"
        fh = logging.FileHandler(log_dir / log_name, encoding="utf-8")
        fh.setLevel(level)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    
    return logger


def get_logger() -> logging.Logger:
    """Zwraca istniejącą instancję loggera (bez konfiguracji)."""
    return logging.getLogger(LOGGER_NAME)
```

### Zmiana w main.py

Zastąpić zawartość `_setup_logging()`:

```python
# PRZED (linie 21-42 w main.py):
def _setup_logging(level: int = logging.INFO) -> None:
    # ... cała obecna implementacja ...

# PO:
def _setup_logging(level: int = logging.INFO) -> None:
    from bid.logging_config import setup_logger
    setup_logger(level=level)
```

---

## 2. ZMIANY W main.py

Istniejące logi pozostają bez zmian. main.py deleguje konfigurację do `bid/logging_config.py`.

---

## 3. ZMIANY W bid/image_processing.py

### 3.1 Funkcja `image_resize()` — dodać log START

**Lokalizacja:** Po obecnej linii `logger.debug("Skaluję zdjęcie do ...")` (ok. linia 61)

Istniejący log jest OK. **Zmienić format** aby zawierał wymiary wejściowe:

```python
# PRZED:
logger.debug(f"Skaluję zdjęcie do {longer_side} px (metoda: {method})")

# PO:
logger.debug(f"Skaluję zdjęcie {img.width}x{img.height} → {longer_side}px (metoda: {method})")
```

### 3.2 Funkcja `image_convert_to_srgb()` — dodać info o profilu

**Lokalizacja:** Linia ~35, zamiast generycznego logu

```python
# PRZED:
logger.debug("Konwertuję zdjęcie na sRGB")

# PO:
icc = img.info.get("icc_profile", "")
if icc:
    logger.debug("Konwertuję zdjęcie na sRGB (znaleziono profil ICC)")
else:
    logger.debug("Brak profilu ICC — pomijam konwersję sRGB")
```

**UWAGA:** Przesunąć log POD pobranie `icc` (przenieść linię).

### 3.3 Funkcja `apply_watermark()` — dodać rozmiar i opacity

**Lokalizacja:** Linia ~104

```python
# PRZED:
logger.debug(f"Nakładam watermark z {logo_path}")

# PO:
logger.debug(f"Nakładam watermark z {logo_path} (rozmiar={size}, opacity={opacity})")
```

### 3.4 Funkcja `process_photo_task()` — kluczowe logi dla testów

**Dodać na POCZĄTKU funkcji** (po `start_time = time.perf_counter()`):

```python
start_time = time.perf_counter()
logger.info(f"[PROCESS] Start: {folder_name}/{photo_name}")
```

**Dodać po KAŻDYM try/except BŁĘDZIE** — log z kontekstem:

```python
# Po linii: results["error_msg"] = f"Błąd otwarcia pliku '{photo_path}': {exc}"
logger.error(f"[PROCESS] Błąd otwarcia: {folder_name}/{photo_name} — {exc}")

# Po linii: results["error_msg"] = f"Błąd odczytu EXIF '{photo_path}': {exc}"
logger.error(f"[PROCESS] Błąd EXIF: {folder_name}/{photo_name} — {exc}")

# Po linii: results["error_msg"] = f"Błąd skalowania w {deliver}: {exc}"
logger.error(f"[PROCESS] Błąd skalowania: {folder_name}/{photo_name} profil={deliver} — {exc}")

# Po linii: results["error_msg"] = f"Błąd konwersji sRGB w {deliver}: {exc}"
logger.error(f"[PROCESS] Błąd sRGB: {folder_name}/{photo_name} profil={deliver} — {exc}")

# Po linii: results["error_msg"] = f"Błąd nakładania logo w {deliver}: {exc}"
logger.error(f"[PROCESS] Błąd watermark: {folder_name}/{photo_name} profil={deliver} — {exc}")
```

**Dodać w PĘTLI eksportu** — log per profil:

```python
# Na początku pętli `for deliver, d_cfg in export_settings.items():`
logger.debug(f"[PROCESS] Eksport profil '{deliver}': {folder_name}/{photo_name}")
```

**Dodać po POMIJENIU istniejącego eksportu:**

```python
# Po: results["exported"][deliver] = existing_path; continue
logger.debug(f"[PROCESS] Pomijam istniejący eksport '{deliver}': {existing_path}")
```

**Dodać po POMIJENIU z powodu ratio:**

```python
# Po: if actual not in ratios: continue
logger.debug(f"[PROCESS] Pomijam '{deliver}' — ratio {actual} poza zakresem {ratios}")
```

**Dodać po ZAPISIE pliku eksportu:**

```python
# Po udanym zapisie (po final_img.save()):
logger.info(f"[PROCESS] Eksport '{deliver}' zapisany: {export_path}")
```

**Dodać na KOŃCU funkcji** (przed `return results`):

```python
results["duration"] = time.perf_counter() - start_time
exported_count = len(results["exported"])
logger.info(f"[PROCESS] Zakończono: {folder_name}/{photo_name} — "
            f"{exported_count} eksportów w {results['duration']:.2f}s")
return results
```

### 3.5 Funkcja `get_all_exif()` — dodać podsumowanie

**Dodać na KOŃCU funkcji** (przed `return`):

```python
logger.debug(f"[EXIF] Odczytano {len(result)} tagów z obrazu")
```

### 3.6 Funkcja `get_logo()` — istniejący log OK

Bez zmian.

---

## 4. ZMIANY W bid/source_manager.py

### 4.1 Funkcja `create_source_dict()` — dodać podsumowanie

**Istniejący log:** `logger.debug("Tworzę source_dict")` — OK.

**Dodać na KOŃCU funkcji** (przed `return output`):

```python
total_files = sum(len(photos) for photos in output.values())
total_folders = len(output)
logger.info(f"[SOURCE] Skanowanie zakończone: {total_folders} folderów, {total_files} plików")
return output
```

### 4.2 Funkcja `update_source_dict()` — dodać podsumowanie

**Istniejący log:** `logger.debug("Aktualizuję source_dict")` — OK.

**Dodać na KOŃCU funkcji** (przed `return`):

```python
if found_new:
    new_count = sum(
        1 for f in source_dict for p in source_dict[f]
        if source_dict[f][p]["state"] == SourceState.NEW
    )
    logger.info(f"[SOURCE] Aktualizacja: znaleziono nowe pliki (NEW: {new_count})")
else:
    logger.debug("[SOURCE] Aktualizacja: brak nowych plików")
```

### 4.3 Funkcja `check_integrity()` — dodać podsumowanie

**Dodać na KOŃCU funkcji** (przed `return changes`):

```python
if changes:
    total_changes = sum(len(v) for v in changes.values())
    logger.info(f"[INTEGRITY] Wykryto {total_changes} zmian integralności")
else:
    logger.debug("[INTEGRITY] Brak zmian integralności")
return changes
```

### 4.4 Funkcja `_read_metadata()` — dodać fallback info

**Istniejący log na error jest OK.**

**Dodać w bloku except** — przed return:

```python
# Istniejący:
except Exception as exc:
    logger.error(f"Cannot open image for EXIF: {folder_name}/{file} — {exc}")
    return default_date, {}

# Dodać logger.debug po udanym odczycie (w bloku try, przed return):
logger.debug(f"[EXIF] Odczyt metadanych: {folder_name}/{file} → data={created or default_date}")
```

### 4.5 Funkcja `save_source_dict()` — istniejący log OK

`logger.debug(f"Zapisano source_dict → {path}")` — bez zmian.

### 4.6 Funkcja `load_source_dict()` — istniejący logi OK

`logger.info("Wczytuję istniejący source_dict.json")` — bez zmian.
`logger.error(...)` na JSONDecodeError — bez zmian.

---

## 5. ZMIANY W bid/config.py

### 5.1 Funkcja `_load_json()` — dodać info o załadowanym pliku

**Istniejący log:** `logger.debug(f"Loaded config: {path}")` — OK.

**Dodać walidację rozmiaru:**

```python
# Po: data = json.load(fh)
logger.debug(f"Loaded config: {path} ({len(data)} keys)")
```

### 5.2 Funkcja `load_export_options()` — dodać info o profilach

**Dodać po załadowaniu:**

```python
def load_export_options(path: Path | None = None) -> dict:
    if path is None:
        path = PROJECT_DIR / "export_option.json"
    data = _load_json(path, "export_options")
    logger.info(f"[CONFIG] Załadowano {len(data)} profili eksportu: {', '.join(data.keys())}")
    return data
```

---

## 6. ZMIANY W bid/app.py

### 6.1 `MainApp.__init__()` — dodać info o konfiguracji

**Po linii `self.max_workers = os.cpu_count() or 4`:**

```python
logger.info(f"[APP] Pool workerów: {self.max_workers} (CPU: {os.cpu_count()})")
```

### 6.2 `scan_photos()` — dodać podsumowanie

**Na początku metody (po `with self.dict_lock:`):**

Istniejący log `logger.info("Brak nowych zdjęć do przetworzenia")` — OK.

**Dodać gdy są zdjęcia do przetworzenia:**

```python
if total_new > 0:
    logger.info(f"[SCAN] Rozpoczynam eksport: {total_new} nowych zdjęć")
    # ... reszta kodu
```

### 6.3 `check_futures()` — dodać obsługę wyników

**Istniejący log w `_mark_error` jest OK.** Dodać:

```python
# Po: result = future.result()
# Przed: self._handle_task_result(folder, photo, result)
if result.get("success"):
    logger.debug(f"[FUTURE] Zakończono pomyślnie: {folder}/{photo}")
else:
    logger.warning(f"[FUTURE] Błąd przetwarzania: {folder}/{photo}: {result.get('error_msg')}")
```

### 6.4 `_update_source_worker()` — dodać czas operacji

**Dodać pomiar czasu:**

```python
def _update_source_worker(self) -> None:
    import time
    t0 = time.perf_counter()
    logger.debug("Cykliczne sprawdzanie source i integralności")
    try:
        # ... istniejący kod ...
        elapsed = time.perf_counter() - t0
        logger.debug(f"[UPDATE] Cykliczne sprawdzanie: {elapsed:.2f}s")
        # ... reszta
```

### 6.5 `_handle_task_result()` — istniejący log OK

`logger.debug(f"[PERF] Zdjęcie {folder}/{photo} przetworzone w {result['duration']:.4f}s")` — bez zmian.

### 6.6 `_mark_error_locked()` i `_mark_error()` — ujednolicić

**Zmienić format:**

```python
# PRZED:
logger.error(msg)

# PO:
logger.error(f"[ERROR] {folder}/{photo}: {msg}")
```

---

## 7. ZMIANY W bid/project_manager.py

### 7.1 `create_project()` — dodać info

**Dodać po utworzeniu folderu:**

```python
logger.info(f"[PROJECT] Tworzę projekt: '{name}' → {project_dir}")
```

### 7.2 `get_recent_projects()` — dodać liczbę

**Dodać przed return:**

```python
logger.debug(f"[PROJECT] Znaleziono {len(existing)} ostatnich projektów")
```

### 7.3 `get_project_details()` — dodać debug

**Dodać po odczytaniu details:**

```python
logger.debug(f"[PROJECT] Detale projektu {project_path}: {photo_count} zdjęć")
```

---

## 8. ZMIANY W bid/ui/

### 8.1 `details_panel.py` — DODAĆ logger

**Na początku pliku (brak loggera!):**

```python
import logging
logger = logging.getLogger("Yapa_CM")
```

**W `update_details()`:**

```python
logger.debug(f"[UI] Aktualizacja panelu dla: {folder}/{photo}")
```

### 8.2 `preview.py` — istniejące logi OK

`logger.error(...)` — bez zmian.

### 8.3 `source_tree.py` — istniejące logi OK

`logger.debug(...)` i `logger.warning(...)` — bez zmian.

### 8.4 `project_selector.py` — DODAĆ logi selekcji

**W `_on_open_selected()`:**

```python
logger.info(f"[UI] Wybrano projekt: {self.selected_project}")
```

**W `_on_browse()`:**

```python
logger.info(f"[UI] Przeglądanie projektu z: {path}")
```

### 8.5 `setup_wizard.py` — istniejące logi OK

`logger.info(f"Utworzono projekt: ...")` — bez zmian.

---

## 9. PODSUMOWANIE DODANYCH LOGÓW

### Nowe logi wg modułu

| Moduł | Nowe logi | Zmienione logi | Razem |
|-------|-----------|----------------|-------|
| `bid/logging_config.py` | NOWY MODUŁ | — | — |
| `bid/image_processing.py` | ~15 | 2 | 17 |
| `bid/source_manager.py` | ~6 | 0 | 6 |
| `bid/config.py` | 1 | 1 | 2 |
| `bid/app.py` | ~6 | 2 | 8 |
| `bid/project_manager.py` | 3 | 0 | 3 |
| `bid/ui/details_panel.py` | 2 (+ import) | 0 | 2 |
| `bid/ui/project_selector.py` | 2 | 0 | 2 |
| `main.py` | 0 | 1 (refactor) | 1 |
| **RAZEM** | **~35** | **6** | **~41** |

### Prefiksy logów (do wyszukiwania w testach)

| Prefiks | Moduł | Cel |
|---------|-------|-----|
| `[PROCESS]` | image_processing | Cykl przetwarzania zdjęcia |
| `[EXIF]` | image_processing, source_manager | Ekstrakcja metadanych |
| `[SOURCE]` | source_manager | Skanowanie i aktualizacja dict |
| `[INTEGRITY]` | source_manager | Sprawdzanie integralności |
| `[CONFIG]` | config | Ładowanie konfiguracji |
| `[APP]` | app | Inicjalizacja aplikacji |
| `[SCAN]` | app | Kolejkowanie eksportów |
| `[FUTURE]` | app | Wyniki ProcessPoolExecutor |
| `[UPDATE]` | app | Cykliczne skanowanie |
| `[ERROR]` | app | Błędy przetwarzania |
| `[PROJECT]` | project_manager | Zarządzanie projektami |
| `[UI]` | bid/ui/* | Interakcje UI |

### Wzorzec wyszukiwania w testach

```python
# Sprawdź że zdjęcie zostało przetworzone:
assert log_capture.has("[PROCESS] Zakończono:", level="INFO")

# Sprawdź że eksport fb został zapisany:
assert log_capture.has("[PROCESS] Eksport 'fb' zapisany:", level="INFO")

# Sprawdź że skanowanie znalazło pliki:
assert log_capture.has("[SOURCE] Skanowanie zakończone:", level="INFO")

# Sprawdź że nie było błędów:
assert not log_capture.at_level("ERROR")

# Sprawdź sekwencję operacji:
log_capture.assert_sequence(
    "[PROCESS] Start:",
    "[PROCESS] Eksport 'fb' zapisany:",
    "[PROCESS] Zakończono:",
)
```

---

### Warunki akceptacji

1. ✅ Wszystkie nowe logi używają prefiksów z tabeli powyżej
2. ✅ Żaden istniejący log nie został usunięty (tylko zmieniony format)
3. ✅ `bid/logging_config.py` umożliwia testom konfigurację bez `main.py`
4. ✅ `pytest tests/ -x` przechodzi bez błędów po zmianach
5. ✅ Logi generowane w formacie: `YYYY-MM-DDThh:mm:ss | LEVEL   : [PREFIX] message`

---

*Koniec dokumentu instrumentacji logów. Implementacja krok-po-kroku → patrz `IMPLEMENTATION_GUIDE.md`.*
