"""
bid/ui/export_wizard.py
Kreator nowego profilu eksportu.

Otwierany jako modalny Toplevel (grab_set + wait_window).
Umożliwia:
  - nazwanie profilu
  - wybór formatu (JPEG / PNG)
  - jakość / kompresja
  - wymaganie logo (per-profil)
  - umiejscowienie logo (4 narożniki)
  - rozmiar logo (piksele) i metoda skalowania
  - filtr proporcji (wielokrotne pary szer×wys → lista wartości dziesiętnych)
"""
from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger("BID")

_PLACEMENTS = ("bottom-right", "bottom-left", "top-right", "top-left")
_PLACEMENT_PL = {
    "bottom-right": "Prawy dół",
    "bottom-left":  "Lewy dół",
    "top-right":    "Prawy góra",
    "top-left":     "Lewy góra",
}
_SIZE_TYPES = ("longer", "shorter", "width", "height")
_SIZE_TYPE_PL = {
    "longer":  "Dłuższy bok",
    "shorter": "Krótszy bok",
    "width":   "Szerokość",
    "height":  "Wysokość",
}


class ExportProfileWizard(tk.Toplevel):
    """Kreator nowego profilu eksportu — uruchamiany jako modalny Toplevel.

    Po zatwierdzeniu ``self.profile_data`` zawiera gotowy słownik
    zgodny ze schematem ``export_option.json``.
    ``self.profile_name`` zawiera nazwę profilu.
    """

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self.completed: bool = False
        self.profile_name: str = ""
        self.profile_data: dict = {}

        self.title("BID — Nowy profil eksportu")
        self.resizable(False, False)
        self._center_window(580, 700)

        self._init_vars()
        self._build_ui()

    # ------------------------------------------------------------------
    # Zmienne Tkinter
    # ------------------------------------------------------------------

    def _init_vars(self) -> None:
        self._name_var        = tk.StringVar(value="nowy_profil")
        self._format_var      = tk.StringVar(value="JPEG")
        self._quality_var     = tk.IntVar(value=88)
        self._logo_req_var    = tk.BooleanVar(value=False)

        # Logo orientacja landscape
        self._land_size_var      = tk.IntVar(value=260)
        self._land_opacity_var   = tk.IntVar(value=60)
        self._land_x_var         = tk.IntVar(value=10)
        self._land_y_var         = tk.IntVar(value=10)
        self._land_place_var     = tk.StringVar(value="bottom-right")
        self._land_method_var    = tk.StringVar(value="longer")

        # Logo orientacja portrait
        self._port_size_var      = tk.IntVar(value=332)
        self._port_opacity_var   = tk.IntVar(value=60)
        self._port_x_var         = tk.IntVar(value=10)
        self._port_y_var         = tk.IntVar(value=10)
        self._port_place_var     = tk.StringVar(value="bottom-right")
        self._port_method_var    = tk.StringVar(value="longer")

        # Filtry proporcji
        self._ratio_w_var  = tk.StringVar(value="")
        self._ratio_h_var  = tk.StringVar(value="")
        self._ratio_calc   = tk.StringVar(value="—")
        self._ratios: list[float] = []

        self._status_var = tk.StringVar()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Buduje layout wizarda z sekcjami w ttk.Notebook."""

        # Przyciski (dół)
        btn_frame = tk.Frame(self)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=18, pady=(8, 16))

        tk.Button(
            btn_frame, text="Anuluj", command=self._on_cancel,
            bg="#f0f0f0", fg="#333", relief=tk.FLAT, borderwidth=1,
            font=("Segoe UI", 9), padx=14, pady=5, cursor="hand2"
        ).pack(side=tk.RIGHT, padx=(8, 0))

        tk.Button(
            btn_frame, text="Utwórz profil", command=self._on_finish,
            bg="#1e3a5f", fg="white", relief=tk.FLAT,
            activebackground="#2a5286", activeforeground="white",
            font=("Segoe UI", 9), padx=14, pady=5, cursor="hand2"
        ).pack(side=tk.RIGHT)

        tk.Label(
            btn_frame, textvariable=self._status_var,
            fg="red", font=("Segoe UI", 9)
        ).pack(side=tk.LEFT)

        # Nagłówek
        header = tk.Frame(self, bg="#1e3a5f")
        header.pack(side=tk.TOP, fill=tk.X)
        tk.Label(
            header, text="⚙  BID — Nowy profil eksportu",
            font=("Segoe UI", 13, "bold"), fg="white", bg="#1e3a5f",
            anchor=tk.W, pady=12, padx=18,
        ).pack(fill=tk.X)

        # Treść — Notebook
        nb = ttk.Notebook(self)
        nb.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=12, pady=8)

        # Karta 1: Podstawowe
        basic_frame = ttk.Frame(nb, padding=12)
        nb.add(basic_frame, text="  Podstawowe  ")
        self._build_basic(basic_frame)

        # Karta 2: Logo
        logo_frame = ttk.Frame(nb, padding=12)
        nb.add(logo_frame, text="  Logo  ")
        self._build_logo(logo_frame)

        # Karta 3: Proporcje
        ratio_frame = ttk.Frame(nb, padding=12)
        nb.add(ratio_frame, text="  Filtr proporcji  ")
        self._build_ratio(ratio_frame)

    # ------------------------------------------------------------------
    # Karta: Podstawowe
    # ------------------------------------------------------------------

    def _build_basic(self, parent: ttk.Frame) -> None:
        grid = parent

        # Nazwa
        tk.Label(grid, text="Nazwa profilu:", anchor=tk.W).grid(row=0, column=0, sticky=tk.W, pady=4, padx=(0, 10))
        ttk.Entry(grid, textvariable=self._name_var, width=28).grid(row=0, column=1, columnspan=2, sticky=tk.EW, pady=4)

        ttk.Separator(grid, orient=tk.HORIZONTAL).grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=8)

        # Format
        tk.Label(grid, text="Format eksportu:", anchor=tk.W).grid(row=2, column=0, sticky=tk.W, pady=4)
        fmt_frame = ttk.Frame(grid)
        fmt_frame.grid(row=2, column=1, columnspan=2, sticky=tk.W)
        ttk.Radiobutton(fmt_frame, text="JPEG", variable=self._format_var, value="JPEG",
                        command=self._on_format_change).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(fmt_frame, text="PNG", variable=self._format_var, value="PNG",
                        command=self._on_format_change).pack(side=tk.LEFT)

        # Jakość
        self._quality_label = tk.Label(grid, text="Jakość JPEG (10–100):", anchor=tk.W)
        self._quality_label.grid(row=3, column=0, sticky=tk.W, pady=4)
        self._quality_scale = ttk.Scale(
            grid, variable=self._quality_var, from_=10, to=100,
            orient=tk.HORIZONTAL, length=160, command=lambda v: self._quality_var.set(int(float(v)))
        )
        self._quality_scale.grid(row=3, column=1, sticky=tk.EW, padx=(0, 6))
        self._quality_val_label = tk.Label(grid, textvariable=tk.StringVar(), anchor=tk.W, width=4)
        # Live readout
        self._quality_disp = tk.StringVar(value=str(self._quality_var.get()))
        self._quality_var.trace_add("write", lambda *_: self._quality_disp.set(str(self._quality_var.get())))
        tk.Label(grid, textvariable=self._quality_disp, width=4).grid(row=3, column=2, sticky=tk.W)

        grid.columnconfigure(1, weight=1)

    def _on_format_change(self) -> None:
        fmt = self._format_var.get()
        if fmt == "JPEG":
            self._quality_label.config(text="Jakość JPEG (10–100):")
            self._quality_scale.config(from_=10, to=100)
            self._quality_var.set(88)
        else:
            self._quality_label.config(text="Kompresja PNG (1–9):")
            self._quality_scale.config(from_=1, to=9)
            self._quality_var.set(6)

    # ------------------------------------------------------------------
    # Karta: Logo
    # ------------------------------------------------------------------

    def _build_logo(self, parent: ttk.Frame) -> None:
        # Wymagalność logo
        req_frame = ttk.LabelFrame(parent, text="Ogólne", padding=10)
        req_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Checkbutton(
            req_frame,
            text="Logo wymagane (pomiń foldery bez logo.png)",
            variable=self._logo_req_var
        ).pack(anchor=tk.W)

        # Landscape
        land_frame = ttk.LabelFrame(parent, text="Logo — Poziomy (landscape)", padding=10)
        land_frame.pack(fill=tk.X, pady=(0, 8))
        self._build_logo_section(land_frame,
                                  self._land_size_var, self._land_opacity_var,
                                  self._land_x_var, self._land_y_var,
                                  self._land_place_var, self._land_method_var)

        # Portrait
        port_frame = ttk.LabelFrame(parent, text="Logo — Pionowy (portrait)", padding=10)
        port_frame.pack(fill=tk.X, pady=(0, 8))
        self._build_logo_section(port_frame,
                                  self._port_size_var, self._port_opacity_var,
                                  self._port_x_var, self._port_y_var,
                                  self._port_place_var, self._port_method_var)

    def _build_logo_section(
        self, parent: ttk.LabelFrame,
        size_var: tk.IntVar, opacity_var: tk.IntVar,
        x_var: tk.IntVar, y_var: tk.IntVar,
        place_var: tk.StringVar, method_var: tk.StringVar,
    ) -> None:
        """Buduje kontrolki dla jednej orientacji logo."""
        # Rozmiar + metoda skalowania
        tk.Label(parent, text="Rozmiar (px):", anchor=tk.W).grid(row=0, column=0, sticky=tk.W, pady=3, padx=(0, 8))
        ttk.Entry(parent, textvariable=size_var, width=8).grid(row=0, column=1, sticky=tk.W, pady=3)

        tk.Label(parent, text="Metoda skalowania:", anchor=tk.W).grid(row=0, column=2, sticky=tk.W, padx=(14, 6))
        method_cb = ttk.Combobox(
            parent, textvariable=method_var,
            values=[_SIZE_TYPE_PL[k] for k in _SIZE_TYPES],
            state="readonly", width=14
        )
        method_cb.grid(row=0, column=3, sticky=tk.W, pady=3)
        # Mapowanie PL → klucz
        method_cb.bind("<<ComboboxSelected>>",
                       lambda e, mv=method_var, cb=method_cb: mv.set(
                           _SIZE_TYPES[[_SIZE_TYPE_PL[k] for k in _SIZE_TYPES].index(cb.get())]
                       ))
        method_cb.set(_SIZE_TYPE_PL.get(method_var.get(), method_var.get()))

        # Opacity
        tk.Label(parent, text="Przezroczystość (0–100):", anchor=tk.W).grid(row=1, column=0, sticky=tk.W, pady=3)
        ttk.Entry(parent, textvariable=opacity_var, width=8).grid(row=1, column=1, sticky=tk.W, pady=3)

        # Offset X/Y
        tk.Label(parent, text="Offset X (px):", anchor=tk.W).grid(row=2, column=0, sticky=tk.W, pady=3)
        ttk.Entry(parent, textvariable=x_var, width=8).grid(row=2, column=1, sticky=tk.W, pady=3)

        tk.Label(parent, text="Offset Y (px):", anchor=tk.W).grid(row=2, column=2, sticky=tk.W, padx=(14, 6))
        ttk.Entry(parent, textvariable=y_var, width=8).grid(row=2, column=3, sticky=tk.W, pady=3)

        # Umiejscowienie
        tk.Label(parent, text="Umiejscowienie:", anchor=tk.W).grid(row=3, column=0, sticky=tk.W, pady=3)
        place_frame = ttk.Frame(parent)
        place_frame.grid(row=3, column=1, columnspan=3, sticky=tk.W)
        for p in _PLACEMENTS:
            ttk.Radiobutton(place_frame, text=_PLACEMENT_PL[p], variable=place_var, value=p).pack(side=tk.LEFT, padx=(0, 10))

    # ------------------------------------------------------------------
    # Karta: Filtr proporcji
    # ------------------------------------------------------------------

    def _build_ratio(self, parent: ttk.Frame) -> None:
        tk.Label(
            parent,
            text="Podaj proporcje jako szer × wys (np. 4 × 5).\nMożesz dodać kilka proporcji — zostaną dołączone do listy filtrów.",
            justify=tk.LEFT, wraplength=500
        ).pack(anchor=tk.W, pady=(0, 8))

        input_frame = ttk.Frame(parent)
        input_frame.pack(fill=tk.X, pady=(0, 6))

        tk.Label(input_frame, text="Szerokość:").pack(side=tk.LEFT)
        ttk.Entry(input_frame, textvariable=self._ratio_w_var, width=6).pack(side=tk.LEFT, padx=(4, 8))
        tk.Label(input_frame, text="×").pack(side=tk.LEFT)
        ttk.Entry(input_frame, textvariable=self._ratio_h_var, width=6).pack(side=tk.LEFT, padx=(4, 8))

        # Auto-kalkulator
        self._ratio_w_var.trace_add("write", lambda *_: self._calc_ratio())
        self._ratio_h_var.trace_add("write", lambda *_: self._calc_ratio())

        tk.Label(input_frame, text="=").pack(side=tk.LEFT, padx=(8, 4))
        tk.Label(input_frame, textvariable=self._ratio_calc, font=("Segoe UI", 9, "bold"), width=6).pack(side=tk.LEFT)

        tk.Button(
            input_frame, text="Dodaj →", command=self._add_ratio,
            bg="#1e3a5f", fg="white", relief=tk.FLAT, padx=10, pady=3, cursor="hand2",
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT, padx=(12, 0))

        # Lista dodanych proporcji
        list_frame = ttk.LabelFrame(parent, text="Dodane filtry proporcji", padding=8)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        self._ratio_listbox = tk.Listbox(list_frame, height=6, font=("Segoe UI", 9))
        self._ratio_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sb = ttk.Scrollbar(list_frame, command=self._ratio_listbox.yview)
        sb.pack(side=tk.LEFT, fill=tk.Y)
        self._ratio_listbox.configure(yscrollcommand=sb.set)

        tk.Button(
            list_frame, text="Usuń zaznaczoną", command=self._remove_ratio,
            bg="#c0392b", fg="white", relief=tk.FLAT, padx=8, pady=3, cursor="hand2",
            font=("Segoe UI", 9)
        ).pack(pady=(6, 0))

        tk.Label(
            parent,
            text="Pusta lista = brak filtrowania (eksportowane wszystkie zdjęcia).",
            font=("Segoe UI", 8), fg="#666"
        ).pack(anchor=tk.W, pady=(6, 0))

    def _calc_ratio(self) -> None:
        """Przelicza proporcję i wyświetla w polu 'kalkulator'."""
        try:
            w = float(self._ratio_w_var.get())
            h = float(self._ratio_h_var.get())
            if h == 0:
                self._ratio_calc.set("—")
                return
            self._ratio_calc.set(f"{round(w / h, 2):.2f}")
        except ValueError:
            self._ratio_calc.set("—")

    def _add_ratio(self) -> None:
        """Dodaje obliczoną proporcję do listy."""
        try:
            w = float(self._ratio_w_var.get())
            h = float(self._ratio_h_var.get())
            if h == 0:
                raise ValueError("Mianownik = 0")
            ratio = round(w / h, 2)
        except ValueError:
            messagebox.showwarning("Błąd", "Podaj poprawne wartości liczbowe dla szerokości i wysokości.", parent=self)
            return

        if ratio in self._ratios:
            messagebox.showinfo("Info", f"Proporcja {ratio} jest już na liście.", parent=self)
            return

        self._ratios.append(ratio)
        self._ratio_listbox.insert(tk.END, f"{self._ratio_w_var.get()} × {self._ratio_h_var.get()} = {ratio:.2f}")
        self._ratio_w_var.set("")
        self._ratio_h_var.set("")
        self._ratio_calc.set("—")

    def _remove_ratio(self) -> None:
        """Usuwa zaznaczoną proporcję z listy."""
        selection = self._ratio_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        self._ratios.pop(idx)
        self._ratio_listbox.delete(idx)

    # ------------------------------------------------------------------
    # Akcje
    # ------------------------------------------------------------------

    def _on_finish(self) -> None:
        """Waliduje i buduje słownik profilu."""
        name = self._name_var.get().strip()
        if not name:
            self._status_var.set("⚠  Podaj nazwę profilu.")
            return

        # Walidacja numeryczna
        try:
            land_size = int(self._land_size_var.get())
            land_opacity = int(self._land_opacity_var.get())
            land_x = int(self._land_x_var.get())
            land_y = int(self._land_y_var.get())
            port_size = int(self._port_size_var.get())
            port_opacity = int(self._port_opacity_var.get())
            port_x = int(self._port_x_var.get())
            port_y = int(self._port_y_var.get())
        except (ValueError, tk.TclError):
            self._status_var.set("⚠  Rozmiar/offset logo musi być liczbą całkowitą.")
            return

        for val, label in [(land_size, "Rozmiar landscape"), (port_size, "Rozmiar portrait")]:
            if val <= 0:
                self._status_var.set(f"⚠  {label} musi być > 0.")
                return

        fmt = self._format_var.get()
        quality = int(self._quality_var.get())

        profile: dict = {
            "size_type": self._land_method_var.get(),
            "size": land_size,
            "format": fmt,
            "quality": quality,
            "logo_required": self._logo_req_var.get(),
            "logo": {
                "landscape": {
                    "size": land_size,
                    "opacity": land_opacity,
                    "x_offset": land_x,
                    "y_offset": land_y,
                    "placement": self._land_place_var.get(),
                },
                "portrait": {
                    "size": port_size,
                    "opacity": port_opacity,
                    "x_offset": port_x,
                    "y_offset": port_y,
                    "placement": self._port_place_var.get(),
                },
            },
        }
        if self._ratios:
            profile["ratio"] = self._ratios

        from bid.validators import validate_export_profile
        errors = validate_export_profile(name, profile)
        if errors:
            self._status_var.set("⚠  " + errors[0])
            return

        self.profile_name = name
        self.profile_data = profile
        self.completed = True
        logger.info(f"Utworzono profil eksportu: {name}")
        self.destroy()

    def _on_cancel(self) -> None:
        self.completed = False
        self.destroy()

    # ------------------------------------------------------------------
    # Pomocnicze
    # ------------------------------------------------------------------

    def _center_window(self, width: int, height: int) -> None:
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")


def run_export_profile_wizard(parent: tk.Misc) -> tuple[bool, str, dict]:
    """Uruchamia kreator jako modalny Toplevel.

    Args:
        parent: Główne okno aplikacji.

    Returns:
        Krotka (success, profile_name, profile_dict).
    """
    wizard = ExportProfileWizard(parent)
    wizard.grab_set()
    parent.wait_window(wizard)
    return wizard.completed, wizard.profile_name, wizard.profile_data
