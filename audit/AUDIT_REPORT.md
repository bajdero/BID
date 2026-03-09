# RAPORT AUDYTU KODU — YAPA/BID

**Projekt:** Batch Image Delivery  
**Data audytu:** 2026-03-09  
**Wersja:** 1.0  
**Audytor:** Senior Architect / AI Code Review  

---

## SPIS TREŚCI

1. [Podsumowanie](#1-podsumowanie)
2. [Architektura](#2-architektura)
3. [Błędy krytyczne](#3-błędy-krytyczne)
4. [Problemy wydajnościowe](#4-problemy-wydajnościowe)
5. [Ulepszenia UI/UX](#5-ulepszenia-uiux)
6. [Jakość kodu](#6-jakość-kodu)
7. [Bezpieczeństwo](#7-bezpieczeństwo)
8. [Przygotowanie do migracji Docker/Web](#8-przygotowanie-do-migracji-dockerweb)
9. [Podsumowanie priorytetów](#9-podsumowanie-priorytetów)

---

## 1. PODSUMOWANIE

### Mocne strony
- Minimalne zależności zewnętrzne (tylko Pillow) — łatwa instalacja
- Kompletna ekstrakcja EXIF (IFD0, ExifIFD, IPTC, XMP, ICC)
- Obsługa przetwarzania równoległego (ProcessPoolExecutor)
- Dobra struktura logów z datowanymi plikami
- Cross-platform (Windows + Linux) z obsługą pathlib

### Główne problemy
- **Blokowanie UI** przy operacjach na dysku sieciowym (SMB/UNC)
- **Race condition** w dostępie do `source_dict`
- **Brak walidacji** profilów eksportu i ścieżek
- **Niepełne testy** — brak testów watermarku, przetwarzania równoległego, UI
- **Ciche awarie** — watermark nie znaleziony → eksport bez watermarku bez ostrzeżenia

---

## 2. ARCHITEKTURA

### Diagram modułów

```
main.py  ─────────────────────────────────────────────────┐
  │ _setup_logging()   │ _parse_args()                    │
  ▼                                                        │
bid/app.py → MainApp(tk.Tk)                                │
  ├─ bid/config.py          → load_settings(), load_export_options()
  ├─ bid/source_manager.py  → create/update/check source_dict
  ├─ bid/image_processing.py → process_photo_task() [ProcessPool]
  ├─ bid/project_manager.py → ProjectManager (create/recent/prune)
  └─ bid/ui/
       ├─ project_selector.py → ProjectSelector (ekran startowy)
       ├─ setup_wizard.py     → SetupWizard (nowy projekt)
       ├─ source_tree.py      → SourceTree (drzewo plików)
       ├─ details_panel.py    → DetailsPanel (EXIF + eksporty)
       └─ preview.py          → PrevWindow (podgląd zdjęć)
```

### Przepływ danych

```
[Dysk sieciowy]
     │
     ▼ os.walk() + PIL.Image.open()
source_manager.create_source_dict()
     │
     ▼ JSON
source_dict.json ◄──► source_dict (in-memory, dict_lock)
     │
     ▼ ProcessPoolExecutor
image_processing.process_photo_task()
     │
     ▼ PIL save (JPEG/PNG + EXIF)
[Export folder na dysku sieciowym]
```

---

## 3. BŁĘDY KRYTYCZNE

### BUG-001: Blokowanie UI przy skanowaniu dysku sieciowego 🔴
- **Lokalizacja:** `bid/app.py` linie 225–259 (`scan_photos`), `bid/source_manager.py` linie 158–182 (`create_source_dict`)
- **Opis:** `os.walk()` + `PIL.Image.open()` dla każdego pliku na dysku SMB/UNC z latencją ~50-200ms per file. Dla 500 zdjęć = 25–100 sekund zamrożonego UI.
- **Warunki:** Dysk sieciowy (SMB/CIFS), mapped drive lub ścieżka UNC, >100 plików w projekcie
- **Wpływ:** Aplikacja wygląda jak zawieszona; użytkownik zamyka ją siłowo
- **Naprawa:**
  1. Przenieść `create_source_dict()` i `update_source_dict()` do wątku tła (daemon thread)
  2. Dodać `threading.Event` do sygnalizacji zakończenia skanowania
  3. Dodać pasek postępu w UI (progress bar)
  4. Implementować lazy-loading EXIF (odczyt EXIF tylko po wybraniu zdjęcia)
  5. Cache source_dict na dysku lokalnym — ładować z JSON, skanować różnice inkrementalnie
- **Log do dodania:** `logger.info(f"Skanowanie: {i}/{total} plików ({elapsed:.1f}s)")` co 50 plików

### BUG-002: Race condition w source_dict 🔴
- **Lokalizacja:** `bid/app.py` linia 389–398 (`_mark_error`) vs linia 378–385 (`_mark_error_locked`)
- **Opis:** Metoda `_mark_error()` modyfikuje `source_dict` BEZ `dict_lock`. Jednocześnie `_update_source_worker()` (wątek tła) czyta i modyfikuje ten sam dict.
- **Warunki:** Przetwarzanie zdjęcia kończy się błędem PODCZAS gdy wątek aktualizacji skanuje source
- **Wpływ:** Uszkodzenie stanu dict, utracone eksporty, niespójny UI
- **Naprawa:**
  1. Zastąpić `dict_lock = threading.Lock()` przez `threading.RLock()` (reentrant)
  2. Stworzyć `ThreadSafeSourceDict` wrapper (patrz `IMPLEMENTATION_GUIDE.md`)
  3. Wszystkie mutacje dict przez wrapper z automatycznym lockowaniem
  4. Usunąć duplikację `_mark_error`/`_mark_error_locked` — jedna metoda z lockiem
- **Log do dodania:** `logger.debug(f"Dict lock acquired by {threading.current_thread().name}")`

### BUG-003: Cicha awaria watermarku 🟡
- **Lokalizacja:** `bid/image_processing.py` linia 228, `bid/source_manager.py` linie 131, 173, 200
- **Opis:** Gdy `logo.png` nie istnieje w folderze źródłowym, `source_manager` loguje `logger.error()` ale kontynuuje. W `process_photo_task` logo jest szukane w `os.path.dirname(photo_path)` — brak fallbacku.
- **Warunki:** Brak pliku logo.png w folderze sesji
- **Wpływ:** Eksporty powstają BEZ watermarku; użytkownik nie wie o problemie do chwili zobaczenia eksportów
- **Naprawa:**
  1. Sprawdzić istnienie logo przy ładowaniu projektu (w `MainApp.__init__`)
  2. Wyświetlić `messagebox.showwarning()` w UI jeśli brak logo
  3. Dodać status w `DetailsPanel` — „⚠ Brak logo" przy dotkniętych folderach
  4. W przyszłości: generacja logo z SVG + nazwa folderu (plan na przyszłość)
- **Log do dodania:** `logger.warning(f"BRAK LOGO: folder {folder} — eksport bez watermarku")`

### BUG-004: Brak timeoutu na przetwarzanie zdjęć 🟡
- **Lokalizacja:** `bid/app.py` linia 269 (`self.executor.submit(...)`) i linia 280–293 (`check_futures`)
- **Opis:** Uszkodzony plik (np. truncated TIFF, corrupt RAW) może zawiesić worker na nieokreślony czas. `check_futures()` sprawdza `future.done()` ale nie ma timeoutu.
- **Warunki:** Uszkodzony plik źródłowy w projekcie
- **Wpływ:** Worker wieczne zablokowany → zmniejszona pula workerów → spowolnienie całego batcha
- **Naprawa:**
  1. Dodać `future.result(timeout=120)` (2 minuty max na zdjęcie)
  2. Implementować mechanizm anulowania (`concurrent.futures.CancelledError`)
  3. Po timeout → `_mark_error_locked(folder, photo, "Timeout")`
- **Log do dodania:** `logger.error(f"TIMEOUT: {folder}/{photo} po 120s")`

### BUG-005: Brak walidacji profilów eksportu 🟡
- **Lokalizacja:** `bid/config.py` linie 60–71 (`load_export_options`), `bid/image_processing.py` linie 188–191
- **Opis:** `load_export_options()` nie waliduje schematu JSON. Brakujący klucz `"size"` lub zły typ `"ratio"` powoduje crash w `process_photo_task`.
- **Warunki:** Ręczna edycja `export_option.json` z literówką
- **Wpływ:** `KeyError` lub `TypeError` w worker → zdjęcie ERROR bez jasnego powodu
- **Naprawa:**
  1. Dodać `validate_export_profile(profile: dict) -> list[str]` z listą błędów
  2. Walidować w `load_export_options()` po załadowaniu JSON
  3. Logować ostrzeżenia dla każdego nieprawidłowego profilu
- **Log do dodania:** `logger.warning(f"Profil '{name}': brakujący klucz '{key}'")`

### BUG-006: Utrata uchwytu pliku (file handle leak) 🟢
- **Lokalizacja:** `bid/source_manager.py` linia 59–61 (`_read_metadata`)
- **Opis:** `Image.open(file_path)` bez `with` statement. PIL zazwyczaj zwalnia, ale przy 500+ plikach na sieci mogą się nagromadzić otwarte uchwyty.
- **Warunki:** Duży projekt (>500 plików) na dysku sieciowym
- **Wpływ:** „Too many open files" error, spowolnione skanowanie
- **Naprawa:** Zamknij jawnie: `with Image.open(file_path) as img:` lub `img.close()` po użyciu

### BUG-007: Nieprawidłowy PROJECT_DIR w config.py 🟢
- **Lokalizacja:** `bid/config.py` linia 17
- **Opis:** `PROJECT_DIR = Path(__file__).parent.parent` zakłada stałą strukturę folderów. Przy uruchomieniu z Dockera lub innej lokalizacji ścieżka będzie błędna.
- **Warunki:** Uruchomienie spoza standardowej struktury katalogów
- **Wpływ:** Nie załaduje ustawień; `SystemExit(1)`
- **Naprawa:** Przyjmować `project_path` jako parametr (dependency injection)

---

## 4. PROBLEMY WYDAJNOŚCIOWE

### PERF-001: Skanowanie sieciowe blokujące ⚡⚡⚡
- **Lokalizacja:** `bid/source_manager.py` linie 166–182 (`create_source_dict`)
- **Pomiar:** 500 plików × 100ms latencja sieciowa = ~50s
- **Naprawa:**
  1. **Inkrementalne skanowanie:** Porównaj `os.stat().st_mtime` z cache zamiast otwierania każdego pliku
  2. **Lazy EXIF:** Odczytuj metadane EXIF dopiero przy wybraniu zdjęcia w UI
  3. **Batching:** Skanuj w partiach po 50 plików, aktualizuj UI między partiami
  4. **Local cache:** Zapisuj source_dict na dysk lokalny, skanuj tylko różnice

### PERF-002: PNG zawsze maksymalna jakość ⚡⚡
- **Lokalizacja:** `bid/image_processing.py` profil eksportu — `"quality": 9`
- **Opis:** PNG compression level 9 jest najwolniejszy. Dla 1500px obrazu = ~2-5s zapisu na dysku sieciowym
- **Naprawa:** Użyj `compress_level=6` w `Image.save()` — 3x szybciej, ~5% większy plik

### PERF-003: Brak cache podglądu ⚡⚡
- **Lokalizacja:** `bid/ui/preview.py` linia 51–62 (`change_img`)
- **Opis:** Każdy klik na foto = nowe `Image.open()` + resize. Brak LRU cache.
- **Naprawa:** Dodać `@lru_cache(maxsize=16)` na załadowane miniatury lub dict cache

### PERF-004: Regex XMP/IPTC bez pre-kompilacji ⚡
- **Lokalizacja:** `bid/image_processing.py` linie 425–428 (`get_all_exif`)
- **Opis:** Regex patterns kompilowane przy każdym wywołaniu `get_all_exif()`
- **Naprawa:** Przenieść `re.compile()` na poziom modułu

### PERF-005: Zbyt dużo workerów na dysku sieciowym ⚡
- **Lokalizacja:** `bid/app.py` linia 126: `self.max_workers = os.cpu_count() or 4`
- **Opis:** Na maszynie 8-core → 8 workerów → 8 równoczesnych zapisów na SMB share → bottleneck I/O
- **Naprawa:** Dodać konfigurowalną liczbę workerów w settings.json, domyślnie `min(cpu_count, 3)` dla sieci

### PERF-006: Pełny reload przy drobnej zmianie ⚡
- **Lokalizacja:** `bid/app.py` linia 318–327 (`update_source`), `bid/source_manager.py`
- **Opis:** Cykliczny `update_source_dict()` co 1000ms wykonuje pełny `os.walk()`
- **Naprawa:** Monitorować tylko nowe pliki (porównanie listy vs cache), nie otwierać plików

---

## 5. ULEPSZENIA UI/UX

### UX-001: Pasek postępu skanowania 🎨🎨🎨
- **Komponent:** `bid/app.py`, `bid/ui/source_tree.py`
- **Stan:** Brak informacji o postępie — UI zamrożony
- **Plan:** Dodać `ttk.Progressbar` + etykietę „Skanowanie: 127/500 plików..."
- **Istniejący TODO:** linia 138 `bid/app.py`

### UX-002: Komunikaty błędów dla użytkownika 🎨🎨🎨
- **Stan:** Błędy tylko w logach — użytkownik widzi pusty ekran
- **Plan:** Dodać `messagebox.showwarning()` dla: brak logo, uszkodzony JSON, timeout przetwarzania
- **Wzorzec:** Toast notification — pojawiają się na 5s w dolnym rogu

### UX-003: Modernizacja stylów Tkinter 🎨🎨
- **Stan:** Domyślny styl ttk + hardcoded kolory (#1e3a5f, #f0f0f0)
- **Plan:**
  1. Stworzyć `bid/ui/theme.py` z centralną paletą kolorów
  2. Dark theme: `bg="#1e1e1e"`, `fg="#d4d4d4"`, accent="#3794ff"
  3. Zastosować `ttk.Style()` globalnie
- **Istniejące TODO:** linie 32, 111 w `project_selector.py` i `setup_wizard.py`

### UX-004: Ikony statusu w drzewie plików 🎨🎨
- **Stan:** Kolorowanie całego wiersza — subtelne, trudne do odróżnienia
- **Plan:** Dodać ikony ●/✓/✗/⏳ przed nazwą pliku + zachować kolory tła
- **Istniejący TODO:** linia 49 `bid/ui/source_tree.py`

### UX-005: Przycisk Cancel podczas przetwarzania 🎨🎨
- **Stan:** Brak możliwości przerwania batch — trzeba zamknąć aplikację
- **Plan:** 
  1. Dodać `threading.Event` jako sygnał anulowania
  2. Przycisk „Anuluj" w pasku statusu (widoczny tylko podczas przetwarzania)
  3. Po anulowaniu — zostawić już przetworzone, oznaczyć resztę jako NEW

### UX-006: Podgląd watermarku 🎨
- **Stan:** Nie widać jak watermark wyglada na zdjęciu przed eksportem
- **Plan:** Overlay watermarku na podglądzie źródłowym (z obniżoną jakością dla szybkości)

### UX-007: Skróty klawiszowe 🎨
- **Stan:** Skróty istnieją ale nie są udokumentowane
- **Plan:** Menu → Pomoc → „Skróty klawiszowe" z listą dostępnych akcji

### UX-008: Walidacja ścieżek w SetupWizard 🎨
- **Lokalizacja:** `bid/ui/setup_wizard.py` linia 224–247 (`_on_finish`)
- **Stan:** Brak sprawdzenia czy source ≠ export folder
- **Plan:** Dodać walidację + ostrzeżenie przed nadpisaniem

### UX-009: Hardcoded polskie stringi 🎨
- **Stan:** Wszystkie stringi UI po polsku, brak i18n
- **Plan na 2027:** Ekstrakcja do `translations.json`, framework i18n
- **Na teraz:** Komentarz `# i18n:` przy każdym stringu UI

---

## 6. JAKOŚĆ KODU

### CODE-001: Brak type hints
- **Pliki:** `bid/source_manager.py`, `bid/image_processing.py` częściowo, `bid/ui/*`
- **Stan:** Niektóre funkcje mają hinty, inne nie
- **Plan:** Dodać type hints do wszystkich publicznych funkcji (atrybut `-> ReturnType`)

### CODE-002: Brak walidacji wejścia
- **Pliki:** `bid/config.py`, `bid/source_manager.py`
- **Plan:** Stworzyć `bid/validators.py` z funkcjami walidacji ścieżek, profili, EXIF

### CODE-003: Niespójna obsługa błędów
- **Wzorzec A** (config.py): `try/except → logger.critical → SystemExit(1)`
- **Wzorzec B** (source_manager.py): `try/except → logger.error → return None`
- **Wzorzec C** (image_processing.py): `try/except → return {"success": False, "error_msg": ...}`
- **Plan:** Hierarchia wyjątków: `YapaError → ConfigError, ImageProcessingError, SourceManagerError`

### CODE-004: Magic numbers
- `bid/app.py:126` → `os.cpu_count() or 4`
- `bid/app.py:273` → `self.after(100, ...)` (100ms poll)
- `bid/app.py:351` → `self.after(1000, ...)` (1s cycle)
- `bid/image_processing.py:19` → `@lru_cache(maxsize=32)`
- `bid/project_manager.py:34` → `recent[:10]` (max 10 recent)
- **Plan:** Zdefiniować stałe w `bid/constants.py`

### CODE-005: Duplikacja kodu logo
- `bid/source_manager.py` linie 131, 173, 200 — ten sam check logo.png w 3 miejscach
- **Plan:** Wydzielić `_check_logo_exists(folder_path: Path) -> bool`

### CODE-006: Logger initialization coupling
- **Stan:** Logger setup w `main.py` — nie jest reużywalny w testach
- **Plan:** Wydzielić do `bid/logging_config.py` z możliwością override w testach

---

## 7. BEZPIECZEŃSTWO

### SEC-001: Brak sanityzacji nazw plików
- **Lokalizacja:** `bid/image_processing.py` linia 244–245, `bid/source_manager.py`
- **Opis:** Nazwa pliku eksportu budowana z `folder_name` + `created_date` — bez sanityzacji znaków specjalnych
- **Ryzyko:** Na Windows znaki `<>:"/\|?*` w nazwie folderu → crash zapisu
- **Naprawa:** `re.sub(r'[<>:"/\\|?*]', '_', filename)`

### SEC-002: Path traversal w source_folder
- **Lokalizacja:** `bid/source_manager.py` `os.walk(source_folder)` — bez walidacji że ścieżka nie wychodzi poza dozwolony zakres
- **Ryzyko niskie:** Użytkownik sam ustawia ścieżki, ale symlinki mogą prowadzić poza source
- **Naprawa:** `os.path.realpath()` + sprawdzenie prefiksu

### SEC-003: JSON injection w metadanych EXIF
- **Lokalizacja:** `bid/image_processing.py` `get_all_exif()` → dane z EXIF trafiają do JSON
- **Ryzyko:** Złośliwe EXIF mogą zawierać bardzo długie stringi (DoS przy serializacji)
- **Naprawa:** Obcinać wartości EXIF do np. 1000 znaków

---

## 8. PRZYGOTOWANIE DO MIGRACJI DOCKER/WEB

### DOCKER-001: Separacja logiki od UI (MVC prep)
- **Stan:** `bid/app.py` miesza logikę biznesową z Tkinter
- **Plan (do marca 2027):**
  1. Wydzielić `bid/core/processor.py` — czysta logika przetwarzania (bez tk import)
  2. Wydzielić `bid/core/project.py` — zarządzanie projektami
  3. `bid/app.py` staje się cienkim adapterem UI → core
  4. Nowy `bid/web/app.py` (Flask/FastAPI) korzysta z tego samego core

### DOCKER-002: JSON event integration point
- **Stan:** Planowana integracja z zewnętrznym JSON opisującym eventy czasowe
- **Interfejs:** `bid/event_matcher.py` (do implementacji)
  ```python
  def match_photos_to_events(
      source_dict: dict,
      events_json: list[dict],  # [{name, start_time, end_time, export_folder}]
  ) -> dict[str, list[str]]:
      """Przypisuje zdjęcia do eventów na podstawie DateTimeOriginal."""
  ```
- **Wymagania:**
  - Parsowanie czasu z EXIF DateTimeOriginal
  - Porównanie z przedziałami czasowymi z JSON
  - Eksport do odpowiednich podfolderów

### DOCKER-003: SVG → PNG logo generation
- **Stan:** Planowana generacja logo z SVG + nazwa folderu (twórcy)
- **Interfejs:** `bid/logo_generator.py` (do implementacji)
  ```python
  def generate_logo(
      svg_template_path: str,
      creator_name: str,
      output_path: str,
      size: tuple[int, int] = (600, 200),
  ) -> str:
      """Generuje PNG logo z szablonu SVG + nazwy twórcy."""
  ```

---

## 9. PODSUMOWANIE PRIORYTETÓW

### Pilne (przed eventem 2026)
| # | Problem | Lokalizacja | Trudność |
|---|---------|-------------|----------|
| BUG-001 | Blokowanie UI na sieci | app.py, source_manager.py | Średnia |
| BUG-002 | Race condition dict | app.py | Niska |
| BUG-003 | Cicha awaria watermarku | image_processing.py | Niska |
| UX-001 | Pasek postępu | app.py, UI | Średnia |
| UX-002 | Komunikaty błędów | Wszystkie moduły | Niska |
| PERF-005 | Za dużo workerów na sieci | app.py | Niska |

### Ważne (po evencie 2026)
| # | Problem | Lokalizacja | Trudność |
|---|---------|-------------|----------|
| BUG-004 | Timeout przetwarzania | app.py | Niska |
| BUG-005 | Walidacja profili | config.py | Niska |
| PERF-001 | Inkrementalne skanowanie | source_manager.py | Średnia |
| PERF-002 | PNG compression level | image_processing.py | Niska |
| CODE-003 | Hierarchia wyjątków | Nowy moduł | Średnia |
| CODE-006 | Logger separation | Nowy moduł | Niska |
| **TESTY** | Automatyczne testy | tests/ | Wysoka |

### Planowane (2027 — migracja Docker/Web)
| # | Problem | Lokalizacja | Trudność |
|---|---------|-------------|----------|
| DOCKER-001 | Separacja MVC | app.py → core/ | Wysoka |
| DOCKER-002 | JSON event matching | Nowy moduł | Średnia |
| DOCKER-003 | SVG → PNG logo gen | Nowy moduł | Średnia |
| UX-003 | Dark theme | ui/theme.py | Średnia |
| UX-009 | Internalizacja i18n | Wszystkie UI | Wysoka |

---

*Koniec raportu audytu. Szczegóły implementacji w `IMPLEMENTATION_GUIDE.md`.*
