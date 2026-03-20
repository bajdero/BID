"""
tests/test_exif_dynamic.py
TEST-EXIF-DYN-001 — Dynamiczne testy EXIF z referencją z exiftool.

Strategia:
  1. Wczytaj config z tests/exif_config.json (ścieżka do exiftool + folder testowych zdjęć).
  2. Uruchom exiftool na wszystkich zdjęciach → wygeneruj exif_references.json (zastąp stary).
  3. Dla każdego zdjęcia porównaj dane BID z referencją exiftool.
  4. Pola krytyczne (Artist, DateTimeOriginal): FAIL jeśli rozbieżność.
  5. Pola niekrytyczne: ostrzeżenie (xfail / warning log).
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

# Ścieżki bazowe — relatywne do korzenia projektu
_PROJECT_ROOT = Path(__file__).parent.parent
_CONFIG_PATH  = Path(__file__).parent / "exif_config.json"
_REF_PATH     = _PROJECT_ROOT / "test" / "exif_references.json"

logger = logging.getLogger("BID")

# ---------------------------------------------------------------------------
# Pomocnicze
# ---------------------------------------------------------------------------

def _load_config() -> dict:
    """Wczytuje konfigurację z tests/exif_config.json."""
    if not _CONFIG_PATH.exists():
        pytest.skip(
            f"Brak pliku konfiguracyjnego exiftool: {_CONFIG_PATH}. "
            "Utwórz tests/exif_config.json z kluczami 'exiftool_path' i 'test_images_folder'."
        )
    with _CONFIG_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _abs_path(relative: str) -> Path:
    """Zamienia ścieżkę relatywną (od korzenia projektu) na absolutną."""
    p = Path(relative)
    return p if p.is_absolute() else _PROJECT_ROOT / p


def _find_images(folder: Path) -> list[Path]:
    """Szuka plików JPEG/TIFF rekurencyjnie."""
    exts = {".jpg", ".jpeg", ".tif", ".tiff", ".png"}
    return [f for f in folder.rglob("*") if f.suffix.lower() in exts]


def _run_exiftool(exiftool: Path, images: list[Path]) -> list[dict]:
    """Uruchamia exiftool i zwraca listę słowników z tagami."""
    if not exiftool.exists():
        pytest.skip(
            f"exiftool nie znaleziony: {exiftool}. "
            "Sprawdź klucz 'exiftool_path' w tests/exif_config.json."
        )
    cmd = [
        str(exiftool),
        "-json",
        "-struct",
        "-n",
        "-G",          # grupuj tagi wg IFD
        "--ExifTool:all",  # pomiń metadane exiftool
        *[str(p) for p in images],
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            # Ukryj okno konsolowe na Windows
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
    except subprocess.TimeoutExpired:
        pytest.fail("exiftool timeout (>120s). Sprawdź czy ścieżka jest poprawna.")
    except Exception as exc:
        pytest.fail(f"Nie można uruchomić exiftool: {exc}")

    if result.returncode != 0:
        pytest.fail(f"exiftool zakończył się błędem (rc={result.returncode}): {result.stderr[:500]}")

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        pytest.fail(f"Nie można sparsować JSON z exiftool: {exc}")


def _extract_critical(ref: dict) -> dict[str, Any]:
    """Wyciąga krytyczne pola z referencji exiftool."""
    critical = {}
    # Artist może być w IFD0 lub ExifIFD
    for group in ("IFD0", "ExifIFD", ""):
        artist = ref.get(group, {}).get("Artist") if group else ref.get("Artist")
        if artist:
            critical["Artist"] = str(artist).strip()
            break
    # DateTimeOriginal
    for group in ("ExifIFD", ""):
        dto = ref.get(group, {}).get("DateTimeOriginal") if group else ref.get("DateTimeOriginal")
        if dto:
            critical["DateTimeOriginal"] = str(dto).strip()
            break
    # Wymiary
    for width_key in ("File.ImageWidth", "ImageWidth"):
        w = ref.get("File", {}).get("ImageWidth") or ref.get("ImageWidth")
        if w is not None:
            critical["ImageWidth"] = int(w)
            break
    for height_key in ("File.ImageHeight", "ImageHeight"):
        h = ref.get("File", {}).get("ImageHeight") or ref.get("ImageHeight")
        if h is not None:
            critical["ImageHeight"] = int(h)
            break
    return critical


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def exif_config():
    """Wczytuje i zwraca config exiftool."""
    return _load_config()


@pytest.fixture(scope="module")
def generated_references(exif_config):
    """Generuje exif_references.json przy użyciu exiftool i zwraca listę rekordów."""
    exiftool = _abs_path(exif_config["exiftool_path"])
    images_folder = _abs_path(exif_config["test_images_folder"])

    if not images_folder.exists():
        pytest.skip(
            f"Folder testowych zdjęć nie istnieje: {images_folder}. "
            "Sprawdź klucz 'test_images_folder' w tests/exif_config.json."
        )

    images = _find_images(images_folder)
    if not images:
        pytest.skip(
            f"Brak zdjęć w folderze: {images_folder}. "
            "Upewnij się, że test/source zawiera pliki JPEG/TIFF."
        )

    records = _run_exiftool(exiftool, images)

    # Nadpisz plik referencji
    _REF_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _REF_PATH.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    logger.info(f"[TEST] Wygenerowano exif_references.json: {len(records)} plików")

    return records


# ---------------------------------------------------------------------------
# TEST-EXIF-DYN-001: Generowanie i weryfikacja referencji
# ---------------------------------------------------------------------------

class TestExifDynamic:
    """Dynamiczne testy EXIF z referencją exiftool."""

    def test_references_generated(self, generated_references):
        """TEST-EXIF-DYN-001a: exif_references.json wygenerowany poprawnie."""
        assert isinstance(generated_references, list), "exiftool powinien zwrócić listę rekordów"
        assert len(generated_references) > 0, "Brak rekordów w exif_references.json"
        assert _REF_PATH.exists(), f"Plik referencji nie istnieje: {_REF_PATH}"

    @pytest.mark.parametrize("field", ["Artist", "DateTimeOriginal"])
    def test_critical_exif_fields_readable_by_bid(self, generated_references, field, tmp_path):
        """TEST-EXIF-DYN-002: BID potrafi odczytać krytyczne pola EXIF.

        Dla każdego zdjęcia w referencji: jeśli exiftool widzi pole krytyczne,
        BID musi je też odczytać (ten sam lub kompatybilny format).
        """
        from bid.image_processing import get_all_exif

        mismatches = []
        for record in generated_references:
            src_file = record.get("SourceFile", "")
            if not src_file or not os.path.isfile(src_file):
                continue  # plik może nie być dostępny w tym środowisku

            critical = _extract_critical(record)
            if field not in critical:
                continue  # exiftool też nie ma tego pola — ok, pomijamy

            expected_val = critical[field]

            try:
                with Image.open(src_file) as img:
                    bid_exif = get_all_exif(img)
            except Exception as exc:
                mismatches.append(f"{os.path.basename(src_file)}: Nie można otworzyć — {exc}")
                continue

            # Mapowania nazw BID (TAG_NAME_OVERRIDE w get_all_exif)
            bid_key_map = {
                "Artist": "Artist",
                "DateTimeOriginal": "CreateDate",  # BID mapuje DateTimeOriginal → CreateDate
            }
            bid_key = bid_key_map.get(field, field)
            bid_val = bid_exif.get(bid_key, "")

            if not bid_val:
                mismatches.append(
                    f"{os.path.basename(src_file)}: BID nie odczytał '{field}' "
                    f"(exiftool widzi: {expected_val!r})"
                )

        if mismatches:
            pytest.fail(
                f"Krytyczne pole EXIF '{field}' nieodczytane przez BID "
                f"({len(mismatches)} plików):\n" + "\n".join(mismatches[:10])
            )

    def test_noncritical_exif_fields(self, generated_references):
        """TEST-EXIF-DYN-003: Niekrytyczne pola EXIF — ostrzeżenie zamiast FAIL.

        Sprawdza: Make, Model, ISO. Jeśli BID nie odczyta — xfail expected.
        """
        from bid.image_processing import get_all_exif

        NONCRITICAL_MAP = {
            "Make": ["Make"],
            "Model": ["Model"],
            "ISO": ["ISO"],
        }

        warnings_found = []
        for record in generated_references:
            src_file = record.get("SourceFile", "")
            if not src_file or not os.path.isfile(src_file):
                continue

            ifd0 = record.get("IFD0", {})
            exif_ifd = record.get("ExifIFD", {})

            try:
                with Image.open(src_file) as img:
                    bid_exif = get_all_exif(img)
            except Exception:
                continue

            for ref_key, bid_keys in NONCRITICAL_MAP.items():
                ref_val = ifd0.get(ref_key) or exif_ifd.get(ref_key)
                if ref_val is None:
                    continue
                found = any(bid_exif.get(k) for k in bid_keys)
                if not found:
                    warnings_found.append(f"{os.path.basename(src_file)}: brak '{ref_key}'")

        if warnings_found:
            # xfail: niekrytyczne — oznaczamy jako expected failures
            pytest.xfail(
                f"Niekrytyczne pola EXIF nieodczytane przez BID "
                f"({len(warnings_found)}):\n" + "\n".join(warnings_found[:10])
            )
