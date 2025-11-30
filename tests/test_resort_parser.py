#!/usr/bin/env python3
"""
Test suite for ResortParser class.

Tests cover:
- HTML loading and parsing
- Tier extraction from icons
- All-inclusive detection
- Text unescaping
- Resort row parsing
- Statistics generation
- JSON output
"""

import json
import pytest
from pathlib import Path
from bs4 import BeautifulSoup
from src.parsers.resort_parser import ResortParser


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_resort_html():
    """Sample HTML for a single resort with one code."""
    return """
    <tr class="resortallInclusive_1">
        <td>
            <h5 class="AI_resort_name">
                <a href="#">Marriott's Maui Ocean Club</a>
            </h5>
            <small>Lahaina, Hawaii, United States</small>
            <div class="resort_details_rd_icons">
                <div class="resort_details_icon_code">
                    <img src="/images/icons/icon_elite_small.png" alt="Elite">
                    <strong>MAW</strong>
                </div>
            </div>
        </td>
    </tr>
    """


@pytest.fixture
def multi_code_resort_html():
    """Sample HTML for a resort with multiple codes."""
    return """
    <tr class="resortallInclusive_2">
        <td>
            <h5 class="AI_resort_name">
                <a href="#">Westin Ka'anapali Ocean Resort Villas</a>
            </h5>
            <small>Lahaina, Hawaii, United States</small>
            <div class="resort_details_rd_icons">
                <div class="resort_details_icon_code">
                    <img src="/images/icons/icon_premier_small.png" alt="Premier">
                    <strong>KAA</strong>
                </div>
                <div class="resort_details_icon_code">
                    <img src="/images/icons/icon_elite_small.png" alt="Elite">
                    <strong>KAN</strong>
                </div>
                <div class="resort_details_icon_code">
                    <img src="/images/icons/icon_select_small.png" alt="Select">
                    <strong>KAO</strong>
                </div>
            </div>
        </td>
    </tr>
    """


@pytest.fixture
def all_inclusive_resort_html():
    """Sample HTML for an all-inclusive resort."""
    return """
    <tr class="resortallInclusive_3">
        <td>
            <h5 class="AI_resort_name">
                <a href="#">Dreams Tulum Resort &amp; Spa</a>
            </h5>
            <small>Tulum, Quintana Roo, Mexico</small>
            <div class="resort_details_rd_icons">
                <img src="/images/icons/all_inc_small.png" alt="All Inclusive">
                <div class="resort_details_icon_code">
                    <img src="/images/icons/icon_premier_boutique_small.png" alt="Premier Boutique">
                    <strong>DTM</strong>
                </div>
            </div>
        </td>
    </tr>
    """


@pytest.fixture
def no_tier_resort_html():
    """Sample HTML for a resort with no tier designation."""
    return """
    <tr class="resortallInclusive_4">
        <td>
            <h5 class="AI_resort_name">
                <a href="#">Basic Resort</a>
            </h5>
            <small>Orlando, Florida, United States</small>
            <div class="resort_details_rd_icons">
                <div class="resort_details_icon_code">
                    <strong>BRC</strong>
                </div>
            </div>
        </td>
    </tr>
    """


