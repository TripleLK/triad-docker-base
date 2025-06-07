from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from .models import CategorizedTag, TagCategory
from django.utils.html import format_html
from django.templatetags.static import static
from wagtail import hooks
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
import json

class TagCategoryViewSet(SnippetViewSet):
    model = TagCategory
    icon = 'folder-open-inverse'
    list_display = ('name', 'color', 'tag_count')
    search_fields = ('name',)
    
    # Set template names explicitly
    index_template_name = 'wagtailsnippets/snippets/index.html'
    create_template_name = 'wagtailsnippets/snippets/create.html'
    edit_template_name = 'wagtailsnippets/snippets/edit.html'
    inspect_view_enabled = True
    
    def get_inspect_template(self):
        return 'wagtailsnippets/snippets/categorized_tags/tagcategory.html'
    
    def get_context_data(self, **kwargs):
        """Add the tags belonging to this category to the context"""
        context = super().get_context_data(**kwargs)
        
        if 'object' in context:
            category = context['object']
            context['tags'] = CategorizedTag.objects.filter(category=category.name)
        
        return context

class CategorizedTagViewSet(SnippetViewSet):
    model = CategorizedTag
    icon = 'tag'
    list_display = ('category', 'name')
    list_filter = ('category',)
    search_fields = ('name', 'category')
    
    # Add ordering
    ordering = ['category', 'name']
    
    # Set template names explicitly
    index_template_name = 'wagtailsnippets/snippets/index.html'
    create_template_name = 'wagtailsnippets/snippets/create.html'
    edit_template_name = 'wagtailsnippets/snippets/edit.html'
    inspect_view_enabled = True
    
    def get_inspect_template(self):
        return 'wagtailsnippets/snippets/categorized_tags/categorizedtag.html'

register_snippet(TagCategoryViewSet)
register_snippet(CategorizedTagViewSet)

@hooks.register('insert_global_admin_css')
def global_admin_css():
    return format_html('<link rel="stylesheet" href="{}">', static('css/jquery.tagit.css'))

@hooks.register('insert_global_admin_js')
def global_admin_js():
    return format_html('<script src="{}"></script>', static('js/tag-it.min.js'))

@hooks.register('insert_editor_js')
def editor_js():
    return format_html(
        '<script>window.categoryTagCategories = {};</script>',
        json.dumps(list(TagCategory.objects.values_list('name', flat=True)))
    )

@hooks.register('insert_editor_css')
def editor_css():
    """Add category colors to the editor"""
    categories = TagCategory.objects.all()
    return format_html(render_to_string('categorized_tags/admin_styles.html', {'categories': categories}))