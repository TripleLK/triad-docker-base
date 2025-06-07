from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.template.response import TemplateResponse
from django.db.models import Count, Q
from django.http import Http404
from django.contrib.contenttypes.models import ContentType

from wagtail.models import Page
from apps.base_site.models import LabEquipmentPage, MultiProductPage
from apps.categorized_tags.models import CategorizedTag, TagCategory

# To enable logging of search queries for use with the "Promoted search results" module
# <https://docs.wagtail.org/en/stable/reference/contrib/searchpromotions.html>
# uncomment the following line and the lines indicated in the search function
# (after adding wagtail.contrib.search_promotions to INSTALLED_APPS):

# from wagtail.contrib.search_promotions.models import Query


def search(request):
    search_query = request.GET.get("query", None)
    page_num = request.GET.get("page", 1)
    
    # Start with all live equipment pages - get the base Page objects
    # This is important because Wagtail pages are stored in the main Page table
    labequipment_content_type = ContentType.objects.get_for_model(LabEquipmentPage)
    base_pages = Page.objects.live().filter(
        content_type=labequipment_content_type
    )
    
    # Apply search if provided
    if search_query:
        # Search happens on the specific pages
        specific_pages = LabEquipmentPage.objects.live()
        search_results = specific_pages.search(search_query)
        
        # Get the IDs from the search results
        result_ids = [result.id for result in search_results]
        
        # Filter the base pages by these IDs
        if result_ids:
            base_pages = base_pages.filter(id__in=result_ids)
        else:
            # No results found
            base_pages = Page.objects.none()
            
        # To log this query for use with the "Promoted search results" module:
        # query = Query.get(search_query)
        # query.add_hit()
    
    # Get all tag categories for building the filter component
    tag_categories = TagCategory.objects.all().order_by('name')
    
    # Create a dictionary of category names to their colors for later use
    category_colors = {category.name: category.color for category in tag_categories}
    
    # Keep track of applied filters
    applied_filters = {}
    
    # Process tag filters from URL parameters
    for category in tag_categories:
        # URL parameter format: ?manufacturer=AirScience&manufacturer=Other&type=Fume+Hood
        category_values = request.GET.getlist(category.name.lower())
        if category_values:
            # Store applied filters for displaying in template
            applied_filters[category.name] = category_values
            
            # Get tag IDs for the selected category values
            tag_ids = CategorizedTag.objects.filter(
                category=category.name,
                name__in=category_values
            ).values_list('id', flat=True)
            
            # Get page IDs that have these tags
            # Using categorized_tagged_items relationship defined in CategorizedPageTag
            page_ids_with_tag = Page.objects.filter(
                categorized_tagged_items__tag_id__in=tag_ids
            ).values_list('id', flat=True)
            
            # Filter base pages to include only those with matching tags
            if page_ids_with_tag:
                base_pages = base_pages.filter(id__in=page_ids_with_tag)
            else:
                # No pages match this filter
                base_pages = Page.objects.none()
                break
    
    # Get the IDs of the filtered base pages
    page_ids = list(base_pages.values_list('id', flat=True))
    
    # Get available tags for each category with counts
    available_filters = {}
    if page_ids:  # Only process if we have results
        # Convert to specific pages for tag counting
        specific_pages = LabEquipmentPage.objects.filter(page_ptr_id__in=page_ids)
        
        for category in tag_categories:
            # Get tags that are used by any of the specific pages
            # Get through the categorized_tagged_items relationship
            tag_ids = (CategorizedTag.objects
                      .filter(category=category.name)
                      .filter(categorized_tags_categorizedpagetag_items__content_object__in=specific_pages)
                      .values_list('id', flat=True)
                      .distinct())
            
            if tag_ids:
                # Get the tags with counts
                tags_with_counts = (
                    CategorizedTag.objects
                    .filter(id__in=tag_ids)
                    .annotate(page_count=Count('categorized_tags_categorizedpagetag_items',
                                              filter=Q(categorized_tags_categorizedpagetag_items__content_object__in=specific_pages)))
                    .values('name', 'page_count')
                    .order_by('name')
                )
                
                # Add the category color to each tag
                tags_list = list(tags_with_counts)
                for tag in tags_list:
                    tag['category_color'] = category_colors.get(category.name, '#777777')
                    
                if tags_list:
                    available_filters[category.name] = tags_list
    
    # Get specific pages for the results (with full data)
    specific_pages = []
    if page_ids:
        specific_pages = [p.specific for p in base_pages]
    
    # Pagination
    paginator = Paginator(specific_pages, 12)  # Show 12 products per page
    try:
        search_results = paginator.page(page_num)
    except PageNotAnInteger:
        search_results = paginator.page(1)
    except EmptyPage:
        search_results = paginator.page(paginator.num_pages)

    # Get the MultiProductPage to use its template
    try:
        multi_product_page = MultiProductPage.objects.live().first()
    except MultiProductPage.DoesNotExist:
        multi_product_page = None

    # Process results to make sure we call main_image() as a method, not a property
    for result in search_results:
        # Ensure main_image is called as a method
        if hasattr(result, 'main_image') and callable(result.main_image):
            result.main_image_url = result.main_image()
        else:
            result.main_image_url = None

    return TemplateResponse(
        request,
        "base_site/multi_product_page.html",  # Use the MultiProductPage template
        {
            "page": multi_product_page,  # Pass the page for consistent template rendering
            "search_query": search_query,
            "search_results": search_results,
            "is_search_results": True,  # Flag to indicate these are search results
            "tag_categories": tag_categories,
            "available_filters": available_filters,
            "applied_filters": applied_filters,
        },
    )

def category_view(request, category_slug, value_slug):
    """
    Dedicated view for specific category pages, e.g. /category/manufacturer/airscience/
    This pre-applies a filter for the specified category and value.
    """
    # Look up the category and value from the slugs
    try:
        tag = CategorizedTag.objects.get(slug__iexact=f"{category_slug}-{value_slug}")
        
        # Add additional check to prevent errors with empty category
        if not tag.category:
            # Fix the tag by adding a generic category if it's missing
            tag.category = "General"
            tag.save()
            
    except CategorizedTag.DoesNotExist:
        raise Http404(f"No tag found for {category_slug}: {value_slug}")
    
    # Add the filter to the request
    request.GET = request.GET.copy()  # Make it mutable
    request.GET.setdefault(tag.category.lower(), [])
    request.GET.appendlist(tag.category.lower(), tag.name)
    
    # Get the page title
    page_title = f"{tag.name} {tag.category}"
    
    # Call the search view with the modified request
    response = search(request)
    
    # Add some custom context for the category page
    response.context_data.update({
        'category_page_title': page_title,
        'category_slug': category_slug,
        'value_slug': value_slug,
        'is_category_page': True,
    })
    
    return response
