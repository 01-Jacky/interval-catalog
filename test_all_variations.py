#!/usr/bin/env python3
"""Test all character variations with the geocoder."""

import ssl
import certifi
from time import sleep
from geopy.geocoders import Nominatim

# Initialize geocoder
ctx = ssl.create_default_context(cafile=certifi.where())
geolocator = Nominatim(user_agent="interval-resort-test", ssl_context=ctx)

# Test all variations
test_cases = [
    ("ASCII backtick (U+0060)", "Princeville, Kaua`i, Hawai`i"),
    ("Apostrophe (U+0027)", "Princeville, Kaua'i, Hawai'i"),
    ("Hawaiian ʻokina (U+02BB)", "Princeville, Kauaʻi, Hawaiʻi"),
    ("Right single quote (U+2019)", "Princeville, Kaua'i, Hawai'i"),
    ("After normalization", "Princeville, Kauai, Hawaii"),
]

print("=" * 80)
print("GEOCODING TEST FOR ALL CHARACTER VARIATIONS")
print("=" * 80)

for name, location in test_cases:
    print(f"\n📍 {name}")
    print(f"   String: '{location}'")
    print("-" * 80)

    try:
        result = geolocator.geocode(location)

        if result:
            print(f"   ✅ SUCCESS")
            print(f"      Lat/Lon: {result.latitude}, {result.longitude}")
        else:
            print(f"   ❌ FAILED - No results")

    except Exception as e:
        print(f"   ❌ ERROR: {e}")

    sleep(1.0)

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
print("\nThe geocoder normalizer only removes ASCII backtick (`).")
print("If the source data contains other characters like ʻokina (ʻ),")
print("they won't be removed and geocoding will fail.")
print("\nSolution: Update the normalizer to handle all these characters:")
print("  - ASCII backtick: ` (U+0060)")
print("  - Apostrophe: ' (U+0027)")
print("  - Hawaiian ʻokina: ʻ (U+02BB)")
print("  - Right single quote: ' (U+2019)")
