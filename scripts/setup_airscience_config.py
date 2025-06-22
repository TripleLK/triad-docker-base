#!/usr/bin/env python
"""
Setup AirScience site configuration for XPath content extraction.

Created by: Joyful Shoe
Date: 2024-12-30
Project: Triad Docker Base
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.contrib.auth.models import User
from apps.xpath_content_extraction.models import SiteConfiguration, FieldConfiguration


def setup_airscience_configuration():
    """Create AirScience site configuration and field configurations."""
    
    print("Setting up AirScience configuration...")
    
    # Get or create admin user for created_by field
    admin_user = User.objects.filter(is_superuser=True).first()
    
    # Create or update SiteConfiguration
    site_config, created = SiteConfiguration.objects.get_or_create(
        name="AirScience",
        defaults={
            'domain': 'https://www.airscience.com',
            'description': 'AirScience laboratory equipment website - primary target for content extraction',
            'is_active': True,
            'default_page_url': 'https://www.airscience.com/products',
            'created_by': admin_user,
        }
    )
    
    if created:
        print(f"✅ Created SiteConfiguration: {site_config}")
    else:
        print(f"ℹ️  SiteConfiguration already exists: {site_config}")
    
    # Field configurations based on archived content_extractor analysis
    field_configs = [
        {
            'field_name': 'full_description',
            'field_type': 'text',
            'display_name': 'Full Description',
            'description': 'Complete product description with features and benefits',
            'is_required': True,
            'processing_notes': 'Main product description, usually in paragraphs with feature lists'
        },
        {
            'field_name': 'short_description',
            'field_type': 'text',
            'display_name': 'Short Description',
            'description': 'Brief product summary or tagline',
            'is_required': False,
            'processing_notes': 'Concise product summary, often appears near title'
        },
        {
            'field_name': 'model_names',
            'field_type': 'list',
            'display_name': 'Model Names',
            'description': 'List of available product models/variations',
            'is_required': False,
            'processing_notes': 'Product variations, model numbers, size options'
        },
        {
            'field_name': 'model_specifications',
            'field_type': 'nested',
            'display_name': 'Model Specifications',
            'description': 'Technical specifications for each model',
            'is_required': False,
            'processing_notes': 'Technical specs per model - dimensions, capacity, power, etc.'
        },
        {
            'field_name': 'technical_info_tables',
            'field_type': 'nested',
            'display_name': 'Technical Info Tables',
            'description': 'Structured technical information in table format',
            'is_required': False,
            'processing_notes': 'Tables with dimensions, filters, applications, technical data'
        },
        {
            'field_name': 'product_images',
            'field_type': 'list',
            'display_name': 'Product Images',
            'description': 'Product image URLs and gallery',
            'is_required': False,
            'processing_notes': 'Image gallery with preserved HTML structure and URLs'
        }
    ]
    
    # Create field configurations
    created_fields = []
    existing_fields = []
    
    for field_data in field_configs:
        field_config, created = FieldConfiguration.objects.get_or_create(
            site_config=site_config,
            field_name=field_data['field_name'],
            defaults=field_data
        )
        
        if created:
            created_fields.append(field_config)
        else:
            existing_fields.append(field_config)
    
    print(f"\n📋 Field Configuration Results:")
    print(f"✅ Created {len(created_fields)} new field configurations:")
    for field in created_fields:
        print(f"   - {field.display_name} ({field.field_name})")
    
    if existing_fields:
        print(f"ℹ️  {len(existing_fields)} field configurations already existed:")
        for field in existing_fields:
            print(f"   - {field.display_name} ({field.field_name})")
    
    print(f"\n🎯 Configuration Summary:")
    print(f"Site: {site_config.name}")
    print(f"Domain: {site_config.domain}")
    print(f"Default URL: {site_config.default_page_url}")
    print(f"Total Fields: {site_config.fields.count()}")
    print(f"Active: {site_config.is_active}")
    
    print(f"\n🔧 Next Steps:")
    print(f"1. Use Chrome extension to connect to Django API")
    print(f"2. Select AirScience site configuration")
    print(f"3. Navigate to product pages and create XPath selectors")
    print(f"4. Test extraction workflow")
    
    return site_config


if __name__ == '__main__':
    try:
        site_config = setup_airscience_configuration()
        print(f"\n✅ AirScience configuration setup completed successfully!")
        print(f"Site Configuration ID: {site_config.pk}")
    except Exception as e:
        print(f"\n❌ Error setting up configuration: {e}")
        import traceback
        traceback.print_exc() 