import unittest
import json
import os
import sys

# Add the project root to the path so we can import the apps
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.ai_processing.utils import extract_universal_specifications

class TestUniversalSpecifications(unittest.TestCase):
    
    def test_no_models(self):
        """Test with no models."""
        data = {
            'title': 'Test Equipment',
            'specifications': []
        }
        result = extract_universal_specifications(data)
        self.assertEqual(result, data)
    
    def test_one_model(self):
        """Test with only one model - should not modify data."""
        data = {
            'title': 'Test Equipment',
            'specifications': [],
            'models': [
                {
                    'name': 'Model A',
                    'model_number': 'A-123',
                    'specifications': [
                        {
                            'name': 'Physical',
                            'specs': [
                                {'key': 'Height', 'value': '10 cm'},
                                {'key': 'Width', 'value': '20 cm'}
                            ]
                        }
                    ]
                }
            ]
        }
        result = extract_universal_specifications(data)
        # With just one model, all specs should be moved to universal level
        self.assertEqual(len(result['specifications']), 1)
        self.assertEqual(result['specifications'][0]['name'], 'Physical')
        self.assertEqual(len(result['specifications'][0]['specs']), 2)
        # Model should keep its specs (since they're universal by default)
        self.assertEqual(len(result['models'][0]['specifications']), 0)
    
    def test_multiple_models_with_common_specs(self):
        """Test with multiple models that have common specifications."""
        data = {
            'title': 'Test Equipment',
            'specifications': [],
            'models': [
                {
                    'name': 'Model A',
                    'model_number': 'A-123',
                    'specifications': [
                        {
                            'name': 'Physical',
                            'specs': [
                                {'key': 'Height', 'value': '10 cm'},  # Common
                                {'key': 'Width', 'value': '20 cm'},   # Common
                                {'key': 'Model-A-Only', 'value': 'Special Feature'}  # Model-specific
                            ]
                        },
                        {
                            'name': 'Performance',
                            'specs': [
                                {'key': 'Speed', 'value': 'Fast'},  # Common
                                {'key': 'A-Performance', 'value': 'Good'}  # Model-specific
                            ]
                        }
                    ]
                },
                {
                    'name': 'Model B',
                    'model_number': 'B-456',
                    'specifications': [
                        {
                            'name': 'Physical',
                            'specs': [
                                {'key': 'Height', 'value': '10 cm'},  # Common
                                {'key': 'Width', 'value': '20 cm'},   # Common
                                {'key': 'Model-B-Only', 'value': 'Extra Feature'}  # Model-specific
                            ]
                        },
                        {
                            'name': 'Performance',
                            'specs': [
                                {'key': 'Speed', 'value': 'Fast'},  # Common
                                {'key': 'B-Performance', 'value': 'Better'}  # Model-specific
                            ]
                        }
                    ]
                }
            ]
        }
        
        result = extract_universal_specifications(data)
        
        # Check universal specs are extracted
        physical_section = next((s for s in result['specifications'] if s['name'] == 'Physical'), None)
        self.assertIsNotNone(physical_section)
        self.assertEqual(len(physical_section['specs']), 2)  # Height and Width
        
        performance_section = next((s for s in result['specifications'] if s['name'] == 'Performance'), None)
        self.assertIsNotNone(performance_section)
        self.assertEqual(len(performance_section['specs']), 1)  # Speed
        
        # Check model A still has only its specific specs
        model_a = result['models'][0]
        model_a_physical = next((s for s in model_a['specifications'] if s['name'] == 'Physical'), None)
        self.assertIsNotNone(model_a_physical)
        self.assertEqual(len(model_a_physical['specs']), 1)  # Model-A-Only
        self.assertEqual(model_a_physical['specs'][0]['key'], 'Model-A-Only')
        
        model_a_performance = next((s for s in model_a['specifications'] if s['name'] == 'Performance'), None)
        self.assertIsNotNone(model_a_performance)
        self.assertEqual(len(model_a_performance['specs']), 1)  # A-Performance
        
        # Check model B still has only its specific specs
        model_b = result['models'][1]
        model_b_physical = next((s for s in model_b['specifications'] if s['name'] == 'Physical'), None)
        self.assertIsNotNone(model_b_physical)
        self.assertEqual(len(model_b_physical['specs']), 1)  # Model-B-Only
        self.assertEqual(model_b_physical['specs'][0]['key'], 'Model-B-Only')
        
        model_b_performance = next((s for s in model_b['specifications'] if s['name'] == 'Performance'), None)
        self.assertIsNotNone(model_b_performance)
        self.assertEqual(len(model_b_performance['specs']), 1)  # B-Performance
    
    def test_with_existing_universal_specs(self):
        """Test with existing universal specifications."""
        data = {
            'title': 'Test Equipment',
            'specifications': [
                {
                    'name': 'Physical',
                    'specs': [
                        {'key': 'Existing', 'value': 'Universal Feature'}
                    ]
                }
            ],
            'models': [
                {
                    'name': 'Model A',
                    'model_number': 'A-123',
                    'specifications': [
                        {
                            'name': 'Physical',
                            'specs': [
                                {'key': 'Height', 'value': '10 cm'},  # Common
                                {'key': 'Model-A-Only', 'value': 'Special Feature'}  # Model-specific
                            ]
                        }
                    ]
                },
                {
                    'name': 'Model B',
                    'model_number': 'B-456',
                    'specifications': [
                        {
                            'name': 'Physical',
                            'specs': [
                                {'key': 'Height', 'value': '10 cm'},  # Common
                                {'key': 'Model-B-Only', 'value': 'Extra Feature'}  # Model-specific
                            ]
                        }
                    ]
                }
            ]
        }
        
        result = extract_universal_specifications(data)
        
        # Check universal specs are merged with existing
        physical_section = next((s for s in result['specifications'] if s['name'] == 'Physical'), None)
        self.assertIsNotNone(physical_section)
        self.assertEqual(len(physical_section['specs']), 2)  # Existing + Height
        
        # Check the existing spec is still there
        existing_spec = next((s for s in physical_section['specs'] if s['key'] == 'Existing'), None)
        self.assertIsNotNone(existing_spec)
        
        # Check Height was added to universal
        height_spec = next((s for s in physical_section['specs'] if s['key'] == 'Height'), None)
        self.assertIsNotNone(height_spec)
        self.assertEqual(height_spec['value'], '10 cm')
    
    def test_with_different_values(self):
        """Test with specifications that have the same key but different values."""
        data = {
            'title': 'Test Equipment',
            'specifications': [],
            'models': [
                {
                    'name': 'Model A',
                    'model_number': 'A-123',
                    'specifications': [
                        {
                            'name': 'Physical',
                            'specs': [
                                {'key': 'Height', 'value': '10 cm'},  # Different in Model B
                                {'key': 'Width', 'value': '20 cm'}   # Common
                            ]
                        }
                    ]
                },
                {
                    'name': 'Model B',
                    'model_number': 'B-456',
                    'specifications': [
                        {
                            'name': 'Physical',
                            'specs': [
                                {'key': 'Height', 'value': '12 cm'},  # Different in Model A
                                {'key': 'Width', 'value': '20 cm'}   # Common
                            ]
                        }
                    ]
                }
            ]
        }
        
        result = extract_universal_specifications(data)
        
        # Check only common specs with same value are extracted
        physical_section = next((s for s in result['specifications'] if s['name'] == 'Physical'), None)
        self.assertIsNotNone(physical_section)
        self.assertEqual(len(physical_section['specs']), 1)  # Width only
        self.assertEqual(physical_section['specs'][0]['key'], 'Width')
        
        # Check both models still have their Height specs
        model_a = result['models'][0]
        model_a_physical = next((s for s in model_a['specifications'] if s['name'] == 'Physical'), None)
        self.assertIsNotNone(model_a_physical)
        self.assertEqual(len(model_a_physical['specs']), 1)  # Height only
        self.assertEqual(model_a_physical['specs'][0]['key'], 'Height')
        self.assertEqual(model_a_physical['specs'][0]['value'], '10 cm')
        
        model_b = result['models'][1]
        model_b_physical = next((s for s in model_b['specifications'] if s['name'] == 'Physical'), None)
        self.assertIsNotNone(model_b_physical)
        self.assertEqual(len(model_b_physical['specs']), 1)  # Height only
        self.assertEqual(model_b_physical['specs'][0]['key'], 'Height')
        self.assertEqual(model_b_physical['specs'][0]['value'], '12 cm')
    
    def test_with_empty_sections(self):
        """Test that empty sections are removed after extraction."""
        data = {
            'title': 'Test Equipment',
            'specifications': [],
            'models': [
                {
                    'name': 'Model A',
                    'model_number': 'A-123',
                    'specifications': [
                        {
                            'name': 'Physical',
                            'specs': [
                                {'key': 'Height', 'value': '10 cm'},  # Common
                                {'key': 'Width', 'value': '20 cm'}   # Common
                            ]
                        }
                    ]
                },
                {
                    'name': 'Model B',
                    'model_number': 'B-456',
                    'specifications': [
                        {
                            'name': 'Physical',
                            'specs': [
                                {'key': 'Height', 'value': '10 cm'},  # Common
                                {'key': 'Width', 'value': '20 cm'}   # Common
                            ]
                        }
                    ]
                }
            ]
        }
        
        result = extract_universal_specifications(data)
        
        # Check all specs were moved to universal
        physical_section = next((s for s in result['specifications'] if s['name'] == 'Physical'), None)
        self.assertIsNotNone(physical_section)
        self.assertEqual(len(physical_section['specs']), 2)  # Height and Width
        
        # Check models no longer have specification sections
        model_a = result['models'][0]
        self.assertEqual(len(model_a['specifications']), 0)
        
        model_b = result['models'][1]
        self.assertEqual(len(model_b['specifications']), 0)

if __name__ == '__main__':
    unittest.main() 