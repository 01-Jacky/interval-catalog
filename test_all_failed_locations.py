#!/usr/bin/env python3
"""Test all failed geocoding locations to find working fallback patterns."""

import json
import ssl
import certifi
from time import sleep
from geopy.geocoders import Nominatim

# Initialize geocoder with SSL context
ctx = ssl.create_default_context(cafile=certifi.where())
geolocator = Nominatim(user_agent="interval-resort-fallback-test", ssl_context=ctx)


def generate_fallback_variations(location):
    """Generate potential fallback variations for a location string."""
    variations = []

    # Original location
    variations.append(("original", location))

    # Normalize backticks
    normalized = location.replace("`", "")
    if normalized != location:
        variations.append(("remove backticks", normalized))

    # Remove "Dutch Caribbean" suffix
    if "Dutch Caribbean" in location:
        fallback = location.replace(", Dutch Caribbean", "")
        variations.append(("remove Dutch Caribbean", fallback))
        # Also try with backticks removed
        fallback_normalized = fallback.replace("`", "")
        if fallback_normalized != fallback:
            variations.append(("remove Dutch Caribbean + backticks", fallback_normalized))

    # Hawaiian locations: remove island (O`ahu, Hawai`i, Moloka`i)
    parts = [p.strip() for p in location.split(",")]
    if len(parts) >= 3:
        # Try removing middle part (often island name)
        fallback = f"{parts[0]}, {parts[-1]}"
        variations.append(("remove middle part", fallback))
        fallback_normalized = fallback.replace("`", "")
        if fallback_normalized != fallback:
            variations.append(("remove middle part + backticks", fallback_normalized))

    # Canary Islands: simplify
    if "Canary Islands, Spain" in location:
        # Try just the island + Spain
        parts = [p.strip() for p in location.split(",")]
        if len(parts) >= 3:
            # City, Island, Canary Islands, Spain -> City, Island, Spain
            island_idx = -2  # "Canary Islands"
            fallback = ", ".join(parts[:island_idx] + [parts[-1]])
            variations.append(("simplify Canary Islands", fallback))
            # Or just island + Spain
            if len(parts) >= 4:
                fallback = f"{parts[-3]}, {parts[-1]}"
                variations.append(("island + Spain", fallback))

    # Margarita Island, Venezuela
    if "Margarita Island, Venezuela" in location:
        parts = [p.strip() for p in location.split(",")]
        if len(parts) >= 3:
            # Try just city + Venezuela
            fallback = f"{parts[0]}, Venezuela"
            variations.append(("remove Margarita Island", fallback))

    # Grand Bahama Island, Bahamas
    if "Grand Bahama Island, Bahamas" in location:
        parts = [p.strip() for p in location.split(",")]
        if len(parts) >= 3:
            # Try just city + Bahamas
            fallback = f"{parts[0]}, Bahamas"
            variations.append(("remove Grand Bahama Island", fallback))

    # Great Exuma, Bahamas
    if "Great Exuma, Bahamas" in location:
        parts = [p.strip() for p in location.split(",")]
        if len(parts) >= 3:
            # Try just city + Bahamas
            fallback = f"{parts[0]}, Bahamas"
            variations.append(("remove Great Exuma", fallback))

    # Algarve, Portugal
    if "Algarve, Portugal" in location:
        parts = [p.strip() for p in location.split(",")]
        if len(parts) >= 3:
            # Try just city + Portugal
            fallback = f"{parts[0]}, Portugal"
            variations.append(("remove Algarve", fallback))

    # "near X" pattern
    if location.startswith("near "):
        fallback = location.replace("near ", "")
        variations.append(("remove 'near'", fallback))

    # Beach/Bay names - try without the beach/bay
    for beach_type in [" Beach", " Bay", " Island"]:
        if beach_type in parts[0] if parts else "":
            city_without_beach = parts[0].replace(beach_type, "").strip()
            if len(parts) > 1:
                fallback = f"{city_without_beach}, {', '.join(parts[1:])}"
                variations.append((f"remove '{beach_type.strip()}' from city", fallback))

    # Try just the last 2 components (city, country)
    if len(parts) >= 2:
        fallback = f"{parts[0]}, {parts[-1]}"
        variations.append(("city + country only", fallback))

    # Try just the last component (country/state)
    if len(parts) >= 1:
        variations.append(("last component only", parts[-1]))

    # Remove duplicates while preserving order
    seen = set()
    unique_variations = []
    for desc, var in variations:
        if var not in seen:
            seen.add(var)
            unique_variations.append((desc, var))

    return unique_variations


def test_location(original_location):
    """Test a location and its variations to find one that geocodes."""
    print(f"\n{'='*80}")
    print(f"Testing: {original_location}")
    print(f"{'='*80}")

    variations = generate_fallback_variations(original_location)

    for desc, variation in variations:
        print(f"\n  [{desc}] '{variation}'")

        try:
            result = geolocator.geocode(variation)
            if result:
                print(f"  ✅ SUCCESS: {result.latitude}, {result.longitude}")
                print(f"     Address: {result.address}")
                return {
                    "original": original_location,
                    "working_variation": variation,
                    "strategy": desc,
                    "latitude": result.latitude,
                    "longitude": result.longitude,
                    "address": result.address
                }
            else:
                print(f"  ❌ No result")
        except Exception as e:
            print(f"  ❌ ERROR: {e}")

        sleep(1.0)  # Rate limiting

    print(f"\n  ⚠️  NO WORKING VARIATION FOUND")
    return {
        "original": original_location,
        "working_variation": None,
        "strategy": None
    }


def main():
    # Load failed resorts
    with open('/Users/jacky/repos/interval-catalog/output/geocode_failed.json', 'r') as f:
        failed = json.load(f)

    # Extract unique locations
    unique_locations = sorted(set(resort['location'] for resort in failed))

    print(f"Testing {len(unique_locations)} unique failed locations...")
    print(f"This will take approximately {len(unique_locations) * 8 / 60:.1f} minutes")

    results = []

    for i, location in enumerate(unique_locations, 1):
        print(f"\n\n[{i}/{len(unique_locations)}]")
        result = test_location(location)
        results.append(result)

        # Save progress every 10 locations
        if i % 10 == 0:
            with open('/Users/jacky/repos/interval-catalog/output/fallback_test_results.json', 'w') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Progress saved ({i}/{len(unique_locations)})")

    # Final save
    with open('/Users/jacky/repos/interval-catalog/output/fallback_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Summary
    successful = [r for r in results if r['working_variation'] is not None]
    print(f"\n\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Total locations tested: {len(results)}")
    print(f"Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
    print(f"Failed: {len(results) - len(successful)}")
    print(f"\nResults saved to: /Users/jacky/repos/interval-catalog/output/fallback_test_results.json")


if __name__ == "__main__":
    main()
