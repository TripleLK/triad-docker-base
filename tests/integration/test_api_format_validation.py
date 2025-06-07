"""
API Format Validation Tests - Comprehensive Data Format Testing

Created by: Crimson Vertex
Date: 2025-01-08
Project: Triad Docker Base

These tests validate that the API input/output formats match exactly
with the documentation in .project_management/api_documentation/triad_api_data_formats.org

Test Coverage:
- All endpoint response formats
- Input data validation
- Error response formats
- Authentication flows
- Data type specifications
"""

import json
import time
from datetime import datetime
from django.test import TestCase, TransactionTestCase, Client
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework.authtoken.models import Token
from django.core.management import call_command
from django.urls import reverse

from apps.base_site.models import (
    LabEquipmentPage, EquipmentModel, LabEquipmentAccessory,
    LabEquipmentPageSpecGroup, EquipmentModelSpecGroup, Spec, EquipmentFeature
)
from apps.categorized_tags.models import CategorizedTag, CategorizedPageTag


class APIFormatValidationTest(TransactionTestCase):
    """Test that API formats match documentation specifications."""
    
    def setUp(self):
        """Set up test data with known formats."""
        self.client = Client()
        
        # Create test user and token
        self.test_user = User.objects.create_user(
            username='format_test',
            email='format@test.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.test_user)
        
        # Set up Wagtail environment
        self.setup_wagtail_environment()
        
        # Create test data with precise known values
        self.create_test_data()
    
    def setup_wagtail_environment(self):
        """Set up minimal Wagtail environment for testing."""
        from wagtail.models import Locale, Site, Page
        from django.contrib.contenttypes.models import ContentType
        
        # Create default locale
        locale, created = Locale.objects.get_or_create(language_code='en')
        
        # Get or create root page
        try:
            root = Page.objects.get(depth=1)
        except Page.DoesNotExist:
            page_content_type = ContentType.objects.get_for_model(Page)
            root = Page.add_root(
                title="Root",
                slug="root",
                content_type=page_content_type,
                locale=locale
            )
        
        # Create test home page
        import uuid
        unique_slug = f"test-home-{uuid.uuid4().hex[:8]}"
        
        page_content_type = ContentType.objects.get_for_model(Page)
        self.root_page = Page(
            title="Test Home",
            slug=unique_slug,
            content_type=page_content_type,
            locale=locale
        )
        root.add_child(instance=self.root_page)
        
        # Ensure default site exists
        if not Site.objects.exists():
            Site.objects.create(
                hostname='localhost',
                port=8000,
                root_page=self.root_page,
                is_default_site=True,
                site_name='Test Site'
            )
    
    def create_test_data(self):
        """Create test data with precise values for format validation."""
        
        # Create categorized tags with known values
        self.optical_tag = CategorizedTag.objects.create(
            name="Optical Equipment",
            category="instrument_type"
        )
        self.research_tag = CategorizedTag.objects.create(
            name="Research Grade",
            category="quality_level"
        )
        
        # Create test equipment with known specifications
        self.test_equipment = LabEquipmentPage(
            title="Advanced Microscope X200",
            slug="advanced-microscope-x200",
            short_description="High-resolution microscope for research",
            full_description="<p>Complete technical description with HTML formatting</p>",
            source_url="https://manufacturer.com/product/x200",
            source_type="new",
            data_completeness=0.95,
            specification_confidence="high",
            needs_review=False,
            live=True
        )
        self.root_page.add_child(instance=self.test_equipment)
        
        # Add tags to equipment
        CategorizedPageTag.objects.create(
            content_object=self.test_equipment,
            tag=self.optical_tag
        )
        CategorizedPageTag.objects.create(
            content_object=self.test_equipment,
            tag=self.research_tag
        )
        
        # Create specification groups and specs - using correct field name
        self.optics_spec_group = LabEquipmentPageSpecGroup.objects.create(
            LabEquipmentPage=self.test_equipment,
            name="Optics"
        )
        self.dimensions_spec_group = LabEquipmentPageSpecGroup.objects.create(
            LabEquipmentPage=self.test_equipment,
            name="Dimensions"
        )
        
        # Create specifications
        Spec.objects.create(
            spec_group=self.optics_spec_group,
            key="Magnification",
            value="40x-1000x"
        )
        Spec.objects.create(
            spec_group=self.optics_spec_group,
            key="Objective Lenses",
            value="4"
        )
        Spec.objects.create(
            spec_group=self.dimensions_spec_group,
            key="Height",
            value="45 cm"
        )
        Spec.objects.create(
            spec_group=self.dimensions_spec_group,
            key="Weight",
            value="12 kg"
        )
        
        # Create equipment model
        self.test_model = EquipmentModel.objects.create(
            page=self.test_equipment,
            name="Basic Model"
        )
        
        # Create model specification group - using correct field name
        self.power_spec_group = EquipmentModelSpecGroup.objects.create(
            equipment_model=self.test_model,
            name="Power"
        )
        
        # Create model specifications - using correct field name for model specs
        Spec.objects.create(
            spec_group=self.power_spec_group,
            key="Power Source",
            value="110V AC"
        )
        Spec.objects.create(
            spec_group=self.power_spec_group,
            key="Power Consumption",
            value="25W"
        )
        
        # Create features
        EquipmentFeature.objects.create(
            page=self.test_equipment,
            feature="LED Illumination"
        )
        EquipmentFeature.objects.create(
            page=self.test_equipment,
            feature="Digital Camera Ready"
        )
        EquipmentFeature.objects.create(
            page=self.test_equipment,
            feature="Ergonomic Design"
        )
        
        # Note: Skipping accessory creation as it requires image field setup
        # which is complex for basic API format validation
    
    def get_auth_headers(self):
        """Get authentication headers for API requests."""
        return {'HTTP_AUTHORIZATION': f'Bearer {self.token.key}'}


class SystemEndpointFormatTest(APIFormatValidationTest):
    """Test system endpoint formats match documentation."""
    
    def test_health_check_format(self):
        """
        Test: Health Check Endpoint Format
        Documentation Reference: System Endpoints -> Health Check
        Validates: GET /api/v3/health response format
        """
        response = self.client.get('/api/v3/health')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        # Validate required fields exist
        required_fields = ['status', 'timestamp', 'version', 'framework', 'database']
        for field in required_fields:
            self.assertIn(field, data, f"Missing required field: {field}")
        
        # Validate field types and values
        self.assertIsInstance(data['status'], str)
        self.assertIn(data['status'], ['healthy', 'degraded'])
        
        self.assertIsInstance(data['timestamp'], str)
        # Validate ISO 8601 format
        datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        
        self.assertEqual(data['version'], '3.0.0')
        self.assertEqual(data['framework'], 'Django Ninja')
        
        # Validate database object structure
        self.assertIsInstance(data['database'], dict)
        self.assertIn('status', data['database'])
        self.assertIn('connection', data['database'])
        
        print("✅ Health Check Format Test: PASSED")
    
    def test_test_endpoint_format(self):
        """
        Test: Test Endpoint Format
        Documentation Reference: System Endpoints -> Test Endpoint
        Validates: GET /api/v3/test response format
        """
        response = self.client.get('/api/v3/test')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        # Validate required fields
        required_fields = ['message', 'timestamp', 'framework', 'wagtail_compatible']
        for field in required_fields:
            self.assertIn(field, data, f"Missing required field: {field}")
        
        # Validate field values
        self.assertEqual(data['message'], 'Django Ninja API v3 is working!')
        self.assertEqual(data['framework'], 'Django Ninja')
        self.assertEqual(data['wagtail_compatible'], True)
        
        # Validate timestamp format
        datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        
        print("✅ Test Endpoint Format Test: PASSED")


class EquipmentEndpointFormatTest(APIFormatValidationTest):
    """Test equipment endpoint formats match documentation."""
    
    def test_equipment_list_format(self):
        """
        Test: Equipment List Format
        Documentation Reference: Equipment Endpoints -> Equipment List
        Validates: GET /api/v3/equipment response format
        """
        response = self.client.get('/api/v3/equipment')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        
        if len(data) > 0:
            equipment = data[0]
            
            # Validate required fields for LabEquipmentPageListSchema
            required_fields = [
                'id', 'title', 'slug', 'short_description', 'source_type',
                'data_completeness', 'specification_confidence', 'needs_review',
                'live', 'first_published_at', 'main_image_url', 'categorized_tags',
                'model_count'
            ]
            
            for field in required_fields:
                self.assertIn(field, equipment, f"Missing required field: {field}")
            
            # Validate field types
            self.assertIsInstance(equipment['id'], int)
            self.assertIsInstance(equipment['title'], str)
            self.assertIsInstance(equipment['slug'], str)
            self.assertIsInstance(equipment['short_description'], str)
            self.assertIn(equipment['source_type'], ['new', 'used', 'refurbished'])
            self.assertIsInstance(equipment['data_completeness'], (int, float))
            self.assertIn(equipment['specification_confidence'], ['low', 'medium', 'high'])
            self.assertIsInstance(equipment['needs_review'], bool)
            self.assertIsInstance(equipment['live'], bool)
            self.assertIsInstance(equipment['categorized_tags'], list)
            self.assertIsInstance(equipment['model_count'], int)
            
            # Validate tag structure
            if len(equipment['categorized_tags']) > 0:
                tag = equipment['categorized_tags'][0]
                self.assertIn('id', tag)
                self.assertIn('name', tag)
                self.assertIn('category', tag)
                self.assertIsInstance(tag['id'], int)
                self.assertIsInstance(tag['name'], str)
                self.assertIsInstance(tag['category'], str)
        
        print("✅ Equipment List Format Test: PASSED")
    
    def test_equipment_detail_format(self):
        """
        Test: Equipment Detail Format
        Documentation Reference: Equipment Endpoints -> Equipment Detail
        Validates: GET /api/v3/equipment/{id} response format
        """
        response = self.client.get(f'/api/v3/equipment/{self.test_equipment.id}')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        # Validate all required fields for LabEquipmentPageDetailSchema
        required_fields = [
            'id', 'title', 'slug', 'short_description', 'full_description',
            'source_url', 'source_type', 'data_completeness', 'specification_confidence',
            'needs_review', 'live', 'first_published_at', 'last_published_at',
            'main_image_url', 'spec_groups', 'models', 'features', 'accessories',
            'categorized_tags', 'gallery_images', 'spec_group_names'
        ]
        
        for field in required_fields:
            self.assertIn(field, data, f"Missing required field: {field}")
        
        # Validate spec_groups structure
        self.assertIsInstance(data['spec_groups'], list)
        if len(data['spec_groups']) > 0:
            spec_group = data['spec_groups'][0]
            self.assertIn('id', spec_group)
            self.assertIn('name', spec_group)
            self.assertIn('specs', spec_group)
            self.assertIsInstance(spec_group['specs'], list)
            
            if len(spec_group['specs']) > 0:
                spec = spec_group['specs'][0]
                self.assertIn('id', spec)
                self.assertIn('key', spec)
                self.assertIn('value', spec)
                self.assertIsInstance(spec['id'], int)
                self.assertIsInstance(spec['key'], str)
                self.assertIsInstance(spec['value'], str)
        
        # Validate models structure
        self.assertIsInstance(data['models'], list)
        if len(data['models']) > 0:
            model = data['models'][0]
            self.assertIn('id', model)
            self.assertIn('name', model)
            self.assertIn('spec_groups', model)
            self.assertIn('merged_spec_groups', model)
        
        # Validate features structure
        self.assertIsInstance(data['features'], list)
        if len(data['features']) > 0:
            feature = data['features'][0]
            self.assertIn('id', feature)
            self.assertIn('feature', feature)
        
        # Validate categorized_tags structure
        self.assertIsInstance(data['categorized_tags'], list)
        
        # Validate gallery_images structure
        self.assertIsInstance(data['gallery_images'], list)
        
        # Validate spec_group_names structure
        self.assertIsInstance(data['spec_group_names'], list)
        
        print("✅ Equipment Detail Format Test: PASSED")
    
    def test_equipment_search_format(self):
        """
        Test: Equipment Search Format
        Documentation Reference: Equipment Endpoints -> Equipment Search
        Validates: GET /api/v3/equipment/search response format and parameters
        """
        # Test with various query parameters
        search_params = {
            'q': 'microscope',
            'tags': 'Optical Equipment',
            'min_completeness': '0.9',
            'limit': '10'
        }
        
        query_string = '&'.join([f'{k}={v}' for k, v in search_params.items()])
        response = self.client.get(f'/api/v3/equipment/search?{query_string}')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        
        # Should return same format as equipment list
        if len(data) > 0:
            equipment = data[0]
            # Verify it contains required list schema fields
            required_fields = ['id', 'title', 'slug', 'categorized_tags', 'model_count']
            for field in required_fields:
                self.assertIn(field, equipment)
        
        print("✅ Equipment Search Format Test: PASSED")
    
    def test_related_equipment_format(self):
        """
        Test: Related Equipment Format
        Documentation Reference: Equipment Endpoints -> Related Equipment
        Validates: GET /api/v3/equipment/{id}/related response format
        """
        response = self.client.get(f'/api/v3/equipment/{self.test_equipment.id}/related')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        # Validate RelatedEquipmentResponseSchema structure
        required_fields = ['related_by_tags', 'related_by_specs']
        for field in required_fields:
            self.assertIn(field, data, f"Missing required field: {field}")
        
        self.assertIsInstance(data['related_by_tags'], list)
        self.assertIsInstance(data['related_by_specs'], list)
        
        # Validate that items in lists follow LabEquipmentPageListSchema format
        for related_list in [data['related_by_tags'], data['related_by_specs']]:
            if len(related_list) > 0:
                item = related_list[0]
                self.assertIn('id', item)
                self.assertIn('title', item)
                self.assertIn('categorized_tags', item)
                self.assertIn('model_count', item)
        
        print("✅ Related Equipment Format Test: PASSED")


class ModelEndpointFormatTest(APIFormatValidationTest):
    """Test model endpoint formats match documentation."""
    
    def test_equipment_models_list_format(self):
        """
        Test: Equipment Models List Format
        Documentation Reference: Model Endpoints -> Equipment Models List
        Validates: GET /api/v3/models response format
        """
        response = self.client.get('/api/v3/models')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        
        if len(data) > 0:
            model = data[0]
            
            # Validate EquipmentModelSchema structure
            required_fields = ['id', 'name', 'spec_groups', 'merged_spec_groups']
            for field in required_fields:
                self.assertIn(field, model, f"Missing required field: {field}")
            
            self.assertIsInstance(model['id'], int)
            self.assertIsInstance(model['name'], str)
            self.assertIsInstance(model['spec_groups'], list)
            self.assertIsInstance(model['merged_spec_groups'], list)
            
            # Validate merged_spec_groups structure
            if len(model['merged_spec_groups']) > 0:
                merged_group = model['merged_spec_groups'][0]
                self.assertIn('name', merged_group)
                self.assertIn('specs', merged_group)
                self.assertIsInstance(merged_group['specs'], list)
                
                if len(merged_group['specs']) > 0:
                    spec = merged_group['specs'][0]
                    self.assertIn('key', spec)
                    self.assertIn('value', spec)
        
        print("✅ Equipment Models List Format Test: PASSED")
    
    def test_equipment_model_detail_format(self):
        """
        Test: Equipment Model Detail Format
        Documentation Reference: Model Endpoints -> Equipment Model Detail
        Validates: GET /api/v3/models/{id} response format
        """
        response = self.client.get(f'/api/v3/models/{self.test_model.id}')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        # Should match EquipmentModelSchema structure
        required_fields = ['id', 'name', 'spec_groups', 'merged_spec_groups']
        for field in required_fields:
            self.assertIn(field, data, f"Missing required field: {field}")
        
        print("✅ Equipment Model Detail Format Test: PASSED")


class AccessoryEndpointFormatTest(APIFormatValidationTest):
    """Test accessory endpoint formats match documentation."""
    
    def test_accessories_list_format(self):
        """
        Test: Accessories List Format
        Documentation Reference: Accessory Endpoints -> Accessories List
        Validates: GET /api/v3/accessories response format
        """
        response = self.client.get('/api/v3/accessories')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        
        if len(data) > 0:
            accessory = data[0]
            
            # Validate LabEquipmentAccessorySchema structure
            required_fields = ['id', 'name', 'model_number', 'image_url']
            for field in required_fields:
                self.assertIn(field, accessory, f"Missing required field: {field}")
            
            self.assertIsInstance(accessory['id'], int)
            self.assertIsInstance(accessory['name'], str)
            # model_number and image_url can be null
            if accessory['model_number'] is not None:
                self.assertIsInstance(accessory['model_number'], str)
            if accessory['image_url'] is not None:
                self.assertIsInstance(accessory['image_url'], str)
        
        print("✅ Accessories List Format Test: PASSED")


class TagEndpointFormatTest(APIFormatValidationTest):
    """Test tag endpoint formats match documentation."""
    
    def test_tags_list_format(self):
        """
        Test: Tags List Format
        Documentation Reference: Tag Endpoints -> Tags List
        Validates: GET /api/v3/tags response format
        """
        response = self.client.get('/api/v3/tags')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        
        if len(data) > 0:
            tag = data[0]
            
            # Validate CategorizedTagSchema structure
            required_fields = ['id', 'name', 'category']
            for field in required_fields:
                self.assertIn(field, tag, f"Missing required field: {field}")
            
            self.assertIsInstance(tag['id'], int)
            self.assertIsInstance(tag['name'], str)
            self.assertIsInstance(tag['category'], str)
        
        print("✅ Tags List Format Test: PASSED")
    
    def test_tag_categories_format(self):
        """
        Test: Tag Categories Format
        Documentation Reference: Tag Endpoints -> Tag Categories
        Validates: GET /api/v3/tags/categories response format
        """
        response = self.client.get('/api/v3/tags/categories')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        # Validate structure
        self.assertIn('categories', data)
        self.assertIsInstance(data['categories'], list)
        
        # Validate that categories are strings
        for category in data['categories']:
            self.assertIsInstance(category, str)
        
        print("✅ Tag Categories Format Test: PASSED")


class ErrorResponseFormatTest(APIFormatValidationTest):
    """Test error response formats match documentation."""
    
    def test_not_found_error_format(self):
        """
        Test: Standard Error Response Format
        Documentation Reference: Error Response Formats -> Standard Error Response
        Validates: 404 error response format
        """
        response = self.client.get('/api/v3/equipment/99999')
        self.assertEqual(response.status_code, 404)
        
        data = response.json()
        
        # Validate ErrorResponseSchema structure
        required_fields = ['error', 'message']
        for field in required_fields:
            self.assertIn(field, data, f"Missing required field: {field}")
        
        self.assertIsInstance(data['error'], str)
        self.assertIsInstance(data['message'], str)
        
        # details field is optional
        if 'details' in data:
            self.assertIsInstance(data['details'], dict)
        
        print("✅ Not Found Error Format Test: PASSED")
    
    def test_validation_error_format(self):
        """
        Test: Validation Error Response Format
        Documentation Reference: Error Response Formats -> Validation Error Response
        Validates: 422 validation error response format
        """
        # Test with invalid pagination parameters
        response = self.client.get('/api/v3/equipment?limit=-1')
        self.assertEqual(response.status_code, 422)
        
        data = response.json()
        
        # Validate error structure
        required_fields = ['error', 'message']
        for field in required_fields:
            self.assertIn(field, data, f"Missing required field: {field}")
        
        print("✅ Validation Error Format Test: PASSED")


class AuthenticationFormatTest(APIFormatValidationTest):
    """Test authentication formats match documentation."""
    
    def test_token_authentication_format(self):
        """
        Test: Token Authentication Format
        Documentation Reference: Authentication and Authorization -> Token Authentication
        Validates: Bearer token authentication works properly
        """
        # Test without authentication (should work for read endpoints)
        response = self.client.get('/api/v3/equipment')
        self.assertEqual(response.status_code, 200)
        
        # Test with authentication
        headers = self.get_auth_headers()
        response = self.client.get('/api/v3/equipment', **headers)
        self.assertEqual(response.status_code, 200)
        
        print("✅ Token Authentication Format Test: PASSED")


class PaginationFormatTest(APIFormatValidationTest):
    """Test pagination parameter formats match documentation."""
    
    def test_pagination_parameters(self):
        """
        Test: Pagination Parameters
        Documentation Reference: Equipment Endpoints -> Equipment List -> Query Parameters
        Validates: limit and offset parameters work correctly
        """
        # Test with specific pagination
        response = self.client.get('/api/v3/equipment?limit=2&offset=0')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        # Should respect limit (though we may not have enough test data)
        
        # Test invalid pagination parameters
        response = self.client.get('/api/v3/equipment?limit=0')
        self.assertEqual(response.status_code, 422)
        
        response = self.client.get('/api/v3/equipment?offset=-1')
        self.assertEqual(response.status_code, 422)
        
        print("✅ Pagination Parameters Test: PASSED")


class DataTypeValidationTest(APIFormatValidationTest):
    """Test data type specifications match documentation."""
    
    def test_data_type_specifications(self):
        """
        Test: Data Type Specifications
        Documentation Reference: Data Type Specifications
        Validates: Field types match documented specifications
        """
        response = self.client.get(f'/api/v3/equipment/{self.test_equipment.id}')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        # Validate specific data types as documented
        self.assertIsInstance(data['id'], int)  # Integer primary key
        self.assertIsInstance(data['title'], str)  # String max 255
        self.assertIsInstance(data['slug'], str)  # URL-safe string
        self.assertIsInstance(data['data_completeness'], (int, float))  # Float 0.0-1.0
        self.assertTrue(0.0 <= data['data_completeness'] <= 1.0)
        self.assertIn(data['specification_confidence'], ['low', 'medium', 'high'])  # Enum
        self.assertIn(data['source_type'], ['new', 'used', 'refurbished'])  # Enum
        self.assertIsInstance(data['needs_review'], bool)  # Boolean
        self.assertIsInstance(data['live'], bool)  # Boolean
        
        # Validate timestamp format (ISO 8601)
        if data['first_published_at']:
            datetime.fromisoformat(data['first_published_at'].replace('Z', '+00:00'))
        
        print("✅ Data Type Specifications Test: PASSED") 