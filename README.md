# BID — Batch Image Delivery

Narzędzie do automatycznego skalowania zdjęć, nakładania watermarku i eksportu do folderów delivery.  
Tool for automatic image scaling, watermark overlay, and delivery folder export.

---

## Wymagania systemowe / System Requirements

| Element | Minimalna wersja |
|---|---|
| Python | 3.10+ |
| Pillow | 10.0+ |
| pytest | 7.0+ (tylko do testów) |
| pytest-html | 4.0+ (tylko do testów) |
| tkinter | (wbudowany w Python na Windows; osobny pakiet na Fedorze) |

---

## Instalacja — Windows

### 1. Sklonuj repozytorium

```bat
git clone <URL_REPO>
cd BID
```

### 2. Uruchom skrypt instalacyjny (jednorazowo)

```bat
setup.bat
```

Skrypt automatycznie:
- tworzy środowisko wirtualne `.venv\`
- instaluje zależności z `requirements.txt`

### 3. Aktywuj środowisko przed każdym uruchomieniem

```bat
.venv\Scripts\activate.bat
```

### 4. Uruchom aplikację

```bat
python main.py
```

---

## Instalacja — Linux (Fedora / RHEL)

### 1. Zainstaluj tkinter (wymagane systemowo, poza pip)

```bash
sudo dnf install python3-tkinter
```

> Na Ubuntu/Debian: `sudo apt install python3-tk`

### 2. Sklonuj repozytorium

```bash
git clone <URL_REPO>
cd BID
```

### 3. Uruchom skrypt instalacyjny (jednorazowo)

```bash
chmod +x setup.sh
./setup.sh
```

### 4. Aktywuj środowisko przed każdym uruchomieniem

```bash
source .venv/bin/activate
```

### 5. Uruchom aplikację

```bash
python main.py
```

---

## Konfiguracja / Configuration

### `settings.json`

```json
{
    "source_folder": "C:/_YAPA/Yapa2024/source",
    "export_folder":  "C:/_YAPA/Yapa2024/export"
}
```

| Klucz | Opis |
|---|---|
| `source_folder` | Folder z podfolderami sesji (każdy podfolder = jeden autor/sesja) |
| `export_folder` | Folder docelowy; podkatalogi delivery tworzone automatycznie |

### `export_option.json`

Definiuje profile eksportu. Każdy profil (`fb`, `insta`, `insta_q`, `lzp`) zawiera:

| Klucz | Opis |
|---|---|
| `size_type` | `"longer"` / `"width"` / `"height"` — która krawędź wyznacza skalowanie |
| `size` | Docelowy rozmiar krawędzi w pikselach |
| `format` | `"JPEG"` lub `"PNG"` |
| `quality` | Jakość JPEG (0–95) lub poziom kompresji PNG (0–9) |
| `ratio` | *(opcjonalne)* lista akceptowanych aspect ratio (np. `[0.8, 1.25]`) |
| `logo.landscape` / `logo.portrait` | Ustawienia watermarku dla poziomego / pionowego zdjęcia |

### Struktura folderu źródłowego

```
source/
├── Jan_Kowalski/          ← nazwa autora/sesji
│   ├── logo.png           ← watermark (PNG z kanałem alpha) — WYMAGANY
│   ├── DSC07100.tif
│   └── DSC07101.tif
└── Anna_Nowak/
    ├── logo.png
    └── ...
```

> **Każdy podfolder musi zawierać `logo.png`** — brak pliku powoduje błąd przetwarzania.

---

## Opcje wiersza poleceń / CLI Options

```
python main.py [--settings PATH] [--export-options PATH] [--debug]
```

| Flaga | Opis |
|---|---|
| `--settings PATH` | Niestandardowa ścieżka do `settings.json` |
| `--export-options PATH` | Niestandardowa ścieżka do `export_option.json` |
| `--debug` | Włącza poziom logowania DEBUG |

---

## Testy / Testing

Do uruchamiania testów wykorzystywany jest framework `pytest`. W projekcie zainstalowany jest również plugin `pytest-html` do generowania czytelnych raportów.

### Uruchamianie wszystkich testów

```bash
pytest tests/ -v
```

W przypadku problemów z wykryciem komendy `pytest` w wierszu poleceń Windows:

```bash
python -m pytest tests/ -v
```

### Testy jednostkowe (unit tests)

Testy jednostkowe weryfikują zachowanie pojedynczych modułów w izolacji:

```bash
# Wszystkie testy jednostkowe
pytest tests/test_image_processing.py tests/test_config.py tests/test_source_manager.py tests/test_project_manager.py -v

# Pojedynczy moduł
pytest tests/test_image_processing.py -v
pytest tests/test_source_manager.py -v
pytest tests/test_config.py -v
pytest tests/test_project_manager.py -v
```

### Testy integracyjne

Testy integracyjne weryfikują współpracę między modułami:

```bash
# Wszystkie testy integracyjne
pytest tests/test_workflows.py tests/test_integrity.py tests/test_config_processing.py -v

# Workflow przetwarzania obrazów (6 testów)
pytest tests/test_workflows.py -v

# Integralność systemu plików (4 testy)
pytest tests/test_integrity.py -v

# Interakcja konfiguracji z przetwarzaniem (4 testy)
pytest tests/test_config_processing.py -v
```

### Przydatne opcje

```bash
# Zatrzymaj na pierwszym błędzie
pytest tests/ -x -v

# Pokaż logi na poziomie DEBUG
pytest tests/ -v --log-cli-level=DEBUG

# Wygeneruj raport HTML
pytest tests/ --html=report.html --self-contained-html
```

Po zakończeniu testów raport HTML dostępny jest w pliku `report.html` w głównym katalogu projektu.

### Struktura testów

```
tests/
├── conftest.py                  ← Globalne fixtures (log_capture, full_test_project, …)
├── test_image_processing.py     ← Testy jednostkowe: skalowanie, watermark, EXIF
├── test_config.py               ← Testy jednostkowe: ładowanie konfiguracji
├── test_source_manager.py       ← Testy jednostkowe: skanowanie, source_dict
├── test_project_manager.py      ← Testy jednostkowe: zarządzanie projektami
├── test_workflows.py            ← Integracyjne: pełny workflow eksportu
├── test_integrity.py            ← Integracyjne: integralność systemu plików
└── test_config_processing.py    ← Integracyjne: konfiguracja → przetwarzanie
```

Zaleca się uruchamianie testów z aktywowanym środowiskiem wirtualnym (krok 3 instalacji).

---

## Struktura projektu / Project Structure

```
BID/
├── main.py                  ← Punkt wejścia / entry point
├── requirements.txt
├── setup.bat                ← Instalator Windows
├── setup.sh                 ← Instalator Linux/macOS
├── settings.json
├── export_option.json
├── src/
│   └── default_prev.png     ← Placeholder podglądu
└── bid/                     ← Package
    ├── app.py               ← MainApp (główna logika)
    ├── config.py            ← Ładowanie konfiguracji
    ├── image_processing.py  ← Operacje PIL (skalowanie, watermark, EXIF)
    ├── source_manager.py    ← Skanowanie folderów, source_dict
    └── ui/
        ├── preview.py       ← Widget podglądu zdjęcia
        └── source_tree.py   ← Widget drzewa plików
```

---

## Logi

Logi zapisywane są automatycznie do katalogu `logs/` obok `main.py`.  
Każde uruchomienie tworzy nowy plik w formacie `YYYY-MM-DD_HH_MM_SS.log`.

---

## Licencja / License

Zobacz plik [LICENSE](LICENSE).
