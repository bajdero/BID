"""
bid/ui/toast.py
Toast — powiadomienia wyskakujące w prawym dolnym rogu okna.

Cechy:
  - Czyste Tkinter, brak zależności zewnętrznych.
  - Maksymalnie jedno powiadomienie widoczne naraz; pozostałe w kolejce.
  - Rate-limiting: ten sam typ wiadomości ignorowany przez 30 s.
  - Auto-zamknięcie po 5 sekundach (konfigurowalny).
"""
from __future__ import annotations

import logging
import time
import tkinter as tk
from collections import deque

logger = logging.getLogger("BID")

_DISMISS_MS = 5000       # czas widoczności w ms
_RATE_LIMIT_S = 30.0     # minimalny odstęp (s) między tymi samymi komunikatami
_BG_WARNING = "#fff3cd"
_BG_ERROR   = "#f8d7da"
_BG_INFO    = "#d1ecf1"


class _ToastManager:
    """Singleton zarządzający kolejką powiadomień toastowych.

    Nie tworzy własnego okna — operuje przez after() na istniejącym tk.Tk.
    """

    def __init__(self) -> None:
        self._queue: deque[tuple[str, str]] = deque()    # (message, level)
        self._last_shown: dict[str, float] = {}          # message → timestamp
        self._current_toast: tk.Toplevel | None = None
        self._root: tk.Tk | None = None

    def init(self, root: tk.Tk) -> None:
        """Powiąż managera z głównym oknem aplikacji.

        Args:
            root: Jedyna instancja tk.Tk.
        """
        self._root = root

    def show(self, message: str, level: str = "warning") -> None:
        """Dodaj komunikat do kolejki toastów (bezpieczne z main thread).

        Args:
            message: Treść powiadomienia.
            level:   ``"info"``, ``"warning"`` lub ``"error"``.
        """
        if self._root is None:
            logger.debug(f"[Toast] Root niezainicjalizowany, pomijam: {message}")
            return

        # Rate limiting
        now = time.monotonic()
        last = self._last_shown.get(message, 0.0)
        if now - last < _RATE_LIMIT_S:
            logger.debug(f"[Toast] Throttled (rate-limit): {message}")
            return

        self._last_shown[message] = now
        self._queue.append((message, level))
        self._try_show_next()

    def _try_show_next(self) -> None:
        """Wyświetl następny toast jeśli żaden nie jest aktualnie widoczny."""
        if self._current_toast is not None or not self._queue:
            return
        message, level = self._queue.popleft()
        self._show_toast(message, level)

    def _show_toast(self, message: str, level: str) -> None:
        """Buduje i wyświetla okno toastu."""
        if self._root is None:
            return

        bg = {"warning": _BG_WARNING, "error": _BG_ERROR}.get(level, _BG_INFO)
        icon = {"warning": "⚠", "error": "✖", "info": "ℹ"}.get(level, "ℹ")

        toast = tk.Toplevel(self._root)
        toast.overrideredirect(True)    # brak ramki/tytułu
        toast.attributes("-topmost", True)
        toast.configure(bg=bg, bd=1, relief=tk.SOLID)
        self._current_toast = toast

        # Zawartość
        frame = tk.Frame(toast, bg=bg, padx=12, pady=8)
        frame.pack()

        tk.Label(
            frame, text=f"{icon}  {message}",
            bg=bg, font=("Segoe UI", 9), wraplength=340, justify=tk.LEFT
        ).pack(side=tk.LEFT)

        btn = tk.Button(
            frame, text="✕", bg=bg, relief=tk.FLAT, cursor="hand2",
            font=("Segoe UI", 8), command=lambda: self._dismiss(toast)
        )
        btn.pack(side=tk.RIGHT, padx=(10, 0))

        # Pozycja: prawy dolny róg okna nadrzędnego
        toast.update_idletasks()
        tw, th = toast.winfo_reqwidth(), toast.winfo_reqheight()
        rw = self._root.winfo_x() + self._root.winfo_width()
        rh = self._root.winfo_y() + self._root.winfo_height()
        x = rw - tw - 20
        y = rh - th - 40
        toast.geometry(f"{tw}x{th}+{x}+{y}")

        # Auto-dismiss
        self._root.after(_DISMISS_MS, lambda: self._dismiss(toast))

    def _dismiss(self, toast: tk.Toplevel) -> None:
        """Zamyka toast i pokazuje następny z kolejki."""
        if self._current_toast is toast:
            self._current_toast = None
        try:
            toast.destroy()
        except tk.TclError:
            pass
        # Pokaż kolejny po krótkim odstępie
        if self._root is not None:
            self._root.after(200, self._try_show_next)


# Singleton dostępny globalnie
toast_manager = _ToastManager()


def init_toasts(root: tk.Tk) -> None:
    """Inicjalizuj system toastów dla danego okna głównego.

    Wywołaj raz, po utworzeniu MainApp.

    Args:
        root: Instancja MainApp (tk.Tk).
    """
    toast_manager.init(root)


def show_toast(message: str, level: str = "warning") -> None:
    """Wyświetl toast z komunikatem.

    Args:
        message: Treść powiadomienia.
        level:   ``"info"``, ``"warning"`` lub ``"error"``.
    """
    toast_manager.show(message, level)
