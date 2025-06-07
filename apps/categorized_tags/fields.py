from django import forms
from taggit.forms import TagField
from .models import CategorizedTag
import logging

# Set up logging
logger = logging.getLogger(__name__)

class CategoryTagField(TagField):
    """Custom field for handling CategoryTags."""
    
    def clean(self, value):
        if value:
            # Handle string values - expected format: 'Category: Tag Name, Another Category: Tag Name'
            if isinstance(value, str):
                # Split the input by comma
                items = [item.strip() for item in value.split(',') if item.strip()]
                result = []
                for item in items:
                    # Extract category and name from 'Category: Tag Name' format
                    parts = item.split(':', 1)
                    if len(parts) == 2:
                        category = parts[0].strip()
                        name = parts[1].strip()
                        
                        # Create or get the tag
                        tag, created = CategorizedTag.objects.get_or_create(
                            category=category, 
                            name=name
                        )
                        result.append(tag)
                        
                        if created:
                            logger.info(f"Created new tag: {tag}")
                    
                return result
            # If already a cleaned list of tags
            if isinstance(value, list) and all(isinstance(item, CategorizedTag) for item in value):
                return value
                
        return super().clean(value)