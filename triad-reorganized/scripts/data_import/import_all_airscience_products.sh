#!/bin/bash

# Script to import all AirScience products and tag them
# This script will:
# 1. Loop through all product URLs from application pages
# 2. Import each product with its URL
# 3. Apply tags to the imported products

# Set parent page ID (change this to your actual parent page ID)
PARENT_PAGE_ID=5

# Whether to update existing pages
UPDATE_EXISTING="--update-existing"

# Whether to skip images
SKIP_IMAGES=""

# Dry run flag (set to "--dry-run" to enable)
DRY_RUN=""

# Process command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --parent-page=*)
      PARENT_PAGE_ID="${1#*=}"
      shift
      ;;
    --skip-images)
      SKIP_IMAGES="--skip-images"
      shift
      ;;
    --dry-run)
      DRY_RUN="--dry-run"
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--parent-page=ID] [--skip-images] [--dry-run]"
      exit 1
      ;;
  esac
done

echo "=== Starting AirScience Product Import ==="
echo "Parent Page ID: $PARENT_PAGE_ID"
echo "Update Existing: Yes"
echo "Skip Images: ${SKIP_IMAGES:+Yes}"
echo "Dry Run: ${DRY_RUN:+Yes}"
echo ""

# First, extract all product URLs from application pages
echo "=== Extracting Product URLs ==="
python -c "
import yaml
import requests
from bs4 import BeautifulSoup

# Base URL for AirScience website
BASE_URL = 'https://www.airscience.com'

# Load application YAML
with open('apps/scrapers/airscience-yamls/applications.yaml', 'r') as f:
    app_config = yaml.safe_load(f)

# Extract base URL pattern and selector
url_pattern = app_config['categorized_tag_page_selector']['url_pattern']
selector = app_config['categorized_tag_page_selector']['product_links_selector']
tag_mapping = app_config['categorized_tag_page_selector']['tag_mapping']

# Collect all product URLs
all_urls = []

# Process each application
for category_value, tag_name in tag_mapping.items():
    print(f'Processing {tag_name}...')
    url = url_pattern.format(category_value=category_value)
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.select(selector)
            
            for link in links:
                href = link.get('href')
                if href:
                    # Make sure URL is absolute
                    if href.startswith('/'):
                        href = f'{BASE_URL}{href}'
                    elif not href.startswith('http'):
                        href = f'{BASE_URL}/{href}'
                        
                    if href not in all_urls:
                        all_urls.append(href)
            
            print(f'  Found {len(links)} products')
        else:
            print(f'  Failed to fetch URL: {url}')
    except Exception as e:
        print(f'  Error: {str(e)}')

# Write URLs to file
with open('product_urls.txt', 'w') as f:
    for url in all_urls:
        f.write(f'{url}\n')

print(f'\nTotal unique product URLs found: {len(all_urls)}')
print(f'URLs written to product_urls.txt')
"

# Check if product_urls.txt was created
if [ ! -f "product_urls.txt" ]; then
    echo "Error: Failed to extract product URLs"
    exit 1
fi

# Import each product
echo ""
echo "=== Importing Products ==="
while IFS= read -r url; do
    echo "Importing: $url"
    python manage.py import_airscience --url="$url" --parent-page=$PARENT_PAGE_ID $UPDATE_EXISTING $SKIP_IMAGES $DRY_RUN
    echo ""
done < "product_urls.txt"

# Process tags
echo "=== Processing Tags ==="
python manage.py import_airscience --process-tags $DRY_RUN

# Clean up
if [ -z "$DRY_RUN" ]; then
    rm product_urls.txt
fi

echo "=== Import Complete ===" 