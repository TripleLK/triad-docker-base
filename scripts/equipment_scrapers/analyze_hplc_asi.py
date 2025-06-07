#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import sys
import json

def analyze_page(url, selectors_file=None):
    print(f"Analyzing URL: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch URL: {response.status_code}")
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Load selectors if provided
    selectors = []
    if selectors_file:
        try:
            with open(selectors_file, 'r') as f:
                selectors = json.load(f)
            print(f"Loaded {len(selectors)} selectors from {selectors_file}")
        except Exception as e:
            print(f"Error loading selectors: {e}")
    
    # Test provided selectors
    if selectors:
        print("\nTesting selectors:")
        for selector_obj in selectors:
            name = selector_obj.get('name', 'Unnamed')
            selector = selector_obj.get('selector', '')
            print(f"\n-- Testing '{name}' selector: {selector}")
            elements = soup.select(selector)
            print(f"   Found {len(elements)} elements")
            
            if len(elements) > 0:
                preserve_html = selector_obj.get('preserve_html', False)
                for i, element in enumerate(elements[:3]):
                    if preserve_html:
                        print(f"   Element {i+1}: {element}")
                    else:
                        print(f"   Element {i+1}: {element.get_text().strip()[:100]}")
                if len(elements) > 3:
                    print(f"   ... and {len(elements) - 3} more elements")
    
    # Test some common product elements
    print("\nCommon product elements:")
    common_selectors = {
        "Product title": [".product-title", "h1", ".product-name", ".product-heading"],
        "Product price": [".price", ".product-price", ".price-value"],
        "Product description": [".product-description", ".product-details", ".description"],
        "Product images": [".product-images", ".product-gallery", ".product-image", "img.mainImg"],
        "Add to cart button": [".add-to-cart", ".button-cart", "button[type='submit']"],
        "Product specs": [".product-specifications", ".specs", ".specifications", ".product-specs"]
    }
    
    for element_name, element_selectors in common_selectors.items():
        print(f"\n  {element_name}:")
        for selector in element_selectors:
            elements = soup.select(selector)
            print(f"    {selector}: {len(elements)} elements")
            if len(elements) > 0 and len(elements) <= 3:
                for i, element in enumerate(elements):
                    print(f"      Element {i+1} text: {element.get_text().strip()[:100]}")

    # Suggested selectors based on analysis
    print("\nSuggested selectors for HPLC-ASI:")
    
    # Product information selector
    product_info = soup.select(".product-main")
    if product_info:
        print(f"  Product main info (.product-main): {len(product_info)} elements")
    
    # Product details
    product_details = soup.select(".productView-details")
    if product_details:
        print(f"  Product details (.productView-details): {len(product_details)} elements")

    # Product description
    product_description = soup.select(".productView-description")
    if product_description:
        print(f"  Product description (.productView-description): {len(product_description)} elements")
    
    # Product images
    product_images = soup.select(".productView-images")
    if product_images:
        print(f"  Product images (.productView-images): {len(product_images)} elements")

if __name__ == "__main__":
    selectors_file = None
    
    if len(sys.argv) > 2:
        url = sys.argv[1]
        selectors_file = sys.argv[2]
    elif len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://www.hplc-asi.com/binary-dynamic-mixer-assembly/"
    
    analyze_page(url, selectors_file) 