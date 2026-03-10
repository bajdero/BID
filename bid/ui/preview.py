"""
bid/ui/preview.py
Widget podglądu zdjęcia — PrevWindow.
"""
from __future__ import annotations

import logging
import os
import queue

import _tkinter
import tkinter as tk

from PIL import Image, ImageTk

from bid.image_processing import image_resize

logger = logging.getLogger("Yapa_CM")


class PrevWindow(tk.Frame):
    """Panel podglądu pojedynczego zdjęcia.

    Wyświetla miniaturę wybranego pliku na canvasie tkinter.
    """

    def __init__(self, root: tk.Tk, size: int = 300) -> None:
        """
        Args:
            root: Okno nadrzędne (MainApp).
            size: Rozmiar boku (kwadrat) podglądu w pikselach.
        """
        super().__init__(root)
        self.root = root
        self.size = size
        self.img_path: str | None = None

        # Domyślny placeholder
        _placeholder_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "src", "default_prev.png"
        )
        _placeholder_path = os.path.normpath(_placeholder_path)
        with Image.open(_placeholder_path) as img:
            self.tk_img = ImageTk.PhotoImage(img)

        # TODO: UX/UI: Dodać zaokrąglenie rogów podglądu, a także zmienić tło canvasu ("gray") na zgodne z nowoczesnym motywem aplikacji (oraz usunąć ramkę obramowania `highlightthickness=0`).
        self.photo_canvas = tk.Canvas(
            self, width=self.size, height=self.size, bg="gray"
        )
        self.photo_canvas.pack()
        self.img_canvas = self.photo_canvas.create_image(
            self.size / 2, self.size / 2, image=self.tk_img
        )
        # Queue used for thread-safe image handoff.
        # Worker threads only ever touch this queue (no Tcl calls).
        # The main thread drains it via _poll_img_queue().
        self._img_queue: queue.Queue = queue.Queue(maxsize=1)
        self._poll_img_queue()  # start polling loop on main thread

    def change_img(self, img_path: str) -> None:
        """Wczytuje zdjęcie z dysku. Bezpieczne do wywołania z DOWOLNEGO wątku.

        Wykonuje tylko I/O + PIL resize, po czym odkrywa wynik w kolejce
        Pythonowej (bez żadnych wywołań Tcl/Tkinter). Główny wątek odbiera
        wynik przez _poll_img_queue() i aktualizuje widget.

        Args:
            img_path: Ścieżka do pliku obrazu.
        """
        self.img_path = img_path
        if not os.path.isfile(img_path):
            logger.error(f"Plik nie istnieje: {img_path}")
            return
        try:
            with Image.open(img_path) as img:
                # TODO: UX/UI: Zastosować płynne przejście/animację przy zmianie zdjęcia.
                resized = image_resize(img, self.size, Image.NEAREST, reducing_gap=1.5)
            # Pure-Python queue put — no Tcl involved at all.
            try:
                self._img_queue.put_nowait(resized)
            except queue.Full:
                pass  # main thread hasn’t consumed the previous frame yet; discard
        except Exception as exc:
            logger.error(f"Błąd wczytywania podglądu '{img_path}': {exc}")

    def _poll_img_queue(self) -> None:
        """Sprawdza kolejkę zdjęć i aktualizuje canvas — TYLKO główny wątek.

        Pierwszy raz wywołana z __init__ (główny wątek), każde kolejne wywołanie
        pochodzi z self.after() — zawsze na głównym wątku. Nigdy nie jest
        wywoływana bezpośrednio z wątku roboczego.
        """
        try:
            pil_img = self._img_queue.get_nowait()
            self._apply_image(pil_img)
        except queue.Empty:
            pass
        try:
            self.after(50, self._poll_img_queue)
        except Exception:
            pass  # widget został zniszczony — kończymy pętlę

    def _apply_image(self, pil_img: Image.Image) -> None:
        """Tworzy PhotoImage i aktualizuje canvas — MUSI być na głównym wątku."""
        try:
            self.tk_img = ImageTk.PhotoImage(pil_img)
            self.photo_canvas.itemconfigure(self.img_canvas, image=self.tk_img)
        except Exception as exc:
            logger.error(f"Błąd aktualizacji podglądu: {exc}")
