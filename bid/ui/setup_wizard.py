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
    "fb": {
        "size_type": "longer",
        "size": 1200,
        "format": "PNG",
        "quality": 9,
        "logo": {
            "landscape": {"size": 240, "opacity": 60, "x_offset": 10, "y_offset": 10},
            "portrait":  {"size": 312, "opacity": 60, "x_offset": 10, "y_offset": 10},
        },
    },
    "insta": {
        "size_type": "width",
        "size": 1080,
        "format": "PNG",
        "quality": 9,
        "logo": {
            "landscape": {"size": 228, "opacity": 60, "x_offset": 10, "y_offset": 10},
            "portrait":  {"size": 296, "opacity": 60, "x_offset": 10, "y_offset": 10},
        },
    },
    "insta_q": {
        "ratio": [1],
        "size_type": "width",
        "size": 1200,
        "format": "PNG",
        "quality": 9,
        "logo": {
            "landscape": {"size": 312, "opacity": 60, "x_offset": 10, "y_offset": 10},
            "portrait":  {"size": 312, "opacity": 60, "x_offset": 10, "y_offset": 10},
        },
    },
    "lzp": {
        "ratio": [0.8, 1.25],
        "size_type": "longer",
        "size": 1500,
        "format": "PNG",
        "quality": 9,
        "logo": {
            "landscape": {"size": 260, "opacity": 60, "x_offset": 10, "y_offset": 10},
            "portrait":  {"size": 332, "opacity": 60, "x_offset": 10, "y_offset": 10},
        },
    },
}


# ---------------------------------------------------------------------------
# Wizard
# ---------------------------------------------------------------------------

