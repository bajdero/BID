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
import sys
import time
import queue
import threading
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor, Future
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import tkinter as tk
from tkinter import ttk
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
    monitor_incomplete_files,
)
from bid.ui.preview import PrevWindow
from bid.ui.source_tree import SourceTree
from bid.ui.details_panel import DetailsPanel
from bid.ui.toast import init_toasts, show_toast

logger = logging.getLogger("BID")


class MainApp(tk.Tk):
    """Główne okno aplikacji BID.

    Jest JEDYNĄ instancją tk.Tk w procesie. Dialog wyboru projektu
    i kreator są pokazywane jako tk.Toplevel wewnątrz tej instancji,
    co zapobiega błędowi:
        Tcl_AsyncDelete: async handler deleted by the wrong thread
    """

    def __init__(
        self,
        project_path: "Path | None" = None,
        debug: bool = False,
    ) -> None:
        """
        Args:
            project_path: Ścieżka do katalogu projektu (None = pokaż selektor).
            debug: Czy uruchomić w trybie debugowania.
        """
        super().__init__()
        self.debug_mode = debug
        self._running = False  # set True only after full successful init

        # Hide the empty shell while we may be showing the selector dialog.
        self.withdraw()

        # ----------------------------------------------------------------
        # Project selection (modal Toplevel — no extra tk.Tk created)
        # ----------------------------------------------------------------
        if project_path is None:
            project_path = self._select_project_modal()
            if project_path is None:
                return  # User cancelled — _running stays False

        if not project_path.exists():
            logger.warning(f"Projekt nie istnieje: {project_path}, uruchamiam wizard")
            success, project_path = self._run_wizard_modal()
            if not success or project_path is None:
                return
        self.project_path = project_path
        self.project_name = project_path.name.replace("_", " ")
        self.title(f"BID — {self.project_name}")

        from bid.project_manager import ProjectManager
        ProjectManager.add_recent_project(str(project_path))

        # ----------------------------------------------------------------
        # Wczytywanie konfiguracji z folderu projektu
        # ----------------------------------------------------------------
        self.settings = cfg_module.load_settings(project_path / "settings.json")
        self.export_settings = cfg_module.load_export_options(project_path / "export_option.json")

        self.source_folder: str = self.settings["source_folder"]
        self.export_folder: str = self.settings["export_folder"]

        logger.info(f"Project: {self.project_name}")
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
        # Source dict — wczytaj z katalogu projektu
        # ----------------------------------------------------------------
        saved = load_source_dict(project_path)
        if saved is not None:
            self.source_dict = saved
            self.source_dict, _ = update_source_dict(
                self.source_dict, self.source_folder, self.export_folder, self.export_settings
            )
        else:
            logger.warning("Tworzę nowy source_dict")
            self.source_dict = create_source_dict(self.source_folder, self.export_folder, self.export_settings)
        save_source_dict(self.source_dict, project_path)

        # ----------------------------------------------------------------
        # UI — Układ główny
        # ----------------------------------------------------------------
        # Pasek menu
        self._build_main_menu()

        # Główny kontener
        # TODO: UX/UI: Użyć nowocześniejszego layoutu (np. grid zamiast pack) dla lepszego skalowania i dodania marginesów.
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Previews (Góra)
        # TODO: UX/UI: Dodać tło lub ramkę oddzielającą strefę podglądu od reszty aplikacji.
        preview_frame = ttk.Frame(main_container)
        preview_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        self.source_prev = PrevWindow(preview_frame)
        self.source_prev.pack(side=tk.LEFT, padx=5)
        
        self.export_prev = PrevWindow(preview_frame)
        self.export_prev.pack(side=tk.LEFT, padx=5)

        # Tree + Details (Dół)
        content_frame = ttk.Frame(main_container)
        content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.source_tree = SourceTree(content_frame, self)
        self.source_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.source_tree.update_tree(self.source_dict)

        self.details_panel = DetailsPanel(content_frame, self)
        self.details_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        # Pasek stanu / Progress (Dół)
        # TODO: UX/UI: Pasek stanu wygląda bardzo surowo. Można dodać drobną ikonę statusu i usunąć relief=tk.SUNKEN dla bardziej nowoczesnego (płaskiego) wyglądu.
        self.status_bar = ttk.Frame(self, relief=tk.SUNKEN, padding=(2, 2))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_label = ttk.Label(self.status_bar, text="Gotowy")
        self.status_label.pack(side=tk.LEFT, padx=5)

        self.progress_bar = ttk.Progressbar(self.status_bar, orient=tk.HORIZONTAL, length=200, mode='determinate')
        self.progress_bar.pack(side=tk.RIGHT, padx=5)

        # ----------------------------------------------------------------
        # Stan przetwarzania
        # ----------------------------------------------------------------
        self.active_scanning: dict[Future, tuple[str, str]] = {}
        self.max_workers: int = os.cpu_count() or 4
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.scan_count: int = 0  # Counter for cleanup every 10 scans

        self.update_source_thread: threading.Thread | None = None
        self.file_monitor_thread: threading.Thread | None = None
        self.find_new: bool = False
        self.dict_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._update_queue: queue.Queue = queue.Queue(maxsize=1)
        self._monitor_queue: queue.Queue = queue.Queue(maxsize=1)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.deiconify()  # show main window now that init is complete
        self._running = True

        init_toasts(self)  # inicjalizuj system powiadomień
        self.monitor_incomplete()  # Start background file monitor
        self.update_source()
        self.scan_photos()

    # ================================================================
    # Project selection helpers (Toplevel dialogs — no extra tk.Tk)
    # ================================================================

    def _select_project_modal(self) -> "Path | None":
        """Pokazuje selektor projektów jako modalny Toplevel."""
        from bid.ui.project_selector import run_project_selector
        success, create_new, selected_path = run_project_selector(parent=self)
        if not success:
            return None
        if create_new:
            ok, path = self._run_wizard_modal()
            return path if ok else None
        return selected_path

    def _run_wizard_modal(self) -> "tuple[bool, Path | None]":
        """Pokazuje kreator projektu jako modalny Toplevel."""
        from bid.ui.setup_wizard import run_wizard_if_needed
        return run_wizard_if_needed(parent=self)

    def on_new_project(self) -> None:
        """Otwiera wizard nowego projektu i przeładowuje aplikację."""
        success, project_path = self._run_wizard_modal()
        if success and project_path:
            self.load_project(str(project_path))

    def load_project(self, path: str) -> None:
        """Przeładowuje aplikację z nowym projektem."""
        logger.info(f"Przełączanie na projekt: {path}")
        # Restart aplikacji z nowym projektem
        # Używamy ścieżki bezwzględnej do main.py, bo filedialog mógł zmienić CWD
        script_path = str(Path(__file__).parent.parent / "main.py")
        args = [sys.executable, script_path, "--project", path]
        if self.debug_mode:
            args.append("--debug")
            
        os.execl(sys.executable, *args)

    def _build_main_menu(self) -> None:
        """Tworzy pasek menu głównego z funkcjami projektowymi."""
        menubar = tk.Menu(self)
        
        # Projekt
        project_menu = tk.Menu(menubar, tearoff=0)
        project_menu.add_command(label="Nowy projekt...", command=self.on_new_project)
        project_menu.add_command(label="Otwórz projekt...", command=self.on_open_project)
        
        # Ostatnie projekty (submenu)
        recent_menu = tk.Menu(project_menu, tearoff=0)
        from bid.project_manager import ProjectManager
        recent_paths = ProjectManager.get_recent_projects()
        
        if recent_paths:
            for path in recent_paths:
                name = os.path.basename(path).replace("_", " ")
                recent_menu.add_command(
                    label=name, 
                    command=lambda p=path: self.load_project(p)
                )
        else:
            recent_menu.add_command(label="(brak)", state=tk.DISABLED)
            
        project_menu.add_cascade(label="Ostatnie projekty", menu=recent_menu)
        project_menu.add_separator()
        project_menu.add_command(label="Wyjście", command=self.quit)
        menubar.add_cascade(label="Projekt", menu=project_menu)

        # Akcje
        action_menu = tk.Menu(menubar, tearoff=0)
        action_menu.add_command(label="Aktualizuj listę (Scan source)", command=self.update_source)
        action_menu.add_command(label="Rozpocznij eksport", command=self.scan_photos)
        action_menu.add_separator()
        action_menu.add_command(label="Nowy profil eksportu...", command=self.on_new_export_profile)
        menubar.add_cascade(label="Akcje", menu=action_menu)

        self.config(menu=menubar)

    def on_new_export_profile(self) -> None:
        """Otwiera kreator nowego profilu eksportu."""
        from bid.ui.export_wizard import run_export_profile_wizard
        import json
        success, name, profile = run_export_profile_wizard(parent=self)
        if not success:
            return
        if name in self.export_settings:
            messagebox.showerror(
                "Profil już istnieje",
                f"Profil '{name}' już istnieje. Zmień nazwę lub usuń stary profil."
            )
            return
        self.export_settings[name] = profile
        # Utwórz folder eksportu dla nowego profilu
        dest = os.path.join(self.export_folder, name)
        os.makedirs(dest, exist_ok=True)
        # Zapisz zaktualizowaną konfigurację
        export_options_path = self.project_path / "export_option.json"
        try:
            with open(export_options_path, "w", encoding="utf-8") as f:
                json.dump(self.export_settings, f, ensure_ascii=False, indent=4)
            logger.info(f"Zapisano nowy profil eksportu: {name}")
        except Exception as exc:
            messagebox.showerror("Błąd zapisu", f"Nie można zapisać profilu eksportu: {exc}")
            return
        # Uruchom skanowanie — nowy profil będzie przetworzony dla plików NEW
        self.scan_photos()

    def on_open_project(self) -> None:
        """Otwiera dialog wyboru folderu projektu."""
        from bid.project_manager import ProjectManager
        path = filedialog.askdirectory(
            title="Wybierz folder projektu",
            initialdir=str(ProjectManager.projects_dir),
            mustexist=True
        )
        if path:
            if os.path.exists(os.path.join(path, "settings.json")):
                self.load_project(path)
            else:
                messagebox.showerror("Błąd", "Wybrany folder nie jest poprawnym projektem BID.")

    # ================================================================
    # Przetwarzanie zdjęć
    # ================================================================

    def scan_photos(self) -> None:
        """Uruchamia przetwarzanie nowych zdjęć w puli procesów."""
        # Cleanup empty files every 10 scans
        self.scan_count += 1
        if self.scan_count % 10 == 0:
            logger.info(f"[CLEANUP] Czyszczenie pustych plików eksportu (skan #{self.scan_count})")
            self._cleanup_empty_exports()
        
        with self.dict_lock:
            # Policz zdjęcia do przetworzenia dla paska postępu
            total_new = sum(1 for f in self.source_dict for p in self.source_dict[f] 
                            if self.source_dict[f][p]["state"] == SourceState.NEW)
            
            if total_new > 0:
                self.progress_bar["maximum"] = total_new
                self.progress_bar["value"] = 0
                self.status_label.config(text=f"Przetwarzanie... (Pozostało: {total_new})")
            else:
                self.status_label.config(text="Wszystko aktualne")
                self.progress_bar["value"] = 0

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
            save_source_dict(self.source_dict, self.project_path)
            self.scan_photos()
        
        if self.active_scanning:
            self.after(200, self.check_futures)

    def _handle_task_result(self, folder: str, photo: str, result: dict) -> None:
        """Applies results from a finished worker task."""
        with self.dict_lock:
            if not result["success"]:
                self._mark_error_locked(folder, photo, result["error_msg"])
                show_toast(f"Błąd przetwarzania: {folder}/{photo}", level="error")
                return

            self.source_dict[folder][photo]["state"] = SourceState.OK
            self.source_dict[folder][photo]["duration_sec"] = result["duration"]
            self.source_dict[folder][photo]["exported"].update(result["exported"])
        
        logger.debug(f"[PERF] Zdjęcie {folder}/{photo} przetworzone w {result['duration']:.4f}s")
        self.source_tree.change_tag(folder, photo, SourceState.OK)

        # Aktualizacja postępu
        self.progress_bar["value"] += 1
        remaining = self.progress_bar["maximum"] - self.progress_bar["value"]
        if remaining > 0:
            self.status_label.config(text=f"Przetwarzanie... (Pozostało: {int(remaining)})")
        else:
            self.status_label.config(text="Zakończono przetwarzanie")

    def _cleanup_empty_exports(self) -> None:
        """Removes empty (0B) export files from export folders.
        
        Called automatically every 10 scans to clean up failed exports
        that left behind empty placeholder files.
        """
        try:
            export_dir = Path(self.export_folder)
            if not export_dir.exists():
                return
            
            deleted_count = 0
            for profile_dir in export_dir.iterdir():
                if not profile_dir.is_dir():
                    continue
                
                # Check all files in profile directory
                for export_file in profile_dir.iterdir():
                    if export_file.is_file():
                        try:
                            # Check if file is exactly 0 bytes
                            if export_file.stat().st_size == 0:
                                logger.warning(f"[CLEANUP] Usuwam pusty plik eksportu (0B): {export_file}")
                                export_file.unlink()
                                deleted_count += 1
                        except OSError as e:
                            logger.debug(f"[CLEANUP] Błąd sprawdzenia pliku {export_file}: {e}")
            
            if deleted_count > 0:
                logger.info(f"[CLEANUP] Usunięto {deleted_count} pustych plików eksportu")
        
        except Exception as exc:
            logger.error(f"[CLEANUP] Błąd podczas czyszczenia pustych plików: {exc}")

    # Te funkcje są teraz zastąpione przez logic w image_processing.py i pool executor
    # def process_photo(self, folder: str, photo: str) -> None: ...
    # def process_next_photo(self) -> None: ...

    # ================================================================
    # Cykliczne odświeżanie source
    # ================================================================

    def update_source(self) -> None:
        """Planuje cykliczne sprawdzanie folderu źródłowego (co sekundę)."""
        if self._stop_event.is_set():
            return
        if self.update_source_thread is not None and self.update_source_thread.is_alive():
            logger.warning("Poprzednia aktualizacja source jeszcze trwa")
            return  # _poll_update_source is already running for this cycle
        self.update_source_thread = threading.Thread(
            target=self._update_source_worker, daemon=True
        )
        self.update_source_thread.start()
        self.after(100, self._poll_update_source)

    def _update_source_worker(self) -> None:
        """Wątek roboczy cyklicznego odświeżania source_dict. NIE wywołuje Tkinter."""
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
                save_source_dict(self.source_dict, self.project_path)

            # Wyniki trafiają do kolejki — main thread odbiera przez _poll_update_source.
            # NIE wolno wołać self.after() z wątku roboczego!
            try:
                self._update_queue.put_nowait((found_new, integrity_changes))
            except queue.Full:
                pass  # main thread is still processing the previous result

        except Exception as exc:
            logger.error(f"Błąd cyklicznego sprawdzania source: {exc}")
            try:
                self._update_queue.put_nowait((False, {}))
            except queue.Full:
                pass

    def _poll_update_source(self) -> None:
        """Odpytuje kolejkę wyników wątku source — wywoływane tylko na głównym wątku."""
        if self._stop_event.is_set():
            return
        try:
            found_new, integrity_changes = self._update_queue.get_nowait()
            self._sync_ui_after_update(found_new, integrity_changes)
            self.after(1000, self.update_source)
        except queue.Empty:
            self.after(100, self._poll_update_source)

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

    # ================================================================
    # Background File Monitoring (DOWNLOADING → NEW transitions)
    # ================================================================

    def monitor_incomplete(self) -> None:
        """Planuje cykliczne monitorowanie niedokończonych plików (co 2 sekundy).
        
        FIX-ASYNC: Runs monitor_incomplete_files() in background to update
        DOWNLOADING files to NEW when they're stable/ready.
        """
        if self._stop_event.is_set():
            return
        if self.file_monitor_thread is not None and self.file_monitor_thread.is_alive():
            # Already running
            pass
        else:
            # Start new monitor thread
            self.file_monitor_thread = threading.Thread(
                target=self._monitor_incomplete_worker, daemon=True, name="FileMonitor"
            )
            self.file_monitor_thread.start()
        
        self.after(100, self._poll_monitor_incomplete)

    def _monitor_incomplete_worker(self) -> None:
        """Wątek roboczy monitorowania niedokończonych plików.
        
        FIX-ASYNC: Periodically checks DOWNLOADING files and updates them to NEW
        when they become stable. Runs blocking is_file_stable() in background.
        """
        while not self._stop_event.is_set():
            try:
                with self.dict_lock:
                    # Check for DOWNLOADING files and update when ready
                    monitor_updates = monitor_incomplete_files(
                        self.source_dict,
                        check_interval=2.0,
                    )
                
                # Send updates to UI thread via queue
                if monitor_updates:
                    try:
                        self._monitor_queue.put_nowait(monitor_updates)
                    except queue.Full:
                        pass  # main thread still processing previous result

                # Wait before next cycle (2 seconds is built into monitor_incomplete_files)
                time.sleep(2)

            except Exception as exc:
                logger.error(f"Błąd monitorowania niedokończonych plików: {exc}")
                time.sleep(2)

    def _poll_monitor_incomplete(self) -> None:
        """Odpytuje kolejkę wyników monitorowania — wywoływane tylko na głównym wątku.
        
        FIX-ASYNC: When DOWNLOADING files become ready, updates UI and triggers
        re-scan for processing.
        """
        if self._stop_event.is_set():
            return
        try:
            monitor_updates = self._monitor_queue.get_nowait()
            self._sync_ui_after_monitoring(monitor_updates)
        except queue.Empty:
            pass
        finally:
            self.after(100, self._poll_monitor_incomplete)

    def _sync_ui_after_monitoring(self, monitor_updates: dict) -> None:
        """UI sync dla rezultatów monitorowania — wywoływane w main thread.
        
        FIX-ASYNC: Applies DOWNLOADING → NEW transitions to UI and triggers
        re-scan for processing.
        
        Args:
            monitor_updates: Dictionary {folder: {file: is_ready_bool}}
        """
        # Count actual transitions (files becoming ready)
        ready_count = 0
        for folder, files_dict in monitor_updates.items():
            for file_name, is_ready in files_dict.items():
                if is_ready:
                    # Update state in source_dict
                    if folder in self.source_dict and file_name in self.source_dict[folder]:
                        self.source_dict[folder][file_name]["state"] = SourceState.NEW
                        ready_count += 1
        
        # If any files became ready, update UI and trigger scanning
        if ready_count > 0:
            logger.info(f"Monitor: {ready_count} files ready for processing")
            self.source_tree.update_tree(self.source_dict)
            save_source_dict(self.source_dict, self.project_path)
            self.scan_photos()

    def _mark_error_locked(self, folder: str, photo: str, msg: str) -> None:
        """Oznacza błąd — MUSI być wewnątrz dict_lock."""
        logger.error(msg)
        self.source_dict[folder][photo]["state"] = SourceState.ERROR
        self.source_dict[folder][photo]["error_msg"] = msg
        self.source_tree.change_tag(folder, photo, SourceState.ERROR)
        save_source_dict(self.source_dict, self.project_path)

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
        save_source_dict(self.source_dict, self.project_path)

    def _on_close(self) -> None:
        """Graceful shutdown — sygnalizuje wątkom, że czas kończyć."""
        self._stop_event.set()
        self.destroy()

    def mainloop(self, n: int = 0) -> None:
        """Nadpisujemy mainloop, aby zwolnić pool przy zamykaniu."""
        if not self._running:
            # __init__ returned early (user cancelled project selection)
            try:
                self.destroy()
            except Exception:
                pass
            return
        try:
            super().mainloop(n)
        finally:
            self._stop_event.set()
            try:
                self.executor.shutdown(wait=False, cancel_futures=True)
            except TypeError:
                self.executor.shutdown(wait=False)
