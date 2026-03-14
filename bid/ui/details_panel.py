"""
bid/ui/details_panel.py
Panel boczny wyświetlający szczegóły wybranego zdjęcia (EXIF, stan eksportu, wydajność).
"""
from __future__ import annotations

import logging
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Dict, Any

logger = logging.getLogger("BID")

if TYPE_CHECKING:
    from bid.app import MainApp

class DetailsPanel(ttk.Frame):
    """Panel wyświetlający metadane i statusy eksportu wybranego elementu."""

    def __init__(self, parent: tk.Widget, root: MainApp) -> None:
        super().__init__(parent, padding=10)
        self.root = root

        # --- Sekcja EXIF ---
        # TODO: UX/UI: Dodanie drobnej ikony (np. info obok nagłówka "Oryginalny EXIF") poprawiłoby wygląd.
        ttk.Label(self, text="Oryginalny EXIF", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        
        exif_container = ttk.Frame(self)
        exif_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.exif_tree = ttk.Treeview(exif_container, columns=["value"], height=12, show="tree headings")
        self.exif_tree.heading("#0", text="Tag")
        self.exif_tree.heading("value", text="Wartość")
        self.exif_tree.column("#0", width=120, minwidth=100)
        self.exif_tree.column("value", width=180, minwidth=150)
        
        v_scrollbar = ttk.Scrollbar(exif_container, orient=tk.VERTICAL, command=self.exif_tree.yview)
        h_scrollbar = ttk.Scrollbar(exif_container, orient=tk.HORIZONTAL, command=self.exif_tree.xview)
        self.exif_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # TODO: UX/UI: Przerobić w przyszłości scrollbary na autoukrywające się (pojawiają się tylko, gdy zawartość wychodzi poza ramy).
        # Layout using grid to accommodate both scrollbars
        self.exif_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        exif_container.grid_columnconfigure(0, weight=1)
        exif_container.grid_rowconfigure(0, weight=1)

        # --- Sekcja Eksporty ---
        event_row = ttk.Frame(self)
        event_row.pack(fill=tk.X, pady=(0, 4))
        ttk.Label(event_row, text="Zdarzenie:",
                  font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        self._event_var = tk.StringVar(value="---")
        ttk.Label(event_row, textvariable=self._event_var,
                  font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(4, 0))

        ttk.Label(self, text="Statusy eksportu", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        self.export_tree = ttk.Treeview(self, columns=["status"], height=4, show="tree headings")
        self.export_tree.heading("#0", text="Profil")
        self.export_tree.heading("status", text="Plik")
        self.export_tree.column("#0", width=80)
        self.export_tree.column("status", width=220)
        self.export_tree.pack(fill=tk.X, pady=(0, 10))

        # --- Sekcja Performance ---
        self.perf_var = tk.StringVar(value="Czas operacji: ---")
        ttk.Label(self, textvariable=self.perf_var, font=("Segoe UI", 9, "italic"), foreground="#666").pack(anchor=tk.W)

    def update_details(self, folder: str, photo: str, meta: Dict[str, Any]) -> None:
        """Odświeża dane w panelu na podstawie metadanych ze słownika.
        
        Args:
            folder: Nazwa folderu.
            photo: Nazwa pliku.
            meta: Metadane zdjęcia z source_dict.
        """
        logger.debug(f"[UI] Aktualizacja panelu dla: {folder}/{photo}")
        # --- EXIF ---
        for item in self.exif_tree.get_children():
            self.exif_tree.delete(item)
        
        # Podstawowe info na górze (sekcja pogrubiona)
        exif_dict = meta.get("exif", {})

        # Autor z EXIF (Artist) lub pusty jeśli brak
        artist_raw = exif_dict.get("Artist", "")
        if not artist_raw or not str(artist_raw).strip():
            logger.debug(f"[UI] Brak pola Artist w EXIF: {folder}/{photo}")
            artist_display = ""
        else:
            artist_display = str(artist_raw).strip()

        # Wymiary w pikselach i proporcje
        # Wymiary pochodzą z PIL (zawsze autorytatywne) przechowywane w metadanych indeksu jako ImageWidth/ImageLength
        # (są ustawiane w get_all_exif() bezpośrednio z img.width/img.height)
        # img_w = exif_dict.get("ImageWidth", "") or exif_dict.get("ExifImageWidth", "")
        # img_h = exif_dict.get("ImageLength", "") or exif_dict.get("ExifImageHeight", "")
        img_w = exif_dict.get("ImageWidth", "")
        img_h = exif_dict.get("ImageLength", "")
        try:
            w_int = int(str(img_w).split()[0]) if img_w else 0
            h_int = int(str(img_h).split()[0]) if img_h else 0
        except (ValueError, IndexError):
            w_int, h_int = 0, 0

        pixel_display = f"{w_int} x {h_int}" if w_int and h_int else "---"
        ratio_display = f"{round(w_int / h_int, 2)}" if w_int and h_int else "---"

        basic_tags = {
            "Rozmiar": meta.get("size", "---"),
            "Data": meta.get("created", "---"),
            "Stan": meta.get("state", "---"),
            "Autor": artist_display,
            "Piksele": pixel_display,
            "Proporcje": ratio_display,
        }
        for k, v in basic_tags.items():
            self.exif_tree.insert("", "end", text=k, values=(v,), tags=("bold",))
        
        # Wszystkie tagi EXIF ze słownika
        exif_dict = meta.get("exif", {})
        if exif_dict:
            # Sortujemy alfabetycznie dla łatwiejszego przeglądania
            for tag in sorted(exif_dict.keys()):
                val = exif_dict[tag]
                # Pomijamy puste wartości w widoku (ale zostają w słowniku)
                if val and str(val).strip():
                    self.exif_tree.insert("", "end", text=tag, values=(val,))
        
        self.exif_tree.tag_configure("bold", font=("Segoe UI", 9, "bold"))

        # --- Eksporty ---
        for item in self.export_tree.get_children():
            self.export_tree.delete(item)
        
        exported = meta.get("exported", {})
        for deliver in self.root.export_settings:
            path = exported.get(deliver, "Brak")
            status = "✓ Istnieje" if path != "Brak" else "---"
            self.export_tree.insert("", "end", text=deliver, values=(status,))

        # --- Zdarzenie ---
        ef = meta.get("event_folder", "")
        en = meta.get("event_name", "")
        if ef:
            self._event_var.set(f"{ef}" + (f"  —  {en}" if en else ""))
        else:
            self._event_var.set("---")

        # --- Performance ---
        duration = meta.get("duration_sec")
        if duration:
            self.perf_var.set(f"Czas operacji: {duration:.4f}s")
        else:
            self.perf_var.set("Czas operacji: ---")
