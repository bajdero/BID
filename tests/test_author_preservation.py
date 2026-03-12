"""
tests/test_author_preservation.py
TEST-AUTHOR-001 / TEST-AUTHOR-002 — Zachowanie pola Author (Artist) w EXIF.

Reguły:
  - Jeśli oryginalne zdjęcie ma pole Artist → wyeksportowany plik MUSI mieć ten sam Artist.
  - Jeśli oryginalne zdjęcie NIE ma pola Artist (lub jest puste) →
      wyeksportowany plik MUSI mieć Artist = folder_name.

Zawiera testy jednostkowe i regresyjne.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pytest
from PIL import Image
from PIL.ExifTags import IFD

from bid.image_processing import process_photo_task, get_all_exif


# ---------------------------------------------------------------------------
# Pomocnicze
# ---------------------------------------------------------------------------

_EXPORT_SETTINGS_JPEG = {
    "test_profile": {
        "size_type": "longer",
        "size": 800,
        "format": "JPEG",
        "quality": 85,
        "logo_required": False,
        "logo": {
            "landscape": {"size": 200, "opacity": 60, "x_offset": 10, "y_offset": 10, "placement": "bottom-right"},
            "portrait":  {"size": 240, "opacity": 60, "x_offset": 10, "y_offset": 10, "placement": "bottom-right"},
        },
    }
}


def _read_exif_artist(path: Path) -> str | None:
    """Odczytuje pole Artist (EXIF tag 315 = 0x013B) z pliku JPEG."""
    with Image.open(path) as img:
        raw_exif = img.getexif()
        artist = raw_exif.get(315)
        if isinstance(artist, bytes):
            return artist.decode("utf-8", errors="ignore").strip("\x00 ")
        return str(artist).strip() if artist else None


def _create_test_image(path: Path, width: int = 1200, height: int = 800,
                        artist: str | None = None) -> Path:
    """Tworzy testowy obraz JPEG z lub bez pola Artist."""
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (width, height), color="green")
    exif = img.getexif()
    if artist is not None:
        exif[315] = artist  # Artist tag (0x013B)
    ifd = exif.get_ifd(IFD.Exif)
    ifd[0x9003] = "2026:01:15 10:00:00"  # DateTimeOriginal
    img.save(path, "JPEG", exif=exif.tobytes())
    return path


# ---------------------------------------------------------------------------
# TEST-AUTHOR-001: Zdjęcie Z polem Artist → zachowaj original Artist
# ---------------------------------------------------------------------------

class TestAuthorPreservationWithArtist:
    """Zdjęcia z istniejącym Artist w EXIF — eksport musi zachować oryginał."""

    def test_artist_preserved_in_jpeg_export(self, tmp_path):
        """TEST-AUTHOR-001a: Artist z EXIF jest zachowany po eksporcie do JPEG."""
        session_dir = tmp_path / "source" / "TestSession"
        photo = _create_test_image(session_dir / "test.jpg", artist="Jan_Kowalski")

        result = process_photo_task(
            photo_path=str(photo),
            folder_name="TestSession",
            photo_name="test.jpg",
            created_date="2026:01:15 10:00:00",
            export_folder=str(tmp_path / "export"),
            export_settings=_EXPORT_SETTINGS_JPEG,
            existing_exports={},
        )

        assert result["success"] is True, f"Eksport nieudany: {result.get('error_msg')}"
        exported = Path(result["exported"]["test_profile"])
        assert exported.exists()

        artist_out = _read_exif_artist(exported)
        assert artist_out == "Jan_Kowalski", (
            f"Artist powinien być zachowany jako 'Jan_Kowalski', ale jest: {artist_out!r}"
        )

    def test_artist_not_overwritten_by_folder_name(self, tmp_path):
        """TEST-AUTHOR-001b: folder_name NIE nadpisuje oryginalnego Artist."""
        session_dir = tmp_path / "source" / "ZupełnieInnyFolder"
        photo = _create_test_image(session_dir / "foto.jpg", artist="Prawdziwy_Autor")

        result = process_photo_task(
            photo_path=str(photo),
            folder_name="ZupełnieInnyFolder",
            photo_name="foto.jpg",
            created_date="2026:01:15 10:00:00",
            export_folder=str(tmp_path / "export"),
            export_settings=_EXPORT_SETTINGS_JPEG,
            existing_exports={},
        )

        assert result["success"] is True
        exported = Path(result["exported"]["test_profile"])

        artist_out = _read_exif_artist(exported)
        assert artist_out == "Prawdziwy_Autor", (
            f"Artist powinien być 'Prawdziwy_Autor', nie folder_name. Otrzymano: {artist_out!r}"
        )
        assert artist_out != "ZupełnieInnyFolder", (
            "folder_name nie powinien nadpisywać oryginalnego Artist."
        )

    def test_original_artist_via_get_all_exif(self, tmp_path):
        """TEST-AUTHOR-001c: get_all_exif() widzi tego samego Artist co oryginał."""
        session_dir = tmp_path / "source" / "SessionABC"
        photo = _create_test_image(session_dir / "img.jpg", artist="Studio_XYZ")

        result = process_photo_task(
            photo_path=str(photo),
            folder_name="SessionABC",
            photo_name="img.jpg",
            created_date="2026:01:15 10:00:00",
            export_folder=str(tmp_path / "export"),
            export_settings=_EXPORT_SETTINGS_JPEG,
            existing_exports={},
        )

        assert result["success"] is True
        exported = Path(result["exported"]["test_profile"])

        with Image.open(exported) as img_out:
            exif_dict = get_all_exif(img_out)

        assert exif_dict.get("Artist") == "Studio_XYZ", (
            f"get_all_exif() powinno zwrócić Artist='Studio_XYZ', ale: {exif_dict.get('Artist')!r}"
        )


# ---------------------------------------------------------------------------
# TEST-AUTHOR-002: Zdjęcie BEZ pola Artist → folder_name jako Artist
# ---------------------------------------------------------------------------

class TestAuthorFallbackToFolderName:
    """Zdjęcia bez Artist w EXIF — BID musi użyć folder_name jako Author."""

    def test_folder_name_used_as_artist_when_no_exif_artist(self, tmp_path):
        """TEST-AUTHOR-002a: Eksport ustawia folder_name jako Artist gdy brak w EXIF."""
        session_dir = tmp_path / "source" / "Fotografik_Nowak"
        photo = _create_test_image(session_dir / "img.jpg", artist=None)

        result = process_photo_task(
            photo_path=str(photo),
            folder_name="Fotografik_Nowak",
            photo_name="img.jpg",
            created_date="2026:01:15 10:00:00",
            export_folder=str(tmp_path / "export"),
            export_settings=_EXPORT_SETTINGS_JPEG,
            existing_exports={},
        )

        assert result["success"] is True, f"Eksport nieudany: {result.get('error_msg')}"
        exported = Path(result["exported"]["test_profile"])

        artist_out = _read_exif_artist(exported)
        assert artist_out == "Fotografik_Nowak", (
            f"Artist powinien być 'Fotografik_Nowak' (folder), ale jest: {artist_out!r}"
        )

    def test_empty_artist_string_treated_as_missing(self, tmp_path):
        """TEST-AUTHOR-002b: Pusty string w Artist EXIF → traktowane jak brak → folder_name."""
        session_dir = tmp_path / "source" / "StudioABC"
        photo = _create_test_image(session_dir / "empty_art.jpg", artist="")

        result = process_photo_task(
            photo_path=str(photo),
            folder_name="StudioABC",
            photo_name="empty_art.jpg",
            created_date="2026:01:15 10:00:00",
            export_folder=str(tmp_path / "export"),
            export_settings=_EXPORT_SETTINGS_JPEG,
            existing_exports={},
        )

        assert result["success"] is True
        exported = Path(result["exported"]["test_profile"])

        artist_out = _read_exif_artist(exported)
        assert artist_out == "StudioABC", (
            f"Pusty Artist → fallback na folder_name 'StudioABC', ale jest: {artist_out!r}"
        )

    def test_warning_logged_when_artist_missing(self, tmp_path, caplog):
        """TEST-AUTHOR-002c: LOG WARNING emitowany gdy oryginał nie ma Artist."""
        session_dir = tmp_path / "source" / "LogTest"
        photo = _create_test_image(session_dir / "no_artist.jpg", artist=None)

        with caplog.at_level(logging.WARNING, logger="BID"):
            process_photo_task(
                photo_path=str(photo),
                folder_name="LogTest",
                photo_name="no_artist.jpg",
                created_date="2026:01:15 10:00:00",
                export_folder=str(tmp_path / "export"),
                export_settings=_EXPORT_SETTINGS_JPEG,
                existing_exports={},
            )

        warning_msgs = [r.message for r in caplog.records if r.levelno == logging.WARNING]
        assert any("LogTest" in str(m) for m in warning_msgs), (
            f"Oczekiwano ostrzeżenia z 'LogTest' w logach BID, ale: {warning_msgs}"
        )


# ---------------------------------------------------------------------------
# TEST-AUTHOR-REG-001 / REG-002: Regresja — Author po pełnym pipeline
# ---------------------------------------------------------------------------

class TestAuthorRegressionFullPipeline:
    """Regression tests — Author przez pełny pipeline source→export."""

    def test_original_author_survives_full_pipeline(self, tmp_path):
        """TEST-AUTHOR-REG-001: Oryginalny Artist zachowany po pełnym pipelinie.

        Scenariusz:
        1. Zdjęcie z Artist="Oryginalny_Fotograf" w EXIF
        2. Eksport przez process_photo_task z folder_name="Sesja_Weselna_2026"
        3. Artist w eksporcie == "Oryginalny_Fotograf" (NIE folder_name)
        """
        folder_name = "Sesja_Weselna_2026"
        original_artist = "Oryginalny_Fotograf"
        session_dir = tmp_path / "source" / folder_name

        photo = _create_test_image(
            session_dir / "wedding.jpg",
            width=2000, height=1333,
            artist=original_artist,
        )

        result = process_photo_task(
            photo_path=str(photo),
            folder_name=folder_name,
            photo_name="wedding.jpg",
            created_date="2026:06:15 12:00:00",
            export_folder=str(tmp_path / "export"),
            export_settings=_EXPORT_SETTINGS_JPEG,
            existing_exports={},
        )

        assert result["success"] is True, f"Pipeline error: {result.get('error_msg')}"
        exported_path = Path(result["exported"]["test_profile"])
        assert exported_path.exists()

        artist_in_export = _read_exif_artist(exported_path)
        assert artist_in_export == original_artist, (
            f"Regresja: Artist w eksporcie to '{artist_in_export}', "
            f"oczekiwano '{original_artist}'"
        )
        assert artist_in_export != folder_name, (
            f"Regresja: folder_name '{folder_name}' nadpisał oryginalnego Artist!"
        )

    def test_fallback_author_portrait_orientation(self, tmp_path):
        """TEST-AUTHOR-REG-002: Fallback na folder_name działa dla orientacji pionowej."""
        folder_name = "PortraitSession"
        session_dir = tmp_path / "source" / folder_name

        photo = _create_test_image(
            session_dir / "portrait.jpg",
            width=1000, height=1500,  # pionowy
            artist=None,  # brak → fallback na folder_name
        )

        result = process_photo_task(
            photo_path=str(photo),
            folder_name=folder_name,
            photo_name="portrait.jpg",
            created_date="2026:06:15 12:00:00",
            export_folder=str(tmp_path / "export"),
            export_settings=_EXPORT_SETTINGS_JPEG,
            existing_exports={},
        )

        assert result["success"] is True
        exported_path = Path(result["exported"]["test_profile"])

        artist_out = _read_exif_artist(exported_path)
        assert artist_out == folder_name, (
            f"Fallback dla orientacji pionowej: {artist_out!r}, oczekiwano '{folder_name}'"
        )
