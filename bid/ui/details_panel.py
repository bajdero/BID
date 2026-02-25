"""
bid/ui/details_panel.py
Panel boczny wyświetlający szczegóły wybranego zdjęcia (EXIF, stan eksportu, wydajność).
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from bid.app import MainApp

class DetailsPanel(ttk.Frame):
    """Panel wyświetlający metadane i statusy eksportu wybranego elementu."""

    def __init__(self, parent: tk.Widget, root: MainApp) -> None:
        super().__init__(parent, padding=10)
        self.root = root

        # --- Sekcja EXIF ---
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
        
        # Layout using grid to accommodate both scrollbars
        self.exif_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        exif_container.grid_columnconfigure(0, weight=1)
        exif_container.grid_rowconfigure(0, weight=1)

        # --- Sekcja Eksporty ---
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
        # --- EXIF ---
        for item in self.exif_tree.get_children():
            self.exif_tree.delete(item)
        
        # Podstawowe info na górze
        basic_tags = {
            "Rozmiar": meta.get("size", "---"),
            "Data": meta.get("created", "---"),
            "Stan": meta.get("state", "---"),
        }
        for k, v in basic_tags.items():
            self.exif_tree.insert("", "end", text=k, values=(v,), tags=("bold",))
        
        # Wszystkie tagi EXIF ze słownika
        exif_dict = meta.get("exif", {})
        if exif_dict:
            # Sortujemy alfabetycznie dla łatwiejszego przeglądania
            for tag in sorted(exif_dict.keys()):
                val = exif_dict[tag]
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

        # --- Performance ---
        duration = meta.get("duration_sec")
        if duration:
            self.perf_var.set(f"Czas operacji: {duration:.4f}s")
        else:
            self.perf_var.set("Czas operacji: ---")
