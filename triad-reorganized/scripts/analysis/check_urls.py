#!/usr/bin/env python
import os
import django
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urljoin

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.base")
django.setup()

from apps.base_site.models import LabEquipmentPage

def fetch_urls(category_url):
    """
    Fetch product URLs from a category page
    """
    print(f"Fetching URLs from: {category_url}")
    response = requests.get(category_url)
    if response.status_code != 200:
        print(f"Failed to fetch URL: {category_url} (Status: {response.status_code})")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.select('h3 > a')
    
    urls = []
    for link in links:
        href = link.get('href')
        if href:
            # Make sure URL is absolute
            if not href.startswith('http'):
                if href.startswith('/'):
                    base_url = category_url.split('//', 1)[1].split('/', 1)[0]
                    href = f"https://{base_url}{href}"
                else:
                    href = urljoin(category_url, href)
                    
            urls.append(href)
    
    return urls

def analyze_urls(urls):
    """
    Analyze URL structures
    """
    print(f"\nAnalyzing {len(urls)} URLs:")
    print("-" * 50)
    
    url_structures = {}
    for url in urls:
        # Parse the URL
        parsed = urlparse(url)
        path = parsed.path
        query = parse_qs(parsed.query)
        
        # Create a template of the URL structure
        if 'brandname' in query and 'brand' in query:
            structure = f"{path}?brandname=X&brand=Y"
        elif 'brandname' in query:
            structure = f"{path}?brandname=X"
        else:
            structure = path
            
        if structure not in url_structures:
            url_structures[structure] = []
        
        url_structures[structure].append(url)
    
    # Print results
    for structure, examples in url_structures.items():
        print(f"Structure: {structure}")
        print(f"Examples ({len(examples)}):")
        for i, example in enumerate(examples[:3]):
            print(f"  {i+1}. {example}")
        if len(examples) > 3:
            print(f"  ... and {len(examples) - 3} more")
        print()
    
def check_db_urls():
    """
    Check URLs stored in the database
    """
    stored_urls = LabEquipmentPage.objects.exclude(airscience_url__isnull=True).exclude(airscience_url='').values_list('airscience_url', flat=True)
    
    print(f"\nStored URLs in Database: {len(stored_urls)}")
    print("-" * 50)
    
    if stored_urls:
        url_structures = {}
        for url in stored_urls:
            # Parse the URL
            parsed = urlparse(url)
            path = parsed.path
            query = parse_qs(parsed.query)
            
            # Create a template of the URL structure
            if 'brandname' in query and 'brand' in query:
                structure = f"{path}?brandname=X&brand=Y"
            elif 'brandname' in query:
                structure = f"{path}?brandname=X"
            else:
                structure = path
                
            if structure not in url_structures:
                url_structures[structure] = []
            
            url_structures[structure].append(url)
        
        # Print results
        for structure, examples in url_structures.items():
            print(f"Structure: {structure}")
            print(f"Examples ({len(examples)}):")
            for i, example in enumerate(examples[:3]):
                print(f"  {i+1}. {example}")
            if len(examples) > 3:
                print(f"  ... and {len(examples) - 3} more")
            print()
    else:
        print("No URLs found in database")

def test_url_matching():
    """
    Test matching URLs from website to database records
    """
    # Get URLs from category page
    urls = fetch_urls('https://www.airscience.com/application-category?cat=balance-enclosures')
    
    print("\nTesting URL matching:")
    print("-" * 50)
    
    matched = 0
    for url in urls:
        page = LabEquipmentPage.objects.filter(airscience_url=url).first()
        if page:
            print(f"URL matched: {url}")
            print(f"  Page: {page.title} (ID: {page.page_ptr_id})")
            matched += 1
        else:
            print(f"URL not matched: {url}")
            
            # Try to find similar URLs
            path = urlparse(url).path
            similar_pages = LabEquipmentPage.objects.filter(airscience_url__contains=path)
            if similar_pages:
                print(f"  Found {similar_pages.count()} similar URLs:")
                for i, page in enumerate(similar_pages[:2]):
                    print(f"    {i+1}. {page.airscience_url}")
            else:
                print("  No similar URLs found")
        print()
    
    print(f"Matched {matched} out of {len(urls)} URLs")

if __name__ == "__main__":
    # Check category page
    category_urls = {
        "Balance Enclosures": "https://www.airscience.com/application-category?cat=balance-enclosures",
        "Biological Safety Cabinets": "https://www.airscience.com/application-category?cat=biological-safety-cabinets",
        "Ductless Fume Hoods": "https://www.airscience.com/application-category?cat=ductless-fume-hoods"
    }
    
    # Pick one category to analyze
    urls = fetch_urls(category_urls["Balance Enclosures"])
    analyze_urls(urls)
    
    # Check database URLs
    check_db_urls()
    
    # Test matching
    test_url_matching() 