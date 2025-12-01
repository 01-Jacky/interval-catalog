"""Resort geocoding enricher."""

import json
import logging
import ssl
from pathlib import Path
from time import sleep
from typing import Dict, List, Optional, Tuple

import certifi
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
            # Create SSL context to avoid certificate verification issues
            ctx = ssl.create_default_context(cafile=certifi.where())
            # Use longer timeout (10s) to handle slow geocoding service responses
            self.geolocator = Nominatim(user_agent=user_agent, ssl_context=ctx, timeout=10)
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
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

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

    def _preprocess_location(self, location: str) -> str:
        """
        Preprocess location string to fix common issues.

        Args:
            location: Original location string

        Returns:
            Preprocessed location string
        """
        processed = location

        # Fix common typos in country names
        typo_fixes = {
            ", lndia": ", India",  # lowercase L instead of uppercase I
            ", Lndia": ", India",
        }
        for typo, fix in typo_fixes.items():
            if processed.endswith(typo):
                processed = processed.replace(typo, fix)
                logger.debug(f"Fixed typo: '{location}' -> '{processed}'")
                return processed

        return processed

    def _get_location_variations(self, location: str) -> List[str]:
        """
        Get multiple variations of a location string to try for geocoding.

        Returns variations in order from most specific to least specific.
        Each variation uses a different strategy that has proven successful.

        Args:
            location: Original location string

        Returns:
            List of location string variations to try
        """
        import re
        variations = []
        parts = [p.strip() for p in location.split(",")]

        # Variation 1: Remove parenthetical content
        # "Intervale (North Conway), NH" -> "Intervale, NH"
        if "(" in location and ")" in location:
            no_parens = re.sub(r'\s*\([^)]*\)', '', location)
            if no_parens != location:
                variations.append(no_parens)
                logger.debug(f"Variation (remove parens): '{no_parens}'")

            # Also try using what's inside the parentheses instead
            # "Intervale (North Conway), NH" -> "North Conway, NH"
            match = re.search(r'\(([^)]+)\)', parts[0])
            if match and len(parts) > 1:
                inner_content = match.group(1).strip()
                alternative = ", ".join([inner_content] + parts[1:])
                variations.append(alternative)
                logger.debug(f"Variation (use parens content): '{alternative}'")

        # Variation 2: Remove common descriptive words from first component
        # "Ialyssos Beach" -> "Ialyssos"
        first_part = parts[0]
        descriptors_to_remove = [" Beach", " Bay", " Harbor", " Harbour"]
        for descriptor in descriptors_to_remove:
            if first_part.endswith(descriptor):
                simplified_first = first_part[:-len(descriptor)]
                simplified_location = ", ".join([simplified_first] + parts[1:])
                variations.append(simplified_location)
                logger.debug(f"Variation (remove '{descriptor}'): '{simplified_location}'")
                break

        # Variation 3: For 3+ components, try first + last (City, Country)
        # "Puerto del Carmen, Lanzarote, Canary Islands, Spain" -> "Puerto del Carmen, Spain"
        if len(parts) >= 3:
            # Special case: if last component is "Dutch Caribbean", remove it first
            if parts[-1] == "Dutch Caribbean":
                simplified = ", ".join(parts[:-1])
                variations.append(simplified)
                logger.debug(f"Variation (remove Dutch Caribbean): '{simplified}'")
            else:
                simplified = f"{parts[0]}, {parts[-1]}"
                variations.append(simplified)
                logger.debug(f"Variation (first + last): '{simplified}'")

        # Variation 4: Just the first component (city/town name)
        # Only use this as a last resort if we have NO country/state info at all
        # This is risky as it can match the wrong location (e.g., San Pedro, CA vs Belize)
        # Skip this variation to avoid ambiguous results
        # if len(parts) > 1:
        #     variations.append(parts[0])
        #     logger.debug(f"Variation (first only): '{parts[0]}'")

        return variations

    def geocode_location(
        self,
        location: str,
        max_retries: int = 2
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Geocode a location string to coordinates.

        Uses a smart fallback strategy:
        1. Try the original location (with retry on actual timeout)
        2. If no results, try multiple variations (remove Beach, parentheticals, simplify, etc.)
        3. Cache the result to avoid repeated API calls

        Args:
            location: Location string to geocode
            max_retries: Maximum retry attempts on actual network timeout (not for "no results")

        Returns:
            Tuple of (latitude, longitude) or (None, None) if failed
        """
        # Preprocess and normalize location string
        preprocessed = self._preprocess_location(location)
        normalized_location = self._normalize_location(preprocessed)

        # Check cache first, but skip cached failures to allow retrying
        if normalized_location in self.cache:
            cached_value = self.cache[normalized_location]
            # Only use cache if it's a successful geocode (not None, None)
            if cached_value[0] is not None and cached_value[1] is not None:
                logger.debug(f"Cache hit for: {normalized_location}")
                return cached_value
            else:
                logger.debug(f"Skipping cached failure for: {normalized_location} (will retry)")

        # Try the original (preprocessed/normalized) location first
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
                    # No results - don't retry, try variations instead
                    logger.debug(f"No results for original location: {normalized_location}")
                    break

            except GeocoderTimedOut:
                # Actual network timeout - retry is worthwhile
                logger.warning(f"Network timeout geocoding {normalized_location}, attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    sleep(self.rate_limit_delay * 2)
                    continue
                else:
                    # After max retries on timeout, still try variations below
                    logger.warning(f"Timeout persists after {max_retries} attempts, trying variations...")
                    break

            except GeocoderServiceError as e:
                logger.error(f"Service error geocoding {normalized_location}: {e}")
                self.cache[normalized_location] = (None, None)
                return (None, None)
            except Exception as e:
                logger.error(f"Unexpected error geocoding {normalized_location}: {e}")
                self.cache[normalized_location] = (None, None)
                return (None, None)

        # Original location failed - try variations
        variations = self._get_location_variations(normalized_location)

        for variation in variations:
            try:
                logger.info(f"Trying variation for '{normalized_location}': '{variation}'")
                result = self.geolocator.geocode(variation)

                if result:
                    coords = (result.latitude, result.longitude)
                    # Cache under the original location key
                    self.cache[normalized_location] = coords
                    logger.info(f"Geocoded via variation '{variation}': {normalized_location} -> {coords}")
                    sleep(self.rate_limit_delay)
                    return coords
                else:
                    logger.debug(f"No results for variation: {variation}")

            except GeocoderTimedOut:
                logger.warning(f"Timeout on variation: {variation}")
                # Continue to next variation
                sleep(self.rate_limit_delay)
                continue

            except GeocoderServiceError as e:
                logger.warning(f"Service error on variation '{variation}': {e}")
                continue
            except Exception as e:
                logger.warning(f"Error on variation '{variation}': {e}")
                continue

            sleep(self.rate_limit_delay)

        # All attempts failed
        logger.error(f"Failed to geocode with all variations: {normalized_location}")
        self.cache[normalized_location] = (None, None)
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
                    "location": location,
                    "tier": resort.get("tier")
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
            json.dump(enriched_resorts, f, indent=2, ensure_ascii=False)

        # Save failed resorts to a separate file for easy review
        if stats["failed_resorts"]:
            failed_file = output_file.parent / "geocode_failed.json"
            logger.info(f"Writing {len(stats['failed_resorts'])} failed resorts to: {failed_file}")
            with open(failed_file, 'w') as f:
                json.dump(stats["failed_resorts"], f, indent=2, ensure_ascii=False)

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
