#!/usr/bin/env python
import requests
from bs4 import BeautifulSoup
import re
import os
import sys
import traceback  # Add traceback import
from urllib.parse import urljoin, urlparse, urlunparse
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG level for more detailed logs
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Base URL of the website
BASE_URL = "http://www.triadscientific.com"
PRODUCTS_URL = "http://www.triadscientific.com/en/products"

# Output file for storing URLs
OUTPUT_FILE = "triad_product_urls.txt"

# Set to keep track of visited URLs
visited_urls = set()
# Set to store product URLs
product_urls = set()

def normalize_url(url):
    """
    Normalize a URL by removing fragments (anchors) and query parameters.
    This helps avoid processing the same page multiple times.
    """
    parsed = urlparse(url)
    # Remove fragments and query parameters
    clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
    return clean_url

def is_product_url(url):
    """
    Check if a URL is a product page.
    """
    # Print the URL being checked to see what patterns we're dealing with
    logger.debug(f"Checking if URL is a product URL: {url}")
    
    # Product URLs typically have the pattern /en/products/category/category-id/product-name/product-id
    url_path = urlparse(url).path
    
    # Must start with /en/products
    if not url_path.startswith('/en/products'):
        logger.debug(f"URL rejected: Does not start with /en/products: {url}")
        return False
    
    # Must end with a numeric ID for individual product pages
    if re.search(r'/\d+$', url_path):
        # Count the number of path segments (should be 6 for product detail pages)
        segments = [s for s in url_path.split('/') if s]
        if len(segments) >= 5:  # en/products/category/[category_id]/product-name/[product_id]
            logger.debug(f"URL accepted as product URL: {url}, segments: {segments}")
            return True
    
    # Add more flexible patterns that might match product URLs
    # Sometimes products have URLs like /en/products/category/product-name
    if '/en/products/' in url_path and len(url_path.split('/')) >= 4:
        logger.debug(f"URL might be a product category or listing: {url}")
        
    logger.debug(f"URL rejected as product URL: {url}")
    return False

