# Startup prompt
This document records one possible starting prompt for this project. 


# Prompt:
"I have an HTML file from Interval International containing a directory of timeshare vacation resorts. I need to extract the following information from each resort listing and save it to a structured format (JSON/CSV) for use in other services.

## Data to extract:
- **Resort Name** - Found in `<h5 class="AI_resort_name"><a>` tags
- **Location** - Found in `<small>` tags immediately after the resort name
- **Resort Code** - 3-letter code found in `<strong>` tags within `<div class="resort_details_icon_code">`
- **Tier** - Extracted from the tier icon image filename within the same `<div class="resort_details_icon_code">` as the code
- **All-Inclusive** - Determined by the presence of `all_inc_small.png` image within the `<div class="resort_details_rd_icons">` section (true if present, false if not)

## Tier mapping (from image filenames):
- `icon_elite_small.png` � "Elite"
- `icon_elite_boutique_small.png` � "Elite Boutique"
- `icon_premier_small.png` � "Premier"
- `icon_premier_boutique_small.png` � "Premier Boutique"
- `icon_select_small.png` � "Select"
- `icon_select_boutique_small.png` � "Select Boutique"
- `icon_preferred_residence_small.png` � "Preferred Residences"
- No icon present � null (or "Standard")

## HTML structure examples:

**Single code resort:**
```html
<tr data-allInclusive="..." class="resortallInclusive_...">
    <h5 class="AI_resort_name">
        <a href="...">124 on Queen Hotel & Spa</a>
    </h5>
    <small>Niagara-on-the-Lake, Ontario</small>
    <div class="resort_details_rd_icons">
        <div class="resort_details_icon">
            <div class="resort_details_icon_code">
                <strong>VVR</strong>
                <span style="position:relative;">
                    <img src='/iimedia/images/icons/tier/icon_premier_boutique_small.png' border="0">
                </span>
            </div>
        </div>
    </div>
</tr>
```

**Multiple code resort:**
```html
<tr data-allInclusive="false" class="resortallInclusive_false">
    <h5 class="AI_resort_name">
        <a href="...">Marriott's Ko Olina Beach Club</a>
    </h5>
    <small>Kapolei, O`ahu, Hawai`i</small>
    <div class="resort_details_rd_icons">
        <div class="resort_details_icon">
            <div class="resort_details_icon_code">
                <strong>MKO</strong>
                <span><img src='/iimedia/images/icons/tier/icon_elite_small.png'></span>
            </div>
        </div>
        <div class="resort_details_icon">
            <div class="resort_details_icon_code">
                <strong>MK1</strong>
                <span><img src='/iimedia/images/icons/tier/icon_elite_small.png'></span>
            </div>
        </div>
    </div>
</tr>
```

**All-inclusive resort:**
```html
<tr data-allInclusive="true" class="resortallInclusive_true">
    <h5 class="AI_resort_name">
        <a href="...">AVA Resort Cancun</a>
    </h5>
    <small>Cancún, Quintana Roo, Mexico</small>
    <div class="resort_details_rd_icons">
        <div class="resort_details_icon">
            <div class="resort_details_icon_code">
                <strong>AWA</strong>
                <span><img src='/iimedia/images/icons/tier/icon_elite_small.png'></span>
            </div>
        </div>
        <!-- All-inclusive indicator: Look for this icon to determine all-inclusive status -->
        <div class="resort_details_icon">
            <span><img src='/images/_icons/all_inc_small.png'></span>
        </div>
    </div>
</tr>
```

## Special case - Multiple codes per resort:
Some resorts have multiple 3-letter codes (e.g., Marriott's Ko Olina Beach Club has both MKO and MK1, Big Sky Resort has 7 codes: APQ, BSS, BSW, BSG, VLQ, PKQ, BSK).

**IMPORTANT:** Each code can have a DIFFERENT tier designation. For example, Big Sky Resort's codes have different tiers:
- BSW � "Select"
- BSG � "Premier"
- BSK � "Premier"
- APQ, BSS, VLQ, PKQ � no tier

**Decision:** Create a SEPARATE record for each code, even if they share the same resort name and location. This is necessary because:
1. Each code can have a different tier
2. The codes likely represent different unit types or buildings within the same resort
3. Other services will look up resorts by code, so each code needs its own entry

## Requirements:
1. Parse the HTML file at `data/interval_11_28/interval_directory_11_28_2025.html`
2. Extract all resort entries (there appear to be thousands)
3. For resorts with multiple codes, create a separate JSON object for each code
4. Output the data as JSON with this structure:
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
     },
     {
       "code": "MK1",
       "name": "Marriott's Ko Olina Beach Club",
       "location": "Kapolei, O`ahu, Hawai`i",
       "tier": "Elite",
       "all_inclusive": false
     },
     {
       "code": "AWA",
       "name": "AVA Resort Cancun",
       "location": "Cancún, Quintana Roo, Mexico",
       "tier": "Elite",
       "all_inclusive": true
     }
   ]
   ```
5. Handle edge cases:
   - Missing tier icons (set tier to null)
   - HTML entities (like `O\`ahu` for O'ahu)
   - Special characters in resort names
   - Resorts with 1-7+ codes
   - Use the `all_inc_small.png` icon (not the `data-allInclusive` attribute) to determine all-inclusive status
6. Provide statistics:
   - Total resort entries (TR elements) parsed
   - Total individual code records created
   - Count by tier type

## Code structure
Please create a Python script using BeautifulSoup or similar library to accomplish this parsing."

Use docker base workflow for development and running. To test or run this script it should be with docker compose commands.

Use type annotation in all function header and class decoration.

Put parsed result in an output folder.