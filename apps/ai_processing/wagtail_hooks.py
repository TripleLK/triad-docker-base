from django.urls import path, include, reverse
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.templatetags.static import static
from wagtail import hooks
from wagtail.admin.menu import MenuItem, Menu, SubmenuMenuItem
from django.contrib.admin.utils import quote
from wagtail.admin.filters import WagtailFilterSet
from django_filters import BooleanFilter
from apps.base_site.models import LabEquipmentPage
from wagtail.admin.widgets.button import Button
from wagtail_modeladmin.options import (
    ModelAdmin, ModelAdminGroup, modeladmin_register
)

from .models import SelectorConfiguration, URLProcessingRequest
from . import urls


class SelectorConfigurationAdmin(ModelAdmin):
    """Wagtail admin interface for SelectorConfiguration model."""
    model = SelectorConfiguration
    menu_label = 'Selector Configurations'
    menu_icon = 'snippet'
    menu_order = 200
    add_to_settings_menu = False
    list_display = ('name', 'description', 'created_by', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description')


class AIProcessingAdminGroup(ModelAdminGroup):
    """Group for AI Processing related models in Wagtail admin."""
    menu_label = 'AI Processing'
    menu_icon = 'cogs'
    menu_order = 800
    items = (SelectorConfigurationAdmin,)


# Register the SelectorConfigurationAdmin but NOT the group
# This registers the model for CRUD operations without creating a menu entry
modeladmin_register(SelectorConfigurationAdmin)

# Comment out or remove the following line to prevent duplicate menu registration
# modeladmin_register(AIProcessingAdminGroup)


@hooks.register('register_admin_urls')
def register_admin_urls():
    """Register the ai_processing URLs in the Wagtail admin."""
    return [
        path('ai-processing/', include('apps.ai_processing.urls', namespace='ai_processing')),
    ]


# Create a menu for the AI Processing section
@hooks.register('register_admin_menu_item')
def register_ai_processing_menu():
    # Create a submenu for AI Processing
    submenu = Menu(items=[
        MenuItem('URL Processing', '/admin/ai-processing/', icon_name='doc-empty', order=100),
        # Add the Selector Configuration menu item under AI Processing
        MenuItem(
            'Selector Configurations',
            '/admin/ai_processing/selectorconfiguration/',
            icon_name='snippet',
            order=200
        ),
        # Move AI-Generated Pages to the bottom and rename to All Pages
        MenuItem(
            'Review AI-Generated Pages',
            reverse('wagtailadmin_explore', args=[get_homepage_id()]) + '?p_type=ai_generated',
            icon_name='doc-empty',
            order=900
        ),
    ])
    
    # Return the menu as a submenu item
    return SubmenuMenuItem('AI Processing', submenu, icon_name='cogs', order=800)


# Add a separate top-level menu item for Lab Equipment
@hooks.register('register_admin_menu_item')
def register_lab_equipment_menu():
    # Get the home page ID
    homepage_id = get_homepage_id()
    
    # Return a top-level menu item for Lab Equipment that links to the children of home page
    return MenuItem(
        'Lab Equipment', 
        reverse('wagtailadmin_explore', args=[homepage_id]),
        icon_name='view', # Using 'view' icon which looks like a microscope/lens
        order=200,
        classnames='lab-equipment-menu'
    )


# Add custom JavaScript to handle active state for the Lab Equipment menu
@hooks.register('insert_global_admin_js')
def lab_equipment_menu_js():
    # This script will mark the Lab Equipment menu item as active when viewing the homepage children
    return format_html(
        '<script>'
        'document.addEventListener("DOMContentLoaded", function() {{'
        '    // Check if we\'re in the page explorer for the home page'
        '    if (window.location.pathname.includes("/admin/pages/") && '
        '        window.location.href.includes("/explore/")) {{'
        '        // Mark the Lab Equipment menu as active'
        '        const menuItem = document.querySelector(".lab-equipment-menu");'
        '        if (menuItem) {{'
        '            menuItem.classList.add("menu-active");'
        '        }}'
        '    }}'
        '}});'
        '</script>'
    )


# Helper function to get the home page ID
def get_homepage_id():
    from wagtail.models import Site
    try:
        site = Site.objects.get(is_default_site=True)
        root_page_id = site.root_page.id
    except:
        # Fallback to a reasonable default if we can't get the root page
        root_page_id = 2  # Default Wagtail home page ID
    return root_page_id


class LabEquipmentPageFilter(WagtailFilterSet):
    """Filter for LabEquipmentPage in the admin interface."""
    needs_review = BooleanFilter(
        field_name='needs_review',
        label='AI-Generated',
        help_text='Show only pages created by AI that need review'
    )
    
    class Meta:
        model = LabEquipmentPage
        fields = ['needs_review', 'live']


@hooks.register('construct_explorer_page_queryset')
def filter_pages_by_ai_generation(parent_page, pages, request):
    """Filter pages in the explorer based on custom parameter."""
    if request.GET.get('p_type') == 'ai_generated':
        # Get the IDs of LabEquipmentPages that have needs_review=True
        ai_page_ids = LabEquipmentPage.objects.filter(
            needs_review=True, 
            live=False
        ).values_list('id', flat=True)
        
        # Then filter the pages queryset by these IDs
        if ai_page_ids:
            pages = pages.filter(id__in=ai_page_ids)
        else:
            # If no pages with needs_review, return an empty queryset
            pages = pages.none()
            
    return pages


@hooks.register('register_page_listing_buttons')
def page_listing_ai_indicator(page, page_perms, is_parent=False, next_url=None):
    """Add an indicator button to show that a page was AI-generated."""
    if hasattr(page, 'needs_review') and page.needs_review:
        yield Button(
            label='AI-Generated',
            attrs={
                'title': 'This page was created by AI and needs review',
                'aria-label': 'This page was created by AI and needs review'
            },
            classname='button-small button-secondary',
            priority=30
        )


# Reorder and rename the main menu items
@hooks.register('construct_main_menu')
def reorder_main_menu(request, menu_items):
    """
    Modify the main menu:
    1. Move Pages to the bottom and rename to All Pages
    2. Remove Reports
    3. Hide SelectorConfiguration from top level menu
    4. Remove Documents
    5. Move Images down
    """
    # Find the menu items
    pages_item = None
    reports_item = None
    selector_config_item = None
    documents_item = None
    images_item = None
    
    # Identify items to modify
    for item in menu_items:
        if item.name == 'explorer':  # 'explorer' is the name of the Pages menu item
            pages_item = item
        elif item.name == 'reports':  # Remove reports menu
            reports_item = item
        elif getattr(item, 'label', '') == 'Selector Configurations':  # Remove Selector Configurations from top level
            selector_config_item = item
        elif item.name == 'documents':  # Remove documents menu
            documents_item = item
        elif item.name == 'images':  # Move images menu down
            images_item = item
    
    # Remove Pages from its current position
    if pages_item:
        menu_items.remove(pages_item)
        # Rename it to "All Pages"
        pages_item.label = "All Pages"
        # Add it back at the end with a high order value
        pages_item.order = 9000
        menu_items.append(pages_item)
    
    # Remove Reports menu item
    if reports_item:
        menu_items.remove(reports_item)
    
    # Remove Selector Configurations from top level menu
    if selector_config_item:
        menu_items.remove(selector_config_item)
    
    # Remove Documents menu item
    if documents_item:
        menu_items.remove(documents_item)
    
    # Move Images down
    if images_item:
        menu_items.remove(images_item)
        # Add it back with a higher order value
        images_item.order = 8000
        menu_items.append(images_item)
    
    # Sort the menu items by order
    menu_items.sort(key=lambda x: x.order) 