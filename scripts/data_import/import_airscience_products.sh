#!/bin/bash

# Script to run the AirScience product importer
# This script helps with common command configurations

# Default settings
PARENT_PAGE_ID=2  # Change this to your actual parent page ID
UPDATE_EXISTING=false
SKIP_IMAGES=false
DRY_RUN=false
VERBOSE=false
URL="https://www.airscience.com/product-category-page?brandname=purair-advanced-ductless-fume-hoods&brand=9"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --parent-page=*)
      PARENT_PAGE_ID="${1#*=}"
      shift
      ;;
    --update-existing)
      UPDATE_EXISTING=true
      shift
      ;;
    --skip-images)
      SKIP_IMAGES=true
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --verbose)
      VERBOSE=true
      shift
      ;;
    --url=*)
      URL="${1#*=}"
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  --parent-page=ID        Set the parent page ID (default: $PARENT_PAGE_ID)"
      echo "  --update-existing       Update existing pages instead of creating new ones"
      echo "  --skip-images           Skip downloading images"
      echo "  --dry-run               Perform a dry run without committing changes"
      echo "  --verbose               Show more detailed output"
      echo "  --url=URL               Set the URL to scrape"
      echo "  --help                  Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Build the command
CMD="python manage.py import_airscience --parent-page=$PARENT_PAGE_ID --url=\"$URL\""

if $UPDATE_EXISTING; then
  CMD="$CMD --update-existing"
fi

if $SKIP_IMAGES; then
  CMD="$CMD --skip-images"
fi

if $DRY_RUN; then
  CMD="$CMD --dry-run"
fi

if $VERBOSE; then
  CMD="$CMD -v 2"
fi

# Print the command
echo "Running command: $CMD"

# Execute the command
eval $CMD 