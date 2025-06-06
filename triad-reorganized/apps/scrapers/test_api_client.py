#!/usr/bin/env python
"""
Test script for the Lab Equipment API Client.
Can be used as a standalone script or imported in Django.

Usage:
    python test_api_client.py [--token TOKEN] [--url URL]
"""

import argparse
import sys
import os
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add Django setup for running directly
if __name__ == "__main__":
    # Add the parent directory to sys.path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    
    # Set up Django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django
    django.setup()

# Import the API client
from apps.scrapers.utils.api_client import LabEquipmentAPIClient

def create_test_equipment(api_client, make_unique=True):
    """
    Create a test equipment entry using the API client.
    
    Args:
        api_client: LabEquipmentAPIClient instance
        make_unique: Add a timestamp to make the entry unique
    
    Returns:
        API response dict
    """
    import time
    
    # Add a timestamp to make entries unique when testing
    suffix = f"-{int(time.time())}" if make_unique else ""
    
    # Sample data that follows the API schema
    equipment_data = {
        "title": f"Test Centrifuge{suffix}",
        "slug": f"test-centrifuge{suffix}",
        "short_description": "A test centrifuge for API validation",
        "full_description": "<p>This is a test entry created by the API client test script.</p>",
        "source_url": "https://example.com/centrifuge",
        "tags": ["centrifuge", "lab equipment", "testing"],
        "specifications": [
            {
                "name": "Dimensions",
                "specs": [
                    {"key": "Height", "value": "24 inches"},
                    {"key": "Width", "value": "18 inches"},
                    {"key": "Depth", "value": "18 inches"}
                ]
            },
            {
                "name": "Performance",
                "specs": [
                    {"key": "Max Speed", "value": "15,000 RPM"},
                    {"key": "Capacity", "value": "24 tubes"}
                ]
            }
        ],
        "features": [
            "Digital speed control",
            "Automatic lid lock",
            "Overspeed protection"
        ],
        "models": [
            {
                "name": "Standard Model",
                "model_number": "CENT-100",
                "specifications": [
                    {
                        "name": "Power",
                        "specs": [
                            {"key": "Power Source", "value": "110V AC"},
                            {"key": "Power Consumption", "value": "600W"}
                        ]
                    }
                ]
            },
            {
                "name": "High Capacity Model",
                "model_number": "CENT-200",
                "specifications": [
                    {
                        "name": "Power",
                        "specs": [
                            {"key": "Power Source", "value": "110-240V AC"},
                            {"key": "Power Consumption", "value": "800W"}
                        ]
                    },
                    {
                        "name": "Performance",
                        "specs": [
                            {"key": "Capacity", "value": "48 tubes"}
                        ]
                    }
                ]
            }
        ],
        "images": [
            "https://example.com/images/centrifuge1.jpg",
            "https://example.com/images/centrifuge2.jpg"
        ]
    }
    
    logger.info(f"Creating test equipment: {equipment_data['title']}")
    result = api_client.create_or_update_equipment(equipment_data)
    
    if result.get("success"):
        logger.info(f"Successfully created equipment with slug: {result.get('page_slug')}")
    else:
        logger.error(f"Failed to create equipment: {result.get('error')}")
    
    return result

def update_test_equipment(api_client, slug):
    """
    Update a test equipment entry using the API client.
    
    Args:
        api_client: LabEquipmentAPIClient instance
        slug: Slug of the equipment to update
    
    Returns:
        API response dict
    """
    # Simpler update data
    update_data = {
        "slug": slug,
        "title": f"Updated {slug}",
        "short_description": "This entry was updated via the API client test script",
        "features": [
            "Digital speed control",
            "Automatic lid lock",
            "Overspeed protection",
            "NEW FEATURE: Temperature monitoring"
        ]
    }
    
    logger.info(f"Updating equipment with slug: {slug}")
    result = api_client.create_or_update_equipment(update_data)
    
    if result.get("success"):
        logger.info(f"Successfully updated equipment with slug: {result.get('page_slug')}")
    else:
        logger.error(f"Failed to update equipment: {result.get('error')}")
    
    return result

def main():
    parser = argparse.ArgumentParser(description="Test the Lab Equipment API Client")
    parser.add_argument("--token", help="API token to use (overrides environment variable)", 
                        default="8b0066bea5e34a07b14a926f37e17dd8")
    parser.add_argument("--url", help="Base URL for the API (defaults to http://localhost:8000)",
                        default="http://localhost:8080")
    parser.add_argument("--update", help="Update the equipment with this slug instead of creating new")
    
    args = parser.parse_args()
    
    # Create the API client
    api_client = LabEquipmentAPIClient(
        base_url=args.url,
        token=args.token
    )
    
    if args.update:
        # Update mode
        result = update_test_equipment(api_client, args.update)
    else:
        # Create mode
        result = create_test_equipment(api_client)
        # If successful, print how to update this equipment
        if result.get("success") and result.get("page_slug"):
            print(f"\nTo update this equipment, run:")
            print(f"python test_api_client.py --update {result['page_slug']}")
    
    # Print the full result
    print("\nAPI Response:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main() 