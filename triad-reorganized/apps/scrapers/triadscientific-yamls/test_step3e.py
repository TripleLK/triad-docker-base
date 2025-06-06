#!/usr/bin/env python3
"""
Test script for Step 3e implementation - Testing short description fallback and complete extraction
"""
import os
import sys
import json
import argparse
from pprint import pprint

# Add the project root to sys.path to allow imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the Scraper class
from apps.scrapers.Scrapers import Scraper

# Sample product URLs for testing
TEST_URLS = [
    "http://www.triadscientific.com/en/products/ftir-ir-and-near-ir-spectroscopy/946/mattson-ati-genesis-series-ftir-with-software/249015",
    "http://www.triadscientific.com/en/products/hplc-systems-and-components/1095/hybrid-biocompatible-peek-coated-fused-silica-tubing-1-16-od-x-250-um-id-x-5m-length/265048",
    "http://www.triadscientific.com/en/products/gas-chromatography/1090/perkin-elmer-clarus-500-gc-gas-chromatograph-with-autosampler/256909"
]

def test_url(scraper, url):
    """Test extraction on a single URL"""
    print(f"\n\nTesting URL: {url}")
    print("=" * 80)
    
    try:
        result = scraper.scrape(url)
        
        # Print the main components
        print("\nProduct Name:")
        print("-" * 50)
        print(result.get('name', 'Not found'))
        
        print("\nShort Description:")
        print("-" * 50)
        print(result.get('short_description', 'Not found'))
        print(f"Length: {len(result.get('short_description', ''))}")
        
        print("\nImages:")
        print("-" * 50)
        imgs = result.get('imgs', [])
        print(f"Found {len(imgs)} images")
        for i, img in enumerate(imgs[:3]):  # Show first 3 images only
            print(f"{i+1}. {img}")
        
        print("\nSpecifications:")
        print("-" * 50)
        specs = result.get('specs_groups', [])
        if specs:
            print(f"Section Title: {specs[0].get('section_title', 'None')}")
            vals = specs[0].get('vals', [])
            for val in vals:
                print(f"- {val.get('spec_name', 'Unknown')}: {val.get('spec_value', 'Unknown')}")
        else:
            print("No specifications found")
        
        print("\nModels:")
        print("-" * 50)
        models = result.get('models', {})
        print(f"Found {len(models)} models")
        
        return True
    except Exception as e:
        print(f"Error scraping URL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='Test Triad Scientific scraper with fallback mechanism')
    parser.add_argument('--url', help='Specific URL to test')
    parser.add_argument('--config', default='apps/scrapers/triadscientific-yamls/mapping.yaml', 
                       help='Path to the mapping configuration file')
    args = parser.parse_args()
    
    # Initialize the scraper
    try:
        scraper = Scraper(args.config)
    except Exception as e:
        print(f"Error initializing scraper: {str(e)}")
        return
    
    if args.url:
        # Test a specific URL
        test_url(scraper, args.url)
    else:
        # Test all sample URLs
        success_count = 0
        for url in TEST_URLS:
            success = test_url(scraper, url)
            if success:
                success_count += 1
        
        print("\n\nTest Summary:")
        print(f"Tested {len(TEST_URLS)} URLs")
        print(f"Success: {success_count}")
        print(f"Failed: {len(TEST_URLS) - success_count}")

if __name__ == "__main__":
    main() 