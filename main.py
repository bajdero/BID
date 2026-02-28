"""
main.py — punkt wejścia aplikacji BID (Batch Image Delivery).

Uruchomienie:
    python main.py
    python main.py --settings /inna/sciezka/settings.json
    python main.py --export-options /inna/sciezka/export_option.json
"""
from __future__ import annotations

import argparse
import datetime
import logging
import os
import sys
from pathlib import Path


def _setup_logging(level: int = logging.INFO) -> None:
    """Konfiguruje loggera — wyjście na konsolę i do pliku w katalogu logs/.

    Args:
        level: Poziom logowania (domyślnie INFO).
    """
    logger = logging.getLogger("Yapa_CM")
    logger.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File handler — katalog logs/ obok main.py
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_name = datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S") + ".log"
    fh = logging.FileHandler(logs_dir / log_name, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(fmt)
    logger.addHandler(fh)


def _parse_args() -> argparse.Namespace:
    """Parsuje argumenty wiersza poleceń.

    Returns:
        Namespace z polami: settings, export_options, debug.
    """
    parser = argparse.ArgumentParser(
        description="BID — Batch Image Delivery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--settings",
        type=Path,
        default=None,
        metavar="PATH",
        help="Ścieżka do pliku settings.json (domyślnie: obok main.py)",
    )
    parser.add_argument(
        "--export-options",
        type=Path,
        default=None,
        metavar="PATH",
        help="Ścieżka do pliku export_option.json (domyślnie: obok main.py)",
    )
    parser.add_argument(
        "--project",
        type=Path,
        default=None,
        metavar="PATH",
        help="Ścieżka do katalogu projektu (domyślnie: ostatnio używany)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Włącz poziom logowania DEBUG",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    _setup_logging(logging.DEBUG if args.debug else logging.INFO)

    logger = logging.getLogger("Yapa_CM")
    logger.info("Uruchamianie BID")

    # Importy po skonfigurowaniu loggera
    from bid.project_manager import ProjectManager
    from bid.ui.setup_wizard import run_wizard_if_needed
    from bid.ui.project_selector import run_project_selector
    from bid.app import MainApp

    project_path: Path | None = args.project

    # Jeśli nie podano projektu w argumentach, otwórz selector
    if project_path is None:
        success, create_new, selected_path = run_project_selector()
        
        if not success:
            logger.info("Nie wybrano projektu. Zamykanie.")
            sys.exit(0)
            
        if create_new:
            success_wizard, project_path = run_wizard_if_needed()
            if not success_wizard or not project_path:
                logger.info("Anulowano tworzenie projektu. Zamykanie.")
                sys.exit(0)
        else:
            project_path = selected_path

    # Podwójne sprawdzenie czy projekt istnieje (np. jeśli podany przez --project)
    if project_path is None or not project_path.exists():
        logger.error(f"Projekt nie istnieje: {project_path}")
        success_wizard, project_path = run_wizard_if_needed()
        if not success_wizard or not project_path:
            logger.info("Anulowano konfigurację. Zamykanie.")
            sys.exit(0)

    app = MainApp(project_path=project_path, debug=args.debug)
    app.mainloop()
    logger.info("Zamknięto aplikację")
