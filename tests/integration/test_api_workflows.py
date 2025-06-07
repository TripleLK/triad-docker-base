"""
Integration Tests for Django Ninja API v3 Workflows

Created by: Thunder Wave
Date: 2025-01-08
Project: Triad Docker Base

Integration tests for complete API workflows and real-world scenarios.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from apps.base_site.models import LabEquipmentPage, EquipmentModel
from apps.categorized_tags.models import CategorizedTag, CategorizedPageTag


class APIWorkflowIntegrationTest(TestCase):
    """Test complete API workflows."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create test user
        self.test_user = User.objects.create_user(
            username='workflow_test',
            email='workflow@test.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.test_user)
        
        # Create test equipment
        self.equipment_page = LabEquipmentPage(
            title="Workflow Test Equipment",
            slug="workflow-test-equipment",
            manufacturer="Test Manufacturer",
            part_number="WF-001",
            description="Equipment for workflow testing"
        )
        self.equipment_page.save()
        
        # Create test tag
        self.tag = CategorizedTag.objects.create(
            name="workflow-test",
            category="test"
        )
        
        # Create tag relationship
        CategorizedPageTag.objects.create(
            tag=self.tag,
            content_object_id=self.equipment_page.id
        )
    
    def test_complete_equipment_discovery_workflow(self):
        """Test complete workflow: health → list → detail → related."""
        
        # Step 1: Check API health
        health_response = self.client.get('/api/v3/health')
        self.assertEqual(health_response.status_code, 200)
        
        # Step 2: List equipment
        list_response = self.client.get('/api/v3/equipment')
        self.assertEqual(list_response.status_code, 200)
        equipment_list = list_response.json()
        self.assertGreater(len(equipment_list), 0)
        
        # Step 3: Get equipment detail
        equipment_id = equipment_list[0]['id']
        detail_response = self.client.get(f'/api/v3/equipment/{equipment_id}')
        self.assertEqual(detail_response.status_code, 200)
        detail_data = detail_response.json()
        self.assertIn('title', detail_data)
        
        # Step 4: Get related equipment
        related_response = self.client.get(f'/api/v3/equipment/{equipment_id}/related')
        self.assertEqual(related_response.status_code, 200)
        related_data = related_response.json()
        self.assertIn('related_by_tags', related_data)
    
    def test_error_handling_workflow(self):
        """Test error handling across multiple requests."""
        
        # Valid request
        valid_response = self.client.get('/api/v3/equipment')
        self.assertEqual(valid_response.status_code, 200)
        
        # Invalid equipment ID
        invalid_response = self.client.get('/api/v3/equipment/99999')
        self.assertEqual(invalid_response.status_code, 404)
        
        # Invalid related equipment
        invalid_related = self.client.get('/api/v3/equipment/99999/related')
        self.assertEqual(invalid_related.status_code, 404)
    
    def test_pagination_workflow(self):
        """Test pagination across different endpoints."""
        
        # Test equipment pagination
        page1 = self.client.get('/api/v3/equipment?limit=1')
        self.assertEqual(page1.status_code, 200)
        
        # Test models pagination
        models_page = self.client.get('/api/v3/models?limit=5')
        self.assertEqual(models_page.status_code, 200)
        
        # Test tags pagination
        tags_page = self.client.get('/api/v3/tags?limit=10')
        self.assertEqual(tags_page.status_code, 200) 