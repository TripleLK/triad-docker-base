#!/usr/bin/env python
import os
import logging
import yaml
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import time
import re
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('triad_url_discovery')

# Constants
BASE_URL = "http://www.triadscientific.com"
YAML_DIR = Path(__file__).parent

# Default rate limiting (can be overridden in constructor)
REQUEST_DELAY = 1  # seconds between requests


class TriadUrlDiscoverer:
    """
    Class for discovering URLs on the Triad Scientific website using YAML selectors.
    """
    
    def __init__(self, base_url=BASE_URL, yaml_dir=YAML_DIR, request_delay=REQUEST_DELAY):
        self.base_url = base_url
        self.yaml_dir = yaml_dir
        self.request_delay = request_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Load selectors
        self.selectors = {
            'categories': self._load_yaml('categories.yaml'),
            'product_urls': self._load_yaml('product_urls.yaml'),
            'pagination': self._load_yaml('pagination.yaml')
        }
        
        # Cache for visited URLs to avoid duplicates
        self.visited_urls = set()
        
        # Results storage
        self.categories = []
        self.product_urls = []
    
    def _load_yaml(self, filename):
        """Load a YAML file and return its contents as a dictionary."""
        try:
            with open(os.path.join(self.yaml_dir, filename), 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return {}
    
    def _make_request(self, url):
        """Make an HTTP request with rate limiting and error handling."""
        if url in self.visited_urls:
            logger.debug(f"Skipping already visited URL: {url}")
            return None
        
        self.visited_urls.add(url)
        logger.info(f"Fetching URL: {url}")
        
        try:
            time.sleep(self.request_delay)  # Use instance-specific rate limiting
            response = self.session.get(url)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def _apply_selector(self, html, selector_type):
        """Apply a selector to HTML content and extract data."""
        if not html or selector_type not in self.selectors:
            return []
        
        selector = self.selectors[selector_type]
        soup = BeautifulSoup(html, 'html.parser')
        
        results = []
        
        # Special case for product_urls
        if selector_type == 'product_urls':
            # Find all "+ details" links
            detail_links = soup.find_all('a', string=lambda s: s and '+ details' in s)
            
            for link in detail_links:
                item = {}
                
                # Get URL
                href = link.get('href', '')
                if href:
                    item['url'] = urljoin(self.base_url, href)
                
                # Get product name - find the text node right before the link
                parent_div = link.parent
                if parent_div:
                    # Extract the text content before the link
                    product_text = ''
                    for content in parent_div.contents:
                        if content == link:
                            break
                        if isinstance(content, str):
                            product_text += content
                        elif hasattr(content, 'get_text'):
                            product_text += content.get_text()
                    
                    if product_text:
                        item['product_name'] = product_text.strip()
                
                if 'url' in item:
                    results.append(item)
            
            return results
        
        # Standard selector processing for other selector types
        if 'css_selector' in selector:
            css_selector = selector['css_selector']['selector']
            multiple = selector['css_selector'].get('multiple', False)
            
            elements = soup.select(css_selector)
            
            for element in elements:
                item = {}
                
                # Extract URL
                if 'url' in selector['css_selector'].get('extract', {}):
                    href = element.get('href', '')
                    if href:
                        # Apply transformation
                        if 'transform' in selector['css_selector'] and 'url_join' in selector['css_selector']['transform']:
                            href = urljoin(self.base_url, href)
                        item['url'] = href
                
                # Extract text content (category name, subcategory name, etc.)
                text_fields = [k for k, v in selector['css_selector'].get('extract', {}).items() 
                              if 'text_selector' in v]
                
                for field in text_fields:
                    item[field] = element.get_text(strip=True)
                
                # Apply filters if specified
                if 'filter' in selector['css_selector']:
                    if 'regex' in selector['css_selector']['filter']:
                        regex_filter = selector['css_selector']['filter']['regex']
                        pattern = regex_filter['pattern']
                        field = regex_filter['field']
                        
                        if field in item and re.match(pattern, item[field]):
                            results.append(item)
                    else:
                        results.append(item)
                else:
                    results.append(item)
            
        return results
    
    def discover_main_categories(self):
        """Discover main category URLs from the homepage."""
        logger.info("Discovering main categories...")
        html = self._make_request(self.base_url)
        if not html:
            return []
        
        categories = self._apply_selector(html, 'categories')
        self.categories = categories
        logger.info(f"Discovered {len(categories)} main categories")
        return categories
    
    def discover_product_urls(self, category_url):
        """Discover product URLs from a category page."""
        logger.info(f"Discovering product URLs for: {category_url}")
        html = self._make_request(category_url)
        if not html:
            return []
        
        products = self._apply_selector(html, 'product_urls')
        self.product_urls.extend(products)
        logger.info(f"Discovered {len(products)} products")
        
        # Check for pagination
        pagination_urls = self._apply_selector(html, 'pagination')
        
        for page in pagination_urls:
            if 'url' in page and page['url'] not in self.visited_urls:
                logger.info(f"Found pagination: {page['url']}")
                page_products = self.discover_product_urls(page['url'])
                products.extend(page_products)
        
        return products
    
    def discover_all_urls(self):
        """
        Comprehensive URL discovery process:
        1. Start with main categories
        2. For each category, discover product URLs
        """
        logger.info("Starting comprehensive URL discovery process...")
        
        # Step 1: Discover main categories
        categories = self.discover_main_categories()
        
        # Step 2: For each category, discover product URLs
        for category in categories:
            if 'url' in category:
                self.discover_product_urls(category['url'])
        
        logger.info(f"URL discovery completed. Found {len(self.product_urls)} product URLs")
        return self.product_urls
    
    def save_results(self, output_file='product_urls.txt'):
        """Save discovered product URLs to a file."""
        with open(os.path.join(self.yaml_dir, output_file), 'w') as f:
            for product in self.product_urls:
                if 'url' in product:
                    product_line = f"{product['url']}"
                    if 'product_name' in product:
                        product_line += f" | {product['product_name']}"
                    f.write(f"{product_line}\n")
        
        logger.info(f"Saved {len(self.product_urls)} product URLs to {output_file}")


if __name__ == "__main__":
    discoverer = TriadUrlDiscoverer()
    discoverer.discover_all_urls()
    discoverer.save_results() 