class SetupWizard(tk.Tk):
    """Okno kreatora pierwszego uruchomienia.

    Po zakończeniu (kliknięcie 'Zakończ') zapisuje settings.json
    i ewentualnie export_option.json, a następnie zamyka okno.
    Jeśli użytkownik anuluje, ``self.completed`` wynosi False.
    """

    def __init__(
        self,
        settings_path: Path,
        export_options_path: Path,
        missing_settings: bool,
        missing_export: bool,
    ) -> None:
        """
        Args:
            settings_path:       Docelowa ścieżka settings.json.
            export_options_path: Docelowa ścieżka export_option.json.
            missing_settings:    Czy settings.json nie istnieje / jest błędny.
            missing_export:      Czy export_option.json nie istnieje / jest błędny.
        """
        super().__init__()
        self.settings_path = settings_path
        self.export_options_path = export_options_path
        self.missing_settings = missing_settings
        self.missing_export = missing_export
        self.completed: bool = False

        self.title("BID — Konfiguracja początkowa")
        self.resizable(False, False)
        self._center_window(520, 380)

        self._build_ui()

    # ------------------------------------------------------------------
    # Budowanie UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Buduje układ okna kreatora."""
        pad = {"padx": 18, "pady": 8}

        # ---- Nagłówek ----
        header = tk.Frame(self, bg="#1e3a5f")
        header.pack(fill=tk.X)
        tk.Label(
            header,
            text="⚙  BID — Konfiguracja początkowa",
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg="#1e3a5f",
            anchor=tk.W,
            pady=14,
            padx=18,
        ).pack(fill=tk.X)

        # ---- Opis brakujących plików ----
        missing = []
        if self.missing_settings:
            missing.append("settings.json")
        if self.missing_export:
            missing.append("export_option.json")

        msg = (
            f"Nie znaleziono plików: {', '.join(missing)}.\n"
            "Uzupełnij poniższe dane, aby uruchomić aplikację."
        )
        tk.Label(self, text=msg, justify=tk.LEFT, wraplength=480, pady=10).pack(
            fill=tk.X, **{"padx": 18}
        )

        ttk.Separator(self).pack(fill=tk.X, padx=18)

        # ---- Sekcja folderów (tylko gdy brakuje settings.json) ----
        if self.missing_settings:
            folders_frame = ttk.LabelFrame(self, text="Foldery", padding=10)
            folders_frame.pack(fill=tk.X, **pad)

            self._source_var = tk.StringVar()
            self._export_var = tk.StringVar()

            self._add_folder_row(
                folders_frame, "Folder źródłowy (source):", self._source_var,
                row=0,
            )
            self._add_folder_row(
                folders_frame, "Folder docelowy (export):", self._export_var,
                row=1,
            )

        # ---- Sekcja delivery (tylko gdy brakuje export_option.json) ----
        if self.missing_export:
            exp_frame = ttk.LabelFrame(
                self, text="Profile eksportu (domyślne)", padding=10
            )
            exp_frame.pack(fill=tk.X, **pad)
            profiles = list(DEFAULT_EXPORT_OPTIONS.keys())
            summary = "  |  ".join(
                f"{k}: {DEFAULT_EXPORT_OPTIONS[k]['size']}px "
                f"({DEFAULT_EXPORT_OPTIONS[k]['format']})"
                for k in profiles
            )
            tk.Label(
                exp_frame,
                text=summary,
                font=("Segoe UI", 9),
                fg="#444",
                wraplength=455,
                justify=tk.LEFT,
            ).pack(anchor=tk.W)
            tk.Label(
                exp_frame,
                text="Możesz edytować export_option.json po zakończeniu.",
                font=("Segoe UI", 8, "italic"),
                fg="#888",
            ).pack(anchor=tk.W)

        # ---- Komunikat walidacji ----
        self._status_var = tk.StringVar()
        self._status_label = tk.Label(
            self,
            textvariable=self._status_var,
            fg="red",
            font=("Segoe UI", 9),
        )
        self._status_label.pack(padx=18, anchor=tk.W)

        # ---- Przyciski ----
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=18, pady=(4, 16), side=tk.BOTTOM)

        # Wspólne style dla przycisków
        btn_style = {
            "font": ("Segoe UI", 9),
            "padx": 15,
            "pady": 5,
            "cursor": "hand2",
        }

        # Przycisk Anuluj
        tk.Button(
            btn_frame,
            text="Anuluj",
            command=self._on_cancel,
            bg="#f0f0f0",
            fg="#333",
            relief=tk.FLAT,
            borderwidth=1,
            **btn_style
        ).pack(side=tk.RIGHT, padx=(8, 0))

        # Przycisk Zakończ
        tk.Button(
            btn_frame,
            text="Zakończ konfigurację",
            command=self._on_finish,
            bg="#1e3a5f",
            fg="white",
            relief=tk.FLAT,
            activebackground="#2a5286",
            activeforeground="white",
            **btn_style
        ).pack(side=tk.RIGHT)

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
        """Waliduje dane, zapisuje pliki konfiguracyjne i zamyka wizard."""
        if self.missing_settings:
            source = self._source_var.get().strip()
            export = self._export_var.get().strip()
            if not source or not export:
                self._status_var.set(
                    "⚠  Podaj oba foldery, aby kontynuować."
                )
                return

            try:
                settings = {
                    "source_folder": source,
                    "export_folder": export,
                }
                with open(self.settings_path, "w", encoding="utf-8") as fh:
                    json.dump(settings, fh, indent=4, ensure_ascii=False)
                logger.info(f"Zapisano settings.json → {self.settings_path}")
            except Exception as exc:
                self._status_var.set(f"⚠  Błąd zapisu settings.json: {exc}")
                return

        if self.missing_export:
            try:
                with open(self.export_options_path, "w", encoding="utf-8") as fh:
                    json.dump(DEFAULT_EXPORT_OPTIONS, fh, indent=4, ensure_ascii=False)
                logger.info(
                    f"Zapisano domyślny export_option.json → {self.export_options_path}"
                )
            except Exception as exc:
                self._status_var.set(f"⚠  Błąd zapisu export_option.json: {exc}")
                return

        self.completed = True
        self.destroy()

    def _on_cancel(self) -> None:
        """Zamyka wizard bez zapisywania — aplikacja nie zostanie uruchomiona."""
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

def run_wizard_if_needed(
    settings_path: Path,
    export_options_path: Path,
) -> bool:
    """Wyświetla kreatora jeśli brakuje któregoś pliku konfiguracji.

    Args:
        settings_path:       Ścieżka do settings.json.
        export_options_path: Ścieżka do export_option.json.

    Returns:
        True jeśli aplikacja może kontynuować (wizard ukończony lub
        oba pliki już istniały), False jeśli użytkownik anulował.
    """
    missing_settings = not settings_path.is_file()
    missing_export   = not export_options_path.is_file()

    if not missing_settings and not missing_export:
        return True  # nic do roboty

    logger.warning(
        "Brakujące pliki konfiguracji: "
        + (", ".join(
            f for f, m in [
                ("settings.json", missing_settings),
                ("export_option.json", missing_export),
            ] if m
        ))
        + " — uruchamiam kreator."
    )

    wizard = SetupWizard(
        settings_path=settings_path,
        export_options_path=export_options_path,
        missing_settings=missing_settings,
        missing_export=missing_export,
    )
    wizard.mainloop()
    return wizard.completed
