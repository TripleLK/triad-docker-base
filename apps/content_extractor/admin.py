"""
Django Admin configuration for Content Extractor models.
"""

from django.contrib import admin
from .models import ExtractionProject, AnalyzedPage, ContentSelector, SelectionSession

@admin.register(ExtractionProject)
class ExtractionProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'domain', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'domain', 'description')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(AnalyzedPage) 
class AnalyzedPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'project', 'analyzed_at')
    list_filter = ('project', 'analyzed_at')
    search_fields = ('title', 'url')
    readonly_fields = ('analyzed_at', 'content_hash')

@admin.register(ContentSelector)
class ContentSelectorAdmin(admin.ModelAdmin):
    list_display = ('label', 'project', 'confidence_score', 'is_generalized', 'created_at')
    list_filter = ('project', 'is_generalized', 'created_by_human')
    search_fields = ('label', 'xpath')
    readonly_fields = ('created_at',)

@admin.register(SelectionSession)
class SelectionSessionAdmin(admin.ModelAdmin):
    list_display = ('project', 'started_at', 'completed_at', 'current_page_index')
    list_filter = ('started_at', 'completed_at')
    readonly_fields = ('started_at',)
