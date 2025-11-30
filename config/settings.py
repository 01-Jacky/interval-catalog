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
