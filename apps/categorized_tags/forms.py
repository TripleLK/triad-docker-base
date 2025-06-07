from django import forms
from taggit.forms import TagField
from wagtail.admin.forms import WagtailAdminPageForm
from .fields import CategoryTagField
from .widgets import CategoryTagWidget
import logging

# Get a logger to output debug info
logger = logging.getLogger(__name__)

class CategoryTagForm(WagtailAdminPageForm):
    """Form for handling categorized tags"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Replace the tag field with our custom one
        if 'categorized_tags' in self.fields:
            self.fields['categorized_tags'] = CategoryTagField(
                required=False,
                help_text=self.fields['categorized_tags'].help_text
            )
            # Also set the widget
            self.fields['categorized_tags'].widget = CategoryTagWidget()
    
    def save_instance(self):
        result = super().save_instance()
        return result
