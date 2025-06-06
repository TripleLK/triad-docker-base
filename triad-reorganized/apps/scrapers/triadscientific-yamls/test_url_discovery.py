#!/usr/bin/env python
import sys
import os
import logging
from url_discovery import TriadUrlDiscoverer

# Configure logging to show more details
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Create a URL discoverer instance
discoverer = TriadUrlDiscoverer()

# Test mode options
TEST_MODES = {
    'main': 'Test main category extraction only',
    'products': 'Test product URL extraction for one category',
    'single': 'Test full workflow for a single category',
    'all': 'Run complete URL discovery process'
}

def print_usage():
    print("Usage: python test_url_discovery.py [mode]")
    print("\nAvailable modes:")
    for mode, desc in TEST_MODES.items():
        print(f"  {mode}: {desc}")

def main():
    # Check command line arguments
    if len(sys.argv) < 2 or sys.argv[1] not in TEST_MODES:
        print_usage()
        return
    
    mode = sys.argv[1]
    print(f"Running test in '{mode}' mode: {TEST_MODES[mode]}")
    
    if mode == 'main':
        # Test main category extraction
        categories = discoverer.discover_main_categories()
        
        print(f"\nDiscovered {len(categories)} main categories:")
        for i, category in enumerate(categories):
            if 'url' in category and 'category_name' in category:
                print(f"{i+1}. {category['category_name']}: {category['url']}")
    
    elif mode == 'products':
        # Test product URL extraction for a single category
        categories = discoverer.discover_main_categories()
        if categories:
            # Use the first category for testing
            category = categories[0]
            print(f"\nTesting product URL extraction for category: {category.get('category_name', 'Unknown')}")
            products = discoverer.discover_product_urls(category['url'])
            
            print(f"\nDiscovered {len(products)} products:")
            for i, product in enumerate(products[:10]):  # Show first 10 only
                if 'url' in product:
                    print(f"{i+1}. {product.get('product_name', 'Unknown')}: {product['url']}")
            
            if len(products) > 10:
                print(f"... and {len(products) - 10} more")
    
    elif mode == 'single':
        # Test the full workflow for a single category
        categories = discoverer.discover_main_categories()
        if not categories:
            print("No categories found!")
            return
            
        # Use the first category for testing
        category = categories[0]
        print(f"\nTesting full workflow for category: {category.get('category_name', 'Unknown')}")
        
        # Get products from the category
        products = discoverer.discover_product_urls(category['url'])
        print(f"Found {len(products)} products in category {category.get('category_name', 'Unknown')}")
        
        print(f"\nTotal products discovered: {len(products)}")
    
    elif mode == 'all':
        # Run the full discovery process
        print("Starting full URL discovery process...")
        products = discoverer.discover_all_urls()
        
        # Save to a test file
        test_output = 'test_product_urls.txt'
        discoverer.save_results(test_output)
        print(f"\nDiscovered {len(products)} products and saved to {test_output}")

if __name__ == "__main__":
    main() 