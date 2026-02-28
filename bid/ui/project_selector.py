import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
from pathlib import Path
import os
from bid.project_manager import ProjectManager

logger = logging.getLogger("Yapa_CM")

class ProjectSelector(tk.Tk):
    """Okno wyboru projektu na starcie aplikacji."""
    
    def __init__(self) -> None:
        super().__init__()
        
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
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 20))

        # Styl dla przycisków
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
            text="Wyjdź", 
            command=self.quit,
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
        self.withdraw()
        self.quit()
        return "break"

    def _on_new_project(self) -> None:
        """Zamyka okno z flagą tworzenia nowego projektu."""
        self.create_new = True
        self.withdraw()
        self.quit()

    def _on_browse(self) -> None:
        """Otwiera dialog wyboru folderu."""
        from bid.project_manager import PROJECTS_DIR
        path = filedialog.askdirectory(
            title="Wybierz folder projektu",
            initialdir=str(PROJECTS_DIR),
            mustexist=True
        )
        if path:
            if os.path.exists(os.path.join(path, "settings.json")):
                self.selected_project = Path(path)
                self.withdraw()
                self.quit()
            else:
                messagebox.showerror("Błąd", "Wybrany folder nie jest poprawnym projektem BID.")

def run_project_selector() -> tuple[bool, bool, Path | None]:
    """Uruchamia okno wyboru projektu.
    
    Returns:
        Krotka (success, create_new, project_path).
    """
    selector = ProjectSelector()
    selector.mainloop()
    
    success = selector.selected_project is not None or selector.create_new
    res = (success, selector.create_new, selector.selected_project)
    
    try:
        selector.destroy()
    except:
        pass
        
    return res
