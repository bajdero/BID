"""
bid/ui/source_tree.py
Widget listy plików źródłowych — SourceTree.
"""
from __future__ import annotations

import logging
from threading import Thread

import _tkinter
import tkinter as tk
from tkinter import ttk

from bid.source_manager import SourceState

logger = logging.getLogger("Yapa_CM")


class SourceTree(tk.Frame):
    """Widok drzewa plików źródłowych z kolorowym kodowaniem statusu.

    Kolory tagów:
        - new:        szary          → gotowe do przetworzenia
        - processing: niebieski      → trwa przetwarzanie
        - ok:         zielony        → zakończono sukcesem
        - error:      czerwony       → błąd
        - deleted:    ciemnoszary    → plik źródłowy usunięty z dysku
    """

    def __init__(self, root: tk.Tk) -> None:
        """
        Args:
            root: Okno nadrzędne (MainApp).
        """
        super().__init__(root)
        self.root = root

        self.source_tree = ttk.Treeview(
            self,
            columns=["rozmiar", "date", "path"],
            displaycolumns=["rozmiar", "date"],
            height=23,
            selectmode="browse",
        )
        self.source_tree.column("#0",      width=200)
        self.source_tree.column("rozmiar", width=80)
        self.source_tree.column("date",    width=120)
        self.source_tree.heading("#0",      text="Nazwa",   anchor=tk.W)
        self.source_tree.heading("rozmiar", text="Rozmiar", anchor=tk.W)
        self.source_tree.heading("date",    text="Data",    anchor=tk.W)

        self.source_tree.tag_configure(SourceState.NEW,        background="light gray")
        self.source_tree.tag_configure(SourceState.PROCESSING, background="sky blue")
        self.source_tree.tag_configure(SourceState.OK,         background="pale green")
        self.source_tree.tag_configure(
            SourceState.OK_OLD,    
            background="#c8e6c9",   # jeszcze bledszy zielony / miętowy
            foreground="#2e7d32",   # ciemniejszy zielony tekst
        )
        self.source_tree.tag_configure(SourceState.ERROR,      background="coral")
        self.source_tree.tag_configure(
            SourceState.DELETED,
            background="#d0d0d0",     # szary tło
            foreground="#888888",     # przyciemniony tekst — sygnalizuje brak pliku
        )

        self.source_tree.bind("<Double-1>", self._on_double_click)
        self.source_tree.pack()

    # ------------------------------------------------------------------
    # Publiczne API
    # ------------------------------------------------------------------

    def change_tag(self, folder: str, photo: str, tag: str) -> None:
        """Zmienia tag (kolor) wpisu w drzewie.

        Args:
            folder: Nazwa folderu / autora.
            photo:  Nazwa pliku zdjęcia.
            tag:    Wartość z klasy SourceState.
        """
        logger.debug(f"Zmieniam tag: {folder}/{photo} → {tag}")
        try:
            self.source_tree.item(f"{folder}_{photo}", tags=tag)
        except _tkinter.TclError as exc:
            logger.warning(f"Nie można zmienić tagu {folder}/{photo}: {exc}")

    def update_tree(self, source_dict: dict) -> None:
        """Dodaje do drzewa nowe foldery i pliki (nie usuwa istniejących).

        Args:
            source_dict: Słownik zdjęć z source_manager.
        """
        for folder, photos in list(source_dict.items()):
            count_label = f"{len(photos)} zdjęć"
            try:
                self.source_tree.insert(
                    "", "end", folder, text=folder, values=(count_label,)
                )
            except _tkinter.TclError:
                # Folder już istnieje — tylko aktualizujemy licznik
                self.source_tree.item(folder, values=(count_label,))

            for file, meta in list(photos.items()):
                try:
                    self.source_tree.insert(
                        folder,
                        "end",
                        id=f"{folder}_{file}",
                        text=file,
                        values=[meta["size"], meta["created"], meta["path"]],
                        tags=meta["state"],
                    )
                except _tkinter.TclError:
                    # Plik już istnieje — odśwież tylko tag (stan mógł się zmienić)
                    try:
                        self.source_tree.item(
                            f"{folder}_{file}", tags=meta["state"]
                        )
                    except _tkinter.TclError:
                        pass

    # ------------------------------------------------------------------
    # Wewnętrzne
    # ------------------------------------------------------------------

    def _on_double_click(self, event: tk.Event) -> None:
        """Obsługa podwójnego kliknięcia — ładuje podgląd zdjęcia.

        Args:
            event: Zdarzenie tkinter.
        """
        tree: ttk.Treeview = event.widget
        try:
            selected = tree.selection()
            if not selected:
                return
            path = tree.item(selected[0])["values"][-1]
            # Aktualizacja podglądu w wątku pomocniczym, żeby nie blokować UI
            Thread(
                target=self.root.source_prev.change_img,
                args=(str(path),),
                daemon=True,
            ).start()
        except (_tkinter.TclError, IndexError) as exc:
            logger.error(f"Błąd wyboru elementu w drzewie: {exc}")
