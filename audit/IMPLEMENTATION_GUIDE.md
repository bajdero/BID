# PRZEWODNIK IMPLEMENTACJI — YAPA/BID

**Cel:** Krok-po-kroku instrukcje dla agenta AI implementującego zmiany.  
**Kolejność:** Fazy 1→2→3→4→5→6 — każda zależy od poprzedniej.  
**Zasada:** Żadna faza nie zmienia zachowania aplikacji — tylko dodaje infrastrukturę i testy.

---

## SPIS TREŚCI

1. [Kontekst projektu](#kontekst-projektu)
2. [Faza 1: Infrastruktura testowa](#faza-1-infrastruktura-testowa)
3. [Faza 2: Testy jednostkowe](#faza-2-testy-jednostkowe)
4. [Faza 3: Testy integracyjne](#faza-3-testy-integracyjne)
5. [Faza 4: Testy E2E i regresji](#faza-4-testy-e2e-i-regresji)
6. [Faza 5: Naprawy bugów i wydajność](#faza-5-naprawy-bugów-i-wydajność)
7. [Faza 6: UI/UX i przygotowanie Docker](#faza-6-uiux-i-przygotowanie-docker)
8. [Warunki akceptacji per faza](#warunki-akceptacji-per-faza)
9. [Pliki referencyjne](#pliki-referencyjne)

---

## KONTEKST PROJEKTU

### Architektura
- **Desktop app** z Tkinter (Python 3.10+)
- **Jedyna zależność:** Pillow>=10.0.0
- **Logger:** `Yapa_CM` (nazwa we wszystkich modułach)
- **Środowisko:** Windows + Linux, dyski sieciowe SMB/UNC
- **Typowy projekt:** 200-1000 zdjęć po ~15MB (JPEG + RAW)

### Struktura plików
```
bid/
├── __init__.py
├── app.py               ← MainApp(tk.Tk), ProcessPoolExecutor, threading
├── config.py             ← load_settings(), load_export_options()
├── image_processing.py   ← process_photo_task(), EXIF, watermark, resize
├── project_manager.py    ← ProjectManager (create/recent/prune)
├── source_manager.py     ← source_dict CRUD, integrity check
└── ui/
    ├── details_panel.py  ← DetailsPanel (EXIF/export display)
    ├── preview.py        ← PrevWindow (canvas Image preview)
    ├── project_selector.py ← ProjectSelector (splash screen)
    ├── setup_wizard.py   ← SetupWizard (new project)
    └── source_tree.py    ← SourceTree (Treeview file list)
```

### Istniejące testy
```
tests/
├── conftest.py                 ← fixtures: temp_dir, sample_project, sample_image
├── test_image_processing.py    ← 7 testów (2 passing, 1 xfail, 4 nowe)
├── test_source_manager.py      ← 4 testy
└── test_project_manager.py     ← 5 testów
```

---

## FAZA 1: INFRASTRUKTURA TESTOWA

### Cel
Dodać moduły pomocnicze + instrumentację logów BEZ zmiany zachowania aplikacji.

### Krok 1.1: Nowe moduły

**Utworzyć plik `bid/logging_config.py`:**
- Patrz: `LOGGING_INSTRUMENTATION.md` sekcja 1
- Wydzielenie konfiguracji loggera z main.py
- Funkcje: `setup_logger()`, `get_logger()`
- Testy: import `setup_logger` zamiast konfiguracji w main.py

**Utworzyć plik `bid/errors.py`:**
```python
"""bid/errors.py — Hierarchia wyjątków YAPA/BID."""

class YapaError(Exception):
    """Bazowy wyjątek dla wszystkich błędów YAPA."""
    pass

class ConfigError(YapaError):
    """Błąd ładowania/walidacji konfiguracji."""
    pass

class ImageProcessingError(YapaError):
    """Błąd przetwarzania obrazu."""
    pass

class SourceManagerError(YapaError):
    """Błąd zarządzania słownikiem źródeł."""
    pass

class ProjectError(YapaError):
    """Błąd operacji na projekcie."""
    pass
```

**Utworzyć plik `bid/validators.py`:**
```python
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
```

### Krok 1.2: Refaktor main.py

W `main.py`, zastąpić ciało `_setup_logging()`:

```python
def _setup_logging(level: int = logging.INFO) -> None:
    from bid.logging_config import setup_logger
    setup_logger(level=level)
```

### Krok 1.3: Instrumentacja logów

Zastosować WSZYSTKIE zmiany z `LOGGING_INSTRUMENTATION.md`:
- `bid/image_processing.py` — ~15 nowych logów z prefiksem `[PROCESS]`
- `bid/source_manager.py` — ~6 nowych logów z prefiksami `[SOURCE]`, `[INTEGRITY]`
- `bid/config.py` — 2 zmiany z prefiksem `[CONFIG]`
- `bid/app.py` — ~6 nowych logów z prefiksami `[APP]`, `[SCAN]`, `[FUTURE]`, `[UPDATE]`
- `bid/project_manager.py` — 3 nowe logi z prefiksem `[PROJECT]`
- `bid/ui/details_panel.py` — dodać import logging + logger + 1 log
- `bid/ui/project_selector.py` — 2 nowe logi

### Krok 1.4: Rozszerzenie conftest.py

Dodać do `tests/conftest.py`:
- Fixture `log_capture` z klasą `LogCaptureHelper`
- Fixture `export_settings_fb`
- Fixture `export_settings_multi`
- Fixture `sample_image_with_exif`
- Fixture `sample_logo`
- Fixture `full_test_project`

Patrz: `TEST_SPECIFICATION.md` sekcja 3 dla pełnego kodu.

### Krok 1.5: Weryfikacja

```bash
# Uruchomić istniejące testy — MUSZĄ przechodzić
pytest tests/ -x -v

# Sprawdzić import nowych modułów
python -c "from bid.logging_config import setup_logger; print('OK')"
python -c "from bid.errors import YapaError; print('OK')"
python -c "from bid.validators import validate_export_profile; print('OK')"
```

---

## FAZA 2: TESTY JEDNOSTKOWE

### Cel
Napisać 55 testów jednostkowych pokrywających core functions.

### Krok 2.1: Rozszerzyć test_image_processing.py

Dodać testy TEST-IP-001 do TEST-IP-022 z `TEST_SPECIFICATION.md` sekcja 4.

**Kluczowe wzorce:**

```python
import logging
from bid.image_processing import (
    image_resize, image_convert_to_srgb, apply_watermark,
    process_photo_task, get_all_exif, exif_clean_from_tiff, get_logo
)

def test_image_resize_landscape_longer(log_capture):
    img = Image.new("RGB", (2000, 1500))
    result = image_resize(img, longer_side=1000, method="longer")
    assert result.size == (1000, 750)
    assert log_capture.has("Skaluję zdjęcie", level="DEBUG")

def test_process_photo_task_success_jpeg(
    log_capture, sample_image_with_exif, sample_logo, tmp_path, export_settings_fb
):
    export_dir = tmp_path / "export"
    export_dir.mkdir()
    (export_dir / "fb").mkdir()
    
    result = process_photo_task(
        photo_path=str(sample_image_with_exif),
        folder_name="session1",
        photo_name="test_exif.jpg",
        created_date="2026:03:09 14:30:00",
        export_folder=str(export_dir),
        export_settings=export_settings_fb,
        existing_exports={},
    )
    
    assert result["success"] is True
    assert "fb" in result["exported"]
    assert result["duration"] > 0
    assert log_capture.has("[PROCESS] Start:")
    assert log_capture.has("[PROCESS] Zakończono:")
```

### Krok 2.2: Utworzyć test_config.py

Nowy plik z testami TEST-CFG-001 do TEST-CFG-009.

```python
import json
import pytest
from pathlib import Path
from bid.config import load_settings, load_export_options

def test_load_settings_valid(log_capture, tmp_path):
    settings = {"source_folder": "/tmp/src", "export_folder": "/tmp/exp"}
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(settings), encoding="utf-8")
    
    result = load_settings(path)
    assert result["source_folder"] == "/tmp/src"
    assert log_capture.has("Loaded config:", level="DEBUG")

def test_load_settings_missing_file(log_capture):
    with pytest.raises(SystemExit):
        load_settings(Path("/tmp/nonexistent_xyz_settings.json"))
    assert log_capture.has("Config file not found:", level="CRITICAL")
```

### Krok 2.3: Rozszerzyć test_source_manager.py

Dodać testy TEST-SM-001 do TEST-SM-016 + weryfikację logów.

### Krok 2.4: Rozszerzyć test_project_manager.py

Dodać testy TEST-PM-005 do TEST-PM-008 + weryfikację logów w istniejących testach.

### Krok 2.5: Utworzyć test_validators.py (opcjonalnie)

```python
from bid.validators import validate_export_profile, validate_source_export_different

def test_validate_complete_profile():
    profile = {
        "size_type": "longer", "size": 1200, "format": "JPEG",
        "quality": 85, "logo": {"landscape": {}, "portrait": {}}
    }
    assert validate_export_profile("fb", profile) == []

def test_validate_missing_size():
    profile = {"size_type": "longer", "format": "JPEG", "quality": 85, "logo": {}}
    errors = validate_export_profile("fb", profile)
    assert any("size" in e for e in errors)
```

### Krok 2.6: Weryfikacja

```bash
pytest tests/ -x -v --log-cli-level=DEBUG
# Oczekiwany wynik: 55+ testów passing (z uwzględnieniem istniejących)
```

---

## FAZA 3: TESTY INTEGRACYJNE

### Cel
25 testów weryfikujących interakcje między modułami.

### Krok 3.1: Utworzyć test_workflows.py

Testy TEST-WF-001 do TEST-WF-006 — pełny workflow przetwarzania.

**Kluczowy test:**

```python
def test_single_photo_full_export(log_capture, full_test_project):
    """Przetworzenie 1 zdjęcia → 1 profil → eksport na dysku."""
    p = full_test_project
    photos = list((p["session_dir"]).glob("photo_*.jpg"))
    
    from bid.image_processing import process_photo_task
    result = process_photo_task(
        photo_path=str(photos[0]),
        folder_name="session1",
        photo_name=photos[0].name,
        created_date="2026:03:09 14:30:00",
        export_folder=str(p["export_dir"]),
        export_settings=p["export_settings"],
        existing_exports={},
    )
    
    assert result["success"] is True
    assert Path(result["exported"]["fb"]).exists()
    
    # Weryfikacja logów
    log_capture.assert_sequence(
        "[PROCESS] Start:",
        "[PROCESS] Eksport 'fb' zapisany:",
        "[PROCESS] Zakończono:",
    )
```

### Krok 3.2: Utworzyć test_integrity.py

Testy TEST-INT-001 do TEST-INT-004 — cykl create→update→check.

### Krok 3.3: Utworzyć test_config_processing.py

Testy TEST-CP-001 do TEST-CP-004 — config kieruje eksportem.

### Krok 3.4: Weryfikacja

```bash
pytest tests/test_workflows.py tests/test_integrity.py tests/test_config_processing.py -x -v
```

---

## FAZA 4: TESTY E2E I REGRESJI

### Cel
9 testów end-to-end + regresje dla znanych bugów.

### Krok 4.1: Utworzyć test_e2e.py

Testy TEST-E2E-001 do TEST-E2E-004.

### Krok 4.2: Utworzyć test_regressions.py

Testy TEST-REG-001 do TEST-REG-005.

**Kluczowy test regresji (BUG-002):**

```python
import threading

def test_source_dict_no_corruption_under_load(log_capture, full_test_project):
    """Regresja BUG-002: race condition w source_dict."""
    from bid.source_manager import create_source_dict, SourceState
    
    sd = create_source_dict(
        str(full_test_project["source_dir"]),
        str(full_test_project["export_dir"]),
        full_test_project["export_settings"],
    )
    
    errors = []
    lock = threading.Lock()  # Symulacja dict_lock z app.py
    
    def modify_entry(folder, photo, new_state):
        try:
            with lock:
                sd[folder][photo]["state"] = new_state
        except Exception as e:
            errors.append(str(e))
    
    threads = []
    for folder in sd:
        for photo in sd[folder]:
            for state in [SourceState.PROCESSING, SourceState.OK, SourceState.NEW]:
                t = threading.Thread(target=modify_entry, args=(folder, photo, state))
                threads.append(t)
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    assert not errors, f"Race condition detected: {errors}"
    # Sprawdź że dict jest spójny
    for folder in sd:
        for photo in sd[folder]:
            assert "state" in sd[folder][photo]
```

### Krok 4.3: Weryfikacja kompletna

```bash
# Pełny suite
pytest tests/ -x -v --log-cli-level=INFO

# Coverage
pytest tests/ --cov=bid --cov-report=term-missing
# Oczekiwany coverage: >70% dla image_processing, config, source_manager, project_manager
```

---

## FAZA 5: NAPRAWY BUGÓW I WYDAJNOŚĆ

### Cel
Naprawić krytyczne bugi z `AUDIT_REPORT.md` sekcja 3.

### Krok 5.1: BUG-001 — Blokowanie UI na sieci

**Pliki:** `bid/app.py`, `bid/source_manager.py`

Zmiany:
1. W `MainApp.__init__()` — przenieść `create_source_dict()` do wątku tła
2. Dodać `ttk.Progressbar` + etykietę postępu skanowania
3. Dodać `threading.Event` do komunikacji wątek→UI
4. W `source_manager.py` — dodać callback progress per plik

**Wzorzec:**

```python
# W app.py __init__():
self.scan_progress = ttk.Progressbar(...)
self.scan_thread = threading.Thread(
    target=self._initial_scan_worker, daemon=True
)
self.scan_thread.start()
self._poll_scan_progress()

def _initial_scan_worker(self):
    """Wątek tła: skanowanie source przy starcie."""
    if saved is not None:
        self.source_dict = saved
        self.source_dict, _ = update_source_dict(...)
    else:
        self.source_dict = create_source_dict(...)
    save_source_dict(...)
    self._scan_complete.set()

def _poll_scan_progress(self):
    """Główny wątek: sprawdza postęp co 100ms."""
    if self._scan_complete.is_set():
        self.source_tree.update_tree(self.source_dict)
        self.scan_photos()
    else:
        self.after(100, self._poll_scan_progress)
```

### Krok 5.2: BUG-002 — Race condition

**Plik:** `bid/app.py`

Zmiany:
1. Zamienić `threading.Lock()` na `threading.RLock()`
2. Dodać `with self.dict_lock:` do `_mark_error()`
3. Usunąć duplikację `_mark_error`/`_mark_error_locked` — jedna metoda

```python
# PRZED:
self.dict_lock = threading.Lock()

# PO:
self.dict_lock = threading.RLock()

# PRZED:
def _mark_error(self, folder, photo, msg):
    logger.error(...)
    self.source_dict[folder][photo]["state"] = SourceState.ERROR
    ...

# PO:
def _mark_error(self, folder, photo, msg):
    with self.dict_lock:
        logger.error(f"[ERROR] {folder}/{photo}: {msg}")
        self.source_dict[folder][photo]["state"] = SourceState.ERROR
        self.source_dict[folder][photo]["error_msg"] = msg
        self.source_tree.change_tag(folder, photo, SourceState.ERROR)
        save_source_dict(self.source_dict, self.project_path)
```

### Krok 5.3: BUG-003 — Cicha awaria watermarku

**Plik:** `bid/image_processing.py`, `bid/app.py`

Zmiany:
1. W `process_photo_task()` sprawdź logo PRZED pętlą eksportu:

```python
# Na początku pętli, przed for deliver:
logo_path = os.path.join(os.path.dirname(photo_path), "logo.png")
if not os.path.isfile(logo_path):
    logger.warning(f"[PROCESS] BRAK LOGO: {folder_name} — eksport bez watermarku")
```

2. W `MainApp.__init__()` — sprawdź logo we wszystkich folderach:

```python
# Po załadowaniu source_dict:
for folder in self.source_dict:
    folder_path = os.path.join(self.source_folder, folder)
    if not os.path.isfile(os.path.join(folder_path, "logo.png")):
        logger.warning(f"BRAK logo.png w folderze: {folder}")
        # Opcjonalnie: messagebox.showwarning(...)
```

### Krok 5.4: BUG-004 — Timeout przetwarzania

**Plik:** `bid/app.py`

```python
# W check_futures(), zamienić:
result = future.result()

# Na:
try:
    result = future.result(timeout=0)  # Non-blocking, bo sprawdzamy done()
except TimeoutError:
    pass  # Nie powinno wystąpić bo sprawdzamy done() wcześniej
```

Oraz dodać globalny timeout w `_submit_photo_task_locked`:
```python
# Dodać timer sprawdzający stare futures:
def _check_stale_futures(self):
    """Sprawdza futures starsze niż 120s i oznacza jako timeout."""
    now = time.time()
    for future, (folder, photo) in list(self.active_scanning.items()):
        # Potrzebujemy pamiętać czas submitu — dodać do tracking dict
        ...
```

### Krok 5.5: PERF-005 — Za dużo workerów

**Plik:** `bid/app.py`

```python
# PRZED:
self.max_workers: int = os.cpu_count() or 4

# PO:
default_workers = min(os.cpu_count() or 4, 3)  # Max 3 dla dysków sieciowych
self.max_workers: int = self.settings.get("max_workers", default_workers)
```

### Krok 5.6: Weryfikacja

```bash
# Uruchomić testy regresji
pytest tests/test_regressions.py -x -v

# Uruchomić pełny suite
pytest tests/ -x -v
```

---

## FAZA 6: UI/UX I PRZYGOTOWANIE DOCKER

### Cel
Poprawki UI na event 2026 + przygotowanie pod migrację web 2027.

### Krok 6.1: Centralizacja stylów

**Utworzyć `bid/ui/theme.py`:**

```python
"""bid/ui/theme.py — Centralna paleta kolorów i styli."""

COLORS = {
    "bg_dark": "#1e1e1e",
    "bg_medium": "#2d2d2d",
    "bg_light": "#3c3c3c",
    "fg_primary": "#d4d4d4",
    "fg_secondary": "#888888",
    "accent": "#1e3a5f",
    "accent_hover": "#2a5286",
    "success": "#4caf50",
    "warning": "#ff9800",
    "error": "#f44336",
    "info": "#2196f3",
    # Status tags
    "tag_new": "#e0e0e0",
    "tag_processing": "#87ceeb",
    "tag_ok": "#98fb98",
    "tag_ok_old": "#c8e6c9",
    "tag_error": "#ff7f50",
    "tag_deleted": "#d0d0d0",
    "tag_skip": "#ffebee",
}

FONTS = {
    "header": ("Segoe UI", 14, "bold"),
    "subheader": ("Segoe UI", 10, "bold"),
    "body": ("Segoe UI", 9),
    "mono": ("Consolas", 9),
    "status": ("Segoe UI", 9, "italic"),
}
```

### Krok 6.2: Komunikaty błędów

Dodać do `bid/app.py` helper:

```python
def _show_user_error(self, title: str, message: str):
    """Wyświetla błąd użytkownikowi i loguje."""
    logger.error(f"[UI] {title}: {message}")
    messagebox.showerror(title, message)

def _show_user_warning(self, title: str, message: str):
    """Wyświetla ostrzeżenie użytkownikowi i loguje."""
    logger.warning(f"[UI] {title}: {message}")
    messagebox.showwarning(title, message)
```

### Krok 6.3: MVC prep (przygotowanie na Docker)

Wydzielić logikę biznesową z `bid/app.py`:

**Utworzyć `bid/core/__init__.py` + `bid/core/processor.py`:**

```python
"""bid/core/processor.py — Logika przetwarzania bez zależności od Tkinter."""

class BatchProcessor:
    """Orkiestracja przetwarzania batch zdjęć."""
    
    def __init__(self, source_dict, export_settings, export_folder, max_workers=3):
        self.source_dict = source_dict
        self.export_settings = export_settings
        self.export_folder = export_folder
        self.max_workers = max_workers
    
    def process_new_photos(self, progress_callback=None):
        """Przetwarza wszystkie nowe zdjęcia."""
        ...
    
    def get_status(self) -> dict:
        """Zwraca aktualny status przetwarzania."""
        ...
```

To przygotowuje pod przyszły `bid/web/app.py` (Flask/FastAPI) który użyje tego samego core.

---

## WARUNKI AKCEPTACJI PER FAZA

### Faza 1 ✓
- [ ] `bid/logging_config.py` istnieje i eksportuje `setup_logger()`
- [ ] `bid/errors.py` istnieje z hierarchią YapaError
- [ ] `bid/validators.py` istnieje z `validate_export_profile()`
- [ ] Wszystkie logi z `LOGGING_INSTRUMENTATION.md` dodane
- [ ] `main.py` deleguje do `bid/logging_config.py`
- [ ] `tests/conftest.py` rozszerzony o nowe fixtures
- [ ] `pytest tests/ -x` → 0 failures (istniejące testy passing)

### Faza 2 ✓
- [ ] 55+ nowych/rozszerzonych testów jednostkowych
- [ ] Nowy plik `tests/test_config.py`
- [ ] Nowy plik `tests/test_validators.py`
- [ ] Testy weryfikują logi (fixture log_capture)
- [ ] `pytest tests/ -x -v` → 0 failures

### Faza 3 ✓
- [ ] Nowe pliki: `test_workflows.py`, `test_integrity.py`, `test_config_processing.py`
- [ ] 14+ testów integracyjnych
- [ ] Testy weryfikują sekwencje logów (`assert_sequence`)
- [ ] `pytest tests/ -x -v` → 0 failures

### Faza 4 ✓
- [ ] Nowe pliki: `test_e2e.py`, `test_regressions.py`
- [ ] 9+ testów E2E i regresji
- [ ] Coverage > 70% dla modułów core (image_processing, config, source_manager)
- [ ] `pytest tests/ --cov=bid --cov-report=term-missing` → raport

### Faza 5 ✓
- [ ] BUG-001: UI nie blokuje się przy skanowaniu (progress bar widoczny)
- [ ] BUG-002: Brak race condition (RLock, jedna _mark_error)
- [ ] BUG-003: Ostrzeżenie o brakującym logo (log + opcjonalnie messagebox)
- [ ] PERF-005: max_workers konfigurowalny (domyślnie ≤3)
- [ ] Testy regresji nadal passing

### Faza 6 ✓
- [ ] `bid/ui/theme.py` z centralną paletą
- [ ] Hardcoded kolory w UI zamienione na COLORS[]
- [ ] `bid/core/processor.py` — logika bez Tkinter
- [ ] Helper `_show_user_error()` w app.py
- [ ] Testy nadal passing

---

## PLIKI REFERENCYJNE

| Dokument | Cel | Kiedy używać |
|----------|-----|-------------|
| `audit/AUDIT_REPORT.md` | Lista bugów, wydajności, UI/UX | Kontekst i priorytety |
| `audit/TEST_SPECIFICATION.md` | Definicje 78 testów | Implementacja testów (Fazy 2-4) |
| `audit/LOGGING_INSTRUMENTATION.md` | Dokładne logi do dodania | Faza 1 |
| `audit/IMPLEMENTATION_GUIDE.md` | Ten dokument | Plan implementacji |
| `audit/PHASE_PROMPTS.md` | Prompty dla agentów AI | Delegacja do agentów |

---

*Koniec przewodnika. Prompty dla agentów AI → patrz `PHASE_PROMPTS.md`.*
