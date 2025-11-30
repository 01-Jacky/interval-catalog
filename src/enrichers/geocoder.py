"""Resort geocoding enricher."""

import json
import logging
from pathlib import Path
from time import sleep
from typing import Dict, List, Optional, Tuple

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError


logger = logging.getLogger(__name__)


class ResortGeocoder:
    """Geocodes resort locations to latitude/longitude coordinates."""

    def __init__(
        self,
        provider: str = "nominatim",
        user_agent: str = "interval-resort-viewer",
        rate_limit_delay: float = 1.0,
        cache_file: Optional[Path] = None
    ) -> None:
        """
        Initialize the geocoder.

        Args:
            provider: Geocoding provider ("nominatim", "google", etc.)
            user_agent: User agent for API requests
            rate_limit_delay: Seconds to wait between requests
            cache_file: Path to cache file for geocoding results
        """
        self.provider = provider
        self.rate_limit_delay = rate_limit_delay
        self.cache_file = cache_file
        self.cache = self._load_cache()

        if provider == "nominatim":
            self.geolocator = Nominatim(user_agent=user_agent)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _load_cache(self) -> Dict[str, Tuple[Optional[float], Optional[float]]]:
        """Load geocoding cache from file."""
        if self.cache_file and self.cache_file.exists():
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
                # Convert lists back to tuples
                return {k: tuple(v) if v else (None, None) for k, v in cache_data.items()}
        return {}

    def _save_cache(self) -> None:
        """Save geocoding cache to file."""
        if self.cache_file:
            with open(self.cache_file, 'w') as f:
                # Convert tuples to lists for JSON serialization
                cache_data = {k: list(v) if v[0] is not None else None for k, v in self.cache.items()}
                json.dump(cache_data, f, indent=2)

    def _normalize_location(self, location: str) -> str:
        """
        Normalize location string for geocoding.

        Removes backticks (used for Hawaiian ʻokina) which most geocoding
        services don't recognize.

        Args:
            location: Original location string

        Returns:
            Normalized location string
        """
        # Remove backticks (Hawaiian ʻokina representation)
        normalized = location.replace("`", "")
        if normalized != location:
            logger.debug(f"Normalized location: '{location}' -> '{normalized}'")
        return normalized

    def geocode_location(
        self,
        location: str,
        max_retries: int = 3
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Geocode a location string to coordinates.

        Args:
            location: Location string to geocode
            max_retries: Maximum retry attempts on timeout

        Returns:
            Tuple of (latitude, longitude) or (None, None) if failed
        """
        # Normalize location string
        normalized_location = self._normalize_location(location)

        # Check cache first
        if normalized_location in self.cache:
            logger.debug(f"Cache hit for: {normalized_location}")
            return self.cache[normalized_location]

        # Attempt geocoding with retries
        for attempt in range(max_retries):
            try:
                result = self.geolocator.geocode(normalized_location)
                if result:
                    coords = (result.latitude, result.longitude)
                    self.cache[normalized_location] = coords
                    logger.info(f"Geocoded: {normalized_location} -> {coords}")
                    sleep(self.rate_limit_delay)
                    return coords
                else:
                    logger.warning(f"No results for: {normalized_location}")
                    self.cache[normalized_location] = (None, None)
                    return (None, None)

            except GeocoderTimedOut:
                logger.warning(f"Timeout geocoding {normalized_location}, attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    sleep(self.rate_limit_delay * 2)
                else:
                    logger.error(f"Failed to geocode after {max_retries} attempts: {normalized_location}")
                    self.cache[normalized_location] = (None, None)
                    return (None, None)

            except GeocoderServiceError as e:
                logger.error(f"Service error geocoding {normalized_location}: {e}")
                self.cache[normalized_location] = (None, None)
                return (None, None)
            except Exception as e:
                logger.error(f"Unexpected error geocoding {normalized_location}: {e}")
                self.cache[normalized_location] = (None, None)
                return (None, None)

        return (None, None)

    def enrich_resorts(
        self,
        resorts: List[Dict],
        save_progress_every: int = 100
    ) -> Tuple[List[Dict], Dict]:
        """
        Enrich resorts list with geocoded coordinates.

        Args:
            resorts: List of resort dictionaries
            save_progress_every: Save cache every N resorts

        Returns:
            Tuple of (enriched resorts, statistics)
        """
        stats = {
            "total": len(resorts),
            "geocoded": 0,
            "failed": 0,
            "cached": 0,
            "skipped": 0,
            "failed_resorts": []  # Track which resorts failed
        }

        for idx, resort in enumerate(resorts, 1):
            location = resort.get("location", "")

            # Skip if already geocoded
            if "latitude" in resort and resort["latitude"] is not None:
                stats["skipped"] += 1
                logger.debug(f"Skipping already geocoded: {resort['name']}")
                continue

            # Check if already in cache (use normalized location)
            normalized_location = self._normalize_location(location)
            was_cached = normalized_location in self.cache

            lat, lon = self.geocode_location(location)

            resort["latitude"] = lat
            resort["longitude"] = lon

            if was_cached:
                stats["cached"] += 1

            if lat is not None and lon is not None:
                stats["geocoded"] += 1
            else:
                stats["failed"] += 1
                stats["failed_resorts"].append({
                    "code": resort.get("code"),
                    "name": resort.get("name"),
                    "location": location
                })

            # Save progress periodically
            if idx % save_progress_every == 0:
                self._save_cache()
                logger.info(f"Progress: {idx}/{stats['total']} resorts processed")

        # Final cache save
        self._save_cache()

        return resorts, stats

    def run(
        self,
        input_file: Path,
        output_file: Path,
        overrides_file: Optional[Path] = None
    ) -> Tuple[List[Dict], Dict]:
        """
        Run the geocoding enrichment.

        Args:
            input_file: Path to input JSON file (resorts.json)
            output_file: Path to output JSON file (resorts_geocoded.json)
            overrides_file: Optional path to manual coordinate overrides

        Returns:
            Tuple of (enriched resorts, statistics)
        """
        logger.info(f"Loading resorts from: {input_file}")
        with open(input_file, 'r') as f:
            resorts = json.load(f)

        # Load manual overrides if provided
        overrides = {}
        if overrides_file and overrides_file.exists():
            with open(overrides_file, 'r') as f:
                overrides = json.load(f)
            logger.info(f"Loaded {len(overrides)} manual overrides")

        # Apply manual overrides first
        for resort in resorts:
            code = resort.get("code")
            if code in overrides:
                resort["latitude"] = overrides[code]["latitude"]
                resort["longitude"] = overrides[code]["longitude"]
                logger.info(f"Applied manual override for {code}: {resort['name']}")

        logger.info(f"Starting geocoding for {len(resorts)} resorts...")
        enriched_resorts, stats = self.enrich_resorts(resorts)

        logger.info(f"Writing enriched data to: {output_file}")
        with open(output_file, 'w') as f:
            json.dump(enriched_resorts, f, indent=2)

        # Save failed resorts to a separate file for easy review
        if stats["failed_resorts"]:
            failed_file = output_file.parent / "geocode_failed.json"
            logger.info(f"Writing {len(stats['failed_resorts'])} failed resorts to: {failed_file}")
            with open(failed_file, 'w') as f:
                json.dump(stats["failed_resorts"], f, indent=2)

        self._log_statistics(stats, output_file.parent / "geocode_failed.json" if stats["failed_resorts"] else None)

        return enriched_resorts, stats

    def _log_statistics(self, stats: Dict, failed_file: Optional[Path] = None) -> None:
        """Log geocoding statistics."""
        logger.info("\n" + "=" * 60)
        logger.info("GEOCODING STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Total resorts:         {stats['total']}")
        logger.info(f"Successfully geocoded: {stats['geocoded']}")
        logger.info(f"Failed:                {stats['failed']}")
        logger.info(f"From cache:            {stats['cached']}")
        logger.info(f"Already had coords:    {stats['skipped']}")
        if stats['total'] > 0:
            success_count = stats['geocoded'] + stats['skipped']
            logger.info(f"Success rate:          {success_count/stats['total']*100:.1f}%")
        if failed_file:
            logger.info(f"\nFailed resorts saved to: {failed_file}")
        logger.info("=" * 60)
