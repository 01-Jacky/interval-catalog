"""Application settings and configuration."""

import os
from pathlib import Path
from typing import Optional


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self) -> None:
        """Initialize settings from environment variables."""
        # Base paths
        self.BASE_DIR = Path(__file__).parent.parent
        self.DATA_DIR = Path(os.getenv("DATA_DIR", self.BASE_DIR / "data"))
        self.OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", self.BASE_DIR / "output"))
        self.LOG_DIR = Path(os.getenv("LOG_DIR", self.BASE_DIR / "logs"))

        # Input/Output files
        self.INPUT_HTML_PATH = os.getenv(
            "INPUT_HTML_PATH",
            "data/interval_11_28/interval_directory_11_28_2025.html"
        )
        self.OUTPUT_JSON_PATH = os.getenv("OUTPUT_JSON_PATH", "output/resorts.json")

        # Logging configuration
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FILE = os.getenv("LOG_FILE", "logs/parser.log")
        self.LOG_FORMAT = os.getenv(
            "LOG_FORMAT",
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Geocoding configuration
        self.GEOCODE_PROVIDER = os.getenv("GEOCODE_PROVIDER", "nominatim")
        self.GEOCODE_USER_AGENT = os.getenv("GEOCODE_USER_AGENT", "interval-resort-viewer")
        self.GEOCODE_RATE_LIMIT = float(os.getenv("GEOCODE_RATE_LIMIT", "1.0"))
        self.GEOCODE_INPUT_PATH = os.getenv("GEOCODE_INPUT_PATH", "output/resorts.json")
        self.GEOCODE_OUTPUT_PATH = os.getenv("GEOCODE_OUTPUT_PATH", "output/resorts_geocoded.json")
        self.GEOCODE_CACHE_PATH = os.getenv("GEOCODE_CACHE_PATH", "output/geocode_cache.json")
        self.GEOCODE_OVERRIDES_PATH = os.getenv("GEOCODE_OVERRIDES_PATH", "data/geocode_overrides.json")
        self.GEOCODE_LOG_FILE = os.getenv("GEOCODE_LOG_FILE", "logs/geocoder.log")

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)

    def get_input_path(self) -> Path:
        """Get the full path to the input HTML file."""
        return self.BASE_DIR / self.INPUT_HTML_PATH

    def get_output_path(self) -> Path:
        """Get the full path to the output JSON file."""
        return self.BASE_DIR / self.OUTPUT_JSON_PATH

    def get_log_path(self) -> Path:
        """Get the full path to the log file."""
        return self.BASE_DIR / self.LOG_FILE

    def get_geocode_input_path(self) -> Path:
        """Get the full path to the geocoding input JSON file."""
        return self.BASE_DIR / self.GEOCODE_INPUT_PATH

    def get_geocode_output_path(self) -> Path:
        """Get the full path to the geocoding output JSON file."""
        return self.BASE_DIR / self.GEOCODE_OUTPUT_PATH

    def get_geocode_cache_path(self) -> Path:
        """Get the full path to the geocoding cache file."""
        return self.BASE_DIR / self.GEOCODE_CACHE_PATH

    def get_geocode_overrides_path(self) -> Path:
        """Get the full path to the geocoding overrides file."""
        return self.BASE_DIR / self.GEOCODE_OVERRIDES_PATH

    def get_geocode_log_path(self) -> Path:
        """Get the full path to the geocoding log file."""
        return self.BASE_DIR / self.GEOCODE_LOG_FILE


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the global settings instance (singleton pattern).

    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
