"""
Unit Tests for Django Ninja API v3 - Lab Equipment API

Created by: Thunder Wave
Date: 2025-01-08
Project: Triad Docker Base

Comprehensive unit tests for all Django Ninja API endpoints
covering the migration from DRF v2 to Django Ninja v3.
"""

import json
from datetime import datetime
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.authtoken.models import Token
from unittest.mock import patch, MagicMock
from wagtail.models import Site

from apps.base_site.models import LabEquipmentPage, EquipmentModel, LabEquipmentAccessory
from apps.categorized_tags.models import CategorizedTag, CategorizedPageTag


class DjangoNinjaAPITestCase(TestCase):
    """Base test case with common setup for Django Ninja API tests."""
    
    def setUp(self):
        """Set up test data for all API tests."""
        self.client = Client()
        
        # Create test user and token for authenticated endpoints
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.test_user)
        
        # Get the root page to add equipment pages as children
        try:
            site = Site.objects.get(is_default_site=True)
            root_page = site.root_page
        except Site.DoesNotExist:
            # Create a default site if none exists
            from wagtail.models import Page
            root_page = Page.objects.first()
            if not root_page:
                root_page = Page.add_root(title="Root", slug="root")
            Site.objects.create(
                hostname='localhost',
                port=8000,
                root_page=root_page,
                is_default_site=True
            )
        
        # Create test equipment page using proper Wagtail pattern
        self.equipment_page = LabEquipmentPage(
            title="Test Equipment",
            slug="test-equipment"
        )
        # Set additional fields after creation
        root_page.add_child(instance=self.equipment_page)
        
        # Set additional fields if they exist in the model
        if hasattr(self.equipment_page, 'short_description'):
            self.equipment_page.short_description = "Test equipment description"
        
        self.equipment_page.save()
        
        # Create test equipment model
        self.equipment_model = EquipmentModel.objects.create(
            page=self.equipment_page,
            name="Test Model"
        )
        
        # Create test tags
        self.tag1 = CategorizedTag.objects.create(
            name="Test Tag 1",
            category="feature"
        )
        self.tag2 = CategorizedTag.objects.create(
            name="Test Tag 2", 
            category="application"
        )
        
        # Create tag relationships
        self.page_tag1 = CategorizedPageTag.objects.create(
            tag=self.tag1,
            content_object_id=self.equipment_page.id
        )
        self.page_tag2 = CategorizedPageTag.objects.create(
            tag=self.tag2,
            content_object_id=self.equipment_page.id
        )
        
        # Create second equipment for related testing
        self.equipment_page2 = LabEquipmentPage(
            title="Related Equipment",
            slug="related-equipment"
        )
        root_page.add_child(instance=self.equipment_page2)
        
        # Set additional fields for second equipment
        if hasattr(self.equipment_page2, 'short_description'):
            self.equipment_page2.short_description = "Related equipment description"
        
        self.equipment_page2.save()
        
        # Create tag relationship for second equipment
        self.page_tag3 = CategorizedPageTag.objects.create(
            tag=self.tag1,  # Same tag as first equipment
            content_object_id=self.equipment_page2.id
        )
    
    def get_auth_headers(self):
        """Get authorization headers for authenticated requests."""
        return {'HTTP_AUTHORIZATION': f'Bearer {self.token.key}'}


