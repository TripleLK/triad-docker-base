#!/bin/bash

# Set up error handling
set -e

# Navigate to the script directory
cd "$(dirname "$0")"

echo "Checking for dependencies..."
# Install dependencies if needed
pip install -r ../requirements.txt

echo "Starting Triad Scientific URL scraper..."
# Run the scraper with improved settings for better coverage
python triad_url_scraper.py --limit 10 --max-pages 150 --max-depth 4

echo "Scraping completed."
echo "Results saved to triad_product_urls.txt"
echo "Found $(wc -l < triad_product_urls.txt) product URLs."
echo "To process these URLs through the AI system, run:"
echo "./triad_queue_processor.sh load triad_product_urls.txt" 