#!/usr/bin/env python3
"""Check the actual character used in the source data."""

import json
import unicodedata

# Load the actual data
with open('/Users/jacky/repos/interval-catalog/output/resorts.json', 'r') as f:
    resorts = json.load(f)

# Find Princeville resorts
princeville_resorts = [r for r in resorts if 'Princeville' in r.get('location', '')]

print("=" * 80)
print("ACTUAL DATA ANALYSIS")
print("=" * 80)

for resort in princeville_resorts[:3]:  # Check first 3
    location = resort['location']
    print(f"\nResort: {resort.get('name', 'N/A')}")
    print(f"Location: {location}")
    print("-" * 80)

    # Find the special character
    for char in location:
        if char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ, ":
            code_point = ord(char)
            try:
                unicode_name = unicodedata.name(char)
            except ValueError:
                unicode_name = "UNKNOWN"

            print(f"  Character: '{char}'")
            print(f"  Unicode: U+{code_point:04X}")
            print(f"  Name: {unicode_name}")

print("\n" + "=" * 80)
print("NORMALIZATION TEST")
print("=" * 80)

if princeville_resorts:
    location = princeville_resorts[0]['location']
    print(f"\nOriginal: {location}")
    print(f"Current normalizer (remove `): {location.replace('`', '')}")
    print(f"Better normalizer (remove `, ', ', ʻ): {location.replace('`', '').replace(chr(0x0027), '').replace(chr(0x2019), '').replace(chr(0x02BB), '')}")
