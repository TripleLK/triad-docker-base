#!/usr/bin/env python3
"""
Analyze Air Science products page to find product links

Created by: Quantum Ridge
Date: 2025-01-22
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def analyze_airscience_products():
    """Analyze the Air Science products page to find product links"""
    url = 'https://www.airscience.com/products'
    
    print(f"🔍 Analyzing: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print("\n=== All links containing 'product-category-page' ===")
        product_category_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(url, href)
            if 'product-category-page' in full_url:
                product_category_links.append(full_url)
                print(f"- {full_url}")
        
        print(f"\nFound {len(product_category_links)} product-category-page links")
        
        print("\n=== Links with 'read more' text ===")
        read_more_links = []
        for a in soup.find_all('a', href=True):
            if a.get_text(strip=True).lower() in ['read more', 'readmore']:
                href = a['href']
                full_url = urljoin(url, href)
                read_more_links.append(full_url)
                print(f"- {full_url}")
        
        print(f"\nFound {len(read_more_links)} 'read more' links")
        
        print("\n=== All links with query parameters ===")
        query_param_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(url, href)
            if '?' in full_url and 'airscience.com' in full_url:
                query_param_links.append(full_url)
                print(f"- {full_url}")
        
        print(f"\nFound {len(query_param_links)} links with query parameters")
        
        print("\n=== Product card analysis ===")
        # Look for product cards or sections
        product_sections = soup.find_all(['div', 'section'], class_=lambda x: x and ('product' in x.lower() or 'card' in x.lower()))
        print(f"Found {len(product_sections)} potential product sections")
        
        # Look for any links in product sections
        for i, section in enumerate(product_sections[:5]):  # Check first 5
            links_in_section = section.find_all('a', href=True)
            if links_in_section:
                print(f"\nProduct section {i+1} links:")
                for a in links_in_section:
                    href = a['href']
                    full_url = urljoin(url, href)
                    text = a.get_text(strip=True)[:50]
                    print(f"  - {full_url} (text: '{text}')")
        
    except Exception as e:
        print(f"❌ Error analyzing page: {e}")

if __name__ == "__main__":
    analyze_airscience_products() 