# Triad Scientific URL Scraper

A simple web scraper to extract product URLs from the Triad Scientific website, focusing primarily on URLs starting with "http://www.triadscientific.com/en/products".

## Prerequisites

- Python 3.6+
- Required packages:
  - requests
  - beautifulsoup4

## Installation

Ensure you have the required packages installed:

```bash
pip install -r requirements.txt
```

## Usage

Run the script from the command line:

```bash
python triad_url_scraper.py
```

The script will:
1. Start crawling from http://www.triadscientific.com/en/products
2. Find all links on each page
3. Identify product URLs (any URL containing "/en/products")
4. Save all discovered product URLs to `triad_product_urls.txt`

## Customization

You can modify the following parameters in the script:

- `PRODUCTS_URL`: The starting URL for crawling (http://www.triadscientific.com/en/products)
- `BASE_URL`: The base domain URL
- `OUTPUT_FILE`: Where to save the discovered URLs
- `max_pages` in the `crawl()` function: Maximum number of pages to process (default: 500)

## Notes

- This script uses a 1-second delay between requests to be polite to the server
- The script primarily identifies product pages by checking if the URL contains "/en/products"
- As a fallback, it also checks for product-related keywords in the URL
- URLs are saved in a sorted order for easier browsing 