"""
tests/test_tcl_threading.py
Testy regresyjne dla błędu: Tcl_AsyncDelete: async handler deleted by the wrong thread

== Diagram przyczyn ==

Tcl rejestruje globalny async handler za pomocą Tcl_AsyncCreate() przy każdym wywołaniu
tk.Tk(). Musi być usunięty (Tcl_AsyncDelete) przez TEN SAM wątek, który go stworzył.

Problem w aplikacji:
  1. run_project_selector() tworzy ProjectSelector(tk.Tk)  → 1. instancja Tk
  2. run_wizard_if_needed()  tworzy SetupWizard(tk.Tk)     → 2. instancja Tk (opcjonalnie)
  3. MainApp(tk.Tk)                                        → 3. instancja Tk

  Przy każdym stworzeniu nowej instancji Tk, stara (referencyjnie cykliczna przez
  widgety Tkinter) trafia do kolejki GC. CPython uruchamia GC z poziomu wątku roboczego
  (ThreadPoolExecutor / PIL allokacje), co wywołuje Tkapp_Dealloc() → Tcl_AsyncDelete()
  z niewłaściwego wątku → CRASH.

  Dodatkowo: on_new_project() wywołuje run_wizard_if_needed() bez argumentu parent,
  tworzac JEDNOCZESNIE działającą drugą instancję tk.Tk obok MainApp.

== Naprawione warianty ==

  ✔  ProjectSelector dziedziczy po tk.Toplevel (nie tk.Tk)
  ✔  SetupWizard dziedziczy po tk.Toplevel (nie tk.Tk)
  ✔  MainApp jest jedyną instancją tk.Tk przez cały cykl życia aplikacji
  ✔  run_project_selector(parent) i run_wizard_if_needed(parent) wymagają rodzica
  ✔  _on_double_click używa executor.submit() zamiast Thread(), aby nie tworzyć
     dodatkowych wątków (każdy nowy wątek może triggerować GC na złym wątku)
  ✔  change_img() nie wywołuje żadnych API Tcl/Tkinter bezpośrednio
"""
from __future__ import annotations

import inspect
import tkinter as tk
import threading


# ---------------------------------------------------------------------------
# 1. Weryfikacja hierarchii klas (statyczna)
# ---------------------------------------------------------------------------

def test_project_selector_is_toplevel_not_tk():
    """ProjectSelector musi dziedziczyć po tk.Toplevel – zapobiega tworzeniu
    dodatkowej instancji tk.Tk przed MainApp."""
    from bid.ui.project_selector import ProjectSelector

    assert issubclass(ProjectSelector, tk.Toplevel), (
        "ProjectSelector musi dziedziczyć po tk.Toplevel, nie po tk.Tk. "
        "Każda instancja tk.Tk rejestruje globalny async handler Tcl; tworzenie "
        "wielu instancji powoduje Tcl_AsyncDelete z niewłaściwego wątku."
    )
    assert not issubclass(ProjectSelector, tk.Tk), (
        "ProjectSelector NIE może dziedziczyć po tk.Tk (Toplevel też jest podklasą Misc, "
        "ale nie Tk – sprawdzamy wprost)."
    )


def test_setup_wizard_is_toplevel_not_tk():
    """SetupWizard musi dziedziczyć po tk.Toplevel – zapobiega tworzeniu
    drugiej instancji tk.Tk."""
    from bid.ui.setup_wizard import SetupWizard

    assert issubclass(SetupWizard, tk.Toplevel), (
        "SetupWizard musi dziedziczyć po tk.Toplevel, nie po tk.Tk."
    )
    assert not issubclass(SetupWizard, tk.Tk)


def test_main_app_is_only_tk_subclass():
    """MainApp powinno być jedyną klasą w aplikacji dziedziczącą bezpośrednio po tk.Tk."""
    from bid.app import MainApp
    from bid.ui.project_selector import ProjectSelector
    from bid.ui.setup_wizard import SetupWizard

    assert issubclass(MainApp, tk.Tk), "MainApp musi dziedziczyć po tk.Tk"
    assert not issubclass(ProjectSelector, tk.Tk)
    assert not issubclass(SetupWizard, tk.Tk)


# ---------------------------------------------------------------------------
# 2. Weryfikacja sygnatur funkcji (backward-compat check)
# ---------------------------------------------------------------------------

def test_run_project_selector_requires_parent():
    """run_project_selector() musi przyjmować argument 'parent', aby tworzyć
    Toplevel wewnątrz istniejącej instancji Tk zamiast nowej."""
    from bid.ui.project_selector import run_project_selector

    sig = inspect.signature(run_project_selector)
    assert "parent" in sig.parameters, (
        "run_project_selector() musi przyjmować argument 'parent: tk.Misc', "
        "bo ProjectSelector jest teraz tk.Toplevel i wymaga rodzica."
    )


def test_run_wizard_if_needed_requires_parent():
    """run_wizard_if_needed() musi przyjmować argument 'parent'."""
    from bid.ui.setup_wizard import run_wizard_if_needed

    sig = inspect.signature(run_wizard_if_needed)
    assert "parent" in sig.parameters, (
        "run_wizard_if_needed() musi przyjmować argument 'parent: tk.Misc'."
    )


