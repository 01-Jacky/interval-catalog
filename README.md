# Interval International Resort Catalog Parser

This project parses HTML files from Interval International containing timeshare resort directory listings and extracts structured data into JSON format.

## Overview

The parser extracts the following information from each resort listing:
- **Resort Code** - 3-letter identification code
- **Resort Name** - Full name of the resort
- **Location** - City, state/province, country
- **Tier** - Quality tier (Elite, Premier, Select, etc.)
- **All-Inclusive** - Whether the resort is all-inclusive

## Important Notes

- Resorts with multiple codes are split into separate records (one per code)
- Each code can have a different tier designation
- All-inclusive status is determined by the presence of the all-inclusive icon

## Project Structure

```
interval-catalog/
├── data/                           # Input data directory
│   └── interval_11_28/
│       └── interval_directory_11_28_2025.html
├── output/                         # Output directory for parsed results
│   └── resorts.json               # Generated JSON output
├── parse_resorts.py               # Main parser script
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Docker container configuration
├── docker-compose.yml             # Docker Compose configuration
└── README.md                      # This file
```

## Requirements

- Docker
- Docker Compose

## Usage

### Running with Docker Compose (Recommended)

1. Build the Docker image:
   ```bash
   docker compose build
   ```

2. Run the parser:
   ```bash
   docker compose run --rm parser
   ```

3. Check the output:
   ```bash
   cat output/resorts.json
   ```

### Running Locally (Alternative)

If you prefer to run without Docker:

1. Install Python 3.11+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the parser:
   ```bash
   python parse_resorts.py
   ```

## Output Format

The parser generates a JSON file with the following structure:

```json
[
  {
    "code": "VVR",
    "name": "124 on Queen Hotel & Spa",
    "location": "Niagara-on-the-Lake, Ontario",
    "tier": "Premier Boutique",
    "all_inclusive": false
  },
  {
    "code": "MKO",
    "name": "Marriott's Ko Olina Beach Club",
    "location": "Kapolei, O`ahu, Hawai`i",
    "tier": "Elite",
    "all_inclusive": false
  }
]
```

## Statistics

The parser automatically generates statistics including:
- Total resort entries parsed
- Total individual code records created
- Count by tier type
- All-inclusive resort count
- Multi-code resort information

## Development

The parser is built with:
- **BeautifulSoup4** - HTML parsing
- **Python 3.11** - Modern Python with type annotations
- **Docker** - Containerized execution environment
