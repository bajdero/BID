"""
bid/logging_config.py
Centralna konfiguracja loggera BID.
Testy mogą importować setup_logger() aby skonfigurować logger bez uruchamiania main.py.
"""
from __future__ import annotations

import datetime
import logging
from pathlib import Path

LOGGER_NAME = "BID"

def setup_logger(
    level: int = logging.INFO,
    log_dir: Path | None = None,
    console: bool = True,
    file: bool = True,
) -> logging.Logger:
    """Konfiguruje i zwraca loggera BID.
    
    Args:
        level: Poziom logowania.
        log_dir: Katalog na pliki logów. None = logs/ obok main.py.
        console: Czy dodać handler konsoli.
        file: Czy dodać handler pliku.
    
    Returns:
        Skonfigurowany logger.
    """
    logger = logging.getLogger(LOGGER_NAME)
    
    # Nie konfiguruj ponownie jeśli handlery już istnieją
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    
    if console:
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(fmt)
        logger.addHandler(ch)
    
    if file:
        if log_dir is None:
            log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        log_name = datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S") + ".log"
        fh = logging.FileHandler(log_dir / log_name, encoding="utf-8")
        fh.setLevel(level)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    
    return logger


def get_logger() -> logging.Logger:
    """Zwraca istniejącą instancję loggera (bez konfiguracji)."""
    return logging.getLogger(LOGGER_NAME)
