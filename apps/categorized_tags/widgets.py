from django import forms
from django.template.loader import render_to_string
from taggit.forms import TagWidget
import logging

# Set up logging
logger = logging.getLogger(__name__)

class ColorPickerWidget(forms.TextInput):
    template_name = 'categorized_tags/widgets/color_picker_widget.html'
    
    class Media:
        css = {
            'all': ('admin/css/spectrum.css',)
        }
        js = ('admin/js/spectrum.js',)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs.update({'class': 'color-picker'})

class CategoryTagWidget(TagWidget):
    template_name = 'categorized_tags/widgets/category_tag_widget.html'
    
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        
        # Import models inside the method to avoid circular imports
        from .models import CategorizedTag, TagCategory
        
        # If value is a list of objects, convert to strings
        if value and isinstance(value, (list, tuple)) and hasattr(value[0], 'category'):
            # The value is a list of CategorizedTag objects
            value_strings = [f"{tag.category}: {tag.name}" for tag in value]
            context['widget']['value'] = value_strings
            
            logger.info(f"Setting widget value to: {value_strings}")
        
        # Add existing tags for the autocomplete
        existing_tags = [
            {
                'id': tag.id, 
                'text': f"{tag.category}: {tag.name}",
                'category': tag.category,
                'category_color': tag.category_color
            } 
            for tag in CategorizedTag.objects.all()
        ]
        context['widget']['existing_tags'] = existing_tags
        
        # Get existing categories for category dropdown
        categories = TagCategory.objects.all().order_by('name')
        
        # Convert to list of category data
        category_data = []
        for cat in categories:
            category_data.append({
                'id': cat.id,
                'name': cat.name,
                'color': cat.color
            })
            
        context['widget']['categories'] = category_data
        
        # Log for debugging
        logger.info(f"Widget context: value={value}, tags count={len(existing_tags)}")
        
        return context
