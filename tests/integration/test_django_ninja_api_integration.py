"""
Integration Tests for Django Ninja API v3 - Complete Workflow Testing

Created by: Thunder Wave
Date: 2025-01-08
Project: Triad Docker Base

Integration tests that verify complete API workflows and real-world scenarios
for the Django Ninja API v3 migration from DRF v2.
"""

import json
import time
from datetime import datetime
from django.test import TestCase, TransactionTestCase, Client
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework.authtoken.models import Token
from django.core.management import call_command

from apps.base_site.models import LabEquipmentPage, EquipmentModel, LabEquipmentAccessory
from apps.categorized_tags.models import CategorizedTag, CategorizedPageTag


class DjangoNinjaAPIIntegrationTest(TransactionTestCase):
    """Integration test base with realistic test data."""
    
    def setUp(self):
        """Set up comprehensive test data for integration testing."""
        self.client = Client()
        
        # Create test user
        self.test_user = User.objects.create_user(
            username='integration_test',
            email='integration@test.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.test_user)
        
        # Set up Wagtail properly first
        self.setup_wagtail_environment()
        
        # Create realistic equipment data
        self.create_realistic_equipment_data()
    
    def setup_wagtail_environment(self):
        """Properly initialize Wagtail environment for testing."""
        # Create default locale first (required for Wagtail pages)
        from wagtail.models import Locale, Site, Page
        from apps.base_site.models import HomePage
        from django.contrib.contenttypes.models import ContentType
        
        # Create default locale if it doesn't exist
        locale, created = Locale.objects.get_or_create(
            language_code='en',
            defaults={'language_code': 'en'}
        )
        
        # Use Django management command approach for proper Wagtail setup
        from django.core.management import call_command
        from io import StringIO
        
        # Suppress output to keep tests clean
        out = StringIO()
        try:
            # Create initial Wagtail page structure if needed
            call_command('create_initial_data', stdout=out, stderr=out)
        except:
            # Ignore if already exists
            pass
        
        # Get or create a suitable parent page for equipment
        try:
            # Try to get existing home page or root page
            self.root_page = Page.objects.filter(depth=2).first()  # Get first level-2 page
            if not self.root_page:
                # Create a simple test page as parent
                page_content_type = ContentType.objects.get_for_model(Page)
                root = Page.objects.get(depth=1)  # Get root page
                
                self.root_page = Page(
                    title="Test Home",
                    slug="test-home",
                    content_type=page_content_type,
                    locale=locale
                )
                root.add_child(instance=self.root_page)
                
        except Exception as e:
            # Fallback: create a minimal test page structure
            page_content_type = ContentType.objects.get_for_model(Page)
            
            # Create or get root page
            try:
                root = Page.objects.get(depth=1)
            except Page.DoesNotExist:
                root = Page.add_root(
                    title="Root",
                    slug="root",
                    content_type=page_content_type,
                    locale=locale
                )
            
            # Create test home page with unique slug
            import uuid
            unique_slug = f"test-home-{uuid.uuid4().hex[:8]}"
            
            self.root_page = Page(
                title="Test Home",
                slug=unique_slug,
                content_type=page_content_type,
                locale=locale
            )
            root.add_child(instance=self.root_page)
        
        # Ensure we have a default site
        if not Site.objects.exists():
            Site.objects.create(
                hostname='localhost',
                port=8000,
                root_page=self.root_page,
                is_default_site=True,
                site_name='Test Site'
            )
    
    def create_realistic_equipment_data(self):
        """Create realistic test data for equipment and related models."""
        
        # Create tag categories and tags
        tag_categories = {
            'microscopy': 'technique',
            'separation': 'technique', 
            'analysis': 'technique',
            'optics': 'feature',
            'precision': 'feature',
            'automation': 'feature',
            'research': 'application',
            'clinical': 'application',
            'quality_control': 'application'
        }
        
        self.tags = {}
        
        for tag_name, category in tag_categories.items():
            tag = CategorizedTag.objects.create(name=tag_name, category=category)
            self.tags[tag_name] = tag
        
        # Equipment test data
        self.equipment_data = [
            {
                'title': 'Advanced Fluorescence Microscope',
                'slug': 'advanced-fluorescence-microscope',
                'description': 'High-resolution fluorescence microscopy system for cellular imaging',
                'tags': ['microscopy', 'optics', 'research']
            },
            {
                'title': 'Liquid Chromatography System',
                'slug': 'liquid-chromatography-system',
                'description': 'Precision HPLC system for analytical separations',
                'tags': ['separation', 'precision', 'analysis']
            },
            {
                'title': 'Automated Plate Reader',
                'slug': 'automated-plate-reader',
                'description': 'Multi-mode microplate reader with automation capabilities',
                'tags': ['automation', 'analysis', 'clinical']
            },
            {
                'title': 'Precision Balance',
                'slug': 'precision-balance',
                'description': 'Ultra-precise analytical balance for quantitative analysis',
                'tags': ['precision', 'quality_control']
            }
        ]
        
        # Create equipment pages
        self.equipment_pages = []
        self.equipment_models = []
        
        # Create equipment and models  
        for equipment_data in self.equipment_data:
            # Create equipment page
            equipment_page = LabEquipmentPage(
                title=equipment_data['title'],
                slug=equipment_data['slug']
            )
            
            # Set additional fields if they exist in the model
            if hasattr(equipment_page, 'short_description'):
                equipment_page.short_description = equipment_data['description']
            
            self.root_page.add_child(instance=equipment_page)
            equipment_page.save()
            self.equipment_pages.append(equipment_page)
            
            # Create equipment model
            model = EquipmentModel.objects.create(
                page=equipment_page,
                name=f"{equipment_data['title']} Model"
            )
            self.equipment_models.append(model)
            
            # Create tag relationships
            for tag_name in equipment_data['tags']:
                CategorizedPageTag.objects.create(
                    tag=self.tags[tag_name],
                    content_object_id=equipment_page.id
                )


class CompleteAPIWorkflowTest(DjangoNinjaAPIIntegrationTest):
    """Test complete API workflows from start to finish."""
    
    def test_complete_equipment_discovery_workflow(self):
        """Test complete workflow: health check → list → detail → related equipment."""
        
        # Step 1: Verify API health
        health_response = self.client.get('/api/v3/health')
        self.assertEqual(health_response.status_code, 200)
        health_data = health_response.json()
        self.assertEqual(health_data['status'], 'healthy')
        
        # Step 2: List all equipment
        list_response = self.client.get('/api/v3/equipment')
        self.assertEqual(list_response.status_code, 200)
        equipment_list = list_response.json()
        self.assertGreaterEqual(len(equipment_list), 4)  # Our test equipment
        
        # Step 3: Get detailed info for each equipment
        for equipment in equipment_list:
            detail_response = self.client.get(f'/api/v3/equipment/{equipment["id"]}')
            self.assertEqual(detail_response.status_code, 200)
            detail_data = detail_response.json()
            
            # Verify detailed data structure
            self.assertIn('title', detail_data)
            self.assertIn('short_description', detail_data)
            self.assertIn('categorized_tags', detail_data)
            self.assertIn('models', detail_data)
            
            # Step 4: Check related equipment
            related_response = self.client.get(f'/api/v3/equipment/{equipment["id"]}/related')
            self.assertEqual(related_response.status_code, 200)
            related_data = related_response.json()
            
            # Verify related equipment structure (schema doesn't include equipment_id)
            self.assertIn('related_by_tags', related_data)
            self.assertIn('related_by_specs', related_data)
    
    def test_tag_based_equipment_discovery(self):
        """Test discovering equipment through tag relationships."""
        
        # Step 1: Get all tags
        tags_response = self.client.get('/api/v3/tags')
        self.assertEqual(tags_response.status_code, 200)
        tags_data = tags_response.json()
        self.assertGreater(len(tags_data), 0)
        
        # Step 2: Filter tags by category
        technique_tags = self.client.get('/api/v3/tags?category=technique')
        self.assertEqual(technique_tags.status_code, 200)
        technique_data = technique_tags.json()
        
        # Verify technique tags exist
        technique_names = [tag['name'] for tag in technique_data]
        self.assertIn('microscopy', technique_names)
        
        # Step 3: Find equipment with shared tags
        # Get equipment with optics tag
        optics_equipment = []
        for equipment_page in self.equipment_pages:
            detail_response = self.client.get(f'/api/v3/equipment/{equipment_page.id}')
            detail_data = detail_response.json()
            
            equipment_tags = [tag['name'] for tag in detail_data['categorized_tags']]
            if 'optics' in equipment_tags:
                optics_equipment.append(equipment_page.id)
        
        # Verify we found optics equipment
        self.assertGreater(len(optics_equipment), 0)
        
        # Step 4: Verify related equipment connections
        for equipment_id in optics_equipment:
            related_response = self.client.get(f'/api/v3/equipment/{equipment_id}/related')
            related_data = related_response.json()
            
            # Should find related equipment through shared tags
            related_by_tags = related_data['related_by_tags']
            # May or may not have related equipment depending on tag overlap
            self.assertIsInstance(related_by_tags, list)
    
    def test_pagination_and_filtering_workflow(self):
        """Test pagination and filtering across different endpoints."""
        
        # Test equipment pagination
        page1 = self.client.get('/api/v3/equipment?limit=2&offset=0')
        self.assertEqual(page1.status_code, 200)
        page1_data = page1.json()
        self.assertLessEqual(len(page1_data), 2)
        
        page2 = self.client.get('/api/v3/equipment?limit=2&offset=2')
        self.assertEqual(page2.status_code, 200)
        page2_data = page2.json()
        
        # Verify pagination works (different results)
        if len(page1_data) > 0 and len(page2_data) > 0:
            self.assertNotEqual(page1_data[0]['id'], page2_data[0]['id'])
        
        # Test models filtering
        first_equipment_id = self.equipment_pages[0].id
        filtered_models = self.client.get(f'/api/v3/models?equipment_id={first_equipment_id}')
        self.assertEqual(filtered_models.status_code, 200)
        models_data = filtered_models.json()
        
        # Should return only models for the specified equipment
        self.assertIsInstance(models_data, list)
        
        # Test tag category filtering
        for category in ['technique', 'application', 'feature']:
            category_tags = self.client.get(f'/api/v3/tags?category={category}')
            self.assertEqual(category_tags.status_code, 200)
            category_data = category_tags.json()
            
            # Verify all returned tags are in the correct category
            for tag in category_data:
                self.assertEqual(tag['category'], category)


class APIPerformanceIntegrationTest(DjangoNinjaAPIIntegrationTest):
    """Test API performance under realistic conditions."""
    
    def test_concurrent_api_requests(self):
        """Test API handles concurrent requests properly."""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request(endpoint, result_queue):
            """Make API request and store result."""
            try:
                response = self.client.get(endpoint)
                result_queue.put({
                    'endpoint': endpoint,
                    'status_code': response.status_code,
                    'success': response.status_code == 200
                })
            except Exception as e:
                result_queue.put({
                    'endpoint': endpoint,
                    'error': str(e),
                    'success': False
                })
        
        # Create multiple threads making concurrent requests
        threads = []
        endpoints = [
            '/api/v3/health',
            '/api/v3/test',
            '/api/v3/equipment',
            '/api/v3/models',
            '/api/v3/tags'
        ]
        
        for endpoint in endpoints:
            thread = threading.Thread(target=make_request, args=(endpoint, results))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests succeeded
        while not results.empty():
            result = results.get()
            self.assertTrue(result['success'], 
                          f"Request to {result['endpoint']} failed: {result.get('error', 'Unknown error')}")
    
    def test_large_dataset_pagination(self):
        """Test pagination performance with larger datasets."""
        
        # Test with various page sizes
        page_sizes = [5, 10, 25, 50]
        
        for page_size in page_sizes:
            response = self.client.get(f'/api/v3/equipment?limit={page_size}')
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Verify response doesn't exceed page size
            self.assertLessEqual(len(data), page_size)
            
            # Verify response structure is consistent
            if data:
                self.assertIn('id', data[0])
                self.assertIn('title', data[0])
    
    def test_api_response_times(self):
        """Test API response times for performance monitoring."""
        
        endpoints_to_test = [
            '/api/v3/health',
            '/api/v3/equipment',
            '/api/v3/tags',
            '/api/v3/models'
        ]
        
        for endpoint in endpoints_to_test:
            start_time = time.time()
            response = self.client.get(endpoint)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Verify response is successful
            self.assertEqual(response.status_code, 200)
            
            # Verify response time is reasonable (under 1 second for test environment)
            self.assertLess(response_time, 1.0, 
                          f"Response time for {endpoint} was {response_time:.2f}s")


class ErrorHandlingIntegrationTest(DjangoNinjaAPIIntegrationTest):
    """Test error handling and edge cases in realistic scenarios."""
    
    def test_cascading_error_handling(self):
        """Test error handling across multiple related requests."""
        
        # Test equipment detail with invalid ID
        invalid_response = self.client.get('/api/v3/equipment/99999')
        self.assertEqual(invalid_response.status_code, 404)
        
        # Test related equipment with invalid ID
        invalid_related = self.client.get('/api/v3/equipment/99999/related')
        self.assertEqual(invalid_related.status_code, 404)
        
        # Test valid equipment followed by invalid related request
        valid_equipment_id = self.equipment_pages[0].id
        valid_response = self.client.get(f'/api/v3/equipment/{valid_equipment_id}')
        self.assertEqual(valid_response.status_code, 200)
        
        # Should still fail for invalid related request
        invalid_related_2 = self.client.get('/api/v3/equipment/99999/related')
        self.assertEqual(invalid_related_2.status_code, 404)
    
    def test_malformed_request_handling(self):
        """Test handling of malformed requests."""
        
        # Test with invalid query parameters
        invalid_params = [
            '/api/v3/equipment?limit=abc',
            '/api/v3/equipment?offset=xyz',
            '/api/v3/equipment?limit=-1',
            '/api/v3/models?equipment_id=invalid',
            '/api/v3/tags?category=',
        ]
        
        for url in invalid_params:
            response = self.client.get(url)
            # Should handle gracefully (not 500 error)
            self.assertNotEqual(response.status_code, 500)
            # Acceptable responses: 200 (handled), 400 (bad request), 422 (validation error)
            self.assertIn(response.status_code, [200, 400, 422])
    
    def test_database_constraint_handling(self):
        """Test handling of database-related constraints and errors."""
        
        # Test equipment detail with very large ID
        large_id_response = self.client.get('/api/v3/equipment/999999999999')
        self.assertEqual(large_id_response.status_code, 404)
        
        # Test with boundary values
        boundary_tests = [
            '/api/v3/equipment/0',
            '/api/v3/equipment/1',
            '/api/v3/equipment/-1'
        ]
        
        for url in boundary_tests:
            response = self.client.get(url)
            # Should handle gracefully
            self.assertIn(response.status_code, [200, 400, 404])


class WagtailCompatibilityIntegrationTest(DjangoNinjaAPIIntegrationTest):
    """Test Wagtail Page inheritance compatibility in realistic scenarios."""
    
    def test_page_ptr_id_consistency_across_endpoints(self):
        """Test that page_ptr_id aliasing works consistently across all endpoints."""
        
        # Get equipment from list endpoint
        list_response = self.client.get('/api/v3/equipment')
        equipment_list = list_response.json()
        
        for equipment in equipment_list:
            equipment_id = equipment['id']
            
            # Get same equipment from detail endpoint
            detail_response = self.client.get(f'/api/v3/equipment/{equipment_id}')
            detail_data = detail_response.json()
            
            # Verify ID consistency
            self.assertEqual(equipment['id'], detail_data['id'])
            
            # Get related equipment
            related_response = self.client.get(f'/api/v3/equipment/{equipment_id}/related')
            related_data = related_response.json()
            
            # Verify related equipment structure (schema doesn't include equipment_id)
            # Verify related equipment IDs are valid
            for related_item in related_data['related_by_tags']:
                self.assertIsInstance(related_item['id'], int)
                self.assertGreater(related_item['id'], 0)
    
    def test_backwards_query_pattern_reliability(self):
        """Test that the backwards query pattern works reliably for related equipment."""
        
        # Test related equipment for multiple pieces of equipment
        for equipment_page in self.equipment_pages:
            response = self.client.get(f'/api/v3/equipment/{equipment_page.id}/related')
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            
            # Verify structure is always consistent
            self.assertIn('related_by_tags', data)
            self.assertIn('related_by_specs', data)
            self.assertIsInstance(data['related_by_tags'], list)
            self.assertIsInstance(data['related_by_specs'], list)
            
            # Verify no self-references in related equipment
            related_ids = [item['id'] for item in data['related_by_tags']]
            self.assertNotIn(equipment_page.id, related_ids)
    
    def test_tag_relationship_query_consistency(self):
        """Test that tag relationships work consistently with Wagtail Page inheritance."""
        
        # For each equipment, verify tag relationships work both ways
        for equipment_page in self.equipment_pages:
            # Get equipment details to see its tags
            detail_response = self.client.get(f'/api/v3/equipment/{equipment_page.id}')
            equipment_data = detail_response.json()
            equipment_tags = [tag['name'] for tag in equipment_data['categorized_tags']]
            
            # Get related equipment based on tags
            related_response = self.client.get(f'/api/v3/equipment/{equipment_page.id}/related')
            related_data = related_response.json()
            
            # If there are related items, verify they share tags
            for related_item in related_data['related_by_tags']:
                related_detail = self.client.get(f'/api/v3/equipment/{related_item["id"]}')
                related_detail_data = related_detail.json()
                related_tags = [tag['name'] for tag in related_detail_data['categorized_tags']]
                
                # Should have at least one shared tag
                shared_tags = set(equipment_tags) & set(related_tags)
                self.assertGreater(len(shared_tags), 0, 
                                 f"No shared tags between {equipment_page.title} and {related_item['title']}")


class APIDocumentationIntegrationTest(DjangoNinjaAPIIntegrationTest):
    """Test API documentation and schema generation."""
    
    def test_api_documentation_completeness(self):
        """Test that API documentation covers all endpoints."""
        
        # Test that docs endpoint is accessible
        docs_response = self.client.get('/api/v3/docs/')
        self.assertIn(docs_response.status_code, [200, 301, 302])
        
        # Test that schema can be generated
        from api import api
        self.assertIsNotNone(api)
        
        # Verify API metadata
        self.assertEqual(api.title, "Lab Equipment API v3")
        self.assertEqual(api.version, "3.0.0")
        self.assertIn("Django Ninja", api.description)
    
    def test_api_endpoints_match_documentation(self):
        """Test that all endpoints work as documented."""
        
        # Define expected endpoints and their methods
        expected_endpoints = [
            ('GET', '/api/v3/health'),
            ('GET', '/api/v3/test'),
            ('GET', '/api/v3/equipment'),
            ('GET', '/api/v3/equipment/{id}'),
            ('GET', '/api/v3/equipment/{id}/related'),
            ('GET', '/api/v3/models'),
            ('GET', '/api/v3/tags'),
        ]
        
        # Test system endpoints
        for method, endpoint_template in expected_endpoints:
            if '{id}' in endpoint_template:
                # Use first equipment ID for testing
                endpoint = endpoint_template.replace('{id}', str(self.equipment_pages[0].id))
            else:
                endpoint = endpoint_template
            
            if method == 'GET':
                response = self.client.get(endpoint)
                # Should not return server error
                self.assertNotEqual(response.status_code, 500)
                # Should return valid response
                self.assertIn(response.status_code, [200, 404])  # 404 is acceptable for some cases 