def get_all_links(url):
    """Extract all links from a webpage."""
    try:
        normalized_url = normalize_url(url)
        if normalized_url in visited_urls and url != PRODUCTS_URL:  # Skip check for the first URL
            logger.debug(f"URL already visited (after normalization): {url}")
            return []
            
        logger.info(f"Fetching: {url}")
        
        # Debug: print before making the request
        logger.debug(f"Attempting to fetch URL: {url}")
        
        try:
            response = requests.get(url, timeout=30)
            logger.debug(f"Received response with status code: {response.status_code}")
        except Exception as req_error:
            logger.error(f"Error during HTTP request: {str(req_error)}")
            return []
            
        response.raise_for_status()
        
        # Debug: print response content length
        content_length = len(response.text)
        logger.debug(f"Response content length: {content_length} bytes")
        
        if content_length == 0:
            logger.error(f"Empty response received for URL: {url}")
            return []
        
        # Save the HTML content to a file for debugging
        if 'products' in url:
            debug_filename = f"debug_page_{int(time.time())}.html"
            with open(debug_filename, 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.debug(f"Saved HTML content to {debug_filename}")
        
        # Log some information about the response
        logger.debug(f"Response status: {response.status_code}, content length: {len(response.text)}")
        logger.debug(f"Response headers: {response.headers}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        
        # Log all links found on the page
        all_links = soup.find_all('a', href=True)
        logger.debug(f"Found {len(all_links)} links on page {url}")
        
        # Debug: print the first few links
        for i, a_tag in enumerate(all_links[:5]):
            logger.debug(f"Sample link {i}: {a_tag['href']}")
        
        for a_tag in all_links:
            href = a_tag['href']
            
            # Skip empty links, javascript, and mail links
            if not href or href.startswith('javascript:') or href.startswith('mailto:'):
                continue
                
            # Convert relative URLs to absolute
            absolute_url = urljoin(url, href)
            
            # Skip URLs with fragments (like #thumbcarousel)
            if '#' in absolute_url:
                absolute_url = absolute_url.split('#')[0]
                
            # Normalize the URL to avoid duplicates due to fragments/query params
            normalized_url = normalize_url(absolute_url)
            
            # Only consider URLs from the same domain
            if urlparse(normalized_url).netloc == urlparse(BASE_URL).netloc:
                # Add to links for crawling
                if normalized_url not in visited_urls:
                    links.append(normalized_url)
                    logger.debug(f"Adding link for crawling: {normalized_url}")
                
                # Check if this might be a product URL
                if is_product_url(normalized_url) and normalized_url not in product_urls:
                    product_urls.add(normalized_url)
                    logger.info(f"Found product URL: {normalized_url}")
        
        logger.debug(f"Returning {len(links)} links for further crawling")
        return links
    
    except Exception as e:
        logger.error(f"Error fetching URL: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []

def crawl(start_url, max_pages=100, max_depth=3):
    """Crawl the website starting from start_url with depth limiting."""
    queue = [(start_url, 0)]  # (url, depth)
    page_count = 0
    
    # Clear the visited_urls set for a fresh start
    visited_urls.clear()
    
    while queue and page_count < max_pages:
        url, depth = queue.pop(0)
        normalized_url = normalize_url(url)
        
        if normalized_url in visited_urls and url != start_url:  # Allow processing the start URL
            logger.debug(f"Skipping already visited URL: {url}")
            continue
            
        logger.debug(f"Processing URL: {url} at depth {depth}")
        visited_urls.add(normalized_url)
        page_count += 1
        
        logger.info(f"Processed {page_count}/{max_pages} pages, depth {depth}, found {len(product_urls)} product URLs")
        
        # Get all links from the current page
        links = get_all_links(url)
        logger.debug(f"Found {len(links)} links on page {url}")
        
        # Only continue crawling if we haven't reached max depth
        if depth < max_depth:
            # Prioritize URLs that look like product categories
            product_category_links = []
            other_links = []
            
            for link in links:
                if normalize_url(link) not in visited_urls:
                    if '/en/products/' in link and normalize_url(link) not in visited_urls:
                        product_category_links.append((link, depth + 1))
                        logger.debug(f"Added product category link: {link}")
                    else:
                        other_links.append((link, depth + 1))
            
            # Add product category links first, then other links
            queue = product_category_links + other_links + queue
            logger.debug(f"Queue size: {len(queue)}")
        
        # Polite crawling - add a small delay
        time.sleep(0.5)  # reduced delay to speed up crawling

def save_urls(limit=None):
    """Save the collected product URLs to a file, optionally limiting the count."""
    urls_to_save = sorted(product_urls)
    if limit and limit > 0 and len(urls_to_save) > limit:
        urls_to_save = urls_to_save[:limit]
    
    with open(OUTPUT_FILE, 'w') as f:
        for url in urls_to_save:
            f.write(f"{url}\n")
    
    logger.info(f"Saved {len(urls_to_save)} product URLs to {OUTPUT_FILE}")

def main():
    logger.info("Starting Triad Scientific URL scraper")
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Scrape product URLs from Triad Scientific website')
    parser.add_argument('--limit', type=int, default=10, 
                        help='Limit the number of URLs to save (default: 10)')
    parser.add_argument('--max-pages', type=int, default=100, 
                        help='Maximum number of pages to crawl (default: 100)')
    parser.add_argument('--max-depth', type=int, default=3, 
                        help='Maximum crawl depth (default: 3)')
    parser.add_argument('--test-fetch', action='store_true',
                        help='Just test fetching the products page')
    args = parser.parse_args()
    
    # Test fetching if requested
    if args.test_fetch:
        logger.info("Testing fetch of products page")
        get_all_links(PRODUCTS_URL)
        return
    
    # Start crawling from the products URL
    try:
        crawl(PRODUCTS_URL, max_pages=args.max_pages, max_depth=args.max_depth)
    except KeyboardInterrupt:
        logger.info("Crawling interrupted by user")
    except Exception as e:
        import traceback
        logger.error(f"Error during crawling: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Save the results, limiting if requested
    save_urls(args.limit)
    
    logger.info("Scraping completed")

if __name__ == "__main__":
    main() 