@pytest.fixture
def complete_html_file(tmp_path, sample_resort_html, multi_code_resort_html, all_inclusive_resort_html):
    """Create a complete HTML file with multiple resorts."""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><title>Resort Directory</title></head>
    <body>
        <table>
            {sample_resort_html}
            {multi_code_resort_html}
            {all_inclusive_resort_html}
        </table>
    </body>
    </html>
    """
    html_file = tmp_path / "resorts.html"
    html_file.write_text(html_content, encoding='utf-8')
    return str(html_file)


@pytest.fixture
def parser_with_loaded_html(complete_html_file):
    """ResortParser instance with HTML already loaded."""
    parser = ResortParser(complete_html_file)
    parser.load_html()
    return parser


# ============================================================================
# Initialization Tests
# ============================================================================

def test_parser_initialization():
    """Test ResortParser initialization with valid path."""
    parser = ResortParser("test.html")
    assert parser.html_path == Path("test.html")
    assert parser.soup is None
    assert parser.resorts == []


def test_tier_mapping_exists():
    """Test that tier mapping dictionary contains expected entries."""
    parser = ResortParser("test.html")
    assert 'icon_elite_small.png' in parser.TIER_MAPPING
    assert parser.TIER_MAPPING['icon_elite_small.png'] == 'Elite'
    assert parser.TIER_MAPPING['icon_premier_small.png'] == 'Premier'
    assert parser.TIER_MAPPING['icon_select_small.png'] == 'Select'
    assert parser.TIER_MAPPING['icon_elite_boutique_small.png'] == 'Elite Boutique'
    assert parser.TIER_MAPPING['icon_premier_boutique_small.png'] == 'Premier Boutique'
    assert parser.TIER_MAPPING['icon_select_boutique_small.png'] == 'Select Boutique'
    assert parser.TIER_MAPPING['icon_preferred_residence_small.png'] == 'Preferred Residences'


# ============================================================================
# HTML Loading Tests
# ============================================================================

def test_load_html_file_not_found():
    """Test load_html raises FileNotFoundError for non-existent file."""
    parser = ResortParser("nonexistent_file.html")
    with pytest.raises(FileNotFoundError, match="HTML file not found"):
        parser.load_html()


def test_load_html_success(tmp_path):
    """Test successful HTML loading."""
    html_file = tmp_path / "test.html"
    html_file.write_text("<html><body><p>Test</p></body></html>", encoding='utf-8')

    parser = ResortParser(str(html_file))
    parser.load_html()

    assert parser.soup is not None
    assert parser.soup.find('p').get_text() == 'Test'


def test_load_html_with_utf8_encoding(tmp_path):
    """Test HTML loading with UTF-8 characters."""
    html_file = tmp_path / "test_utf8.html"
    html_file.write_text("<html><body>Cañón, München, 东京</body></html>", encoding='utf-8')

    parser = ResortParser(str(html_file))
    parser.load_html()

    assert parser.soup is not None
    assert 'Cañón' in parser.soup.get_text()
    assert 'München' in parser.soup.get_text()


# ============================================================================
# Tier Extraction Tests
# ============================================================================

def test_extract_tier_from_icon_elite():
    """Test tier extraction for Elite tier."""
    parser = ResortParser("test.html")
    html = '<div><img src="/images/icons/icon_elite_small.png" alt="Elite"></div>'
    soup = BeautifulSoup(html, 'html.parser')
    code_div = soup.find('div')

    tier = parser.extract_tier_from_icon(code_div)
    assert tier == 'Elite'


def test_extract_tier_from_icon_premier():
    """Test tier extraction for Premier tier."""
    parser = ResortParser("test.html")
    html = '<div><img src="/path/to/icon_premier_small.png"></div>'
    soup = BeautifulSoup(html, 'html.parser')
    code_div = soup.find('div')

    tier = parser.extract_tier_from_icon(code_div)
    assert tier == 'Premier'


def test_extract_tier_from_icon_boutique():
    """Test tier extraction for boutique tiers."""
    parser = ResortParser("test.html")

    # Elite Boutique
    html = '<div><img src="/icons/icon_elite_boutique_small.png"></div>'
    soup = BeautifulSoup(html, 'html.parser')
    tier = parser.extract_tier_from_icon(soup.find('div'))
    assert tier == 'Elite Boutique'

    # Premier Boutique
    html = '<div><img src="/icons/icon_premier_boutique_small.png"></div>'
    soup = BeautifulSoup(html, 'html.parser')
    tier = parser.extract_tier_from_icon(soup.find('div'))
    assert tier == 'Premier Boutique'


def test_extract_tier_from_icon_no_image():
    """Test tier extraction when no image is present."""
    parser = ResortParser("test.html")
    html = '<div><strong>ABC</strong></div>'
    soup = BeautifulSoup(html, 'html.parser')
    code_div = soup.find('div')

    tier = parser.extract_tier_from_icon(code_div)
    assert tier is None


def test_extract_tier_from_icon_unknown_tier():
    """Test tier extraction with unknown tier icon."""
    parser = ResortParser("test.html")
    html = '<div><img src="/icons/unknown_tier.png"></div>'
    soup = BeautifulSoup(html, 'html.parser')
    code_div = soup.find('div')

    tier = parser.extract_tier_from_icon(code_div)
    assert tier is None


def test_extract_tier_from_icon_no_src():
    """Test tier extraction when img tag has no src attribute."""
    parser = ResortParser("test.html")
    html = '<div><img alt="Icon"></div>'
    soup = BeautifulSoup(html, 'html.parser')
    code_div = soup.find('div')

    tier = parser.extract_tier_from_icon(code_div)
    assert tier is None


# ============================================================================
# All-Inclusive Detection Tests
# ============================================================================

def test_is_all_inclusive_true():
    """Test all-inclusive detection when icon is present."""
    parser = ResortParser("test.html")
    html = '''
    <div class="resort_details_rd_icons">
        <img src="/images/icons/all_inc_small.png" alt="All Inclusive">
        <div>Other content</div>
    </div>
    '''
    soup = BeautifulSoup(html, 'html.parser')
    icons_div = soup.find('div', class_='resort_details_rd_icons')

    assert parser.is_all_inclusive(icons_div) is True


def test_is_all_inclusive_false():
    """Test all-inclusive detection when icon is not present."""
    parser = ResortParser("test.html")
    html = '''
    <div class="resort_details_rd_icons">
        <img src="/images/icons/other_icon.png" alt="Other">
    </div>
    '''
    soup = BeautifulSoup(html, 'html.parser')
    icons_div = soup.find('div', class_='resort_details_rd_icons')

    assert parser.is_all_inclusive(icons_div) is False


def test_is_all_inclusive_multiple_icons():
    """Test all-inclusive detection with multiple all-inclusive icons."""
    parser = ResortParser("test.html")
    html = '''
    <div class="resort_details_rd_icons">
        <img src="/images/icons/all_inc_small.png">
        <img src="/images/icons/all_inc_small.png">
    </div>
    '''
    soup = BeautifulSoup(html, 'html.parser')
    icons_div = soup.find('div', class_='resort_details_rd_icons')

    assert parser.is_all_inclusive(icons_div) is True


# ============================================================================
# Text Unescaping Tests
# ============================================================================

def test_unescape_text_html_entities():
    """Test unescaping of HTML entities."""
    parser = ResortParser("test.html")

    assert parser.unescape_text("&amp;") == "&"
    assert parser.unescape_text("&lt;") == "<"
    assert parser.unescape_text("&gt;") == ">"
    assert parser.unescape_text("&quot;") == '"'
    assert parser.unescape_text("Dreams Tulum Resort &amp; Spa") == "Dreams Tulum Resort & Spa"


def test_unescape_text_with_whitespace():
    """Test text unescaping also strips whitespace."""
    parser = ResortParser("test.html")

    assert parser.unescape_text("  Resort Name  ") == "Resort Name"
    assert parser.unescape_text("\n\tTabbed Text\n") == "Tabbed Text"


def test_unescape_text_no_entities():
    """Test unescaping text without HTML entities."""
    parser = ResortParser("test.html")

    assert parser.unescape_text("Normal Text") == "Normal Text"
    assert parser.unescape_text("Marriott's Resort") == "Marriott's Resort"


# ============================================================================
# Resort Row Parsing Tests
# ============================================================================

def test_parse_resort_row_single_code(sample_resort_html):
    """Test parsing a resort row with a single code."""
    parser = ResortParser("test.html")
    soup = BeautifulSoup(sample_resort_html, 'html.parser')
    row = soup.find('tr')

    records = parser.parse_resort_row(row)

    assert len(records) == 1
    assert records[0]['code'] == 'MAW'
    assert records[0]['name'] == "Marriott's Maui Ocean Club"
    assert records[0]['location'] == 'Lahaina, Hawaii, United States'
    assert records[0]['tier'] == 'Elite'
    assert records[0]['all_inclusive'] is False


def test_parse_resort_row_multiple_codes(multi_code_resort_html):
    """Test parsing a resort row with multiple codes."""
    parser = ResortParser("test.html")
    soup = BeautifulSoup(multi_code_resort_html, 'html.parser')
    row = soup.find('tr')

    records = parser.parse_resort_row(row)

    assert len(records) == 3

    assert records[0]['code'] == 'KAA'
    assert records[0]['tier'] == 'Premier'
    assert records[0]['name'] == "Westin Ka'anapali Ocean Resort Villas"

    assert records[1]['code'] == 'KAN'
    assert records[1]['tier'] == 'Elite'

    assert records[2]['code'] == 'KAO'
    assert records[2]['tier'] == 'Select'

    # All should share same name and location
    for record in records:
        assert record['name'] == "Westin Ka'anapali Ocean Resort Villas"
        assert record['location'] == 'Lahaina, Hawaii, United States'
        assert record['all_inclusive'] is False


def test_parse_resort_row_all_inclusive(all_inclusive_resort_html):
    """Test parsing an all-inclusive resort."""
    parser = ResortParser("test.html")
    soup = BeautifulSoup(all_inclusive_resort_html, 'html.parser')
    row = soup.find('tr')

    records = parser.parse_resort_row(row)

    assert len(records) == 1
    assert records[0]['code'] == 'DTM'
    assert records[0]['name'] == 'Dreams Tulum Resort & Spa'
    assert records[0]['location'] == 'Tulum, Quintana Roo, Mexico'
    assert records[0]['tier'] == 'Premier Boutique'
    assert records[0]['all_inclusive'] is True


def test_parse_resort_row_no_tier(no_tier_resort_html):
    """Test parsing a resort with no tier designation."""
    parser = ResortParser("test.html")
    soup = BeautifulSoup(no_tier_resort_html, 'html.parser')
    row = soup.find('tr')

    records = parser.parse_resort_row(row)

    assert len(records) == 1
    assert records[0]['code'] == 'BRC'
    assert records[0]['name'] == 'Basic Resort'
    assert records[0]['tier'] is None


def test_parse_resort_row_missing_name():
    """Test parsing a row with missing resort name."""
    parser = ResortParser("test.html")
    html = '<tr class="resortallInclusive_1"><td><small>Location</small></td></tr>'
    soup = BeautifulSoup(html, 'html.parser')
    row = soup.find('tr')

    records = parser.parse_resort_row(row)

    assert records == []


def test_parse_resort_row_missing_icons_div():
    """Test parsing a row with missing icons div."""
    parser = ResortParser("test.html")
    html = '''
    <tr class="resortallInclusive_1">
        <td>
            <h5 class="AI_resort_name"><a href="#">Test Resort</a></h5>
            <small>Location</small>
        </td>
    </tr>
    '''
    soup = BeautifulSoup(html, 'html.parser')
    row = soup.find('tr')

    records = parser.parse_resort_row(row)

    assert records == []


def test_parse_resort_row_missing_code_strong():
    """Test parsing when code div exists but strong tag is missing."""
    parser = ResortParser("test.html")
    html = '''
    <tr class="resortallInclusive_1">
        <td>
            <h5 class="AI_resort_name"><a href="#">Test Resort</a></h5>
            <small>Location</small>
            <div class="resort_details_rd_icons">
                <div class="resort_details_icon_code">
                    <img src="/icons/icon_elite_small.png">
                </div>
            </div>
        </td>
    </tr>
    '''
    soup = BeautifulSoup(html, 'html.parser')
    row = soup.find('tr')

    records = parser.parse_resort_row(row)

    assert records == []


# ============================================================================
# Full Parsing Tests
# ============================================================================

def test_parse_all_resorts_not_loaded():
    """Test parse_all_resorts raises error when HTML not loaded."""
    parser = ResortParser("test.html")

    with pytest.raises(ValueError, match="HTML not loaded"):
        parser.parse_all_resorts()


def test_parse_all_resorts_success(parser_with_loaded_html):
    """Test parsing all resorts from loaded HTML."""
    parser_with_loaded_html.parse_all_resorts()

    # Should have 5 total records (1 + 3 + 1 from fixtures)
    assert len(parser_with_loaded_html.resorts) == 5

    # Verify codes are present
    codes = [r['code'] for r in parser_with_loaded_html.resorts]
    assert 'MAW' in codes
    assert 'KAA' in codes
    assert 'KAN' in codes
    assert 'KAO' in codes
    assert 'DTM' in codes


def test_parse_all_resorts_empty_html(tmp_path):
    """Test parsing HTML with no resort rows."""
    html_file = tmp_path / "empty.html"
    html_file.write_text("<html><body><table></table></body></html>", encoding='utf-8')

    parser = ResortParser(str(html_file))
    parser.load_html()
    parser.parse_all_resorts()

    assert parser.resorts == []


# ============================================================================
# Statistics Tests
# ============================================================================

def test_generate_statistics_empty():
    """Test statistics generation with no data."""
    parser = ResortParser("test.html")

    stats = parser.generate_statistics()

    assert stats['total_resort_rows'] == 0
    assert stats['total_code_records'] == 0
    assert stats['all_inclusive_count'] == 0
    assert stats['tier_counts'] == {}
    assert stats['multi_code_resort_count'] == 0
    assert stats['max_codes_per_resort'] == 0


def test_generate_statistics_with_data(parser_with_loaded_html):
    """Test statistics generation with parsed data."""
    parser_with_loaded_html.parse_all_resorts()

    stats = parser_with_loaded_html.generate_statistics()

    assert stats['total_code_records'] == 5
    assert stats['all_inclusive_count'] == 1  # Only DTM is all-inclusive
    assert stats['total_resort_rows'] == 3  # 3 unique resorts

    # Check tier counts
    assert stats['tier_counts']['Elite'] == 2  # MAW and KAN
    assert stats['tier_counts']['Premier'] == 1  # KAA
    assert stats['tier_counts']['Select'] == 1  # KAO
    assert stats['tier_counts']['Premier Boutique'] == 1  # DTM

    # Check multi-code resort stats
    assert stats['multi_code_resort_count'] == 1  # Westin has 3 codes
    assert stats['max_codes_per_resort'] == 3


def test_generate_statistics_tier_none():
    """Test statistics with resorts having no tier."""
    parser = ResortParser("test.html")
    parser.resorts = [
        {'code': 'ABC', 'name': 'Resort 1', 'location': 'Place', 'tier': None, 'all_inclusive': False},
        {'code': 'DEF', 'name': 'Resort 2', 'location': 'Place', 'tier': None, 'all_inclusive': False},
    ]

    stats = parser.generate_statistics()

    assert stats['tier_counts'][None] == 2


# ============================================================================
# JSON Output Tests
# ============================================================================

def test_save_to_json_creates_file(tmp_path, parser_with_loaded_html):
    """Test that save_to_json creates a valid JSON file."""
    parser_with_loaded_html.parse_all_resorts()
    output_file = tmp_path / "output.json"

    parser_with_loaded_html.save_to_json(str(output_file))

    assert output_file.exists()

    # Verify JSON content
    with open(output_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert len(data) == 5
    assert data[0]['code'] == 'MAW'


def test_save_to_json_creates_parent_directory(tmp_path, parser_with_loaded_html):
    """Test that save_to_json creates parent directories if needed."""
    parser_with_loaded_html.parse_all_resorts()
    output_file = tmp_path / "nested" / "dir" / "output.json"

    parser_with_loaded_html.save_to_json(str(output_file))

    assert output_file.exists()
    assert output_file.parent.exists()


def test_save_to_json_utf8_encoding(tmp_path):
    """Test that JSON is saved with proper UTF-8 encoding."""
    parser = ResortParser("test.html")
    parser.resorts = [
        {
            'code': 'TST',
            'name': 'Résort Münchën 东京',
            'location': 'Cañón City',
            'tier': 'Elite',
            'all_inclusive': False
        }
    ]

    output_file = tmp_path / "utf8.json"
    parser.save_to_json(str(output_file))

    with open(output_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert data[0]['name'] == 'Résort Münchën 东京'
    assert data[0]['location'] == 'Cañón City'


def test_save_to_json_pretty_printed(tmp_path):
    """Test that JSON output is properly indented."""
    parser = ResortParser("test.html")
    parser.resorts = [{'code': 'TST', 'name': 'Test', 'location': 'Place', 'tier': None, 'all_inclusive': False}]

    output_file = tmp_path / "pretty.json"
    parser.save_to_json(str(output_file))

    content = output_file.read_text()

    # Pretty-printed JSON should have indentation
    assert '  ' in content
    assert '\n' in content


# ============================================================================
# Integration Tests (run() method)
# ============================================================================

def test_run_complete_pipeline(complete_html_file, tmp_path):
    """Test the complete run() pipeline."""
    parser = ResortParser(complete_html_file)
    output_file = tmp_path / "output.json"

    resorts, stats = parser.run(str(output_file))

    # Check return values
    assert len(resorts) == 5
    assert stats['total_code_records'] == 5

    # Check file was created
    assert output_file.exists()

    # Check parser state
    assert parser.soup is not None
    assert len(parser.resorts) == 5


def test_run_with_nonexistent_file():
    """Test run() with non-existent HTML file."""
    parser = ResortParser("nonexistent.html")

    with pytest.raises(FileNotFoundError):
        parser.run("output.json")


# ============================================================================
# Edge Cases and Boundary Tests
# ============================================================================

def test_empty_location():
    """Test parsing when location element is missing."""
    parser = ResortParser("test.html")
    html = '''
    <tr class="resortallInclusive_1">
        <td>
            <h5 class="AI_resort_name"><a href="#">Test Resort</a></h5>
            <div class="resort_details_rd_icons">
                <div class="resort_details_icon_code">
                    <strong>TST</strong>
                </div>
            </div>
        </td>
    </tr>
    '''
    soup = BeautifulSoup(html, 'html.parser')
    row = soup.find('tr')

    records = parser.parse_resort_row(row)

    assert len(records) == 1
    assert records[0]['location'] == ''


def test_whitespace_in_code():
    """Test that whitespace in codes is stripped."""
    parser = ResortParser("test.html")
    html = '''
    <tr class="resortallInclusive_1">
        <td>
            <h5 class="AI_resort_name"><a href="#">Test Resort</a></h5>
            <small>Location</small>
            <div class="resort_details_rd_icons">
                <div class="resort_details_icon_code">
                    <strong>  ABC  </strong>
                </div>
            </div>
        </td>
    </tr>
    '''
    soup = BeautifulSoup(html, 'html.parser')
    row = soup.find('tr')

    records = parser.parse_resort_row(row)

    assert records[0]['code'] == 'ABC'


def test_special_characters_in_resort_name():
    """Test parsing resort names with special characters."""
    parser = ResortParser("test.html")
    html = '''
    <tr class="resortallInclusive_1">
        <td>
            <h5 class="AI_resort_name">
                <a href="#">Marriott's Ko Olina Beach Club</a>
            </h5>
            <small>Kapolei, Hawaii, United States</small>
            <div class="resort_details_rd_icons">
                <div class="resort_details_icon_code">
                    <strong>KBC</strong>
                </div>
            </div>
        </td>
    </tr>
    '''
    soup = BeautifulSoup(html, 'html.parser')
    row = soup.find('tr')

    records = parser.parse_resort_row(row)

    assert records[0]['name'] == "Marriott's Ko Olina Beach Club"
