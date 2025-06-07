#!/usr/bin/env python3
# Test script for Triad Scientific selectors

import os
import sys
import requests
from bs4 import BeautifulSoup

# Add the apps directory to the Python path so we can import the scraper modules
sys.path.append('.')

from apps.scrapers.selectors.base import Selected, SelectedType
from apps.scrapers.selectors.file_selector import FileSelector

# URL to test
TEST_URL = "http://www.triadscientific.com/en/products/atomic-absorption/942/universal-xyz-autosampler-auroraa-s-revolutionary/250558"

def fetch_page(url):
    """Fetch a page and return a Selected object with the parsed HTML"""
    response = requests.get(url)
    response.raise_for_status()
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    
    # Create a Selected object with the HTML content
    # Using SelectedType.SINGLE for BeautifulSoup object
    return Selected(
        value=soup,
        selected_type=SelectedType.SINGLE
    )

def test_selector(file_path, selected):
    """Test a single selector and print the results"""
    print(f"\nTesting selector: {file_path}")
    try:
        selector = FileSelector(file_path)
        result = selector.select(selected)
        print(f"Result: {result}")
        if result.selected_type == SelectedType.MULTIPLE:
            print(f"Number of items: {len(result.value)}")
            for i, item in enumerate(result.value[:3]):  # Show first 3 items
                print(f"  Item {i}: {item}")
            if len(result.value) > 3:
                print(f"  ... and {len(result.value) - 3} more items")
        elif result.selected_type == SelectedType.VALUE:
            print(f"Value: {result.value}")
        return result
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    """Main test function"""
    # Fetch the test page
    print(f"Fetching test page: {TEST_URL}")
    selected = fetch_page(TEST_URL)
    
    # Test each selector
    selectors = [
        "apps/scrapers/triadscientific-yamls/name.yaml",
        "apps/scrapers/triadscientific-yamls/short_description.yaml",
        "apps/scrapers/triadscientific-yamls/full_description.yaml",
        "apps/scrapers/triadscientific-yamls/imgs.yaml",
        "apps/scrapers/triadscientific-yamls/specs_groups.yaml",
        "apps/scrapers/triadscientific-yamls/models.yaml",
    ]
    
    for selector_path in selectors:
        test_selector(selector_path, selected)
    
    # Test the mapping yaml last
    test_selector("apps/scrapers/triadscientific-yamls/mapping.yaml", selected)

if __name__ == "__main__":
    main() 