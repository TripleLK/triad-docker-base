# myapp/wagtail_hooks.py

from django.urls import path, reverse
from django.utils.safestring import mark_safe
from wagtail import hooks
from django.templatetags.static import static
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from wagtail.admin.menu import MenuItem
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .models import APIToken, LabEquipmentPage
from django.contrib.auth.decorators import permission_required
from wagtail.admin.ui.tables import Column, DateColumn
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models
from wagtail.models import Site

@hooks.register('insert_global_admin_js')
def labequipment_editor_js():
    return mark_safe(f'<script src="{static("admin/js/labequipment_controller.js")}"></script>')

# Register API Token as a snippet
class APITokenViewSet(SnippetViewSet):
    model = APIToken
    icon = "key"
    list_display = ['name', 'created_at', 'is_active']
    search_fields = ['name', 'description']
    list_filter = ['is_active']
    
    # Don't expose the token in the admin interface for security
    exclude_form_fields = ['token']

register_snippet(APITokenViewSet)

# The old AI-Generated Drafts functionality has been replaced by the new implementation
# in apps/ai_processing/wagtail_hooks.py

@hooks.register('after_create_page')
def redirect_after_page_create(request, page):
    """After saving a new page, go straight to edit rather than explorer."""
    return redirect('wagtailadmin_pages:edit', page.id)

def get_homepage_id():
    """Helper function to get the home page ID."""
    try:
        site = Site.objects.get(is_default_site=True)
        return site.root_page.id
    except:
        # Fallback to a reasonable default if we can't get the root page
        return 2  # Default Wagtail home page ID
