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
import threading
from concurrent.futures import ProcessPoolExecutor, Future
from pathlib import Path

import tkinter as tk
from PIL.PngImagePlugin import PngInfo

from bid import config as cfg_module
from bid.config import PROJECT_DIR
from bid.image_processing import (
    image_resize,
    image_convert_to_srgb,
    process_photo_task,
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
                self.source_dict, self.source_folder, self.export_folder, self.export_settings
            )
        else:
            logger.warning("Tworzę nowy source_dict")
            self.source_dict = create_source_dict(self.source_folder, self.export_folder, self.export_settings)
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
        self.active_scanning: dict[Future, tuple[str, str]] = {}
        self.max_workers: int = os.cpu_count() or 4
        self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
        
        self.update_source_thread: threading.Thread | None = None
        self.find_new: bool = False
        self.dict_lock = threading.Lock()

        self.update_source()
        self.scan_photos()

    # ================================================================
    # Przetwarzanie zdjęć
    # ================================================================

    def scan_photos(self) -> None:
        """Uruchamia przetwarzanie nowych zdjęć w puli procesów."""
        with self.dict_lock:
            if len(self.active_scanning) >= self.max_workers:
                return

            # Tworzymy snapshot bazy (listę krotek), aby uniknąć RuntimeError
            # podczas iteracji, gdyby coś (np. worker) zmieniło dict w międzyczasie.
            for folder, photos in list(self.source_dict.items()):
                for photo, meta in list(photos.items()):
                    if meta["state"] == SourceState.NEW:
                        # Sprawdź czy już nie jest w kolejce do przetwarzania
                        if any((f, p) == (folder, photo) for f, p in self.active_scanning.values()):
                            continue
                        
                        if len(self.active_scanning) >= self.max_workers:
                            return

                        self._submit_photo_task_locked(folder, photo)

            if not self.active_scanning:
                logger.info("Brak nowych zdjęć do przetworzenia")

    def _submit_photo_task_locked(self, folder: str, photo: str) -> None:
        """Submit task — MUSI być wywołane wewnątrz with self.dict_lock."""
        meta = self.source_dict[folder][photo]
        meta["state"] = SourceState.PROCESSING
        logger.info(f"Kolejkuję: {folder}/{photo}")
        self.source_tree.change_tag(folder, photo, SourceState.PROCESSING)
        
        future = self.executor.submit(
            process_photo_task,
            photo_path=meta["path"],
            folder_name=folder,
            photo_name=photo,
            created_date=meta["created"],
            export_folder=self.export_folder,
            export_settings=self.export_settings,
            existing_exports=meta.get("exported", {}),
        )
        self.active_scanning[future] = (folder, photo)
        # Use after() to check results periodically
        self.after(100, self.check_futures)

    def check_futures(self) -> None:
        """Sprawdza zakończone zadania w puli."""
        done_futures = [f for f in self.active_scanning if f.done()]
        for future in done_futures:
            folder, photo = self.active_scanning.pop(future)
            try:
                result = future.result()
                self._handle_task_result(folder, photo, result)
            except Exception as exc:
                self._mark_error(folder, photo, f"Błąd krytyczny procesu: {exc}")
        
        if done_futures:
            save_source_dict(self.source_dict, PROJECT_DIR)
            self.scan_photos()
        
        if self.active_scanning:
            self.after(200, self.check_futures)

    def _handle_task_result(self, folder: str, photo: str, result: dict) -> None:
        """Applies results from a finished worker task."""
        with self.dict_lock:
            if not result["success"]:
                self._mark_error_locked(folder, photo, result["error_msg"])
                return

            self.source_dict[folder][photo]["state"] = SourceState.OK
            self.source_dict[folder][photo]["duration_sec"] = result["duration"]
            self.source_dict[folder][photo]["exported"].update(result["exported"])
        
        logger.debug(f"[PERF] Zdjęcie {folder}/{photo} przetworzone w {result['duration']:.4f}s")
        self.source_tree.change_tag(folder, photo, SourceState.OK)

    # Te funkcje są teraz zastąpione przez logic w image_processing.py i pool executor
    # def process_photo(self, folder: str, photo: str) -> None: ...
    # def process_next_photo(self) -> None: ...

    # ================================================================
    # Cykliczne odświeżanie source
    # ================================================================

    def update_source(self) -> None:
        """Planuje cykliczne sprawdzanie folderu źródłowego (co sekundę)."""
        if self.update_source_thread is not None and self.update_source_thread.is_alive():
            logger.warning("Poprzednia aktualizacja source jeszcze trwa")
            self.after(1000, self.update_source)
            return
        self.update_source_thread = threading.Thread(
            target=self._update_source_worker, daemon=True
        )
        self.update_source_thread.start()

    def _update_source_worker(self) -> None:
        """Wątek roboczy cyklicznego odświeżania source_dict."""
        logger.debug("Cykliczne sprawdzanie source i integralności")
        try:
            with self.dict_lock:
                # 1. Nowe pliki
                self.source_dict, found_new = update_source_dict(
                    self.source_dict, self.source_folder, self.export_folder, self.export_settings
                )

                # 2. Integralność
                integrity_changes = check_integrity(
                    self.source_dict,
                    self.export_settings,
                    self.export_folder,
                )

                # 3. Zapis
                save_source_dict(self.source_dict, PROJECT_DIR)

            # 4. Odświeżenie UI i start skanowania — musi być w main thread!
            self.after(0, self._sync_ui_after_update, found_new, integrity_changes)

        except Exception as exc:
            logger.error(f"Błąd cyklicznego sprawdzania source: {exc}")
        finally:
            self.after(1000, self.update_source)

    def _sync_ui_after_update(self, found_new: bool, integrity_changes: dict) -> None:
        """UI sync — wywoływane w main thread (przez after)."""
        # Odświeżenie drzewa
        self.source_tree.update_tree(self.source_dict)

        # Jeśli cokolwiek wymaga przetworzenia — ruszamy kolejkę
        needs_scan = found_new or any(
            state in (SourceState.NEW,)
            for folder_changes in integrity_changes.values()
            for state in folder_changes.values()
        )
        if needs_scan:
            self.scan_photos()

    def _mark_error_locked(self, folder: str, photo: str, msg: str) -> None:
        """Oznacza błąd — MUSI być wewnątrz dict_lock."""
        logger.error(msg)
        self.source_dict[folder][photo]["state"] = SourceState.ERROR
        self.source_dict[folder][photo]["error_msg"] = msg
        self.source_tree.change_tag(folder, photo, SourceState.ERROR)
        save_source_dict(self.source_dict, PROJECT_DIR)

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
        save_source_dict(self.source_dict, PROJECT_DIR)

    def mainloop(self, n: int = 0) -> None:
        """Nadpisujemy mainloop, aby zwolnić pool przy zamykaniu."""
        try:
            super().mainloop(n)
        finally:
            self.executor.shutdown(wait=False)