class SystemEndpointsTest(DjangoNinjaAPITestCase):
    """Test system monitoring and health check endpoints."""
    
    def test_health_check_endpoint(self):
        """Test /api/v3/health endpoint returns proper health status."""
        response = self.client.get('/api/v3/health')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
        self.assertIn('version', data)
        self.assertIn('framework', data)
        self.assertIn('database', data)
        
        # Verify health status values
        self.assertIn(data['status'], ['healthy', 'degraded'])
        self.assertEqual(data['version'], '3.0.0')
        self.assertEqual(data['framework'], 'Django Ninja')
        
        # Verify database status structure
        db_status = data['database']
        self.assertIn('status', db_status)
        self.assertIn('connection', db_status)
    
    @patch('django.db.connection.cursor')
    def test_health_check_database_error(self, mock_cursor):
        """Test health check handles database connection errors gracefully."""
        # Mock database connection error
        mock_cursor.side_effect = Exception("Database connection failed")
        
        response = self.client.get('/api/v3/health')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['status'], 'degraded')
        self.assertIn('error', data['database']['status'])
    
    def test_test_endpoint(self):
        """Test /api/v3/test endpoint returns expected test data."""
        response = self.client.get('/api/v3/test')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn('message', data)
        self.assertIn('timestamp', data)
        self.assertIn('framework', data)
        self.assertIn('wagtail_compatible', data)
        
        # Verify test values
        self.assertEqual(data['message'], 'Django Ninja API v3 is working!')
        self.assertEqual(data['framework'], 'Django Ninja')
        self.assertTrue(data['wagtail_compatible'])


class EquipmentEndpointsTest(DjangoNinjaAPITestCase):
    """Test equipment listing and detail endpoints."""
    
    def test_equipment_list_endpoint(self):
        """Test /api/v3/equipment returns paginated equipment list."""
        response = self.client.get('/api/v3/equipment')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response is a list
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)  # At least our test equipment
        
        # Verify equipment structure
        equipment = data[0]
        self.assertIn('id', equipment)
        self.assertIn('title', equipment)
        self.assertIn('slug', equipment)
    
    def test_equipment_list_pagination(self):
        """Test equipment list pagination parameters work correctly."""
        # Test with limit
        response = self.client.get('/api/v3/equipment?limit=1')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertLessEqual(len(data), 1)
        
        # Test with offset
        response = self.client.get('/api/v3/equipment?offset=0&limit=10')
        self.assertEqual(response.status_code, 200)
        # Should return successfully even if fewer results exist
    
    def test_equipment_detail_endpoint(self):
        """Test /api/v3/equipment/{id} returns detailed equipment info."""
        response = self.client.get(f'/api/v3/equipment/{self.equipment_page.id}')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify detailed equipment structure
        self.assertIn('id', data)
        self.assertIn('title', data)
        self.assertIn('slug', data)
        
        # Verify actual values
        self.assertEqual(data['title'], 'Test Equipment')
    
    def test_equipment_detail_not_found(self):
        """Test equipment detail endpoint returns 404 for non-existent equipment."""
        response = self.client.get('/api/v3/equipment/99999')
        
        self.assertEqual(response.status_code, 404)
    
    def test_related_equipment_endpoint(self):
        """Test /api/v3/equipment/{id}/related returns related equipment by tags."""
        response = self.client.get(f'/api/v3/equipment/{self.equipment_page.id}/related')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure (schema doesn't include equipment_id)
        self.assertIn('related_by_tags', data)
        self.assertIn('related_by_specs', data)
        
        # Verify related equipment structure
        related_tags = data['related_by_tags']
        self.assertIsInstance(related_tags, list)
    
    def test_related_equipment_not_found(self):
        """Test related equipment endpoint returns proper structure for non-existent equipment."""
        response = self.client.get('/api/v3/equipment/99999/related')
        
        self.assertEqual(response.status_code, 404)


class ModelsEndpointsTest(DjangoNinjaAPITestCase):
    """Test equipment models endpoints."""
    
    def test_models_list_endpoint(self):
        """Test /api/v3/models returns equipment models list."""
        response = self.client.get('/api/v3/models')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response is a list
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)  # At least our test model
        
        # Verify model structure
        model = data[0]
        self.assertIn('id', model)
        self.assertIn('name', model)
        # Note: EquipmentModel only has 'name' field, no 'model_number' or 'description'
    
    def test_models_list_filtered_by_equipment(self):
        """Test models list can be filtered by equipment_id."""
        response = self.client.get(f'/api/v3/models?equipment_id={self.equipment_page.id}')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should return models associated with the specific equipment
        self.assertIsInstance(data, list)
        if len(data) > 0:
            model = data[0]
            self.assertEqual(model['name'], 'Test Model')
    
    def test_models_list_pagination(self):
        """Test models list pagination parameters."""
        response = self.client.get('/api/v3/models?limit=5&offset=0')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertLessEqual(len(data), 5)


