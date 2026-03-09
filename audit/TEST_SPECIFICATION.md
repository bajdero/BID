# SPECYFIKACJA TESTÓW — YAPA/BID

**Projekt:** Batch Image Delivery  
**Data:** 2026-03-09  
**Strategia:** Weryfikacja zachowania poprzez output logów + asercje stanów  

---

## SPIS TREŚCI

1. [Filozofia testowania](#1-filozofia-testowania)
2. [Architektura testów](#2-architektura-testów)
3. [Konfiguracja (conftest.py)](#3-konfiguracja-conftestpy)
4. [Faza 2A: Testy jednostkowe — image_processing](#4-faza-2a-testy-jednostkowe--image_processing)
5. [Faza 2B: Testy jednostkowe — config](#5-faza-2b-testy-jednostkowe--config)
6. [Faza 2C: Testy jednostkowe — source_manager](#6-faza-2c-testy-jednostkowe--source_manager)
7. [Faza 2D: Testy jednostkowe — project_manager](#7-faza-2d-testy-jednostkowe--project_manager)
8. [Faza 3A: Testy integracyjne — workflow przetwarzania](#8-faza-3a-testy-integracyjne--workflow-przetwarzania)
9. [Faza 3B: Testy integracyjne — integralność plików](#9-faza-3b-testy-integracyjne--integralność-plików)
10. [Faza 3C: Testy integracyjne — config + processing](#10-faza-3c-testy-integracyjne--config--processing)
11. [Faza 4A: Testy E2E — cykl życia projektu](#11-faza-4a-testy-e2e--cykl-życia-projektu)
12. [Faza 4B: Testy regresji](#12-faza-4b-testy-regresji)
13. [Dane testowe](#13-dane-testowe)

---

## 1. FILOZOFIA TESTOWANIA

### Weryfikacja przez logi

Każdy test weryfikuje zachowanie modułu przez:
1. **Asercje logów** — sprawdzenie że logger `Yapa_CM` wyemitował oczekiwane wiadomości
2. **Asercje stanów** — sprawdzenie wyników funkcji (return value, side effects)
3. **Asercje plików** — sprawdzenie że pliki zostały utworzone/zmodyfikowane

### Wzorzec testu

```python
def test_example(caplog, sample_image):
    """Każdy test ma 3 sekcje: GIVEN, WHEN, THEN."""
    # GIVEN — przygotowanie danych
    photo_path = sample_image

    # WHEN — wywołanie testowanej funkcji
    with caplog.at_level(logging.DEBUG, logger="Yapa_CM"):
        result = tested_function(photo_path)

    # THEN — weryfikacja
    # 1) Sprawdź return value
    assert result["success"] is True
    # 2) Sprawdź logi
    assert any("Skanowanie" in r.message for r in caplog.records)
    # 3) Sprawdź side effects (opcjonalnie)
    assert Path(expected_output).exists()
```

### Konwencje nazewnictwa

- Plik: `test_{moduł}.py`
- Klasa: `Test{Moduł}{Kontekst}` (opcjonalnie)
- Funkcja: `test_{funkcja}_{scenariusz}` — np. `test_image_resize_landscape_longer`
- Fixture: `{opis_danych}` — np. `sample_project`, `export_settings_fb`

---

## 2. ARCHITEKTURA TESTÓW

```
tests/
├── conftest.py                    # Globalne fixtures (rozszerzone)
├── test_image_processing.py       # Faza 2A: testy jednostkowe (ISTNIEJĄCY + rozszerzenie)
├── test_config.py                 # Faza 2B: testy konfiguracji (NOWY)
├── test_source_manager.py         # Faza 2C: testy source (ISTNIEJĄCY + rozszerzenie)
├── test_project_manager.py        # Faza 2D: testy projektów (ISTNIEJĄCY + rozszerzenie)
├── test_validators.py             # Faza 2E: testy walidatorów (NOWY, po utworzeniu validators.py)
├── test_workflows.py              # Faza 3A: integracja przetwarzania (NOWY)
├── test_integrity.py              # Faza 3B: integracja plików (NOWY)
├── test_config_processing.py      # Faza 3C: integracja config+processing (NOWY)
├── test_e2e.py                    # Faza 4A: end-to-end (NOWY)
└── test_regressions.py            # Faza 4B: regresje (NOWY)
```

### Zależności testów

```
Faza 1 (logging_config, errors, validators) ← MUSI być gotowa przed testami
    ↓
Faza 2 (unit tests) ← niezależne od siebie
    ↓
Faza 3 (integration) ← wymaga działających unit testów
    ↓
Faza 4 (e2e + regresje)
```

---

## 3. KONFIGURACJA (conftest.py)

### Rozszerzenie istniejącego conftest.py

Poniższe fixtures DODAĆ do istniejącego pliku `tests/conftest.py`:

```python
import logging
import pytest
import json
import os
import shutil
from pathlib import Path
from PIL import Image

LOGGER_NAME = "Yapa_CM"

# ─── ISTNIEJĄCE FIXTURES (zachować bez zmian) ───

# temp_dir, sample_project, sample_image — już istnieją

# ─── NOWE FIXTURES ───

@pytest.fixture
def log_capture(caplog):
    """Przechwytuje logi Yapa_CM na poziomie DEBUG.
    
    Użycie w teście:
        def test_x(log_capture):
            do_something()
            assert log_capture.has("Skanowanie", level="INFO")
    """
    with caplog.at_level(logging.DEBUG, logger=LOGGER_NAME):
        yield LogCaptureHelper(caplog)


class LogCaptureHelper:
    """Helper do weryfikacji logów w testach."""
    
    def __init__(self, caplog):
        self._caplog = caplog
    
    @property
    def records(self):
        return self._caplog.records
    
    @property
    def messages(self):
        return [r.message for r in self._caplog.records]
    
    def has(self, substring: str, level: str = None) -> bool:
        """Czy jest log zawierający substring (opcjonalnie na danym poziomie)."""
        for r in self._caplog.records:
            if substring in r.message:
                if level is None or r.levelname == level:
                    return True
        return False
    
    def count(self, substring: str) -> int:
        """Ile logów zawiera substring."""
        return sum(1 for r in self._caplog.records if substring in r.message)
    
    def at_level(self, level: str) -> list[str]:
        """Wszystkie wiadomości na danym poziomie."""
        return [r.message for r in self._caplog.records if r.levelname == level]
    
    def assert_sequence(self, *substrings: str):
        """Sprawdź czy logi zawierają podane substringi W KOLEJNOŚCI."""
        msgs = self.messages
        pos = 0
        for sub in substrings:
            found = False
            for i in range(pos, len(msgs)):
                if sub in msgs[i]:
                    pos = i + 1
                    found = True
                    break
            assert found, f"Brak '{sub}' w logach po pozycji {pos}. Logi: {msgs}"


@pytest.fixture
def export_settings_fb():
    """Pojedynczy profil eksportu 'fb' do testów."""
    return {
        "fb": {
            "size_type": "longer",
            "size": 1200,
            "format": "JPEG",
            "quality": 85,
            "logo": {
                "landscape": {"size": 240, "opacity": 60, "x_offset": 10, "y_offset": 10},
                "portrait": {"size": 312, "opacity": 60, "x_offset": 10, "y_offset": 10}
            }
        }
    }


@pytest.fixture
def export_settings_multi():
    """Wieloprofilowy export settings (fb + insta)."""
    return {
        "fb": {
            "size_type": "longer",
            "size": 1200,
            "format": "JPEG",
            "quality": 85,
            "logo": {
                "landscape": {"size": 240, "opacity": 60, "x_offset": 10, "y_offset": 10},
                "portrait": {"size": 312, "opacity": 60, "x_offset": 10, "y_offset": 10}
            }
        },
        "insta": {
            "size_type": "width",
            "size": 1080,
            "format": "PNG",
            "quality": 9,
            "logo": {
                "landscape": {"size": 228, "opacity": 60, "x_offset": 10, "y_offset": 10},
                "portrait": {"size": 296, "opacity": 60, "x_offset": 10, "y_offset": 10}
            }
        }
    }


@pytest.fixture
def sample_image_with_exif(tmp_path):
    """Tworzy JPEG z podstawowymi tagami EXIF."""
    from PIL.ExifTags import IFD
    img = Image.new("RGB", (2000, 1500), color="blue")
    exif = img.getexif()
    exif[0x010F] = "TestCamera"          # Make
    exif[0x0110] = "TestModel"           # Model
    exif[0x0132] = "2026:03:09 14:30:00" # DateTime
    ifd = exif.get_ifd(IFD.Exif)
    ifd[0x9003] = "2026:03:09 14:30:00"  # DateTimeOriginal
    ifd[0x9004] = "2026:03:09 14:30:00"  # DateTimeDigitized
    
    session_dir = tmp_path / "source" / "session1"
    session_dir.mkdir(parents=True)
    img_path = session_dir / "test_exif.jpg"
    img.save(img_path, "JPEG", exif=exif.tobytes())
    return img_path


@pytest.fixture
def sample_logo(tmp_path):
    """Tworzy logo.png w folderze źródłowym."""
    logo = Image.new("RGBA", (600, 200), color=(255, 255, 255, 128))
    # Dodaj jakiś wzór
    for x in range(100, 500):
        for y in range(50, 150):
            logo.putpixel((x, y), (0, 0, 0, 200))
    session_dir = tmp_path / "source" / "session1"
    session_dir.mkdir(parents=True, exist_ok=True)
    logo_path = session_dir / "logo.png"
    logo.save(logo_path, "PNG")
    return logo_path


@pytest.fixture
def full_test_project(tmp_path, export_settings_fb):
    """Kompletny projekt testowy z ustawieniami, zdjęciami i logo."""
    project_dir = tmp_path / "projects" / "TestProject"
    source_dir = tmp_path / "source"
    export_dir = tmp_path / "export"
    
    for d in [project_dir, source_dir, export_dir]:
        d.mkdir(parents=True)
    
    # Settings
    settings = {"source_folder": str(source_dir), "export_folder": str(export_dir)}
    (project_dir / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
    (project_dir / "export_option.json").write_text(
        json.dumps(export_settings_fb), encoding="utf-8"
    )
    
    # Zdjęcia testowe
    session_dir = source_dir / "session1"
    session_dir.mkdir()
    
    for i in range(3):
        img = Image.new("RGB", (2000, 1500), color=(100 + i * 50, 50, 50))
        exif = img.getexif()
        exif[0x0132] = f"2026:03:09 14:{30+i}:00"
        img.save(session_dir / f"photo_{i}.jpg", "JPEG", exif=exif.tobytes())
    
    # Logo
    logo = Image.new("RGBA", (600, 200), color=(255, 255, 255, 128))
    logo.save(session_dir / "logo.png", "PNG")
    
    return {
        "project_dir": project_dir,
        "source_dir": source_dir,
        "export_dir": export_dir,
        "session_dir": session_dir,
        "settings": settings,
        "export_settings": export_settings_fb,
    }
```

---

## 4. FAZA 2A: TESTY JEDNOSTKOWE — image_processing

**Plik:** `tests/test_image_processing.py`  
**Akcja:** Rozszerzyć istniejący plik o nowe testy  
**Wymagania:** Po Fazie 1 (logging instrumentation)

### TEST-IP-001: test_image_resize_landscape_longer
```
GIVEN: Obraz 2000x1500 (landscape)
WHEN:  image_resize(img, longer_side=1000, method="longer")
THEN:  Rozmiar wyniku = 1000x750
LOG:   "Skaluję zdjęcie do 1000 px (metoda: longer)" na DEBUG
```

### TEST-IP-002: test_image_resize_portrait_longer
```
GIVEN: Obraz 1500x2000 (portrait)
WHEN:  image_resize(img, longer_side=1000, method="longer")
THEN:  Rozmiar wyniku = 750x1000
LOG:   "Skaluję zdjęcie do 1000 px (metoda: longer)" na DEBUG
```

### TEST-IP-003: test_image_resize_width_method
```
GIVEN: Obraz 2000x1500
WHEN:  image_resize(img, longer_side=800, method="width")
THEN:  Rozmiar wyniku: width=800, height proporcjonalna
LOG:   "Skaluję zdjęcie do 800 px (metoda: width)" na DEBUG
```

### TEST-IP-004: test_image_resize_height_method
```
GIVEN: Obraz 2000x1500
WHEN:  image_resize(img, longer_side=600, method="height")
THEN:  Rozmiar wyniku: height=600, width proporcjonalna
LOG:   "Skaluję zdjęcie do 600 px (metoda: height)" na DEBUG
```

### TEST-IP-005: test_image_resize_square_input
```
GIVEN: Obraz 1000x1000 (kwadrat)
WHEN:  image_resize(img, longer_side=500, method="longer")
THEN:  Rozmiar wyniku = 500x500
```

### TEST-IP-006: test_image_resize_already_smaller
```
GIVEN: Obraz 500x300
WHEN:  image_resize(img, longer_side=1000, method="longer")
THEN:  Obraz NIE powiększony — rozmiar bez zmian LUB ograniczony do oryginału
       (sprawdzić aktualną logikę — czy powiększa czy nie)
```

### TEST-IP-007: test_srgb_conversion_no_profile
```
GIVEN: Obraz RGB bez profilu ICC
WHEN:  image_convert_to_srgb(img)
THEN:  Zwracany obraz jest taki sam (brak konwersji)
LOG:   "Konwertuję zdjęcie na sRGB" na DEBUG LUB brak logu (zależnie od im. zmiany)
```

### TEST-IP-008: test_srgb_conversion_with_profile
```
GIVEN: Obraz z osadzonym profilem ICC (np. Adobe RGB)
WHEN:  image_convert_to_srgb(img)
THEN:  Profil ICC po konwersji = sRGB
LOG:   "Konwertuję zdjęcie na sRGB" na DEBUG
```

### TEST-IP-009: test_watermark_applied_correct_position
```
GIVEN: Obraz 2000x1500 + logo.png 600x200
WHEN:  apply_watermark(base, logo_path, size=240, opacity=60, x_offset=10, y_offset=10)
THEN:  Wynik ma rozmiar 2000x1500 (niezmieniony)
       Piksele w prawym dolnym rogu różnią się od oryginału (watermark widoczny)
LOG:   "Nakładam watermark z {logo_path}" na DEBUG
```

### TEST-IP-010: test_watermark_opacity_range
```
GIVEN: Obraz + logo
WHEN:  apply_watermark(..., opacity=100) vs apply_watermark(..., opacity=10)
THEN:  Watermark z opacity=100 bardziej widoczny (większa różnica pikseli)
```

### TEST-IP-011: test_watermark_missing_logo_file
```
GIVEN: Ścieżka do nieistniejącego logo.png
WHEN:  apply_watermark(base, "/tmp/nonexistent_logo.png", ...)
THEN:  Rzuca FileNotFoundError LUB zwraca obraz bez watermarku
LOG:   Zawiera "logo" i "ERROR" lub "WARNING"
```

### TEST-IP-012: test_exif_clean_preserves_mandatory
```
GIVEN: EXIF z tagami: Make(0x010F), Model(0x0110), DateTime(0x0132), + TIFF tags
WHEN:  exif_clean_from_tiff(exif)
THEN:  Make, Model, DateTime zachowane
       StripOffsets(0x0111), Compression(0x0103) usunięte
LOG:   "Czyszczę EXIF z tagów TIFF" na DEBUG
```

### TEST-IP-013: test_get_all_exif_datetime_extracted
```
GIVEN: JPEG z DateTimeOriginal w EXIF
WHEN:  get_all_exif(img)
THEN:  Wynik zawiera klucz "DateTimeOriginal" z wartością "2026:03:09 14:30:00"
```

### TEST-IP-014: test_get_all_exif_camera_info
```
GIVEN: JPEG z Make="Canon", Model="EOS R6"
WHEN:  get_all_exif(img)
THEN:  Wynik zawiera "Make"="Canon" i "Model"="EOS R6"
```

### TEST-IP-015: test_get_all_exif_blacklisted_tags_excluded
```
GIVEN: JPEG z GPS danymi + ExifIFD pointer
WHEN:  get_all_exif(img)
THEN:  Wynik NIE zawiera kluczy z BLACK_LIST_TAGS {34665, 34853, 40965}
```

### TEST-IP-016: test_get_all_exif_with_real_camera_files
```
GIVEN: Pliki z test/source/ (Canon_50D, Canon_R, Canon_R6, Canon_RP, SONY)
WHEN:  get_all_exif(img) dla każdego
THEN:  Każdy wynik zawiera przynajmniej DateTimeOriginal lub ModifyDate
       (powiązane z istniejącym test_exif_mandatory_tags)
```

### TEST-IP-017: test_process_photo_task_success_jpeg
```
GIVEN: JPEG 2000x1500, export_settings z profilem "fb" (JPEG, longer=1200)
WHEN:  process_photo_task(photo_path, "session1", "photo.jpg", "2026:03:09", export_dir, settings, {})
THEN:  result["success"] == True
       result["exported"]["fb"] istnieje jako plik JPEG
       Rozmiar eksportu: dłuższa krawędź = 1200px
LOG:   Sekwencja: "Starting export fb" → "Export fb complete" (po dodaniu logów w Fazie 1)
```

### TEST-IP-018: test_process_photo_task_success_png
```
GIVEN: JPEG 2000x1500, export_settings z profilem "insta" (PNG, width=1080)
WHEN:  process_photo_task(...)
THEN:  result["success"] == True
       Plik eksportu ma rozszerzenie .png
       Width eksportu = 1080px
```

### TEST-IP-019: test_process_photo_task_with_watermark
```
GIVEN: JPEG + logo.png w tym samym folderze
WHEN:  process_photo_task(...) z export_settings zawierającym konfigurację logo
THEN:  result["success"] == True
       Eksport zawiera watermark (piksel check)
LOG:   Zawiera "watermark" lub "logo"
```

### TEST-IP-020: test_process_photo_task_missing_source
```
GIVEN: Ścieżka do nieistniejącego pliku
WHEN:  process_photo_task("/nonexistent.jpg", ...)
THEN:  result["success"] == False
       result["error_msg"] zawiera informację o braku pliku
```

### TEST-IP-021: test_process_photo_task_returns_duration
```
GIVEN: Dowolne poprawne zdjęcie
WHEN:  process_photo_task(...)
THEN:  result["duration"] > 0 i jest typu float
```

### TEST-IP-022: test_get_logo_caching
```
GIVEN: Plik logo.png
WHEN:  get_logo(logo_path) wywołane 3 razy z tą samą ścieżką
THEN:  Wynik identyczny (ten sam obiekt — cache hit)
LOG:   "Wczytuję logo (cache miss)" pojawia się TYLKO RAZ
```

---

## 5. FAZA 2B: TESTY JEDNOSTKOWE — config

**Plik:** `tests/test_config.py` (NOWY)

### TEST-CFG-001: test_load_settings_valid
```
GIVEN: Poprawny settings.json: {"source_folder": "/tmp/src", "export_folder": "/tmp/exp"}
WHEN:  load_settings(path)
THEN:  Zwraca dict z kluczami "source_folder", "export_folder"
LOG:   "Loaded config:" na DEBUG
```

### TEST-CFG-002: test_load_settings_missing_file
```
GIVEN: Ścieżka do nieistniejącego pliku
WHEN:  load_settings(Path("/tmp/no_such_settings.json"))
THEN:  Rzuca SystemExit(1)
LOG:   "Config file not found:" na CRITICAL
```

### TEST-CFG-003: test_load_settings_invalid_json
```
GIVEN: Plik z nieprawidłowym JSON: "{ broken json }"
WHEN:  load_settings(path)
THEN:  Rzuca SystemExit(1)
LOG:   "Invalid JSON in" na CRITICAL
```

### TEST-CFG-004: test_load_export_options_valid
```
GIVEN: Poprawny export_option.json z profilami fb, insta
WHEN:  load_export_options(path)
THEN:  Zwraca dict z kluczami "fb", "insta"
       Każdy profil zawiera "size_type", "size", "format"
LOG:   "Loaded config:" na DEBUG
```

### TEST-CFG-005: test_load_export_options_empty
```
GIVEN: export_option.json = {}
WHEN:  load_export_options(path)
THEN:  Zwraca pusty dict (bez crash)
```

### TEST-CFG-006: test_load_export_options_missing_file
```
GIVEN: Ścieżka do nieistniejącego pliku
WHEN:  load_export_options(Path("/tmp/no_export.json"))
THEN:  Rzuca SystemExit(1)
LOG:   "Config file not found:" na CRITICAL
```

### TEST-CFG-007: test_validate_export_profile_valid (wymaga validators.py)
```
GIVEN: Kompletny profil eksportu z wszystkimi kluczami
WHEN:  validate_export_profile(profile)
THEN:  Zwraca pustą listę błędów []
```

### TEST-CFG-008: test_validate_export_profile_missing_size (wymaga validators.py)
```
GIVEN: Profil bez klucza "size"
WHEN:  validate_export_profile(profile)
THEN:  Zwraca listę z błędem o brakującym "size"
```

### TEST-CFG-009: test_validate_export_profile_invalid_ratio (wymaga validators.py)
```
GIVEN: Profil z "ratio": "not_a_list"
WHEN:  validate_export_profile(profile)
THEN:  Zwraca listę z błędem o nieprawidłowym "ratio"
```

---

## 6. FAZA 2C: TESTY JEDNOSTKOWE — source_manager

**Plik:** `tests/test_source_manager.py`  
**Akcja:** Rozszerzyć istniejący plik

### TEST-SM-001: test_create_source_dict_basic (ISTNIEJĄCY)
```
Zachować bez zmian — rozszerzyć o sprawdzenie logów:
LOG:   "Tworzę source_dict" na DEBUG
```

### TEST-SM-002: test_create_source_dict_excludes_logo
```
GIVEN: Folder z photo.jpg + logo.png
WHEN:  create_source_dict(source_folder, ...)
THEN:  Dict zawiera "photo.jpg" ale NIE zawiera "logo.png"
```

### TEST-SM-003: test_create_source_dict_multiple_formats
```
GIVEN: Folder z plikami: test.jpg, test.png, test.tiff, test.cr2 (jeśli PIL obsługuje)
WHEN:  create_source_dict(source_folder, ...)
THEN:  Wszystkie pliki obrazów znalezione w dict (z wyjątkiem nieobsługiwanych formatów)
```

### TEST-SM-004: test_create_source_dict_nested_folders
```
GIVEN: Struktura: source/session1/photo1.jpg, source/session2/photo2.jpg
WHEN:  create_source_dict(source_folder, ...)
THEN:  Dict ma klucze "session1" i "session2"
LOG:   Zawiera "Nowy folder" dla obu sesji
```

### TEST-SM-005: test_create_source_dict_all_states_new
```
GIVEN: Nowy folder z 3 zdjęciami
WHEN:  create_source_dict(...)
THEN:  Wszystkie entries mają state == SourceState.NEW
```

### TEST-SM-006: test_update_source_dict_adds_new (ISTNIEJĄCY — rozszerzyć)
```
Dodać weryfikację logów:
LOG:   "Nowy plik:" na INFO
```

### TEST-SM-007: test_update_source_dict_new_folder
```
GIVEN: Istniejący dict + nowy folder dodany do source
WHEN:  update_source_dict(source_dict, ...)
THEN:  Nowy folder pojawia się w dict
LOG:   "Nowy folder: '...'" na INFO
```

### TEST-SM-008: test_update_source_dict_no_changes
```
GIVEN: Dict i source folder identyczne
WHEN:  update_source_dict(source_dict, ...)
THEN:  found_new == False, dict bez zmian
```

### TEST-SM-009: test_check_integrity_deleted (ISTNIEJĄCY — rozszerzyć)
```
Dodać weryfikację logów:
LOG:   "[INTEGRITY] Plik źródłowy usunięty:" na WARNING
```

### TEST-SM-010: test_check_integrity_modified (ISTNIEJĄCY — rozszerzyć)
```
Dodać weryfikację logów:
LOG:   "[INTEGRITY] Plik źródłowy zmieniony" na WARNING
```

### TEST-SM-011: test_check_integrity_missing_export
```
GIVEN: Dict z entry state=OK + exported={"fb": "/path/export.jpg"}
       Ale plik exportu nie istnieje na dysku
WHEN:  check_integrity(source_dict, ...)
THEN:  Entry state → zmieniony na NEW (do reprocessingu)
LOG:   "[INTEGRITY] Brak pliku eksportu" na WARNING
```

### TEST-SM-012: test_check_integrity_all_ok
```
GIVEN: Dict z entry state=OK + wszystkie pliki istnieją
WHEN:  check_integrity(source_dict, ...)
THEN:  Brak zmian w dict
       Brak ostrzeżeń w logach
```

### TEST-SM-013: test_save_load_source_dict_roundtrip
```
GIVEN: source_dict z 5 entries
WHEN:  save_source_dict(dict, dir) → load_source_dict(dir)
THEN:  Załadowany dict identyczny z zapisanym
LOG:   "Zapisano source_dict" na DEBUG → "Wczytuję istniejący source_dict" na INFO
```

### TEST-SM-014: test_load_source_dict_corrupted_json
```
GIVEN: source_dict.json z nieprawidłowym JSON
WHEN:  load_source_dict(project_dir)
THEN:  Zwraca None
LOG:   "Plik source_dict.json jest uszkodzony" na ERROR
```

### TEST-SM-015: test_read_metadata_with_exif
```
GIVEN: JPEG z DateTimeOriginal
WHEN:  _read_metadata(path, folder, filename, stats)
THEN:  Zwraca (created_date, exif_dict) gdzie created_date == "2026:03:09 14:30:00"
```

### TEST-SM-016: test_read_metadata_fallback_mtime
```
GIVEN: JPEG bez EXIF (lub z uszkodzonym EXIF)
WHEN:  _read_metadata(path, folder, filename, stats)
THEN:  Zwraca created_date z mtime pliku (fallback)
LOG:   Może zawierać "Cannot open image for EXIF" na ERROR
```

---

## 7. FAZA 2D: TESTY JEDNOSTKOWE — project_manager

**Plik:** `tests/test_project_manager.py`  
**Akcja:** Rozszerzyć istniejące testy o weryfikację logów

### TEST-PM-001: test_create_project (ISTNIEJĄCY — rozszerzyć)
```
Dodać weryfikację logów:
LOG:   "Zapisano ustawienia projektu" na DEBUG
LOG:   "Zapisano opcje eksportu projektu" na DEBUG
```

### TEST-PM-002: test_create_project_duplicate (ISTNIEJĄCY)
```
Zachować bez zmian
```

### TEST-PM-003: test_recent_projects_list (ISTNIEJĄCY — rozszerzyć)
```
Dodać:
LOG:   "Zaktualizowano listę ostatnich projektów" na DEBUG
```

### TEST-PM-004: test_prune_recent_projects (ISTNIEJĄCY — rozszerzyć)
```
Dodać:
LOG:   "Przeczyszczono listę ostatnich projektów" na DEBUG
```

### TEST-PM-005: test_get_project_details_with_source_dict
```
GIVEN: Projekt z source_dict.json zawierającym 5 zdjęć
WHEN:  ProjectManager.get_project_details(path)
THEN:  result["photo_count"] == 5
       result["last_modified"] jest poprawną datą
```

### TEST-PM-006: test_get_project_details_no_source_dict
```
GIVEN: Projekt BEZ source_dict.json
WHEN:  ProjectManager.get_project_details(path)
THEN:  result["photo_count"] == 0 lub klucz nie istnieje
```

### TEST-PM-007: test_recent_projects_max_10
```
GIVEN: Dodanie 15 projektów do recent_projects
WHEN:  get_recent_projects()
THEN:  Zwraca maksymalnie 10 projektów
       Najnowszy na pozycji [0]
```

### TEST-PM-008: test_create_project_spaces_in_name
```
GIVEN: Nazwa projektu = "Projekt Z Odstępami"
WHEN:  create_project("Projekt Z Odstępami", ...)
THEN:  Folder = "Projekt_Z_Odstępami" (spacje → podkreślniki)
       settings.json i export_option.json istnieją
```

---

## 8. FAZA 3A: TESTY INTEGRACYJNE — workflow przetwarzania

**Plik:** `tests/test_workflows.py` (NOWY)

### TEST-WF-001: test_single_photo_full_export
```
GIVEN: full_test_project fixture (3 zdjęcia + logo)
WHEN:  process_photo_task(photo_0, "session1", "photo_0.jpg", created_date,
           export_dir, export_settings_fb, {})
THEN:  result["success"] == True
       Plik eksportu istnieje w export_dir/fb/
       Rozmiar eksportu: dłuższa krawędź = 1200px
       Eksport zawiera EXIF (DateTimeOriginal zachowany)
LOG:   Sekwencja log messages w poprawnej kolejności
```

### TEST-WF-002: test_batch_3_photos_single_profile
```
GIVEN: full_test_project (3 zdjęcia)
WHEN:  process_photo_task() × 3 (sekwencyjnie)
THEN:  3 pliki eksportu w export_dir/fb/
       Każdy result["success"] == True
       Każdy result["duration"] > 0
```

### TEST-WF-003: test_batch_multi_profile
```
GIVEN: 1 zdjęcie + export_settings_multi (fb + insta)
WHEN:  process_photo_task(..., export_settings_multi, {})
THEN:  result["exported"] zawiera klucze "fb" i "insta"
       Oba pliki istnieją na dysku
       fb = JPEG, insta = PNG
```

### TEST-WF-004: test_export_preserves_exif_after_resize
```
GIVEN: JPEG z richm EXIF (Make, Model, DateTime, ISO, FocalLength)
WHEN:  process_photo_task(...)
THEN:  Otwarty plik eksportu zawiera te same tagi EXIF (minus TIFF-specific)
```

### TEST-WF-005: test_export_creates_subfolder
```
GIVEN: export_dir istnieje ale export_dir/fb/ NIE istnieje
WHEN:  process_photo_task(...)
THEN:  export_dir/fb/ automatycznie utworzony
```

### TEST-WF-006: test_export_skip_existing
```
GIVEN: existing_exports = {"fb": "/existing/path.jpg"}
WHEN:  process_photo_task(..., existing_exports={"fb": "/path"})
THEN:  Profil "fb" pominięty (nie nadpisywany)
       result["exported"] NIE zawiera "fb"
```

---

## 9. FAZA 3B: TESTY INTEGRACYJNE — integralność plików

**Plik:** `tests/test_integrity.py` (NOWY)

### TEST-INT-001: test_full_cycle_create_check_update
```
GIVEN: Folder z 3 zdjęciami
WHEN:  1) create_source_dict()
       2) Dodaj 2 nowe zdjęcia do folderu
       3) update_source_dict()
       4) check_integrity()
THEN:  Po kroku 1: 3 entries, all NEW
       Po kroku 3: 5 entries, 2 nowe = NEW
       Po kroku 4: Brak zmian integralnościowych
LOG:   "Tworzę source_dict" → "Nowy plik:" × 2 → logi integrity (lub brak ostrzeżeń)
```

### TEST-INT-002: test_delete_then_readd_photo
```
GIVEN: source_dict z photo.jpg (state=OK)
WHEN:  1) Usuń photo.jpg z dysku
       2) check_integrity() → state=DELETED
       3) Przywróć photo.jpg (kopiuj z powrotem)
       4) update_source_dict()
THEN:  Po kroku 2: state=DELETED
       Po kroku 4: Nowy entry lub state=NEW (zależy od implementacji)
```

### TEST-INT-003: test_concurrent_dict_updates_thread_safe
```
GIVEN: source_dict z 100 entries
WHEN:  10 wątków jednocześnie modyfikuje entries (stan/exported)
       (symulacja race condition z BUG-002)
THEN:  Po zakończeniu: dict spójny, żaden entry nie utracony
       Brak wyjątków
```

### TEST-INT-004: test_save_load_preserves_unicode
```
GIVEN: source_dict z polskimi znakami w nazwach: "Zdjęcia_ŻŹĆ/foto_ąę.jpg"
WHEN:  save_source_dict() → load_source_dict()
THEN:  Nazwy zachowane poprawnie (UTF-8)
```

---

## 10. FAZA 3C: TESTY INTEGRACYJNE — config + processing

**Plik:** `tests/test_config_processing.py` (NOWY)

### TEST-CP-001: test_config_drives_export_size
```
GIVEN: export_option z "fb": {"size": 800, "size_type": "longer"}
WHEN:  Załaduj config → process_photo_task z tymi settings
THEN:  Eksport ma dłuższą krawędź = 800px
```

### TEST-CP-002: test_config_jpeg_vs_png_format
```
GIVEN: Dwa profile: fb (JPEG) i insta (PNG)
WHEN:  process_photo_task z oboma profilami
THEN:  fb → .jpg, insta → .png
       fb ma JPEG EXIF, insta ma PngInfo metadata
```

### TEST-CP-003: test_config_with_ratio_filter
```
GIVEN: Profil z "ratio": [0.8, 1.25] (odrzuca ultra-panoramiczne)
       Zdjęcie 3000x1000 (ratio 3:1 = 3.0)
WHEN:  process_photo_task(...)
THEN:  Export SKIP (ratio 3.0 > 1.25) — plik NIE tworzony dla tego profilu
```

### TEST-CP-004: test_missing_logo_exports_without_watermark
```
GIVEN: Export settings z konfiguracją logo, ale BRAK logo.png w folderze
WHEN:  process_photo_task(...)
THEN:  result["success"] == True (eksport się udaje)
       Export BEZ watermarku
LOG:   Ostrzeżenie o brakującym logo
```

---

## 11. FAZA 4A: TESTY E2E — cykl życia projektu

**Plik:** `tests/test_e2e.py` (NOWY)

### TEST-E2E-001: test_new_project_full_workflow
```
GIVEN: Pusty tmp_dir
WHEN:  1) ProjectManager.create_project("Test", source, export, settings)
       2) create_source_dict(source, export, settings)
       3) Dla każdego zdjęcia: process_photo_task(...)
       4) save_source_dict()
THEN:  Projekt istnieje z settings.json, export_option.json
       source_dict.json zawiera entries z state=OK
       Eksporty istnieją na dysku
LOG:   Pełna sekwencja od "Zapisano ustawienia" do "Export complete"
```

### TEST-E2E-002: test_reopen_project_incremental
```
GIVEN: Istniejący projekt z przetworzonymi zdjęciami
WHEN:  1) load_source_dict()
       2) Dodaj 2 nowe zdjęcia do source
       3) update_source_dict()
       4) Przetwórz TYLKO nowe zdjęcia
THEN:  Stare eksporty nietknięte
       Nowe eksporty utworzone
       source_dict zaktualizowany
```

### TEST-E2E-003: test_error_recovery_workflow
```
GIVEN: Projekt z 5 zdjęciami, z czego 1 uszkodzone
WHEN:  process_photo_task() × 5
THEN:  4 z success=True, 1 z success=False
       source_dict: 4x OK + 1x ERROR
LOG:   4x "Export complete" + 1x "error"
```

### TEST-E2E-004: test_performance_100_images
```
GIVEN: 100 syntetycznych zdjęć 200x150 (małe dla szybkości)
WHEN:  Przetworzenie wszystkich sekwencyjnie
THEN:  Łączny czas < 60s (benchmark, nie twardy wymóg)
       Wszystkie eksporty poprawne
LOG:   100x "Export complete", 0x ERROR
       Logowany sumaryczny czas przetwarzania
```

---

## 12. FAZA 4B: TESTY REGRESJI

**Plik:** `tests/test_regressions.py` (NOWY)

### TEST-REG-001: test_watermark_always_applied_when_logo_exists (BUG-003)
```
GIVEN: Zdjęcie + logo.png w folderze
WHEN:  process_photo_task(...)
THEN:  Eksport zawiera watermark (piksel check: piksele w prawym dolnym rogu ≠ oryginał resized)
       NIGDY cichy brak watermarku
```

### TEST-REG-002: test_source_dict_no_corruption_under_load (BUG-002)
```
GIVEN: source_dict z 50 entries
WHEN:  50 równoczesnych zapisów z różnych wątków (symulacja race condition)
THEN:  Dict po zakończeniu: dokładnie 50 entries, każdy poprawny
       Żaden entry nie utracony/zduplikowany
```

### TEST-REG-003: test_unicode_filenames_roundtrip
```
GIVEN: Pliki z polskimi znakami: "Zdjęcia/foto_ąęść.jpg"
WHEN:  create_source_dict → save → load → export
THEN:  Cały pipeline działa bez UnicodeError
```

### TEST-REG-004: test_unc_path_handling
```
GIVEN: source_folder jako ścieżka UNC: "\\\\server\\share\\photos"
WHEN:  create_source_dict(source_folder, ...)
THEN:  Poprawne parsowanie ścieżki (nie crash na podwójnych backslashach)
       (test z mockowanym os.walk)
```

### TEST-REG-005: test_export_option_with_all_format_types
```
GIVEN: Profile z format: "JPEG", "PNG" (i potencjalnie "TIFF" w przyszłości)
WHEN:  process_photo_task() dla każdego formatu
THEN:  Każdy eksport poprawny, odpowiednie rozszerzenie
```

---

## 13. DANE TESTOWE

### Istniejące zasoby (zachować)
- `test/exif_references.json` — referencyjne tagi EXIF
- `test/exiftool-13.51_64/` — narzędzie referencyjne
- `test/source/Canon_50D/`, `Canon_R/`, `Canon_R6/`, `Canon_RP/`, `SONY/` — prawdziwe zdjęcia

### Nowe zasoby do stworzenia

| Zasób | Opis | Tworzony przez |
|-------|------|---------------|
| Syntetyczne JPEG 100x100 | Fixture `sample_image` (istniejący) | conftest.py |
| JPEG z EXIF 2000x1500 | Fixture `sample_image_with_exif` | conftest.py |
| Logo PNG 600x200 RGBA | Fixture `sample_logo` | conftest.py |
| Kompletny projekt | Fixture `full_test_project` | conftest.py |
| Uszkodzony JPEG | Plik z obciętymi danymi | Można utworzyć w fixtures |

### Szacowana liczba testów

| Faza | Plik | Nowe testy | Rozszerzone | Suma |
|------|------|-----------|------------|------|
| 2A | test_image_processing.py | 18 | 4 | 22 |
| 2B | test_config.py (NOWY) | 9 | 0 | 9 |
| 2C | test_source_manager.py | 12 | 4 | 16 |
| 2D | test_project_manager.py | 4 | 4 | 8 |
| 3A | test_workflows.py (NOWY) | 6 | 0 | 6 |
| 3B | test_integrity.py (NOWY) | 4 | 0 | 4 |
| 3C | test_config_processing.py (NOWY) | 4 | 0 | 4 |
| 4A | test_e2e.py (NOWY) | 4 | 0 | 4 |
| 4B | test_regressions.py (NOWY) | 5 | 0 | 5 |
| **RAZEM** | | **66** | **12** | **78** |

---

### Polecenia uruchomienia testów

```bash
# Szybki run — tylko unit testy
pytest tests/test_image_processing.py tests/test_config.py tests/test_source_manager.py tests/test_project_manager.py -x -v

# Integration tests
pytest tests/test_workflows.py tests/test_integrity.py tests/test_config_processing.py -x -v

# E2E + regresje
pytest tests/test_e2e.py tests/test_regressions.py -x -v

# Pełny suite z logami
pytest tests/ -x -v --log-cli-level=DEBUG

# Coverage report
pytest tests/ --cov=bid --cov-report=html --cov-report=term-missing
```

---

*Koniec specyfikacji testów. Zmiany do kodu potrzebne przed implementacją testów → patrz `LOGGING_INSTRUMENTATION.md`.*
