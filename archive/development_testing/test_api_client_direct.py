#!/usr/bin/env python
"""
Standalone test script for the Lab Equipment API Client.
This avoids issues with Python module naming conflicts.
"""

import os
import json
import time
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API client class (copied directly to avoid import issues)
class LabEquipmentAPIClient:
    """
    Client for the Lab Equipment API.
    """
    
    def __init__(self, base_url=None, token=None):
        self.base_url = base_url or os.getenv('API_BASE_URL', 'http://localhost:8080')
        self.token = token or os.getenv('API_TOKEN', '8b0066bea5e34a07b14a926f37e17dd8')
        
        if not self.token:
            logger.warning("No API token provided. Authentication will fail.")
        
        self.api_endpoint = f"{self.base_url}/api/lab-equipment/"
    
    def create_or_update_equipment(self, equipment_data):
        """Create or update lab equipment through the API."""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                data=json.dumps(equipment_data),
                timeout=30
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    return error_data
                except ValueError:
                    pass
            
            return {
                "success": False,
                "error": f"API request failed: {str(e)}"
            }

def create_test_equipment():
    """Create a test equipment page."""
    # Create API client
    api_client = LabEquipmentAPIClient()
    
    # Generate a unique slug with timestamp
    timestamp = int(time.time())
    
    # Prepare test data
    equipment_data = {
        "title": f"API Test Spectrometer {timestamp}",
        "slug": f"api-test-spectrometer-{timestamp}",
        "short_description": "A test spectrometer created via API",
        "full_description": "<p>This is a detailed description of the test spectrometer.</p>",
        "source_url": "https://example.com/spectrometer",
        "features": [
            "High-resolution analysis",
            "Advanced optics",
            "Digital interface",
            "Auto-calibration"
        ],
        "specifications": [
            {
                "name": "Technical",
                "specs": [
                    {"key": "Resolution", "value": "0.1 nm"},
                    {"key": "Wavelength Range", "value": "200-1100 nm"}
                ]
            }
        ],
        "models": [
            {
                "name": "Standard Edition",
                "model_number": "SPEC-1000",
                "specifications": [
                    {
                        "name": "Power",
                        "specs": [
                            {"key": "Voltage", "value": "110V"}
                        ]
                    }
                ]
            }
        ]
    }
    
    # Send request to API
    logger.info(f"Creating test equipment: {equipment_data['title']}")
    result = api_client.create_or_update_equipment(equipment_data)
    
    # Log result
    if result.get("success"):
        logger.info(f"Successfully created equipment with slug: {result.get('page_slug')}")
    else:
        logger.error(f"Failed to create equipment: {result.get('error')}")
    
    # Print full result
    print("\nAPI Response:")
    print(json.dumps(result, indent=2))
    
    # Verify the page was created by checking the database
    if result.get("success") and result.get("page_slug"):
        verify_equipment_created(result.get("page_slug"))
    
    return result

def verify_equipment_created(slug):
    """
    Verify the equipment page was actually created in the database.
    This makes a direct request to the Django site to get page details.
    """
    print("\nVerifying page creation in database...")
    
    try:
        # Make a request to the admin API to verify the page exists
        # This is a simple way to check without importing Django models
        url = f"http://localhost:8080/admin/api/v2beta/pages/?slug={slug}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("items") and len(data["items"]) > 0:
                page = data["items"][0]
                print(f"✅ Page verified! ID: {page.get('id')}, Title: {page.get('title')}")
                return True
            else:
                print(f"❌ Page with slug '{slug}' not found in database")
                return False
        else:
            print(f"❌ Failed to verify page: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error verifying page: {str(e)}")
        return False

if __name__ == "__main__":
    create_test_equipment() 