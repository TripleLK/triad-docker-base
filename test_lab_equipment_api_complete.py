#!/usr/bin/env python3
"""
Comprehensive test script for Lab Equipment API v2.

Tests all endpoints:
- System endpoints (health, stats, auth, test)  
- Equipment CRUD operations
- Models, accessories, tags
- Search and filtering
- Bulk operations
- Rate limiting

Created by: Noble Harbor
Date: 2025-01-19
Project: Triad Docker Base
"""

import requests
import json
import time
import sys
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/v2/"
API_TOKEN = None  # Will be set after authentication

# Test data
TEST_USER = {
    "username": "testuser",
    "password": "testpass123"
}

SAMPLE_EQUIPMENT = {
    "title": "Test Microscope API v2",
    "short_description": "A high-quality test microscope for API testing",
    "full_description": "<p>This is a comprehensive test microscope with advanced features for API validation.</p>",
    "source_type": "new",
    "data_completeness": 0.95,
    "specification_confidence": "high",
    "needs_review": False,
    "specifications": [
        {
            "name": "Optics",
            "specs": [
                {"key": "Magnification", "value": "40x-1000x"},
                {"key": "Objective Lenses", "value": "4"}
            ]
        },
        {
            "name": "Dimensions",
            "specs": [
                {"key": "Height", "value": "45 cm"},
                {"key": "Weight", "value": "12 kg"}
            ]
        }
    ],
    "models_data": [
        {
            "name": "Basic Model",
            "model_number": "TEST-100",
            "specifications": [
                {
                    "name": "Power",
                    "specs": [
                        {"key": "Power Source", "value": "110V AC"},
                        {"key": "Power Consumption", "value": "25W"}
                    ]
                }
            ]
        }
    ],
    "features_data": [
        "LED Illumination",
        "Digital Camera Ready",
        "Ergonomic Design"
    ]
}

BULK_EQUIPMENT = {
    "equipment_list": [
        {
            "title": "Bulk Test Equipment 1",
            "short_description": "First bulk test equipment",
            "source_type": "used",
            "data_completeness": 0.8
        },
        {
            "title": "Bulk Test Equipment 2", 
            "short_description": "Second bulk test equipment",
            "source_type": "refurbished",
            "data_completeness": 0.9
        }
    ]
}