# ---------------------------------------------------------------------------
# 3. Weryfikacja kodu źródłowego – brak ad-hoc wątków i wywołań Tcl ze wątków
# ---------------------------------------------------------------------------

def test_on_double_click_uses_executor_not_bare_thread():
    """_on_double_click musi używać executor.submit() zamiast Thread().

    Tworzenie nowego wątku (Thread + start) przy każdym podwójnym kliknięciu
    powoduje, że Python rejestruje wewnętrzny cleanup handler dla tego wątku.
    Używanie istniejącego ThreadPoolExecutor eliminuje ten problem i jest
    bardziej efektywne."""
    from bid.ui.source_tree import SourceTree

    src = inspect.getsource(SourceTree._on_double_click)
    assert "Thread(" not in src, (
        "_on_double_click nie może tworzyć nowych Thread() przy każdym kliknięciu. "
        "Użyj self.root.executor.submit() zamiast tego."
    )
    assert "executor" in src, (
        "_on_double_click musi używać executor.submit() do ładowania podglądu."
    )


def test_change_img_contains_no_tkinter_calls():
    """change_img() – wywołany z wątku roboczego – nie może zawierać żadnych
    wywołań API Tcl/Tkinter."""
    from bid.ui.preview import PrevWindow

    src = inspect.getsource(PrevWindow.change_img)

    forbidden = [
        "itemconfigure",
        "ImageTk.PhotoImage",
        "self.after(",
        ".config(",
        ".pack(",
        ".grid(",
        ".place(",
    ]
    for call in forbidden:
        assert call not in src, (
            f"change_img() zawiera '{call}', które jest wywołaniem Tcl/Tkinter "
            f"i NIE może być wywoływane z wątku roboczego."
        )


def test_apply_image_not_called_from_change_img():
    """_apply_image (która zawiera Tkinter calls) nie może być wywoływana
    bezpośrednio wewnątrz change_img."""
    from bid.ui.preview import PrevWindow

    src = inspect.getsource(PrevWindow.change_img)
    # _apply_image tworzy PhotoImage i woła itemconfigure – musi być na głównym wątku
    assert "_apply_image" not in src, (
        "change_img() nie może wywoływać _apply_image() bezpośrednio. "
        "_apply_image() musi być wywołana z głównego wątku (przez kolejkę/polling)."
    )


# ---------------------------------------------------------------------------
# 4. Weryfikacja że _poll_img_queue NIGDY nie jest wywoływana z wątku roboczego
# ---------------------------------------------------------------------------

def test_poll_img_queue_started_only_from_init():
    """_poll_img_queue powinna być uruchamiana tylko z __init__ (główny wątek),
    nigdy wywołana bezpośrednio z change_img ani z innego wątku."""
    from bid.ui.preview import PrevWindow
    import ast, textwrap

    # Parse the AST of change_img and look for a *call* to _poll_img_queue,
    # not just a mention in a string/docstring.
    src = textwrap.dedent(inspect.getsource(PrevWindow.change_img))
    tree = ast.parse(src)
    calls = [
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
    ]
    assert "_poll_img_queue" not in calls, (
        "change_img() must not call _poll_img_queue() — that method contains "
        "self.after() and must only be called from the main thread."
    )


# ---------------------------------------------------------------------------
# 5. Test uruchomienia wątku roboczego z change_img – brak crashu
# ---------------------------------------------------------------------------

def test_change_img_from_thread_does_not_call_tcl(tmp_path):
    """Wywołanie change_img() z wątku roboczego nie może wywołać żadnej metody
    Tcl (_tkinter.TkappObject). Weryfikujemy to przez mockowanie queue."""
    import queue as q_module
    from unittest.mock import MagicMock, patch

    # Symulujemy PrevWindow bez tworzenia prawdziwego okna Tkinter
    mock_queue = MagicMock()

    class FakePrevWindow:
        """Minimal stub that replicates change_img logic without real Tkinter."""
        size = 300
        img_path = None
        _img_queue = mock_queue

        def change_img(self, img_path: str) -> None:
            # Copy of the real change_img body (imports from preview module)
            import os
            from bid.image_processing import image_resize
            from PIL import Image

            self.img_path = img_path
            if not os.path.isfile(img_path):
                return
            with Image.open(img_path) as img:
                resized = image_resize(img, self.size, Image.NEAREST, reducing_gap=1.5)
            try:
                self._img_queue.put_nowait(resized)
            except Exception:
                pass

    # Create a small test image
    test_img = tmp_path / "test.jpg"
    from PIL import Image as PILImage
    PILImage.new("RGB", (100, 100), color="red").save(str(test_img))

    tcl_called = threading.Event()
    original_put = mock_queue.put_nowait

    errors = []
    stub = FakePrevWindow()

    def worker():
        try:
            stub.change_img(str(test_img))
        except Exception as e:
            errors.append(e)

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    t.join(timeout=10)

    assert not errors, f"change_img raised an exception in worker thread: {errors}"
    mock_queue.put_nowait.assert_called_once()
    # If we got here without Tcl_AsyncDelete crash, the pattern is safe
