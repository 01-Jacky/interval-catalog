#!/usr/bin/env python3
"""Fix Honolulu cache entry using the fallback pattern."""

import json
import ssl
import certifi
from time import sleep
from geopy.geocoders import Nominatim

cache_file = '/Users/jacky/repos/interval-catalog/output/geocode_cache.json'

# Load cache
print("Loading cache...")
with open(cache_file, 'r') as f:
    cache = json.load(f)

print(f"Cache has {len(cache)} entries")

# Initialize geocoder
print("\nInitializing geocoder...")
ctx = ssl.create_default_context(cafile=certifi.where())
geolocator = Nominatim(user_agent="interval-resort-honolulu-fix", ssl_context=ctx)

# The problematic entries
original_key = "Honolulu, O`ahu, Hawai`i"  # With backticks
normalized_key = "Honolulu, Oahu, Hawaii"   # Normalized (currently null)
fallback_query = "Honolulu, Hawaii"         # What actually works

print("\n" + "=" * 80)
print("FIXING HONOLULU CACHE ENTRIES")
print("=" * 80)

print(f"\nCurrent state:")
print(f"  '{original_key}': {cache.get(original_key, 'NOT FOUND')}")
print(f"  '{normalized_key}': {cache.get(normalized_key, 'NOT FOUND')}")

# Geocode the fallback
print(f"\n🔍 Geocoding fallback: '{fallback_query}'")
result = geolocator.geocode(fallback_query)

if result:
    coords = [result.latitude, result.longitude]
    print(f"✅ SUCCESS: {coords}")
    print(f"   Address: {result.address}")

    # Update cache
    print(f"\n🔄 Updating cache...")

    # Remove backtick version if it exists
    if original_key in cache:
        print(f"  🗑️  Removing: '{original_key}'")
        del cache[original_key]

    # Update normalized version with correct coordinates
    print(f"  ✏️  Updating: '{normalized_key}' = {coords}")
    cache[normalized_key] = coords

    # Save updated cache
    print(f"\n💾 Saving updated cache...")
    with open(cache_file, 'w') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Cache updated successfully!")
    print(f"\nFinal state:")
    print(f"  '{normalized_key}': {cache[normalized_key]}")

else:
    print(f"❌ Failed to geocode fallback location")

print("\n" + "=" * 80)
