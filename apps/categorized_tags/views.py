from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count
from django.views.decorators.http import require_GET
from .models import TagCategory, CategorizedTag
from apps.base_site.auth import token_required

# Create your views here.

@require_GET
@token_required
def get_tags_api(request):
    """
    API endpoint to retrieve all tags in a hierarchical format
    
    Query parameters:
        - min_count: Minimum number of pages using a tag (default: 0)
        - category: Filter by specific category (optional)
    
    Returns:
        JSON with categories and their tags
    """
    min_count = int(request.GET.get('min_count', 0))
    category_filter = request.GET.get('category')
    
    # Get all tag categories
    categories = TagCategory.objects.all().order_by('name')
    
    # If category filter is provided, filter the categories
    if category_filter:
        categories = categories.filter(name__iexact=category_filter)
    
    # Dictionary to store the hierarchical tag data
    tag_hierarchy = {}
    
    for category in categories:
        # Get tags for this category
        tags = CategorizedTag.objects.filter(category=category.name)
        
        # Sort tags by name
        tags = tags.order_by('name')
        
        # Create a list for tag data
        tag_data = []
        
        # For each tag, calculate its usage count directly
        for tag in tags:
            # Get the direct count of related page tags
            page_count = tag.categorized_tags_categorizedpagetag_items.count()
            
            # Filter by minimum count if specified
            if page_count >= min_count:
                tag_data.append({'name': tag.name, 'count': page_count})
        
        # Add to hierarchy if there are any tags
        if tag_data:
            tag_hierarchy[category.name] = {
                'color': category.color,
                'tags': tag_data
            }
    
    return JsonResponse(tag_hierarchy)
