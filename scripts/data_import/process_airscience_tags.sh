#!/bin/bash

# Default values
DRY_RUN=0
VERBOSE=0
CATEGORIES_ONLY=0
APPLICATIONS_ONLY=0

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    
    case $key in
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --verbose|-v)
            VERBOSE=1
            shift
            ;;
        --categories-only)
            CATEGORIES_ONLY=1
            shift
            ;;
        --applications-only)
            APPLICATIONS_ONLY=1
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Process AirScience tags for products"
            echo
            echo "Options:"
            echo "  --dry-run            Perform a dry run without applying any changes"
            echo "  --verbose, -v        Show more detailed output"
            echo "  --categories-only    Only process product category tags"
            echo "  --applications-only  Only process product application tags"
            echo "  --help, -h           Display this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $key"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build command
CMD="python manage.py import_airscience --tags-only"

# Add options based on flags
if [ $DRY_RUN -eq 1 ]; then
    CMD="$CMD --dry-run"
fi

if [ $VERBOSE -eq 1 ]; then
    CMD="$CMD -v 2"
else
    CMD="$CMD -v 1"
fi

if [ $CATEGORIES_ONLY -eq 1 ]; then
    CMD="$CMD --categories-only"
fi

if [ $APPLICATIONS_ONLY -eq 1 ]; then
    CMD="$CMD --applications-only"
fi

echo "Running: $CMD"
eval $CMD 