class TagsEndpointsTest(DjangoNinjaAPITestCase):
    """Test categorized tags endpoints."""
    
    def test_tags_list_endpoint(self):
        """Test /api/v3/tags returns categorized tags list."""
        response = self.client.get('/api/v3/tags')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response is a list
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 2)  # At least our test tags
        
        # Verify tag structure
        tag = data[0]
        self.assertIn('id', tag)
        self.assertIn('name', tag)
        self.assertIn('category', tag)
    
    def test_tags_list_filtered_by_category(self):
        """Test tags list can be filtered by category."""
        response = self.client.get('/api/v3/tags?category=feature')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should return only tags in the specified category
        self.assertIsInstance(data, list)
        if len(data) > 0:
            for tag in data:
                self.assertEqual(tag['category'], 'feature')
    
    def test_tags_list_pagination(self):
        """Test tags list pagination parameters."""
        response = self.client.get('/api/v3/tags?limit=1')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertLessEqual(len(data), 1)


class APIErrorHandlingTest(DjangoNinjaAPITestCase):
    """Test API error handling and edge cases."""
    
    def test_invalid_parameters_handling(self):
        """Test API handles invalid parameters gracefully."""
        # Test invalid limit parameter
        response = self.client.get('/api/v3/equipment?limit=invalid')
        # Django Ninja should handle parameter validation
        self.assertIn(response.status_code, [200, 400, 422])  # Acceptable responses
        
        # Test negative offset
        response = self.client.get('/api/v3/equipment?offset=-1')
        self.assertIn(response.status_code, [200, 400, 422])
    
    def test_large_pagination_values(self):
        """Test API handles large pagination values appropriately."""
        response = self.client.get('/api/v3/equipment?limit=1000&offset=0')
        
        # Should not crash and should return reasonable amount of data
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)


class WagtailCompatibilityTest(DjangoNinjaAPITestCase):
    """Test Wagtail Page inheritance compatibility with Django Ninja."""
    
    def test_page_ptr_id_aliasing(self):
        """Test that page_ptr_id is properly aliased to id in API responses."""
        response = self.client.get(f'/api/v3/equipment/{self.equipment_page.id}')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify id field exists and matches expected value
        self.assertIn('id', data)
        self.assertEqual(data['id'], self.equipment_page.id)
        
        # Verify this works with page_ptr_id value
        self.assertEqual(data['id'], self.equipment_page.page_ptr_id)
    
    def test_related_equipment_query_pattern(self):
        """Test that the backwards query pattern works for related equipment."""
        response = self.client.get(f'/api/v3/equipment/{self.equipment_page.id}/related')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should successfully return related equipment structure
        self.assertIn('related_by_tags', data)
        self.assertIn('related_by_specs', data)
        
        # Verify no database errors occurred (would result in 500 status)
        related_tags = data['related_by_tags']
        self.assertIsInstance(related_tags, list)


class APIDocumentationTest(DjangoNinjaAPITestCase):
    """Test API documentation and schema endpoints."""
    
    def test_api_docs_endpoint_accessible(self):
        """Test that API documentation endpoint is accessible."""
        response = self.client.get('/api/v3/docs/')
        
        # Documentation should be accessible (may redirect or return HTML)
        self.assertIn(response.status_code, [200, 301, 302])
    
    def test_api_schema_generation(self):
        """Test that API schema can be generated without errors."""
        # This test ensures the API structure is valid for documentation
        from api import api
        
        # Should be able to access the API instance without errors
        self.assertIsNotNone(api)
        self.assertEqual(api.title, "Lab Equipment API v3")
        self.assertEqual(api.version, "3.0.0") 