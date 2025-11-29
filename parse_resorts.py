#!/usr/bin/env python3
"""
Interval International Resort Directory Parser

This script parses an HTML file from Interval International containing timeshare
resort directory listings and extracts structured data for each resort code.
"""

import json
import html
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import Counter
from bs4 import BeautifulSoup, Tag


class ResortParser:
    """Parser for Interval International resort directory HTML."""

    # Mapping of tier icon filenames to tier names
    TIER_MAPPING = {
        'icon_elite_small.png': 'Elite',
        'icon_elite_boutique_small.png': 'Elite Boutique',
        'icon_premier_small.png': 'Premier',
        'icon_premier_boutique_small.png': 'Premier Boutique',
        'icon_select_small.png': 'Select',
        'icon_select_boutique_small.png': 'Select Boutique',
        'icon_preferred_residence_small.png': 'Preferred Residences',
    }

    def __init__(self, html_path: str) -> None:
        """
        Initialize the parser with the path to the HTML file.

        Args:
            html_path: Path to the HTML file to parse
        """
        self.html_path = Path(html_path)
        self.soup: Optional[BeautifulSoup] = None
        self.resorts: List[Dict[str, any]] = []

    def load_html(self) -> None:
        """Load and parse the HTML file."""
        print(f"Loading HTML file: {self.html_path}")
        with open(self.html_path, 'r', encoding='utf-8') as f:
            self.soup = BeautifulSoup(f.read(), 'html.parser')
        print("HTML file loaded successfully")

    def extract_tier_from_icon(self, code_div: Tag) -> Optional[str]:
        """
        Extract tier designation from the tier icon image.

        Args:
            code_div: The div element containing the resort code and tier icon

        Returns:
            Tier name or None if no tier icon found
        """
        img = code_div.find('img')
        if not img or not img.get('src'):
            return None

        src = img['src']
        # Extract filename from src path
        filename = src.split('/')[-1]

        return self.TIER_MAPPING.get(filename)

    def is_all_inclusive(self, icons_div: Tag) -> bool:
        """
        Determine if a resort is all-inclusive by checking for the all-inclusive icon.

        Args:
            icons_div: The div element containing all resort detail icons

        Returns:
            True if all-inclusive icon is present, False otherwise
        """
        all_inc_imgs = icons_div.find_all('img', src=lambda x: x and 'all_inc_small.png' in x)
        return len(all_inc_imgs) > 0

    def unescape_text(self, text: str) -> str:
        """
        Unescape HTML entities in text.

        Args:
            text: Text potentially containing HTML entities

        Returns:
            Unescaped text
        """
        return html.unescape(text.strip())

    def parse_resort_row(self, row: Tag) -> List[Dict[str, any]]:
        """
        Parse a single resort row and extract all code records.

        Args:
            row: The TR element containing resort data

        Returns:
            List of resort records (one per code)
        """
        records = []

        # Extract resort name
        name_elem = row.find('h5', class_='AI_resort_name')
        if not name_elem:
            return records

        name_link = name_elem.find('a')
        if not name_link:
            return records

        resort_name = self.unescape_text(name_link.get_text())

        # Extract location
        location_elem = row.find('small')
        location = self.unescape_text(location_elem.get_text()) if location_elem else ''

        # Find the resort details icons container
        icons_div = row.find('div', class_='resort_details_rd_icons')
        if not icons_div:
            return records

        # Determine all-inclusive status
        all_inclusive = self.is_all_inclusive(icons_div)

        # Find all code divs
        code_divs = icons_div.find_all('div', class_='resort_details_icon_code')

        # Extract each code and its tier
        for code_div in code_divs:
            code_elem = code_div.find('strong')
            if not code_elem:
                continue

            code = code_elem.get_text().strip()
            tier = self.extract_tier_from_icon(code_div)

            record = {
                'code': code,
                'name': resort_name,
                'location': location,
                'tier': tier,
                'all_inclusive': all_inclusive
            }
            records.append(record)

        return records

    def parse_all_resorts(self) -> None:
        """Parse all resort rows from the HTML."""
        if not self.soup:
            raise ValueError("HTML not loaded. Call load_html() first.")

        print("Parsing resort rows...")

        # Find all TR elements that contain resort data
        # They typically have class 'resortallInclusive_*'
        resort_rows = self.soup.find_all('tr', class_=lambda x: x and 'resortallInclusive' in x)

        total_rows = len(resort_rows)
        print(f"Found {total_rows} resort rows")

        for idx, row in enumerate(resort_rows, 1):
            if idx % 100 == 0:
                print(f"Processing row {idx}/{total_rows}...")

            records = self.parse_resort_row(row)
            self.resorts.extend(records)

        print(f"Parsing complete. Extracted {len(self.resorts)} resort code records")

    def generate_statistics(self) -> Dict[str, any]:
        """
        Generate statistics about the parsed data.

        Returns:
            Dictionary containing statistics
        """
        stats = {
            'total_resort_rows': len(set((r['name'], r['location']) for r in self.resorts)),
            'total_code_records': len(self.resorts),
            'all_inclusive_count': sum(1 for r in self.resorts if r['all_inclusive']),
            'tier_counts': {},
            'codes_per_resort': {}
        }

        # Count by tier
        tier_counter = Counter(r['tier'] for r in self.resorts)
        stats['tier_counts'] = dict(tier_counter)

        # Count codes per resort name
        resort_code_counts = Counter(r['name'] for r in self.resorts)
        multi_code_resorts = {name: count for name, count in resort_code_counts.items() if count > 1}
        stats['multi_code_resort_count'] = len(multi_code_resorts)
        stats['max_codes_per_resort'] = max(resort_code_counts.values()) if resort_code_counts else 0

        return stats

    def print_statistics(self, stats: Dict[str, any]) -> None:
        """
        Print statistics in a readable format.

        Args:
            stats: Statistics dictionary
        """
        print("\n" + "="*60)
        print("PARSING STATISTICS")
        print("="*60)
        print(f"Total resort entries (unique name+location): {stats['total_resort_rows']}")
        print(f"Total code records created: {stats['total_code_records']}")
        print(f"All-inclusive resorts: {stats['all_inclusive_count']}")
        print(f"\nResorts with multiple codes: {stats['multi_code_resort_count']}")
        print(f"Maximum codes per resort: {stats['max_codes_per_resort']}")
        print("\nCount by tier:")
        for tier, count in sorted(stats['tier_counts'].items(), key=lambda x: x[1], reverse=True):
            tier_name = tier if tier else 'No tier (Standard)'
            print(f"  {tier_name}: {count}")
        print("="*60 + "\n")

    def save_to_json(self, output_path: str) -> None:
        """
        Save parsed resort data to a JSON file.

        Args:
            output_path: Path where JSON file should be saved
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        print(f"Saving data to {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.resorts, f, indent=2, ensure_ascii=False)
        print(f"Data saved successfully ({len(self.resorts)} records)")

    def run(self, output_path: str) -> Tuple[List[Dict[str, any]], Dict[str, any]]:
        """
        Run the complete parsing pipeline.

        Args:
            output_path: Path where JSON output should be saved

        Returns:
            Tuple of (parsed resort list, statistics dictionary)
        """
        self.load_html()
        self.parse_all_resorts()
        stats = self.generate_statistics()
        self.print_statistics(stats)
        self.save_to_json(output_path)

        return self.resorts, stats


def main() -> None:
    """Main entry point for the script."""
    # Input and output paths
    input_html = 'data/interval_11_28/interval_directory_11_28_2025.html'
    output_json = 'output/resorts.json'

    # Create parser and run
    parser = ResortParser(input_html)
    parser.run(output_json)

    print("\nParsing complete! Check the output folder for results.")


if __name__ == '__main__':
    main()
