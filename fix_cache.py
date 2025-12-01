#!/usr/bin/env python3
"""Fix the geocode cache by removing/updating stale entries."""

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

# Find problematic entries with backticks
problematic_entries = {k: v for k, v in cache.items() if '`' in k}

print(f"\nFound {len(problematic_entries)} entries with backticks:")
for key, value in problematic_entries.items():
    print(f"  '{key}': {value}")

# Initialize geocoder
print("\nInitializing geocoder...")
ctx = ssl.create_default_context(cafile=certifi.where())
geolocator = Nominatim(user_agent="interval-resort-cache-fix", ssl_context=ctx)

# Process each problematic entry
print("\nFixing entries...")
for key in list(problematic_entries.keys()):
    normalized = key.replace("`", "")
    print(f"\nProcessing: '{key}'")
    print(f"Normalized: '{normalized}'")

    # Check if normalized version already exists in cache
    if normalized in cache:
        print(f"  ℹ️  Normalized version already in cache: {cache[normalized]}")
        print(f"  🗑️  Removing old backtick version from cache")
        del cache[key]
    else:
        # Try to geocode the normalized version
        print(f"  🔍 Geocoding normalized version...")
        try:
            result = geolocator.geocode(normalized)
            if result:
                coords = [result.latitude, result.longitude]
                print(f"  ✅ SUCCESS: {coords}")
                print(f"  🔄 Updating cache with normalized key")
                cache[normalized] = coords
                del cache[key]
            else:
                print(f"  ❌ Still failed, keeping as null but with normalized key")
                cache[normalized] = None
                del cache[key]
            sleep(1.0)
        except Exception as e:
            print(f"  ❌ Error: {e}")
            print(f"  🔄 Moving to normalized key anyway")
            cache[normalized] = None
            del cache[key]

# Save updated cache
print(f"\nSaving updated cache...")
with open(cache_file, 'w') as f:
    json.dump(cache, f, indent=2, ensure_ascii=False)

print(f"✅ Cache updated! Now has {len(cache)} entries")
print(f"\n🎉 Done! Re-run your geocoder to process any previously failed locations.")
