#!/usr/bin/env python3
"""
Interval International Resort Geocoding Enrichment Script

This script enriches the parsed resort data with geocoded coordinates
(latitude/longitude) based on the location field.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_settings
from src.utils import setup_logging
from src.enrichers import ResortGeocoder


logger = logging.getLogger(__name__)


def main() -> int:
    """
    Main entry point for the geocoding script.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Load settings
    settings = get_settings()

    # Setup logging
    setup_logging(
        log_file=settings.get_geocode_log_path(),
        log_level=settings.LOG_LEVEL,
        log_format=settings.LOG_FORMAT
    )

    logger.info("=" * 60)
    logger.info("Resort Geocoding Enrichment")
    logger.info("=" * 60)

    try:
        input_file = settings.get_geocode_input_path()
        output_file = settings.get_geocode_output_path()
        cache_file = settings.get_geocode_cache_path()
        overrides_file = settings.get_geocode_overrides_path()

        logger.info(f"Input file:     {input_file}")
        logger.info(f"Output file:    {output_file}")
        logger.info(f"Cache file:     {cache_file}")
        logger.info(f"Overrides file: {overrides_file}")

        # Create geocoder
        geocoder = ResortGeocoder(
            provider=settings.GEOCODE_PROVIDER,
            user_agent=settings.GEOCODE_USER_AGENT,
            rate_limit_delay=settings.GEOCODE_RATE_LIMIT,
            cache_file=cache_file
        )

        # Run geocoding
        resorts, stats = geocoder.run(
            input_file=input_file,
            output_file=output_file,
            overrides_file=overrides_file if overrides_file.exists() else None
        )

        logger.info("\nGeocoding complete! Check the output folder for results.")
        logger.info(f"Total records: {len(resorts)}")

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.exception(f"An error occurred during geocoding: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
