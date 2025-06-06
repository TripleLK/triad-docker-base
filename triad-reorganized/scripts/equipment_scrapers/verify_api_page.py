#!/usr/bin/env python
"""
Script to verify a lab equipment page was created correctly.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.abspath("."))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

# Import after Django setup
from apps.base_site.models import LabEquipmentPage

def verify_page(slug):
    """Verify the lab equipment page was created with correct data."""
    try:
        # Get the page
        page = LabEquipmentPage.objects.get(slug=slug)
        
        # Print basic details
        print(f"✅ Page found: ID={page.id}, Title='{page.title}'")
        print(f"Short description: {page.short_description}")
        print(f"Source URL: {page.source_url}")
        
        # Print features
        features = page.features.all()
        print(f"\nFeatures ({features.count()}):")
        for feature in features:
            print(f"  • {feature.feature}")
        
        # Print models
        models = page.models.all()
        print(f"\nModels ({models.count()}):")
        for model in models:
            print(f"  • {model.name} (Model #: {model.model_number})")
            
            # Print model specs if any
            for spec_group in model.spec_groups.all():
                print(f"    • {spec_group.name}:")
                for spec in spec_group.specs.all():
                    print(f"      - {spec.key}: {spec.value}")
        
        # Print page specs
        print("\nPage Specifications:")
        for spec_group in page.spec_groups.all():
            print(f"  • {spec_group.name}:")
            for spec in spec_group.specs.all():
                print(f"    - {spec.key}: {spec.value}")
                
        return True
    except LabEquipmentPage.DoesNotExist:
        print(f"❌ Page with slug '{slug}' not found")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        slug = sys.argv[1]
    else:
        slug = 'api-test-spectrometer-1747238714'  # Default to our test page
        
    verify_page(slug) 