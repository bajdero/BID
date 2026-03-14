"""
bid/ui/events_window.py
Singleton Toplevel for managing event JSON sources and viewing the schedule.

Layout
------
Top section  : registered source URLs/files  + Add URL / Add File / Remove / Reload
Bottom section: chronological event timeline  with photo counts per event
"""
from __future__ import annotations

import logging
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bid.app import MainApp

logger = logging.getLogger("BID")


class EventsWindow(tk.Toplevel):
    """Single-instance events management window.

    Open via ``EventsWindow.show(root)``; calling it again just raises the
    existing window.
    """

    _instance: "EventsWindow | None" = None

    @classmethod
    def show(cls, root: "MainApp") -> "EventsWindow":
        """Return existing window (focused) or create a new one."""
        if cls._instance is not None:
            try:
                if cls._instance.winfo_exists():
                    cls._instance.lift()
                    cls._instance.focus_force()
                    return cls._instance
            except Exception:
                pass
        win = cls(root)
        cls._instance = win
        return win

    # ------------------------------------------------------------------
    def __init__(self, root: "MainApp") -> None:
        super().__init__(root)
        self.root = root
        self.title("Zdarzenia — źródła i harmonogram")
        self.geometry("860x540")
        self.minsize(600, 400)
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # ---- Sources ----
        src_lf = ttk.LabelFrame(self, text="Źródła JSON", padding=6)
        src_lf.pack(fill=tk.X, padx=8, pady=6)

        lb_frame = ttk.Frame(src_lf)
        lb_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._lb = tk.Listbox(lb_frame, height=4, selectmode=tk.SINGLE,
                              font=("Segoe UI", 9))
        sb = ttk.Scrollbar(lb_frame, orient=tk.VERTICAL, command=self._lb.yview)
        self._lb.configure(yscrollcommand=sb.set)
        self._lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        btn_f = ttk.Frame(src_lf)
        btn_f.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0))
        for text, cmd in [
            ("+ URL",      self._add_url),
            ("+ Plik",     self._add_file),
            ("Usuń",       self._remove),
            (None,         None),          # separator
            ("Przeładuj",  self._reload),
        ]:
            if text is None:
                ttk.Separator(btn_f, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=4)
            else:
                ttk.Button(btn_f, text=text, width=11,
                           command=cmd).pack(pady=2, fill=tk.X)

        # ---- Timeline ----
        tl_lf = ttk.LabelFrame(self, text="Harmonogram", padding=6)
        tl_lf.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 6))

        cols = ("nr", "czas", "nazwa", "folder", "zdjecia", "status")
        self._tl = ttk.Treeview(tl_lf, columns=cols, show="headings",
                                 height=16, selectmode="browse")
        col_cfg = {
            "nr":      ("#",        35,  tk.CENTER),
            "czas":    ("Czas",     115, tk.W),
            "nazwa":   ("Nazwa",    220, tk.W),
            "folder":  ("Folder",   165, tk.W),
            "zdjecia": ("Zdjęcia",  62,  tk.CENTER),
            "status":  ("Status",   56,  tk.CENTER),
        }
        for col, (label, width, anchor) in col_cfg.items():
            self._tl.heading(col, text=label, anchor=anchor)
            self._tl.column(col, width=width, minwidth=30, anchor=anchor,
                            stretch=(col == "nazwa"))

        self._tl.tag_configure("was",  background="#e8f5e9")
        self._tl.tag_configure("will", background="#e3f2fd")

        tl_sb = ttk.Scrollbar(tl_lf, orient=tk.VERTICAL, command=self._tl.yview)
        self._tl.configure(yscrollcommand=tl_sb.set)
        self._tl.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tl_sb.pack(side=tk.RIGHT, fill=tk.Y)

        # ---- Status bar ----
        self._status_var = tk.StringVar()
        ttk.Label(self, textvariable=self._status_var,
                  font=("Segoe UI", 8), foreground="#555",
                  padding=(8, 2)).pack(side=tk.BOTTOM, fill=tk.X)

    # ------------------------------------------------------------------
    # Data refresh
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Re-populate sources list and timeline from current EventManager state."""
        self._refresh_sources()
        self._refresh_timeline()

    def _refresh_sources(self) -> None:
        self._lb.delete(0, tk.END)
        for src in self.root.event_manager.sources:
            self._lb.insert(tk.END, src.location)

    def _refresh_timeline(self) -> None:
        for item in self._tl.get_children():
            self._tl.delete(item)

        em = self.root.event_manager
        folder_map = em.folder_map

        # Count photos per event_folder
        photo_counts: dict[str, int] = {}
        for folder_photos in self.root.source_dict.values():
            for meta in folder_photos.values():
                ef = meta.get("event_folder")
                if ef:
                    photo_counts[ef] = photo_counts.get(ef, 0) + 1

        # Collect and sort all events
        all_events = []
        for schedule in em.schedules:
            for event in schedule.events:
                all_events.append(event)
        all_events.sort(key=lambda e: e.start)

        if not all_events:
            self._status_var.set(
                "Brak załadowanych zdarzeń. Dodaj źródło JSON i kliknij Przeładuj."
            )
            return

        # Pick timezone for display
        try:
            tz = em.local_tz
        except AttributeError:
            tz = None

        for idx, event in enumerate(all_events, start=1):
            if tz:
                t_start = event.start.astimezone(tz)
                t_end = event.end.astimezone(tz)
            else:
                t_start = event.start
                t_end = event.end
            czas = f"{t_start.strftime('%H:%M')}\u2013{t_end.strftime('%H:%M')}"

            subfolder = folder_map.get(event.id, "")
            n_photos = photo_counts.get(subfolder, 0)
            status = event.status.value if hasattr(event.status, "value") else str(event.status)
            tag = status if status in ("was", "will", "now") else ""

            self._tl.insert("", "end",
                            values=(idx, czas, event.name, subfolder or "---", n_photos, status),
                            tags=(tag,) if tag else ())

        total_photos = sum(photo_counts.values())
        self._status_var.set(
            f"Zdarzeń: {len(all_events)}   |   Przypisanych zdjęć: {total_photos}"
        )

    # ------------------------------------------------------------------
    # Source actions
    # ------------------------------------------------------------------

    def _add_url(self) -> None:
        url = simpledialog.askstring(
            "Dodaj URL",
            "Adres URL do pliku JSON ze zdarzeniami:",
            parent=self,
        )
        if url and url.strip():
            self._do_add(url.strip())

    def _add_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Wybierz plik JSON ze zdarzeniami",
            filetypes=[("JSON", "*.json"), ("Wszystkie pliki", "*.*")],
            parent=self,
        )
        if path:
            self._do_add(path)

    def _do_add(self, location: str) -> None:
        try:
            self.root.event_manager.add_source(location)
        except ValueError as exc:
            messagebox.showerror("Błąd", str(exc), parent=self)
            return
        except Exception as exc:
            messagebox.showerror("Błąd", f"Nie można dodać źródła:\n{exc}", parent=self)
            return

        # Apply: load → annotate → move files → queue new photos
        self.root._events_apply(move_files=True, trigger_scan=True)
        self.refresh()

    def _remove(self) -> None:
        sel = self._lb.curselection()
        if not sel:
            return
        location = self._lb.get(sel[0])
        if not messagebox.askyesno(
            "Usuń źródło", f"Usunąć źródło?\n{location}", parent=self
        ):
            return
        try:
            self.root.event_manager.remove_source(location)
        except Exception as exc:
            messagebox.showerror("Błąd", str(exc), parent=self)
            return
        self.refresh()
        self.root._update_events_toolbar()

    def _reload(self) -> None:
        """Reload all sources, re-annotate, move misplaced files."""
        self.root._events_apply(move_files=True, trigger_scan=False)
        self.refresh()

    # ------------------------------------------------------------------
    def _on_close(self) -> None:
        EventsWindow._instance = None
        self.destroy()
