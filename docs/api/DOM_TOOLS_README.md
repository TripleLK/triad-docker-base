# HTML to JSON DOM Converter & Page Comparison Tools

This repository contains two Python scripts for converting HTML pages to JSON DOM representations and comparing multiple pages to find differing elements.

## Scripts

### 1. `html_to_json.py`
Converts HTML pages to filtered JSON DOM representations with CSS selectors.

### 2. `compare_pages.py` 
Compares multiple JSON files OR URLs to identify elements that differ between pages.

## Installation

```bash
pip install -r requirements.txt
```

The required packages are:
- `requests` - for fetching HTML content
- `beautifulsoup4` - for parsing HTML
- `lxml` - for faster XML/HTML parsing

## Usage

### Converting HTML to JSON

```bash
# Basic usage - output to console
python html_to_json.py https://example.com

# Save to file with pretty formatting
python html_to_json.py https://example.com -o page1.json --pretty

# Convert multiple pages
python html_to_json.py https://example.com/page1 -o page1.json --pretty
python html_to_json.py https://example.com/page2 -o page2.json --pretty
python html_to_json.py https://example.com/page3 -o page3.json --pretty
```

### Comparing Pages

#### Option 1: Compare URLs directly (NEW!)
```bash
# Compare URLs directly - the tool will convert them to JSON automatically
python compare_pages.py --urls https://example.com/page1 https://example.com/page2 --pretty

# Keep temporary JSON files for inspection
python compare_pages.py --urls https://example.com/page1 https://example.com/page2 --keep-temp-files

# Show only CSS selectors of different elements
python compare_pages.py --urls https://example.com/page1 https://example.com/page2 --show-selectors
```

#### Option 2: Compare existing JSON files
```bash
# Compare multiple JSON files
python compare_pages.py --json-files page1.json page2.json page3.json --pretty

# Save comparison report
python compare_pages.py --json-files page1.json page2.json -o comparison_report.json --pretty
```

## Features

### HTML to JSON Converter
- **Filtered DOM**: Only includes elements with text content, images, or parents of such elements
- **CSS Selectors**: Generates valid CSS selectors for every element
- **Validation**: Verifies all generated selectors work on the original HTML
- **Content Extraction**: Extracts text content while excluding script/style tags
- **Token Optimization**: Reduces JSON size by filtering unnecessary elements

### Page Comparator
- **URL Support**: Can compare URLs directly without pre-converting to JSON
- **Content Comparison**: Identifies elements with different content across pages
- **Hierarchy Analysis**: Finds highest-level elements containing only distinct leaves
- **Detailed Reports**: Generates comprehensive comparison reports
- **Selector Output**: Can output just the CSS selectors for integration
- **Temporary File Management**: Automatically cleans up temporary files

## Algorithm Details

### DOM Filtering
The converter uses a multi-pass approach:
1. Identifies elements with meaningful content (text or images)
2. Marks parent elements that contain meaningful content
3. Filters out elements that don't meet either criterion
4. Validates all generated CSS selectors

### CSS Selector Generation
Selectors are built using:
- Element IDs (when available, provides uniqueness)
- Class names combined with tag names
- nth-of-type positioning for disambiguation
- Hierarchical parent-child relationships

### Difference Detection - Highest Level Parent Algorithm
The comparator finds the **highest level parent that only has leaves that are different**:

1. **Index Elements**: Maps all CSS selectors to their content across pages
2. **Find Different Elements**: Identifies selectors with different content between pages
3. **Hierarchy Analysis**: Groups elements by depth in the DOM tree
4. **Leaf Detection**: For each different element, checks if it contains only leaf-level differences
5. **Parent Selection**: Selects the highest-level container that wraps only differing leaf content

This ensures you get the most efficient selectors that capture meaningful content differences without including unnecessary parent containers.

## JSON Structure

The HTML to JSON converter produces the following structure:

```json
{
  "url": "https://example.com",
  "title": "Page Title",
  "total_elements": 42,
  "dom_tree": {
    "id": 1,
    "tag": "body",
    "css_selector": "body",
    "attributes": {"class": ["main-content"]},
    "text_content": "Combined text content",
    "children": [
      {
        "id": 2,
        "tag": "div",
        "css_selector": "body > div.header",
        "attributes": {"class": ["header"]},
        "text_content": "Header text",
        "children": []
      }
    ]
  }
}
```

## Comparison Report Structure

The page comparator generates reports like:

```json
{
  "summary": {
    "total_pages_compared": 3,
    "total_different_elements": 15,
    "highest_level_different_elements": 5
  },
  "pages": [
    {
      "id": 0,
      "url": "https://example.com/page1",
      "title": "Page 1",
      "file_path": "page1.json"
    }
  ],
  "highest_level_different_elements": [
    {
      "selector": "body > main > article > h1",
      "content_by_page": {
        "0": "text:Welcome to Page 1",
        "1": "text:Welcome to Page 2"
      }
    }
  ]
}
```

## Example Usage

Run the example script to see all features in action:

```bash
python example_usage.py
```

This will demonstrate:
1. Converting a single URL to JSON
2. Comparing multiple URLs directly
3. Getting only CSS selectors of different elements
4. Comparing existing JSON files

## Use Cases

- **Web Scraping**: Identify dynamic content areas on similar pages
- **A/B Testing**: Compare page variants to find differing elements
- **Content Management**: Track changes across page templates
- **Token Optimization**: Reduce LLM input size by filtering relevant content
- **Site Analysis**: Understand content structure patterns
- **Template Comparison**: Find template differences across similar pages

## Command Line Options

### html_to_json.py
- `url`: URL to convert (required)
- `-o, --output`: Output JSON file path
- `--pretty`: Pretty print JSON output

### compare_pages.py
- `--urls`: URLs to convert and compare (minimum 2)
- `--json-files`: JSON files to compare (minimum 2)
- `-o, --output`: Output JSON report file path
- `--pretty`: Pretty print JSON output
- `--show-selectors`: Show only CSS selectors of different elements
- `--keep-temp-files`: Keep temporary JSON files when using --urls

## Error Handling

Both scripts include comprehensive error handling:
- Network timeouts and connection issues
- Invalid CSS selector detection
- Missing or malformed JSON files
- HTML parsing errors
- Temporary file cleanup failures

## Performance Considerations

- The HTML converter filters aggressively to reduce token count
- CSS selector validation ensures accuracy but adds processing time
- Memory usage scales with page complexity and number of elements
- Large sites may benefit from targeted scraping of specific sections
- URL comparison creates temporary files that are automatically cleaned up 