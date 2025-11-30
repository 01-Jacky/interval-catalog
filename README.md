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
├── src/                            # Source code
│   ├── parsers/                    # Parser modules
│   │   ├── __init__.py
│   │   └── resort_parser.py       # Resort HTML parser
│   └── utils/                      # Utility modules
│       ├── __init__.py
│       └── logging_config.py      # Logging configuration
├── scripts/                        # Entry point scripts
│   ├── __init__.py
│   └── parse_resorts.py           # Main parsing script
├── config/                         # Configuration management
│   ├── __init__.py
│   └── settings.py                # Settings and environment variables
├── data/                           # Input data directory
│   └── interval_11_28/
│       └── interval_directory_11_28_2025.html
├── output/                         # Output directory for parsed results
│   └── resorts.json               # Generated JSON output
├── logs/                           # Log files directory
│   └── parser.log                 # Application logs
├── tests/                          # Unit tests
│   └── __init__.py
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Docker container configuration
├── docker-compose.yml             # Docker Compose configuration
├── .env.example                   # Example environment variables
├── .gitignore                     # Git ignore rules
├── .dockerignore                  # Docker ignore rules
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

3. Check the output and logs:
   ```bash
   cat output/resorts.json
   cat logs/parser.log
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
   python scripts/parse_resorts.py
   ```

### Configuration

The application can be configured using environment variables. Copy the example file:

```bash
cp .env.example .env
```

Then edit `.env` to customize settings:

- `INPUT_HTML_PATH` - Path to input HTML file
- `OUTPUT_JSON_PATH` - Path to output JSON file
- `LOG_FILE` - Path to log file
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

When using Docker Compose, you can also set these in your environment before running.

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

## Architecture

This project follows Python best practices for offline task applications:

- **Modular Design**: Code is organized into reusable modules (`src/parsers`, `src/utils`)
- **Configuration Management**: Centralized settings with environment variable support
- **Logging**: Comprehensive logging to both console and file
- **Docker-First**: Designed to run in containerized environments
- **Type Safety**: Full type annotations throughout the codebase

## Development

The parser is built with:
- **BeautifulSoup4** - HTML parsing
- **Python 3.11** - Modern Python with type annotations
- **Docker** - Containerized execution environment
- **python-dotenv** - Environment variable management

### Adding New Parsers

To add a new parser:

1. Create a new module in `src/parsers/`
2. Import it in `src/parsers/__init__.py`
3. Create a new script in `scripts/` to run it
4. Update the Dockerfile and docker-compose.yml if needed

### Testing

The project includes a comprehensive test suite with 50+ test cases covering all parser functionality.

#### Running Tests with Docker Compose (Recommended)

```bash
# Run tests with coverage report
docker compose run --rm test

# Run specific test file
docker compose run --rm test tests/test_resort_parser.py

# Run tests matching a pattern
docker compose run --rm test -k "tier"

# Run tests without coverage
docker compose run --rm test -v
```

Coverage reports are generated in `htmlcov/index.html`.

#### Running Tests Locally

If running without Docker:

```bash
# Install dependencies including pytest
pip install -r requirements.txt

# Run all tests with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_resort_parser.py

# Run with verbose output
pytest -v
```
