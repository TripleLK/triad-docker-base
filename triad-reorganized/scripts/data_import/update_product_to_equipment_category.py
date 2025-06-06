#!/usr/bin/env python
"""
One-time script to update all "Product Category" tags to "Equipment Category"
"""

import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

# Import Django models after setup
from apps.categorized_tags.models import CategorizedTag, TagCategory

def update_product_to_equipment_category():
    """
    Updates all tags with category "Product Category" to "Equipment Category"
    """
    # First check if Equipment Category exists, if not create it
    equipment_category, created = TagCategory.objects.get_or_create(
        name="Equipment Category",
        defaults={"color": "hsl(220, 65%, 75%)"}  # Blue color
    )
    
    if created:
        print(f"Created new category: Equipment Category")
    
    # Get all Product Category tags
    product_tags = CategorizedTag.objects.filter(category="Product Category")
    tag_count = product_tags.count()
    
    if tag_count == 0:
        print("No Product Category tags found.")
        return
    
    print(f"Found {tag_count} Product Category tags to update:")
    for tag in product_tags:
        print(f"- {tag.name}")
    
    # Update each tag to use Equipment Category
    for tag in product_tags:
        # Check if a tag with the same name already exists in Equipment Category
        existing_tag = CategorizedTag.objects.filter(
            category="Equipment Category",
            name=tag.name
        ).first()
        
        if existing_tag:
            print(f"Tag '{tag.name}' already exists in Equipment Category. Merging...")
            # Move all page associations from product tag to existing equipment tag
            for page_tag in tag.categorized_tags_categorizedpagetag_items.all():
                # Check if this page is already tagged with the equipment tag
                if not page_tag.content_object.categorized_tagged_items.filter(tag=existing_tag).exists():
                    # Create new association with the equipment tag
                    page_tag.content_object.categorized_tags.add(existing_tag)
                    print(f"  - Moved page {page_tag.content_object.id} to existing Equipment Category tag")
            
            # Delete the product tag
            tag.delete()
            print(f"  - Deleted Product Category tag '{tag.name}'")
        else:
            # Update the tag's category
            old_name = tag.name
            tag.category = "Equipment Category"
            tag.save()
            print(f"Updated tag '{old_name}' to Equipment Category")
    
    # Check if there are any Product Category tags left
    remaining = CategorizedTag.objects.filter(category="Product Category").count()
    print(f"Update complete. {remaining} Product Category tags remaining.")
    
    # Try to delete the Product Category if it's empty
    try:
        product_category = TagCategory.objects.get(name="Product Category")
        if CategorizedTag.objects.filter(category="Product Category").count() == 0:
            product_category.delete()
            print("Deleted empty Product Category")
    except TagCategory.DoesNotExist:
        print("Product Category already deleted")

if __name__ == "__main__":
    update_product_to_equipment_category() 