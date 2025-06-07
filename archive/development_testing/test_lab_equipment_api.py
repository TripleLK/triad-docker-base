#!/usr/bin/env python
import requests
import json
import sys

API_TOKEN = "8b0066bea5e34a07b14a926f37e17dd8"  # Replace with your actual token
API_ENDPOINT = "http://localhost:8080/api/lab-equipment/"

def create_lab_equipment():
    """Create a sample lab equipment page"""
    data = {
        "title": "Test Microscope",
        "slug": "test-microscope",
        "short_description": "A test microscope for API validation",
        "full_description": "<p>This is a detailed description of the test microscope.</p>",
        "source_url": "https://example.com/microscope",
        "tags": ["microscope", "optical", "testing"],
        "specifications": [
            {
                "name": "Dimensions",
                "specs": [
                    {"key": "Height", "value": "15 inches"},
                    {"key": "Width", "value": "8 inches"},
                    {"key": "Depth", "value": "10 inches"}
                ]
            },
            {
                "name": "Optics",
                "specs": [
                    {"key": "Magnification", "value": "40x-1000x"},
                    {"key": "Objective Lens", "value": "4x, 10x, 40x, 100x"}
                ]
            }
        ],
        "features": [
            "LED illumination",
            "Binocular viewing head",
            "Adjustable stage"
        ],
        "models": [
            {
                "name": "Basic Model",
                "model_number": "MICRO-100",
                "specifications": [
                    {
                        "name": "Power",
                        "specs": [
                            {"key": "Power Source", "value": "110V AC"},
                            {"key": "Power Consumption", "value": "20W"}
                        ]
                    }
                ]
            },
            {
                "name": "Advanced Model",
                "model_number": "MICRO-200",
                "specifications": [
                    {
                        "name": "Power",
                        "specs": [
                            {"key": "Power Source", "value": "110-240V AC"},
                            {"key": "Power Consumption", "value": "30W"}
                        ]
                    }
                ]
            }
        ],
        "images": [
            "https://example.com/images/microscope1.jpg",
            "https://example.com/images/microscope2.jpg"
        ]
    }
    
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(API_ENDPOINT, headers=headers, data=json.dumps(data))
    
    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))
    
    return response.json()

def update_lab_equipment(slug):
    """Update an existing lab equipment page"""
    data = {
        "title": "Updated Test Microscope",
        "slug": slug,
        "short_description": "An updated test microscope",
        "full_description": "<p>This is an updated description of the test microscope.</p>",
        "features": [
            "LED illumination",
            "Binocular viewing head",
            "Adjustable stage",
            "Digital camera attachment"
        ]
    }
    
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(API_ENDPOINT, headers=headers, data=json.dumps(data))
    
    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "update":
        # Update mode - requires a slug
        if len(sys.argv) > 2:
            update_lab_equipment(sys.argv[2])
        else:
            print("Error: Please provide a slug to update")
            print("Usage: python test_lab_equipment_api.py update <slug>")
    else:
        # Create mode
        result = create_lab_equipment()
        if result.get("success") and result.get("page_slug"):
            print(f"\nTo update this page, run:")
            print(f"python test_lab_equipment_api.py update {result['page_slug']}") 