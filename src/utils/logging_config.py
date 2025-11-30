"""Logging configuration utilities."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_file: Optional[Path] = None,
    log_level: str = "INFO",
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
) -> None:
    """
    Configure logging for the application.

    Sets up both console and file handlers with the specified configuration.

    Args:
        log_file: Path to the log file. If None, only console logging is enabled.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format string for log messages
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove any existing handlers
    root_logger.handlers.clear()

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if log file is specified)
    if log_file:
        # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        root_logger.info(f"Logging to file: {log_file}")

    root_logger.info(f"Logging initialized at {log_level} level")
