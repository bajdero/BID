"""
bid/app.py
Główna klasa aplikacji — MainApp.

Odpowiada za:
  - ładowanie konfiguracji (przez bid.config)
  - budowanie i aktualizację source_dict (przez bid.source_manager)
  - sekwencyjne przetwarzanie zdjęć w tle (Threading)
  - zarządzanie UI (za pomocą komponentów z bid.ui)
"""
from __future__ import annotations

import datetime
import logging
import os
import time
from pathlib import Path
from threading import Thread

import tkinter as tk
from PIL.PngImagePlugin import PngInfo

from bid import config as cfg_module
from bid.config import PROJECT_DIR
from bid.image_processing import (
    apply_watermark,
    exif_clean_from_tiff,
    image_resize,
    image_convert_to_srgb,
)
from bid.source_manager import (
    SourceState,
    check_integrity,
    create_source_dict,
    load_source_dict,
    save_source_dict,
    update_source_dict,
)
from bid.ui.preview import PrevWindow
from bid.ui.source_tree import SourceTree

logger = logging.getLogger("Yapa_CM")


class MainApp(tk.Tk):
    """Główne okno aplikacji BID."""

    def __init__(
        self,
        settings_path: Path | None = None,
        export_options_path: Path | None = None,
    ) -> None:
        """
        Args:
            settings_path:       Opcjonalna niestandardowa ścieżka do settings.json.
            export_options_path: Opcjonalna niestandardowa ścieżka do export_option.json.
        """
        super().__init__()
        self.title("BID — Batch Image Delivery")

        # ----------------------------------------------------------------
        # Wczytywanie konfiguracji
        # ----------------------------------------------------------------
        self.settings = cfg_module.load_settings(settings_path)
        self.export_settings = cfg_module.load_export_options(export_options_path)

        self.source_folder: str = self.settings["source_folder"]
        self.export_folder: str = self.settings["export_folder"]

        logger.info(f"Source folder: {self.source_folder}")
        logger.info(f"Export folder: {self.export_folder}")

        # ----------------------------------------------------------------
        # Upewniamy się, że foldery istnieją
        # ----------------------------------------------------------------
        os.makedirs(self.source_folder, exist_ok=True)
        os.makedirs(self.export_folder, exist_ok=True)
        for deliver in self.export_settings:
            dest = os.path.join(self.export_folder, deliver)
            os.makedirs(dest, exist_ok=True)

        # ----------------------------------------------------------------
        # Source dict — wczytaj z pliku lub zbuduj od nowa
        # ----------------------------------------------------------------
        saved = load_source_dict(PROJECT_DIR)
        if saved is not None:
            self.source_dict = saved
            self.source_dict, _ = update_source_dict(
                self.source_dict, self.source_folder
            )
        else:
            logger.warning("Tworzę nowy source_dict")
            self.source_dict = create_source_dict(self.source_folder)
        save_source_dict(self.source_dict, PROJECT_DIR)

        # ----------------------------------------------------------------
        # UI
        # ----------------------------------------------------------------
        self.source_prev = PrevWindow(self)
        self.source_prev.grid(column=0, row=0)

        self.source_tree = SourceTree(self)
        self.source_tree.grid(column=0, row=1)
        self.source_tree.update_tree(self.source_dict)

        self.export_prev = PrevWindow(self)
        self.export_prev.grid(column=1, row=0)

        # ----------------------------------------------------------------
        # Stan przetwarzania
        # ----------------------------------------------------------------
        self.active_scanning: list[int] | None = None
        self.update_source_thread: Thread | None = None
        self.find_new: bool = False

        self.update_source()
        self.scan_photos()

    # ================================================================
    # Przetwarzanie zdjęć
    # ================================================================

    def scan_photos(self) -> None:
        """Uruchamia przetwarzanie pierwszego nowego zdjęcia w kolejce."""
        if self.active_scanning is not None:
            return

        for folder_idx, folder in enumerate(self.source_dict):
            folder_photos = self.source_dict[folder]
            if not folder_photos:
                continue
            first_photo = next(iter(folder_photos))
            self.active_scanning = [folder_idx, 0]
            Thread(
                target=self.process_photo,
                args=(folder, first_photo),
                daemon=True,
            ).start()
            return

        logger.info("Brak nowych zdjęć do przetworzenia")

    def process_photo(self, folder: str, photo: str) -> None:
        """Przetwarza jedno zdjęcie i uruchamia przetwarzanie kolejnego.

        Args:
            folder: Nazwa folderu (autora/sesji).
            photo:  Nazwa pliku zdjęcia.
        """
        next_thread = Thread(target=self.process_next_photo, daemon=True)

        if self.source_dict[folder][photo]["state"] != SourceState.NEW:
            next_thread.start()
            return

        logger.info(f"Przetwarzam: {folder}/{photo}")
        self.source_tree.change_tag(folder, photo, SourceState.PROCESSING)

        start_time = time.perf_counter()

        now = datetime.datetime.now()
        photo_path: str = self.source_dict[folder][photo]["path"]

        # ---- Wczytywanie ----
        try:
            from PIL import Image
            raw_photo = Image.open(photo_path)
        except Exception as exc:
            self._mark_error(folder, photo, f"Błąd otwarcia pliku '{photo_path}': {exc}")
            next_thread.start()
            return

        # ---- EXIF ----
        try:
            exif = exif_clean_from_tiff(raw_photo.getexif())
        except Exception as exc:
            self._mark_error(folder, photo, f"Błąd odczytu EXIF '{photo_path}': {exc}")
            next_thread.start()
            return

        # Standardowe pola EXIF
        exif[0x0001] = "R98"   # InteropIndex sRGB
        exif[0x00FE] = 0x1     # SubfileType: reduced-resolution
        exif[0x0106] = 2       # PhotometricInterpretation: RGB
        exif[0x0112] = 0       # Orientation: horizontal
        exif[0x013B] = folder.encode("utf-8")  # Artist
        exif[0xC71B] = now.strftime("%Y:%m:%d %H:%M:%S")  # PreviewDateTime

        # Orientacja: landscape = szerszy, portrait = wyższy
        orientation = "landscape" if raw_photo.width >= raw_photo.height else "portrait"

        # ---- Eksport dla każdego delivery ----
        success = True
        for deliver, d_cfg in self.export_settings.items():
            # Optymalizacja: jeśli plik już istnieje, pomijamy ten wariant
            existing_path = self.source_dict[folder][photo].get("exported", {}).get(deliver)
            if existing_path and os.path.isfile(existing_path):
                logger.debug(f"Pomijam istniejący eksport '{deliver}': {folder}/{photo}")
                continue

            if not self._check_ratio(raw_photo, deliver, d_cfg):
                continue

            # Skalowanie
            try:
                resized = image_resize(
                    raw_photo,
                    d_cfg["size"],
                    method=d_cfg.get("size_type", "longer"),
                )
            except Exception as exc:
                self._mark_error(folder, photo, f"Błąd skalowania w {deliver}: {exc}")
                success = False
                break

            exif[256] = resized.width
            exif[257] = resized.height

            # Konwersja przestrzeni barwowej
            try:
                img_conv = image_convert_to_srgb(resized)
            except Exception as exc:
                self._mark_error(folder, photo, f"Błąd konwersji sRGB w {deliver}: {exc}")
                success = False
                break

            # Watermark / logo
            logo_path = os.path.join(self.source_folder, folder, "logo.png")
            logo_cfg = d_cfg["logo"][orientation]
            try:
                final_img = apply_watermark(
                    base=img_conv,
                    logo_path=logo_path,
                    size=logo_cfg["size"],
                    opacity=logo_cfg["opacity"],
                    x_offset=logo_cfg["x_offset"],
                    y_offset=logo_cfg["y_offset"],
                )
            except Exception as exc:
                self._mark_error(folder, photo, f"Błąd nakładania logo w {deliver}: {exc}")
                success = False
                break

            # Nazwa pliku eksportu
            created_tag = (
                self.source_dict[folder][photo]["created"]
                .replace(" ", "_")
                .replace(":", "-")
            )
            orig_stem = os.path.splitext(photo)[0]
            folder_tag = folder.replace(" ", "_")
            export_name = f"YAPA{created_tag}_{folder_tag}_{orig_stem}"

            # Zapis
            fmt = d_cfg["format"]
            try:
                export_path = self._save_image(
                    final_img,
                    export_name,
                    deliver,
                    fmt,
                    d_cfg["quality"],
                    folder,
                    photo,
                    now,
                    exif,
                )
            except Exception as exc:
                self._mark_error(folder, photo, f"Błąd zapisu w {deliver}: {exc}")
                success = False
                break

            self.source_dict[folder][photo]["exported"][deliver] = export_path

        if success:
            duration = time.perf_counter() - start_time
            self.source_dict[folder][photo]["state"] = SourceState.OK
            self.source_dict[folder][photo]["duration_sec"] = round(duration, 4)
            logger.debug(f"[PERF] Zdjęcie {folder}/{photo} przetworzone w {duration:.4f}s")

        self.source_tree.change_tag(
            folder, photo, self.source_dict[folder][photo]["state"]
        )
        next_thread.start()

    def process_next_photo(self) -> None:
        """Inkrementuje kursor w kolejce i uruchamia przetwarzanie kolejnego zdjęcia."""
        if self.active_scanning is None:
            return

        folder_idx, photo_idx = self.active_scanning
        folders = list(self.source_dict)

        photo_idx += 1
        while True:
            if folder_idx >= len(folders):
                # Koniec kolejki
                self.active_scanning = None
                logger.info("Zakończono przetwarzanie całej kolejki")
                return

            folder = folders[folder_idx]
            photos = list(self.source_dict[folder])

            if photo_idx < len(photos):
                photo = photos[photo_idx]
                self.active_scanning = [folder_idx, photo_idx]
                Thread(
                    target=self.process_photo,
                    args=(folder, photo),
                    daemon=True,
                ).start()
                return
            else:
                # Przejdź do następnego folderu
                folder_idx += 1
                photo_idx = 0

    # ================================================================
    # Cykliczne odświeżanie source
    # ================================================================

    def update_source(self) -> None:
        """Planuje cykliczne sprawdzanie folderu źródłowego (co sekundę)."""
        if self.update_source_thread is not None and self.update_source_thread.is_alive():
            logger.warning("Poprzednia aktualizacja source jeszcze trwa")
            self.after(1000, self.update_source)
            return
        self.update_source_thread = Thread(
            target=self._update_source_worker, daemon=True
        )
        self.update_source_thread.start()

    def _update_source_worker(self) -> None:
        """Wątek roboczy cyklicznego odświeżania source_dict.

        Kolejność działań w każdym cyklu:
        1. Szukanie nowych plików w folderze źródłowym.
        2. Sprawdzenie integralności (usunięte / zmienione / brak eksportów).
        3. Aktualizacja tree view.
        4. Uruchomienie scan_photos() jeśli pojawiły się nowe/zmienione pliki.
        """
        logger.debug("Cykliczne sprawdzanie source i integralności")
        try:
            # 1. Nowe pliki — update_source_dict zwraca flagę found_new
            self.source_dict, found_new = update_source_dict(
                self.source_dict, self.source_folder
            )

            # 2. Integralność — check_integrity modyfikuje source_dict in-place
            #    i zwraca słownik zmian {folder: {photo: new_state}}
            integrity_changes = check_integrity(
                self.source_dict,
                self.export_settings,
                self.export_folder,
            )

            # 3. Przetrwałość stanu na dysk
            save_source_dict(self.source_dict, PROJECT_DIR)

            # 4. Odświeżenie drzewa (update_tree obsługuje nowe wpisy i zmianę tagów)
            self.source_tree.update_tree(self.source_dict)

            # 5. Jeśli cokolwiek wymaga przetworzenia — ruszamy kolejkę
            needs_scan = found_new or any(
                state in (SourceState.NEW,)
                for folder_changes in integrity_changes.values()
                for state in folder_changes.values()
            )
            if needs_scan:
                self.scan_photos()

        except Exception as exc:
            logger.error(f"Błąd cyklicznego sprawdzania source: {exc}")
        finally:
            self.after(1000, self.update_source)

    # ================================================================
    # Pomocnicze
    # ================================================================

    def _mark_error(self, folder: str, photo: str, msg: str) -> None:
        """Oznacza zdjęcie jako błędne i loguje komunikat.

        Args:
            folder: Nazwa folderu.
            photo:  Nazwa pliku.
            msg:    Treść błędu.
        """
        logger.error(msg)
        self.source_dict[folder][photo]["state"] = SourceState.ERROR
        self.source_dict[folder][photo]["error_msg"] = msg
        self.source_tree.change_tag(folder, photo, SourceState.ERROR)

    @staticmethod
    def _check_ratio(raw_photo, deliver: str, d_cfg: dict) -> bool:
        """Sprawdza, czy zdjęcie spełnia wymagania aspect ratio danego delivery.

        Args:
            raw_photo: Otwarty obraz PIL.
            deliver:   Nazwa delivery (do logowania).
            d_cfg:     Konfiguracja delivery.

        Returns:
            True jeśli brak ograniczeń ratio lub zdjęcie spełnia warunki.
        """
        ratios = d_cfg.get("ratio")
        if ratios is None:
            return True
        actual = round(raw_photo.width / raw_photo.height, 2)
        if actual not in ratios:
            logger.debug(f"Pomijam {deliver}: ratio {actual} ∉ {ratios}")
            return False
        return True

    def _save_image(
        self,
        img,
        base_name: str,
        deliver: str,
        fmt: str,
        quality: int,
        folder: str,
        photo: str,
        now: datetime.datetime,
        exif,
    ) -> str:
        """Zapisuje obraz w odpowiednim formacie do folderu delivery.

        Args:
            img:       Obraz PIL do zapisania.
            base_name: Nazwa pliku bez rozszerzenia.
            deliver:   Nazwa delivery (pdfolder).
            fmt:       Format: ``"JPEG"`` lub ``"PNG"``.
            quality:   Jakość / compression level.
            folder:    Nazwa folderu autora (do metadanych PNG).
            photo:     Oryginalna nazwa pliku (do metadanych PNG).
            now:       Aktualny czas (do metadanych PNG).
            exif:      Obiekt EXIF PIL.

        Returns:
            Pełna ścieżka do zapisanego pliku.

        Raises:
            ValueError: dla nieznanego formatu.
            IOError:    gdy zapis się nie powiedzie.
        """
        if fmt == "JPEG":
            export_path = os.path.join(
                self.export_folder, deliver, base_name + ".jpg"
            )
            img.save(export_path, format="JPEG", optimize=True, quality=quality)

        elif fmt == "PNG":
            export_path = os.path.join(
                self.export_folder, deliver, base_name + ".png"
            )
            png_meta = PngInfo()
            png_meta.add_text("Artist", folder)
            png_meta.add_text("OriginalRawFileName", photo)
            png_meta.add_text("DocumentName", "YAPA")
            png_meta.add_text("ImageDescription", "YAPA")
            png_meta.add_text(
                "DateTimeOriginal", self.source_dict[folder][photo]["created"]
            )
            png_meta.add_text("PreviewDateTime", now.strftime("%Y:%m:%d %H:%M:%S"))
            img.save(
                export_path,
                format="PNG",
                optimize=True,
                compress_level=quality,
                pnginfo=png_meta,
            )
        else:
            raise ValueError(f"Nieznany format eksportu: {fmt!r}")

        logger.info(f"Zapisano: {export_path}")
        return export_path
