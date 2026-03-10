"""
bid/ui/setup_wizard.py
Kreator pierwszego uruchomienia — uruchamiany, gdy brakuje settings.json
lub export_option.json.

Wizard zbiera ścieżki folderów source i export, zapisuje settings.json
i (jeśli brakuje) tworzy export_option.json z domyślnymi wartościami.
"""
from __future__ import annotations

import json
import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable

logger = logging.getLogger("Yapa_CM")

# ---------------------------------------------------------------------------
# Domyślna konfiguracja eksportu (kopiowana gdy brakuje export_option.json)
# ---------------------------------------------------------------------------
DEFAULT_EXPORT_OPTIONS: dict = {
    "lzp": {
        "ratio": [0.8],
        "size_type": "longer",
        "size": 1350,
        "format": "JPEG",
        "quality": 88,
        "logo": {
            "landscape": {"size": 260, "opacity": 60, "x_offset": 10, "y_offset": 10},
            "portrait":  {"size": 332, "opacity": 60, "x_offset": 10, "y_offset": 10},
        },
    },
}


# ---------------------------------------------------------------------------
# Wizard
# ---------------------------------------------------------------------------

class SetupWizard(tk.Toplevel):
    """Okno kreatora pierwszego uruchomienia — uruchamiane jako Toplevel.

    Nigdy nie tworzy własnej instancji tk.Tk, aby uniknąć błędu:
    ``Tcl_AsyncDelete: async handler deleted by the wrong thread``.

    Po zakończeniu (kliknięcie 'Zakończ') zapisuje settings.json
    i ewentualnie export_option.json, a następnie zamyka okno.
    Jeśli użytkownik anuluje, ``self.completed`` wynosi False.
    """

    def __init__(
        self,
        parent: tk.Misc,
        settings_path: Path | None = None,
        export_options_path: Path | None = None,
        missing_settings: bool = True,
        missing_export: bool = True,
    ) -> None:
        """
        Args:
            parent:              Rodzic (istniejąca instancja Tk lub Toplevel).
            settings_path:       Docelowa ścieżka settings.json (nieużywana w nowym modelu).
            export_options_path: Docelowa ścieżka export_option.json (nieużywana w nowym modelu).
            missing_settings:    Czy settings.json nie istnieje / jest błędny.
            missing_export:      Czy export_option.json nie istnieje / jest błędny.
        """
        super().__init__(parent)
        self.settings_path = settings_path
        self.export_options_path = export_options_path
        self.missing_settings = missing_settings
        self.missing_export = missing_export
        self.completed: bool = False
        self.project_path: Path | None = None

        # Inicjalizacja zmiennych przed budową UI
        self._project_name_var = tk.StringVar(value="Nowy Projekt")
        self._source_var = tk.StringVar()
        self._export_var = tk.StringVar()
        self._status_var = tk.StringVar()

        self.title("BID — Kreator projektu")
        self.resizable(False, False)
        self._center_window(520, 500)

        self._build_ui()

    # ------------------------------------------------------------------
    # Budowanie UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Buduje układ okna kreatora z poprawnym kolejkowaniem pack()."""
        # Inicjalizacja zmiennych
        self._status_var = tk.StringVar()
        self._source_var = tk.StringVar()
        self._export_var = tk.StringVar()
        self._project_name_var = tk.StringVar(value="Nowy Projekt")

        # 1. PRZYCISKI (Pakujemy jako pierwsze z side=BOTTOM, aby zarezerwować miejsce na dole)
        # TODO: UX/UI: Przenieść hardkodowane kolory ('#f0f0f0', '#1e3a5f') do globalnego pliku konfiguracyjnego motywu (np. style.py).
        btn_frame = tk.Frame(self)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=18, pady=(10, 20))

        tk.Button(
            btn_frame,
            text="Anuluj",
            command=self._on_cancel,
            bg="#f0f0f0",
            fg="#333",
            relief=tk.FLAT,
            borderwidth=1,
            font=("Segoe UI", 9),
            padx=15,
            pady=5,
            cursor="hand2"
        ).pack(side=tk.RIGHT, padx=(8, 0))

        tk.Button(
            btn_frame,
            text="Zakończ konfigurację",
            command=self._on_finish,
            bg="#1e3a5f",
            fg="white",
            relief=tk.FLAT,
            activebackground="#2a5286",
            activeforeground="white",
            font=("Segoe UI", 9),
            padx=15,
            pady=5,
            cursor="hand2"
        ).pack(side=tk.RIGHT)

        # 2. NAGŁÓWEK (Na górze)
        # TODO: UX/UI: Dodać logo/ikonę aplikacji obok tytułu "BID — Kreator projektu" żeby rozbić tekst.
        header = tk.Frame(self, bg="#1e3a5f")
        header.pack(side=tk.TOP, fill=tk.X)
        tk.Label(
            header,
            text="⚙  BID — Kreator projektu",
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg="#1e3a5f",
            anchor=tk.W,
            pady=14,
            padx=18,
        ).pack(fill=tk.X)

        # 3. TREŚĆ (Wypełnia resztę)
        content_frame = tk.Frame(self)
        content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=18, pady=10)

        msg = (
            "Skonfiguruj nowy projekt, wskazując foldery źródłowe i docelowe.\n"
            "Projekt zostanie zapisany w katalogu 'projects/'."
        )
        tk.Label(content_frame, text=msg, justify=tk.LEFT, wraplength=460).pack(
            fill=tk.X, pady=(0, 10)
        )

        ttk.Separator(content_frame).pack(fill=tk.X, pady=(0, 10))

        # Sekcja Projektu
        proj_frame = ttk.LabelFrame(content_frame, text="Informacje o projekcie", padding=10)
        proj_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(proj_frame, text="Nazwa projektu:", anchor=tk.W).grid(
            row=0, column=0, sticky=tk.W, pady=4, padx=(0, 8)
        )
        ttk.Entry(proj_frame, textvariable=self._project_name_var, width=38).grid(
            row=0, column=1, sticky=tk.EW, pady=4
        )
        proj_frame.columnconfigure(1, weight=1)

        # Sekcja folderów
        folders_frame = ttk.LabelFrame(content_frame, text="Foldery", padding=10)
        folders_frame.pack(fill=tk.X, pady=(0, 10))

        self._add_folder_row(
            folders_frame, "Folder źródłowy (source):", self._source_var,
            row=0,
        )
        self._add_folder_row(
            folders_frame, "Folder docelowy (export):", self._export_var,
            row=1,
        )

        # Sekcja delivery
        if self.missing_export:
            exp_frame = ttk.LabelFrame(content_frame, text="Profile eksportu (domyślne)", padding=10)
            exp_frame.pack(fill=tk.X, pady=(0, 10))
            
            profiles = list(DEFAULT_EXPORT_OPTIONS.keys())
            summary = "  |  ".join(
                f"{k}: {DEFAULT_EXPORT_OPTIONS[k]['size']}px"
                for k in profiles
            )
            tk.Label(exp_frame, text=summary, font=("Segoe UI", 9), fg="#444", wraplength=440, justify=tk.LEFT).pack(anchor=tk.W)

        # Komunikat błędu
        self._status_label = tk.Label(
            content_frame,
            textvariable=self._status_var,
            fg="red",
            font=("Segoe UI", 9),
        )
        self._status_label.pack(anchor=tk.W)

    def _add_folder_row(
        self,
        parent: tk.Frame,
        label_text: str,
        var: tk.StringVar,
        row: int,
    ) -> None:
        """Dodaje wiersz z etykietą, polem tekstowym i przyciskiem Browse.

        Args:
            parent:     Ramka nadrzędna.
            label_text: Etykieta pola.
            var:        Zmienna tkinter przechowująca ścieżkę.
            row:        Numer wiersza w gridzie.
        """
        tk.Label(parent, text=label_text, anchor=tk.W).grid(
            row=row, column=0, sticky=tk.W, pady=4, padx=(0, 8)
        )
        entry = ttk.Entry(parent, textvariable=var, width=38)
        entry.grid(row=row, column=1, sticky=tk.EW, pady=4)
        # TODO: UX/UI: Zamiast szarego przycisku '…', użyć ikony folderu z biblioteki ikon (np. z Pillow/SVG).
        tk.Button(
            parent,
            text=" … ",
            command=lambda v=var: self._browse(v),
            bg="#e1e1e1",
            relief=tk.FLAT,
            borderwidth=1,
            cursor="hand2",
        ).grid(row=row, column=2, padx=(6, 0), pady=4)
        parent.columnconfigure(1, weight=1)

    # ------------------------------------------------------------------
    # Zdarzenia
    # ------------------------------------------------------------------

    def _browse(self, var: tk.StringVar) -> None:
        """Otwiera okno wyboru folderu i zapisuje wynik do var.

        Args:
            var: Zmienna tkinter do aktualizacji.
        """
        path = filedialog.askdirectory(title="Wybierz folder", mustexist=False)
        if path:
            var.set(path)

    def _on_finish(self) -> None:
        """Waliduje dane, tworzy projekt przez ProjectManager i zamyka wizard."""
        name = self._project_name_var.get().strip()
        source = self._source_var.get().strip()
        export = self._export_var.get().strip()
        
        if not name or not source or not export:
            self._status_var.set("⚠  Podaj nazwę projektu i oba foldery.")
            return

        try:
            from bid.project_manager import ProjectManager
            self.project_path = ProjectManager.create_project(
                name, source, export, DEFAULT_EXPORT_OPTIONS
            )
            self.completed = True
            logger.info(f"Utworzono projekt: {name} → {self.project_path}")
            self.destroy()  # triggers wait_window() return in parent
        except FileExistsError as exc:
            messagebox.showerror("Projekt już istnieje", f"Projekt o nazwie '{name}' już istnieje. Podaj inną nazwę.")
            return
        except Exception as exc:
            self._status_var.set(f"⚠  Błąd tworzenia projektu: {exc}")
            logger.error(f"SetupWizard Error: {exc}")

    def _on_cancel(self) -> None:
        """Zamyka wizard bez zapisywania."""
        self.completed = False
        self.destroy()

    # ------------------------------------------------------------------
    # Pomocnicze
    # ------------------------------------------------------------------

    def _center_window(self, width: int, height: int) -> None:
        """Wyśrodkowuje okno na ekranie.

        Args:
            width:  Szerokość okna w pikselach.
            height: Wysokość okna w pikselach.
        """
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")


# ---------------------------------------------------------------------------
# Funkcja pomocnicza — do wywołania z main.py
# ---------------------------------------------------------------------------

def run_wizard_if_needed(parent: tk.Misc) -> tuple[bool, Path | None]:
    """Wyświetla kreator projektu jako modalny Toplevel.

    WYMAGA istniejącej instancji tk.Tk jako 'parent'. Nie tworzy własnej tk.Tk,
    co zapobiega błędowi ``Tcl_AsyncDelete: async handler deleted by the wrong thread``.

    Args:
        parent: Istniejące okno Tkinter (np. instancja MainApp).

    Returns:
        Krotka (success, project_path).
    """
    logger.info("Uruchamiam kreator projektu.")

    wizard = SetupWizard(parent)
    wizard.grab_set()           # modal — blokuje interakcję z głównym oknem
    parent.wait_window(wizard)  # blokuje do czasu zamknięcia Toplevel

    return (wizard.completed, wizard.project_path)
