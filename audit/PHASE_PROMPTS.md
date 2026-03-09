# PROMPTY DLA AGENTÓW AI — YAPA/BID

**Cel:** Gotowe prompty do skopiowania i wklejenia dla agenta AI implementującego kolejne fazy.  
**Zasada:** Każdy prompt zawiera pełny kontekst — agent nie musi czytać innych dokumentów.  
**Język:** Angielski (prompty) z polskimi komentarzami w kodzie.

---

## SPIS TREŚCI

1. [Prompt: Faza 1 — Infrastruktura testowa](#prompt-faza-1)
2. [Prompt: Faza 2 — Testy jednostkowe](#prompt-faza-2)
3. [Prompt: Faza 3 — Testy integracyjne](#prompt-faza-3)
4. [Prompt: Faza 4 — E2E + regresje](#prompt-faza-4)
5. [Prompt: Faza 5 — Naprawy bugów](#prompt-faza-5)
6. [Prompt: Faza 6 — UI/UX + Docker prep](#prompt-faza-6)

---

## PROMPT: FAZA 1

```markdown
# TASK: Add logging infrastructure and test fixtures to YAPA/BID

You are implementing Phase 1 of the YAPA/BID automated testing preparation.
This is a Tkinter-based desktop app for batch image processing (Python 3.10+, Pillow dependency).

## GOAL
Add logging instrumentation and create helper modules for testability.
**ALL changes are NON-BREAKING.** No application behavior changes allowed.

## CONTEXT
- Logger name: "Yapa_CM" (used in all modules)
- Framework: Tkinter + Pillow
- Existing tests in tests/ must continue passing
- Code comments are in Polish — preserve the language

## MUST COMPLETE (in order):

### 1. Create `bid/logging_config.py`
New module that centralizes logger setup. Read `audit/LOGGING_INSTRUMENTATION.md` section 1 for exact code.
- Function `setup_logger(level, log_dir, console, file) -> Logger`
- Function `get_logger() -> Logger`
- Must be importable without starting the app

### 2. Create `bid/errors.py`
Custom exception hierarchy. Read `audit/IMPLEMENTATION_GUIDE.md` Krok 1.1 for exact code.
- YapaError (base), ConfigError, ImageProcessingError, SourceManagerError, ProjectError

### 3. Create `bid/validators.py`
Input validation functions. Read `audit/IMPLEMENTATION_GUIDE.md` Krok 1.1 for exact code.
- validate_export_profile(name, profile) -> list[str]
- validate_path_exists(path, label) -> str | None
- validate_source_export_different(source, export) -> str | None

### 4. Refactor `main.py` _setup_logging()
Replace the function body to delegate to bid/logging_config.setup_logger().
Keep the function signature unchanged. See `audit/LOGGING_INSTRUMENTATION.md` section 2.

### 5. Add logging instrumentation
Apply ALL changes from `audit/LOGGING_INSTRUMENTATION.md` sections 3-8:
- bid/image_processing.py: ~15 new logger calls with [PROCESS] prefix
- bid/source_manager.py: ~6 new logger calls with [SOURCE], [INTEGRITY] prefixes
- bid/config.py: 2 changes with [CONFIG] prefix
- bid/app.py: ~6 new logger calls with [APP], [SCAN], [FUTURE], [UPDATE] prefixes
- bid/project_manager.py: 3 new logger calls with [PROJECT] prefix
- bid/ui/details_panel.py: Add `import logging` + logger + 1 debug log
- bid/ui/project_selector.py: 2 new logger calls with [UI] prefix

IMPORTANT: Do NOT remove or delete any existing logger calls. Only ADD new ones or MODIFY format of existing ones as specified.

### 6. Extend `tests/conftest.py`
Add these fixtures to the EXISTING file (do not overwrite existing fixtures):
- `log_capture(caplog)` — with LogCaptureHelper class (has(), count(), at_level(), assert_sequence())
- `export_settings_fb()` — single FB export profile dict
- `export_settings_multi()` — FB + Insta profiles dict
- `sample_image_with_exif(tmp_path)` — 2000x1500 JPEG with EXIF tags
- `sample_logo(tmp_path)` — 600x200 RGBA PNG
- `full_test_project(tmp_path, export_settings_fb)` — complete project with images + logo

Read `audit/TEST_SPECIFICATION.md` section 3 for exact fixture code.

## DO NOT:
- Change any application behavior or user-facing logic
- Add new features or UI changes
- Remove existing code (only add/modify)
- Break existing tests
- Touch files not mentioned above

## VERIFICATION:
Run after all changes:
```bash
pytest tests/ -x -v
python -c "from bid.logging_config import setup_logger; print('OK')"
python -c "from bid.errors import YapaError; print('OK')"
python -c "from bid.validators import validate_export_profile; print('OK')"
```
All existing tests must pass with 0 failures.
```

---

## PROMPT: FAZA 2

```markdown
# TASK: Write unit tests for YAPA/BID core modules

You are implementing Phase 2 of YAPA/BID automated testing.
Phase 1 (logging infrastructure) is already complete.

## GOAL
Write 55+ unit tests covering all core functions. Tests verify behavior via:
1. Return values and side effects
2. Logger output (using `log_capture` fixture from conftest.py)
3. File creation/modification

## CONTEXT
- Test framework: pytest
- Logger name: "Yapa_CM"  
- Log prefixes: [PROCESS], [SOURCE], [INTEGRITY], [CONFIG], [PROJECT], [EXIF]
- Fixture `log_capture` provides: .has(substring, level), .count(substring), .at_level(level), .assert_sequence(*substrings)
- All log messages contain context (filename, profile name, dimensions, duration)
- Code and test descriptions in Polish

## FILE: tests/test_image_processing.py (EXTEND existing file)

Add these tests (see `audit/TEST_SPECIFICATION.md` section 4 for details):
- test_image_resize_landscape_longer — 2000x1500 → 1000px → 1000x750
- test_image_resize_portrait_longer — 1500x2000 → 1000px → 750x1000
- test_image_resize_width_method — 2000x1500 → width=800
- test_image_resize_height_method — 2000x1500 → height=600
- test_image_resize_square_input — 1000x1000 → 500px
- test_image_resize_already_smaller — 500x300 with target 1000 (check behavior)
- test_srgb_conversion_no_profile — RGB without ICC → same image
- test_srgb_conversion_with_profile — RGB with ICC → sRGB converted
- test_watermark_applied_correct_position — 2000x1500 + logo → pixels differ at bottom-right
- test_watermark_opacity_range — opacity 100 vs 10 → different pixel intensity
- test_watermark_missing_logo_file — nonexistent path → FileNotFoundError or handled
- test_exif_clean_preserves_mandatory — Make, Model preserved; TIFF tags removed
- test_get_all_exif_datetime_extracted — JPEG with DateTime → extracted correctly
- test_get_all_exif_camera_info — JPEG with Make/Model → extracted
- test_get_all_exif_blacklisted_tags_excluded — GPS/ExifIFD pointers not in result
- test_process_photo_task_success_jpeg — full export → success, file exists, logs
- test_process_photo_task_success_png — PNG export → .png file
- test_process_photo_task_with_watermark — logo exists → watermark in export
- test_process_photo_task_missing_source — nonexistent file → success=False
- test_process_photo_task_returns_duration — duration > 0 and is float
- test_get_logo_caching — 3 calls same path → cache miss log only once

Each test MUST use `log_capture` fixture and verify at least one log message.

## FILE: tests/test_config.py (NEW file)

Create with tests (see `audit/TEST_SPECIFICATION.md` section 5):
- test_load_settings_valid
- test_load_settings_missing_file
- test_load_settings_invalid_json
- test_load_export_options_valid
- test_load_export_options_empty
- test_load_export_options_missing_file
- test_validate_export_profile_valid (uses bid.validators)
- test_validate_export_profile_missing_size
- test_validate_export_profile_invalid_ratio

## FILE: tests/test_source_manager.py (EXTEND existing file)

Add tests (see `audit/TEST_SPECIFICATION.md` section 6):
- test_create_source_dict_excludes_logo
- test_create_source_dict_multiple_formats (if applicable)
- test_create_source_dict_nested_folders
- test_create_source_dict_all_states_new
- test_update_source_dict_new_folder
- test_update_source_dict_no_changes
- test_check_integrity_missing_export
- test_check_integrity_all_ok
- test_save_load_source_dict_roundtrip
- test_load_source_dict_corrupted_json
- test_read_metadata_with_exif
- test_read_metadata_fallback_mtime
- Add log verification to existing 4 tests

## FILE: tests/test_project_manager.py (EXTEND existing file)

Add tests (see `audit/TEST_SPECIFICATION.md` section 7):
- test_get_project_details_with_source_dict
- test_get_project_details_no_source_dict
- test_recent_projects_max_10
- test_create_project_spaces_in_name
- Add log verification to existing 5 tests

## FILE: tests/test_validators.py (NEW file, optional)

Tests for bid/validators.py functions.

## PATTERNS TO FOLLOW:

```python
import logging
import pytest
from PIL import Image

def test_example(log_capture, sample_image_with_exif, tmp_path):
    from bid.image_processing import process_photo_task
    
    result = process_photo_task(...)
    
    # 1. Assert return value
    assert result["success"] is True
    
    # 2. Assert log output
    assert log_capture.has("[PROCESS] Start:", level="INFO")
    assert not log_capture.at_level("ERROR")
    
    # 3. Assert side effects
    assert Path(result["exported"]["fb"]).exists()
```

## DO NOT:
- Modify source code (bid/*.py) — only test files
- Skip log assertions — every test must verify at least 1 log
- Use mocks for file I/O in unit tests — use tmp_path fixtures instead
- Add Tkinter/UI tests (those are Phase 6)

## VERIFICATION:
```bash
pytest tests/ -x -v --log-cli-level=DEBUG
# Expected: 55+ tests, 0 failures
```
```

---

## PROMPT: FAZA 3

```markdown
# TASK: Write integration tests for YAPA/BID

You are implementing Phase 3 of YAPA/BID automated testing.
Phases 1-2 (infrastructure + unit tests) are complete.

## GOAL
Write 14+ integration tests verifying module interactions.

## CONTEXT
Same as Phase 2. All unit tests from Phase 2 are passing.

## FILES TO CREATE:

### tests/test_workflows.py (NEW)
6 tests verifying complete image processing workflow:
- test_single_photo_full_export — 1 photo → 1 profile → file on disk
- test_batch_3_photos_single_profile — 3 photos → 3 exports
- test_batch_multi_profile — 1 photo → 2 profiles (fb+insta) → 2 files
- test_export_preserves_exif_after_resize — EXIF round-trip verification
- test_export_creates_subfolder — auto-creates export/fb/ directory
- test_export_skip_existing — existing_exports not overwritten

Use `full_test_project` fixture. Each test uses log_capture.assert_sequence().

### tests/test_integrity.py (NEW)
4 tests verifying file system integrity:
- test_full_cycle_create_check_update — create → add files → update → check
- test_delete_then_readd_photo — delete → DELETED → re-add → NEW
- test_concurrent_dict_updates_thread_safe — 10 threads modifying dict
- test_save_load_preserves_unicode — Polish characters in paths

### tests/test_config_processing.py (NEW)
4 tests verifying config → processing interaction:
- test_config_drives_export_size — size from config → correct output dimensions
- test_config_jpeg_vs_png_format — JPEG → .jpg, PNG → .png
- test_config_with_ratio_filter — ratio filter excludes wrong aspect ratios
- test_missing_logo_exports_without_watermark — no logo.png → export without watermark

See `audit/TEST_SPECIFICATION.md` sections 8-10 for exact test definitions.

## VERIFICATION:
```bash
pytest tests/ -x -v
# Expected: 70+ tests total (55 unit + 14 integration), 0 failures
```
```

---

## PROMPT: FAZA 4

```markdown
# TASK: Write E2E and regression tests for YAPA/BID

You are implementing Phase 4 of YAPA/BID automated testing.
Phases 1-3 (infrastructure + unit + integration tests) are complete.

## GOAL
Write 9 tests: 4 end-to-end + 5 regression tests for known bugs.

## FILES TO CREATE:

### tests/test_e2e.py (NEW)
4 tests verifying complete application lifecycles:
- test_new_project_full_workflow — create project → scan → export → save
- test_reopen_project_incremental — load existing → add new → only process new
- test_error_recovery_workflow — 5 photos, 1 corrupted → 4 OK + 1 ERROR
- test_performance_100_images — 100 synthetic 200x150 images → all processed

### tests/test_regressions.py (NEW)
5 regression tests for bugs from audit/AUDIT_REPORT.md:
- test_watermark_always_applied_when_logo_exists (BUG-003)
- test_source_dict_no_corruption_under_load (BUG-002) — thread safety
- test_unicode_filenames_roundtrip — Polish chars in filenames
- test_unc_path_handling — Windows UNC paths (mock os.walk)
- test_export_option_with_all_format_types — JPEG + PNG formats

See `audit/TEST_SPECIFICATION.md` sections 11-12 for exact definitions.

## VERIFICATION:
```bash
pytest tests/ -x -v --log-cli-level=INFO
pytest tests/ --cov=bid --cov-report=term-missing
# Expected: 78+ tests, 0 failures, >70% coverage for core modules
```
```

---

## PROMPT: FAZA 5

```markdown
# TASK: Fix critical bugs in YAPA/BID

You are implementing Phase 5 — fixing bugs identified in the code audit.
Phases 1-4 (infrastructure + all tests) are complete.

## CONTEXT
- App runs on NETWORK DRIVES (SMB/CIFS, mapped drives, UNC paths)
- Typical project: 200-1000 photos, ~15MB each
- Event in March 2026 — changes must be stable and tested

## BUGS TO FIX (in priority order):

### BUG-001: UI freezes during file scanning (CRITICAL)
**Location:** bid/app.py MainApp.__init__(), bid/source_manager.py create_source_dict()
**Problem:** os.walk() + PIL.Image.open() for each file blocks the main thread. On network drive with 500 photos = 50s freeze.
**Fix:**
1. Move create_source_dict() and update_source_dict() calls in __init__() to a daemon thread
2. Add threading.Event() for scan completion signaling
3. Show ttk.Progressbar during scan (update via self.after())
4. UI stays responsive — user sees "Skanowanie: X/Y plików..."
See `audit/IMPLEMENTATION_GUIDE.md` Krok 5.1 for code pattern.

### BUG-002: Race condition in source_dict (HIGH)
**Location:** bid/app.py _mark_error() at line ~389
**Problem:** _mark_error() modifies source_dict WITHOUT dict_lock. Background thread also modifies dict.
**Fix:**
1. Change `threading.Lock()` to `threading.RLock()` (reentrant lock)
2. Merge _mark_error() and _mark_error_locked() into single method with `with self.dict_lock:`
3. All source_dict mutations must be inside lock
See `audit/IMPLEMENTATION_GUIDE.md` Krok 5.2.

### BUG-003: Silent watermark failure (MEDIUM)
**Location:** bid/image_processing.py process_photo_task()
**Problem:** When logo.png missing, exports are created without watermark — user unaware.
**Fix:**
1. Check logo existence BEFORE export loop in process_photo_task()
2. Log WARNING: "[PROCESS] BRAK LOGO: {folder} — eksport bez watermarku"
3. In MainApp.__init__(), check all folders for logo after loading source_dict
See `audit/IMPLEMENTATION_GUIDE.md` Krok 5.3.

### PERF-005: Too many workers for network drive (LOW)
**Location:** bid/app.py line ~126
**Problem:** `os.cpu_count() or 4` on 8-core machine = 8 concurrent writes to SMB = I/O bottleneck
**Fix:** `default_workers = min(os.cpu_count() or 4, 3)`, allow override via settings.json "max_workers" key.

## DO NOT:
- Break existing tests (run pytest after each change)
- Change the UI layout or add features
- Modify image processing logic (only add checks)
- Remove Polish comments or log messages

## VERIFICATION:
```bash
pytest tests/ -x -v
pytest tests/test_regressions.py -x -v  # Specific regression tests
```
```

---

## PROMPT: FAZA 6

```markdown
# TASK: UI/UX improvements and Docker prep for YAPA/BID

You are implementing Phase 6 — final improvements before the March 2026 event, plus architecture prep for Docker/web migration in 2027.

## CONTEXT
- Phases 1-5 complete (tests + bug fixes)
- This year: Tkinter stays. Next year: Docker + web UI
- App used once a year for a photo event

## MUST COMPLETE:

### 1. Create bid/ui/theme.py — centralized color palette
- Define COLORS dict and FONTS dict
- Replace hardcoded colors in: project_selector.py (#1e3a5f), setup_wizard.py (#1e3a5f, #f0f0f0)
- Replace hardcoded fonts in: details_panel.py ("Segoe UI", 10, "bold")

### 2. Add user-facing error messages
In bid/app.py, add helpers:
- _show_user_error(title, message) — messagebox.showerror + logger.error
- _show_user_warning(title, message) — messagebox.showwarning + logger.warning
Use these for: missing logo, invalid project, export failures

### 3. Create bid/core/__init__.py + bid/core/processor.py
Extract business logic from app.py into a Tkinter-free module:
- Class BatchProcessor with process_new_photos() and get_status()
- This will be reused by the future web API (Flask/FastAPI)
- Keep app.py as a thin UI adapter that delegates to BatchProcessor

### 4. Note integration points for future features
Add comments in code marking where future features plug in:
- bid/source_manager.py: `# FUTURE: event_matcher.py — match photos to time-based events from JSON`
- bid/image_processing.py: `# FUTURE: logo_generator.py — generate PNG from SVG template + creator name`
- bid/app.py: `# FUTURE: Docker/Web — replace MainApp with Flask/FastAPI routes`

## DO NOT:
- Rewrite the entire UI — only centralize colors/fonts
- Add web framework dependencies
- Implement the event matcher or logo generator (just add comments)
- Break existing tests

## VERIFICATION:
```bash
pytest tests/ -x -v
python -c "from bid.core.processor import BatchProcessor; print('OK')"
```
```

---

## WSKAZÓWKI DLA OPERATORA

### Jak używać tych promptów

1. **Skopiuj prompt** odpowiedniej fazy
2. **Wklej do nowego czatu** z agentem AI (np. GitHub Copilot Chat, Claude, GPT-4)
3. **Przekaż kontekst workspace** — agent powinien mieć dostęp do plików projektu
4. **Zweryfikuj wyniki** — uruchom polecenia z sekcji VERIFICATION
5. **Przejdź do następnej fazy** dopiero gdy obecna jest kompletna

### Kolejność jest WAŻNA

```
Faza 1 → Faza 2 → Faza 3 → Faza 4 → Faza 5 → Faza 6
  │          │         │         │         │         │
  │          │         │         │         │         └─ UI/UX + Docker prep
  │          │         │         │         └─ Bug fixes + performance
  │          │         │         └─ E2E + regression tests
  │          │         └─ Integration tests
  │          └─ Unit tests (55+)
  └─ Logging + fixtures + helpers (NON-BREAKING)
```

Fazy 5 i 6 mogą być zamienione kolejnością — ale obie wymagają Faz 1-4.

### Jeśli agent utknie

- Podaj mu ścieżkę do odpowiedniego pliku z `audit/`
- Agent powinien przeczytać `audit/TEST_SPECIFICATION.md` dla dokładnych definicji testów
- Agent powinien przeczytać `audit/LOGGING_INSTRUMENTATION.md` dla dokładnych logów
- Przypomnij: "Read audit/IMPLEMENTATION_GUIDE.md for step-by-step instructions"

---

*Koniec dokumentu promptów. Gotowe do implementacji.*
