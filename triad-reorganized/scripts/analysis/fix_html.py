#!/usr/bin/env python
"""
Script to fix malformed HTML in Wagtail rich text fields.
"""
import os
import django
import re

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.base_site.models import LabEquipmentPage

def fix_lab_equipment_html(page_id):
    """
    Fix malformed HTML in the full_description field of a LabEquipmentPage.
    Specifically addressing the issue with unmatched <br> and </p> tags.
    """
    try:
        page = LabEquipmentPage.objects.get(id=page_id)
        print(f"Fixing HTML for page: {page.title}")
        
        # Get current content
        content = page.full_description
        print(f"Original content: {content[:150]}...")
        
        # Fix approach: Convert the content to proper paragraphs
        if content.startswith('<p>'):
            # Remove the initial <p> tag
            content = content[3:]
            # Split by <br> tags
            parts = re.split(r'<br>|<br/>', content)
            # Create proper paragraphs
            fixed_content = ''
            for part in parts:
                part = part.strip()
                if part:
                    # Remove any closing </p> tags
                    part = part.replace('</p>', '')
                    fixed_content += f'<p>{part}</p>'
            
            # Save the fixed content
            page.full_description = fixed_content
            
            # Create a revision and publish
            revision = page.save_revision()
            revision.publish()
            print("✅ Fixed and published the page")
            return True
        else:
            print("Content format is different than expected, manual inspection needed")
            return False
    
    except LabEquipmentPage.DoesNotExist:
        print(f"❌ Error: Page with ID {page_id} not found")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        page_id = int(sys.argv[1])
    else:
        page_id = 46  # Default to page 46 based on the error
    
    success = fix_lab_equipment_html(page_id)
    if success:
        print(f"Successfully fixed HTML for page ID {page_id}")
    else:
        print(f"Failed to fix HTML for page ID {page_id}") 