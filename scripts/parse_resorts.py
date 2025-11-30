#!/usr/bin/env python3
"""
Interval International Resort Directory Parser - Entry Point Script

This script serves as the main entry point for parsing resort data from
Interval International HTML files. It uses the configuration and logging
setup to run the parser in a production-ready manner.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_settings
from src.utils import setup_logging
from src.parsers import ResortParser


logger = logging.getLogger(__name__)


def main() -> int:
    """
    Main entry point for the resort parsing script.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Load settings
    settings = get_settings()

    # Setup logging
    setup_logging(
        log_file=settings.get_log_path(),
        log_level=settings.LOG_LEVEL,
        log_format=settings.LOG_FORMAT
    )

    logger.info("=" * 60)
    logger.info("Interval International Resort Directory Parser")
    logger.info("=" * 60)

    try:
        # Get input and output paths
        input_path = settings.get_input_path()
        output_path = settings.get_output_path()

        logger.info(f"Input file: {input_path}")
        logger.info(f"Output file: {output_path}")

        # Create parser and run
        parser = ResortParser(str(input_path))
        resorts, stats = parser.run(str(output_path))

        logger.info("\nParsing complete! Check the output folder for results.")
        logger.info(f"Total records: {len(resorts)}")

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.exception(f"An error occurred during parsing: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
