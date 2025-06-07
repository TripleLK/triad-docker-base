#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import sys

def analyze_page(url):
    print(f"Analyzing URL: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch URL: {response.status_code}")
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Check for product links with current selector
    product_links = soup.select('.product-link a')
    print(f"Product links found with '.product-link a': {len(product_links)}")
    
    # Try h3 > a selector suggested by user
    h3_links = soup.select('h3 > a')
    print(f"Product links found with 'h3 > a': {len(h3_links)}")
    if h3_links:
        print("    Examples:")
        for i, link in enumerate(h3_links[:3]):
            print(f"      {i+1}. {link.get('href')} - '{link.text.strip()}'")
    
    # Try alternative selectors
    alternative_selectors = [
        'a[href*="/product/"]',
        '.products a',
        '.product a',
        '.product-item a',
        '.card a',
        '.card-body a',
        'a.product-link',
        '.card-title a',
        'h3 a'  # Alternative way to select h3 anchors
    ]
    
    print("\nAlternative selectors to try:")
    for selector in alternative_selectors:
        links = soup.select(selector)
        print(f"  {selector}: {len(links)}")
        if len(links) > 0 and len(links) <= 10:
            # Show examples
            print("    Examples:")
            for i, link in enumerate(links[:3]):
                print(f"      {i+1}. {link.get('href')} - '{link.text.strip()}'")
    
    # Look for common container elements
    print("\nExamining container elements:")
    containers = [
        '.products',
        '.product-grid',
        '.card',
        '.product-item',
        '.product-catalog',
        '.product-list',
        '.row'
    ]
    
    for container in containers:
        elements = soup.select(container)
        print(f"  {container}: {len(elements)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # Updated URL to match the example page
        url = "https://www.airscience.com/application-category?cat=balance-enclosures"
    
    analyze_page(url) 