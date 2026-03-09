"""
bid/ui/preview.py
Widget podglądu zdjęcia — PrevWindow.
"""
from __future__ import annotations

import logging
import os

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

    def change_img(self, img_path: str) -> None:
        """Ładuje i wyświetla nowe zdjęcie.

        Przeznaczone do wywołania z wątku pomocniczego.

        Args:
            img_path: Ścieżka do pliku obrazu.
        """
        self.img_path = img_path
        if not os.path.isfile(img_path):
            logger.error(f"Plik nie istnieje: {img_path}")
            return
        try:
            with Image.open(img_path) as img:
                img = image_resize(img, self.size, Image.NEAREST, reducing_gap=1.5)
                # TODO: UX/UI: Zastosować płynne przejście/animację (np. alfa blend w canvasie) przy zmianie zdjęcia, aby uniknąć błyskania.
                self.tk_img = ImageTk.PhotoImage(img)
            self.photo_canvas.itemconfigure(self.img_canvas, image=self.tk_img)
        except Exception as exc:
            logger.error(f"Błąd wczytywania podglądu '{img_path}': {exc}")
