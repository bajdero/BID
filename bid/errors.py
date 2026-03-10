"""bid/errors.py — Hierarchia wyjątków YAPA/BID."""

class YapaError(Exception):
    """Bazowy wyjątek dla wszystkich błędów YAPA."""
    pass

class ConfigError(YapaError):
    """Błąd ładowania/walidacji konfiguracji."""
    pass

class ImageProcessingError(YapaError):
    """Błąd przetwarzania obrazu."""
    pass

class SourceManagerError(YapaError):
    """Błąd zarządzania słownikiem źródeł."""
    pass

class ProjectError(YapaError):
    """Błąd operacji na projekcie."""
    pass
