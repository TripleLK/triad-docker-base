import requests
import json
import logging
import os

logger = logging.getLogger(__name__)

class LabEquipmentAPIClient:
    """
    Client for the Lab Equipment API endpoints
    """
    
    def __init__(self, base_url=None, api_token=None):
        """
        Initialize the API client
        
        Args:
            base_url (str): Base URL for the API (e.g., 'http://localhost:8000')
                           If not provided, uses the API_BASE_URL environment variable
                           or defaults to localhost:8000
            api_token (str): API token for authentication
                            If not provided, uses the API_TOKEN environment variable
        """
        self.base_url = (base_url or os.getenv('API_BASE_URL', 'http://localhost:8000')).rstrip('/')
        self.api_token = api_token or os.getenv('API_TOKEN')
        
        if not self.api_token:
            logger.warning("No API token provided. API authentication will fail.")
            
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_token}'
        }
    
    def create_or_update_lab_equipment(self, data):
        """
        Create or update a lab equipment page
        
        Args:
            data (dict): Lab equipment data including title, short_description, etc.
        
        Returns:
            dict: Response from the API
        """
        endpoint = f"{self.base_url}/api/lab-equipment/"
        
        try:
            logger.info(f"Sending request to {endpoint} with data: {json.dumps(data)[:1000]}...")
            response = requests.post(
                endpoint,
                headers=self.headers,
                data=json.dumps(data)
            )
            
            # Try to parse the response body
            try:
                response_data = response.json()
            except ValueError:
                response_data = {"success": False, "error": f"Invalid JSON response: {response.text}"}
            
            # Check for HTTP errors
            if response.status_code >= 400:
                error_message = response_data.get("error", response_data.get("message", f"HTTP error {response.status_code}"))
                logger.error(f"API request failed: {error_message}")
                return {"success": False, "error": error_message}
            
            # Success case
            return response_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    return error_data
                except ValueError:
                    return {"success": False, "error": f"Request error: {str(e)}"}
            return {"success": False, "error": f"Request error: {str(e)}"}


# Example usage:
"""
from apps.scrapers.utils.api_client import LabEquipmentAPIClient

# Create client
api_client = LabEquipmentAPIClient(token="your-token-here")

# Prepare data
equipment_data = {
    "title": "Microscope Model X",
    "short_description": "High-quality microscope",
    "specifications": [
        {
            "name": "Physical",
            "specs": [
                {"key": "Weight", "value": "5 kg"}
            ]
        }
    ]
}

# Send to API
result = api_client.create_or_update_equipment(equipment_data)
print(result)
""" 