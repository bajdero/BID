"""
bid/ui/source_tree.py
Widget listy plików źródłowych — SourceTree.
"""
from __future__ import annotations

import logging

import _tkinter
import tkinter as tk
from tkinter import ttk

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from bid.app import MainApp

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

    def __init__(self, parent: tk.Widget, root: MainApp) -> None:
        """
        Args:
            parent: Widget nadrzędny (np. Frame).
            root:   Instancja MainApp (tk.Tk).
        """
        super().__init__(parent)
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

        # TODO: UX/UI: Zamiast kolorowania całego tła wiersza (co może być jaskrawe/nieczytelne), użyć ikon statusu (np. ✅, ❌, ⏳) w nowej kolumnie "Status". Kolory można zarezerwować tylko dla ikony lub delikatnego paska z lewej strony.
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
            foreground="#888888",     # przyciemniony tekst
        )
        self.source_tree.tag_configure(
            SourceState.SKIP,
            background="#ffebee",     # bardzo lekki czerwony/różowy
            foreground="#b71c1c",     # ciemnoczerwony tekst
        )

        self.source_tree.bind("<Double-1>", self._on_double_click)
        self.source_tree.bind("<<TreeviewSelect>>", self._on_select)
        self.source_tree.bind("<Button-3>", self._show_context_menu)
        self.source_tree.pack(fill=tk.BOTH, expand=True)

        self._build_context_menu()

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

        Używa MainApp.executor (ThreadPoolExecutor) zamiast tworzyć nowy wątek.
        Eliminuje problem przypadkowego uruchamiania GC na starych obiektach
        Tkinter z nowego wątku, co powodowało Tcl_AsyncDelete.
        """
        tree: ttk.Treeview = event.widget
        selected = tree.selection()
        if not selected:
            return
        item_id = selected[0]
        if "_" not in item_id:
            return

        path = tree.item(item_id)["values"][-1]
        self.root.executor.submit(self.root.source_prev.change_img, str(path))

    def _on_select(self, event: tk.Event) -> None:
        """Obsługa wyboru elementu — aktualizuje panel szczegółów."""
        tree: ttk.Treeview = event.widget
        selected = tree.selection()
        if not selected:
            return
        
        item_id = selected[0]
        # Sprawdzamy czy to plik (ma folder w ID)
        if "_" not in item_id:
            return
            
        folder, photo = item_id.split("_", 1)
        meta = self.root.source_dict.get(folder, {}).get(photo)
        if meta and hasattr(self.root, "details_panel"):
            self.root.details_panel.update_details(folder, photo, meta)

    def _build_context_menu(self) -> None:
        """Tworzy menu kontekstowe."""
        # TODO: UX/UI: Dodać argumenty `image=` do `add_command` aby w menu kontekstowym pojawiły się małe ikony akcji (np. odśwież, usuń). Zwiększy to profesjonalizm.
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Rerun all / Przetwórz ponownie", command=self._rerun_selected)
        self.context_menu.add_command(label="Skip / Pomiń (Delete from list)", command=self._skip_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Refresh / Odśwież", command=lambda: self.root.update_source())

    def _show_context_menu(self, event: tk.Event) -> None:
        """Wyświetla menu kontekstowe pod kursorem."""
        item = self.source_tree.identify_row(event.y)
        if item:
            self.source_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _rerun_selected(self) -> None:
        """Resetuje stan wybranego zdjęcia do NEW."""
        selected = self.source_tree.selection()
        if not selected or "_" not in selected[0]:
            return
        folder, photo = selected[0].split("_", 1)
        self.root.source_dict[folder][photo]["state"] = SourceState.NEW
        self.root.source_dict[folder][photo]["exported"] = {}
        self.change_tag(folder, photo, SourceState.NEW)
        self.root.scan_photos()

    def _skip_selected(self) -> None:
        """Oznacza wybrane zdjęcie jako SKIP."""
        selected = self.source_tree.selection()
        if not selected or "_" not in selected[0]:
            return
        folder, photo = selected[0].split("_", 1)
        self.root.source_dict[folder][photo]["state"] = SourceState.SKIP
        self.change_tag(folder, photo, SourceState.SKIP)
