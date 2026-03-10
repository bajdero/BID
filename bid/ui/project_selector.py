import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
from pathlib import Path
import os
from bid.project_manager import ProjectManager

logger = logging.getLogger("Yapa_CM")

class ProjectSelector(tk.Toplevel):
    """Okno wyboru projektu — uruchamiane jako Toplevel w​ istniejącej instancji Tk.

    Nigdy nie tworzy własnej instancji tk.Tk, aby uniknąć błędu:
    ``Tcl_AsyncDelete: async handler deleted by the wrong thread``.
    """

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        
        self.title("BID — Wybierz projekt")
        self.geometry("600x450")
        self.resizable(False, False)
        
        self.selected_project: Path | None = None
        self.create_new: bool = False
        
        # Pruning (usuwamy niedziałające projekty)
        ProjectManager.prune_recent_projects()
        self.recent_projects = ProjectManager.get_recent_projects()
        
        self._center_window(600, 450)
        self._build_ui()

    def _center_window(self, width: int, height: int) -> None:
        """Centruje okno na ekranie."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self) -> None:
        """Buduje układ okna."""
        # ---- Nagłówek ----
        # TODO: UX/UI: Przenieść hardkodowany kolor nagłówka (#1e3a5f) do scentralizowanego motywu.
        header = tk.Frame(self, bg="#1e3a5f")
        header.pack(fill=tk.X)
        tk.Label(
            header,
            text="📁  BID — Wybierz projekt",
            font=("Segoe UI", 16, "bold"),
            fg="white",
            bg="#1e3a5f",
            anchor=tk.W,
            pady=20,
            padx=20,
        ).pack(fill=tk.X)

        # ---- Kontener główny ----
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # ---- Lista projektów (Treeview) ----
        # TODO: UX/UI: Poprawić styl Treeview (np. zwiększyć padding wierszy, usunąć standardowe ramki) przez ttk.Style.
        columns = ("name", "last_mod", "photos")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=8)
        
        self.tree.heading("name", text="Nazwa projektu")
        self.tree.heading("last_mod", text="Ostatnia edycja")
        self.tree.heading("photos", text="Zdjęcia")
        
        self.tree.column("name", width=250)
        self.tree.column("last_mod", width=150)
        self.tree.column("photos", width=80, anchor=tk.CENTER)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Wypełnianie danymi
        for path in self.recent_projects:
            details = ProjectManager.get_project_details(path)
            self.tree.insert("", tk.END, iid=path, values=(
                details["name"],
                details["last_modified"],
                details["photo_count"]
            ))

        # Domyślnie zaznacz pierwszy
        if self.recent_projects:
            self.tree.selection_set(self.recent_projects[0])

        self.tree.bind("<Double-1>", lambda e: self._on_open_selected())

        # ---- Przyciski ----
        # TODO: UX/UI: Dodać tło do ramki przycisków lub separator, żeby wyraźnie oddzielić je od listy projektów.
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 20))

        # Styl dla przycisków
        # TODO: UX/UI: Przyciski ttk domyślnie są dość małe. Warto stworzyć customowy styl (TButton) z większym paddingiem i lepszym fontem.
        btn_style = {"width": 15}

        ttk.Button(
            btn_frame, 
            text="Otwórz wybrany", 
            command=self._on_open_selected,
            **btn_style
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            btn_frame, 
            text="Nowy projekt...", 
            command=self._on_new_project,
            **btn_style
        ).pack(side=tk.LEFT, padx=10)

        ttk.Button(
            btn_frame, 
            text="Inny folder...", 
            command=self._on_browse,
            **btn_style
        ).pack(side=tk.LEFT)

        ttk.Button(
            btn_frame,
            text="Wyjść",
            command=self.destroy,
            **btn_style
        ).pack(side=tk.RIGHT)

    def _on_open_selected(self, event=None) -> str:
        """Otwiera zaznaczony projekt."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Wybór", "Proszę zaznaczyć projekt z listy.")
            return "break"

        path = selection[0]
        self.selected_project = Path(path)
        logger.info(f"[UI] Wybrano projekt: {self.selected_project}")
        self.destroy()  # triggers wait_window() return in parent
        return "break"

    def _on_new_project(self) -> None:
        """Zamyka okno z flagą tworzenia nowego projektu."""
        self.create_new = True
        self.destroy()

    def _on_browse(self) -> None:
        """Otwiera dialog wyboru folderu."""
        from bid.project_manager import PROJECTS_DIR
        path = filedialog.askdirectory(
            title="Wybierz folder projektu",
            initialdir=str(PROJECTS_DIR),
            mustexist=True
        )
        if path:
            logger.info(f"[UI] Przeglądanie projektu z: {path}")
            if os.path.exists(os.path.join(path, "settings.json")):
                self.selected_project = Path(path)
                self.destroy()
            else:
                messagebox.showerror("Błąd", "Wybrany folder nie jest poprawnym projektem BID.")

def run_project_selector(parent: tk.Misc) -> tuple[bool, bool, Path | None]:
    """Uruchamia okno wyboru projektu jako modalny Toplevel.

    WYMAGA istniejącej instancji tk.Tk jako 'parent'. Nie tworzy własnej tk.Tk,
    co zapobiega błędowi ``Tcl_AsyncDelete: async handler deleted by the wrong thread``.

    Args:
        parent: Istniejące okno Tkinter (np. instancja MainApp).

    Returns:
        Krotka (success, create_new, project_path).
    """
    selector = ProjectSelector(parent)
    selector.grab_set()           # modal — blokuje interakcję z głównym oknem
    parent.wait_window(selector)  # blokuje do czasu zamknięcia Toplevel

    success = selector.selected_project is not None or selector.create_new
    return (success, selector.create_new, selector.selected_project)