class APITester:
    """Comprehensive API tester for Lab Equipment API v2."""
    
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        self.created_equipment_ids = []
    
    def log(self, message, level="INFO"):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def assert_response(self, response, expected_status, test_name, check_json=True):
        """Assert response status and track results."""
        try:
            if response.status_code == expected_status:
                self.test_results["passed"] += 1
                self.log(f"✅ {test_name} - Status: {response.status_code}")
                if check_json:
                    return response.json()
                return response
            else:
                self.test_results["failed"] += 1
                error_msg = f"❌ {test_name} - Expected: {expected_status}, Got: {response.status_code}"
                self.log(error_msg, "ERROR")
                try:
                    error_detail = response.json()
                    self.log(f"Response: {json.dumps(error_detail, indent=2)}", "ERROR")
                except:
                    self.log(f"Response text: {response.text}", "ERROR")
                self.test_results["errors"].append(error_msg)
                return None
        except Exception as e:
            self.test_results["failed"] += 1
            error_msg = f"❌ {test_name} - Exception: {str(e)}"
            self.log(error_msg, "ERROR")
            self.test_results["errors"].append(error_msg)
            return None
    
    def get_headers(self, include_auth=True):
        """Get request headers with optional authentication."""
        headers = {"Content-Type": "application/json"}
        if include_auth and self.token:
            headers["Authorization"] = f"Token {self.token}"
        return headers
    
    def test_system_endpoints(self):
        """Test all system endpoints."""
        self.log("=" * 50)
        self.log("TESTING SYSTEM ENDPOINTS")
        self.log("=" * 50)
        
        # Test health check
        response = self.session.get(f"{self.base_url}health/")
        data = self.assert_response(response, 200, "Health Check")
        if data:
            self.log(f"System Status: {data.get('status', 'unknown')}")
        
        # Test authentication
        auth_data = {
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        }
        response = self.session.post(
            f"{self.base_url}auth/token/",
            json=auth_data,
            headers={"Content-Type": "application/json"}
        )
        data = self.assert_response(response, 200, "Token Authentication")
        if data:
            self.token = data.get("token")
            self.log(f"Token obtained: {self.token[:20]}...")
        
        # Test stats endpoint (requires auth)
        response = self.session.get(
            f"{self.base_url}stats/",
            headers=self.get_headers()
        )
        data = self.assert_response(response, 200, "System Stats")
        if data:
            self.log(f"Total equipment: {data.get('equipment', {}).get('total_equipment', 0)}")
        
        # Test endpoint
        response = self.session.get(f"{self.base_url}test/")
        data = self.assert_response(response, 200, "Test Endpoint GET")
        
        response = self.session.post(
            f"{self.base_url}test/",
            json={"test": "data"},
            headers=self.get_headers(include_auth=False)
        )
        self.assert_response(response, 200, "Test Endpoint POST")
    
    def test_equipment_crud(self):
        """Test equipment CRUD operations."""
        self.log("=" * 50)
        self.log("TESTING EQUIPMENT CRUD OPERATIONS")
        self.log("=" * 50)
        
        # Create equipment
        response = self.session.post(
            f"{self.base_url}equipment/",
            json=SAMPLE_EQUIPMENT,
            headers=self.get_headers()
        )
        data = self.assert_response(response, 201, "Create Equipment")
        equipment_id = None
        if data:
            equipment_id = data.get("page_ptr_id")
            self.created_equipment_ids.append(equipment_id)
            self.log(f"Created equipment ID: {equipment_id}")
        
        # List equipment
        response = self.session.get(
            f"{self.base_url}equipment/",
            headers=self.get_headers()
        )
        data = self.assert_response(response, 200, "List Equipment")
        if data:
            self.log(f"Total equipment count: {data.get('count', 0)}")
        
        # Get equipment detail
        if equipment_id:
            response = self.session.get(
                f"{self.base_url}equipment/{equipment_id}/",
                headers=self.get_headers()
            )
            data = self.assert_response(response, 200, "Get Equipment Detail")
            if data:
                self.log(f"Equipment title: {data.get('title', 'Unknown')}")
                self.log(f"Models count: {len(data.get('models', []))}")
                self.log(f"Features count: {len(data.get('features', []))}")
        
        # Update equipment
        if equipment_id:
            update_data = {
                "short_description": "Updated description for API test",
                "data_completeness": 0.98
            }
            response = self.session.patch(
                f"{self.base_url}equipment/{equipment_id}/",
                json=update_data,
                headers=self.get_headers()
            )
            self.assert_response(response, 200, "Update Equipment")
    
    def test_search_and_filtering(self):
        """Test search and filtering capabilities."""
        self.log("=" * 50) 
        self.log("TESTING SEARCH AND FILTERING")
        self.log("=" * 50)
        
        # Basic search
        response = self.session.get(
            f"{self.base_url}equipment/?search=microscope",
            headers=self.get_headers()
        )
        data = self.assert_response(response, 200, "Basic Search")
        if data:
            self.log(f"Search results: {data.get('count', 0)} items")
        
        # Filter by source type
        response = self.session.get(
            f"{self.base_url}equipment/?source_type=new",
            headers=self.get_headers()
        )
        data = self.assert_response(response, 200, "Filter by Source Type")
        if data:
            self.log(f"New equipment: {data.get('count', 0)} items")
        
        # Advanced search endpoint
        response = self.session.get(
            f"{self.base_url}equipment/search/?q=test&min_completeness=0.9",
            headers=self.get_headers()
        )
        data = self.assert_response(response, 200, "Advanced Search")
        if data:
            self.log(f"Advanced search results: {len(data)} items")
        
        # Related equipment
        if self.created_equipment_ids:
            equipment_id = self.created_equipment_ids[0]
            response = self.session.get(
                f"{self.base_url}equipment/{equipment_id}/related/",
                headers=self.get_headers()
            )
            data = self.assert_response(response, 200, "Related Equipment")
            if data:
                self.log(f"Related by tags: {len(data.get('related_by_tags', []))}")
                self.log(f"Related by specs: {len(data.get('related_by_specs', []))}")
    
    def test_bulk_operations(self):
        """Test bulk operations."""
        self.log("=" * 50)
        self.log("TESTING BULK OPERATIONS")
        self.log("=" * 50)
        
        # Bulk create
        response = self.session.post(
            f"{self.base_url}equipment/bulk-create/",
            json=BULK_EQUIPMENT,
            headers=self.get_headers()
        )
        data = self.assert_response(response, 201, "Bulk Create Equipment")
        if data:
            self.log(f"Bulk created: {data.get('total_created', 0)} items")
            self.log(f"Bulk errors: {data.get('total_errors', 0)} items")
            
            # Store created IDs for cleanup
            for page in data.get('created_pages', []):
                if page.get('page_ptr_id'):
                    self.created_equipment_ids.append(page['page_ptr_id'])
        
        # Bulk update
        if len(self.created_equipment_ids) >= 2:
            update_data = {
                "updates": [
                    {
                        "page_ptr_id": self.created_equipment_ids[0],
                        "data": {"data_completeness": 0.95}
                    },
                    {
                        "page_ptr_id": self.created_equipment_ids[1], 
                        "data": {"data_completeness": 0.92}
                    }
                ]
            }
            response = self.session.patch(
                f"{self.base_url}equipment/bulk-update/",
                json=update_data,
                headers=self.get_headers()
            )
            data = self.assert_response(response, 200, "Bulk Update Equipment")
            if data:
                self.log(f"Bulk updated: {data.get('total_updated', 0)} items")
    
    def test_other_endpoints(self):
        """Test models, accessories, tags, and cart endpoints."""
        self.log("=" * 50)
        self.log("TESTING OTHER ENDPOINTS")
        self.log("=" * 50)
        
        # Test models endpoint
        response = self.session.get(
            f"{self.base_url}models/",
            headers=self.get_headers()
        )
        data = self.assert_response(response, 200, "List Equipment Models")
        if data:
            self.log(f"Total models: {data.get('count', 0)}")
        
        # Test accessories endpoint
        response = self.session.get(
            f"{self.base_url}accessories/",
            headers=self.get_headers()
        )
        data = self.assert_response(response, 200, "List Accessories")
        if data:
            self.log(f"Total accessories: {data.get('count', 0)}")
        
        # Test tags endpoint
        response = self.session.get(
            f"{self.base_url}tags/",
            headers=self.get_headers()
        )
        data = self.assert_response(response, 200, "List Tags")
        if data:
            self.log(f"Total tags: {data.get('count', 0)}")
        
        # Test tag categories
        response = self.session.get(
            f"{self.base_url}tags/categories/",
            headers=self.get_headers()
        )
        data = self.assert_response(response, 200, "List Tag Categories")
        if data:
            self.log(f"Tag categories: {data.get('categories', [])}")
        
        # Test cart endpoint
        response = self.session.get(
            f"{self.base_url}cart/",
            headers=self.get_headers()
        )
        data = self.assert_response(response, 200, "List Cart Items")
        if data:
            self.log(f"Cart items: {data.get('count', 0)}")
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        self.log("=" * 50)
        self.log("TESTING RATE LIMITING")
        self.log("=" * 50)
        
        # Make several rapid requests to test throttling
        # Note: In production, you'd need to make many more requests to hit limits
        self.log("Making rapid requests to test throttling...")
        
        for i in range(5):
            response = self.session.get(
                f"{self.base_url}equipment/",
                headers=self.get_headers()
            )
            if response.status_code == 429:
                self.log("✅ Rate limiting working - got 429 status")
                self.test_results["passed"] += 1
                return
            time.sleep(0.1)  # Small delay between requests
        
        self.log("ℹ️  Rate limiting not triggered (normal for test environment)")
    
    def test_permissions(self):
        """Test permission system."""
        self.log("=" * 50)
        self.log("TESTING PERMISSIONS")
        self.log("=" * 50)
        
        # Test unauthorized access
        response = self.session.get(f"{self.base_url}equipment/")
        self.assert_response(response, 401, "Unauthorized Access")
        
        # Test authorized access (already covered in other tests)
        response = self.session.get(
            f"{self.base_url}equipment/",
            headers=self.get_headers()
        )
        self.assert_response(response, 200, "Authorized Access")
    
    def cleanup(self):
        """Clean up created test data."""
        self.log("=" * 50)
        self.log("CLEANING UP TEST DATA")
        self.log("=" * 50)
        
        for equipment_id in self.created_equipment_ids:
            try:
                response = self.session.delete(
                    f"{self.base_url}equipment/{equipment_id}/",
                    headers=self.get_headers()
                )
                if response.status_code in [204, 404]:
                    self.log(f"✅ Deleted equipment {equipment_id}")
                else:
                    self.log(f"⚠️  Could not delete equipment {equipment_id} - Status: {response.status_code}")
            except Exception as e:
                self.log(f"❌ Error deleting equipment {equipment_id}: {e}")
    
    def run_all_tests(self):
        """Run complete test suite."""
        self.log("🚀 Starting Lab Equipment API v2 Complete Test Suite")
        self.log(f"Base URL: {self.base_url}")
        
        try:
            self.test_system_endpoints()
            
            if self.token:  # Only run auth-required tests if we have a token
                self.test_equipment_crud()
                self.test_search_and_filtering()
                self.test_bulk_operations()
                self.test_other_endpoints()
                self.test_rate_limiting()
                self.test_permissions()
            else:
                self.log("❌ No authentication token obtained - skipping auth-required tests")
            
        except KeyboardInterrupt:
            self.log("🛑 Tests interrupted by user")
        except Exception as e:
            self.log(f"❌ Unexpected error: {e}")
        finally:
            if self.created_equipment_ids:
                self.cleanup()
            self.print_results()
    
    def print_results(self):
        """Print test results summary."""
        self.log("=" * 50)
        self.log("TEST RESULTS SUMMARY")
        self.log("=" * 50)
        
        total_tests = self.test_results["passed"] + self.test_results["failed"]
        pass_rate = (self.test_results["passed"] / total_tests * 100) if total_tests > 0 else 0
        
        self.log(f"Total Tests: {total_tests}")
        self.log(f"Passed: {self.test_results['passed']}")
        self.log(f"Failed: {self.test_results['failed']}")
        self.log(f"Pass Rate: {pass_rate:.1f}%")
        
        if self.test_results["errors"]:
            self.log("\nERRORS:")
            for error in self.test_results["errors"]:
                self.log(f"  - {error}")
        
        if pass_rate >= 80:
            self.log("🎉 Test suite PASSED!")
        else:
            self.log("❌ Test suite FAILED!")


def main():
    """Main test execution."""
    print("Lab Equipment API v2 - Comprehensive Test Suite")
    print("=" * 60)
    
    # Verify test user exists
    print(f"Testing against: {BASE_URL}")
    print(f"Test user: {TEST_USER['username']}")
    print("Note: Make sure the test user exists and the server is running!")
    print()
    
    # Run tests
    tester = APITester(BASE_URL)
    tester.run_all_tests()


if __name__ == "__main__":
    main() 