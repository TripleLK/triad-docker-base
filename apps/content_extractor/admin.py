"""
Django Admin configuration for Content Extractor models.
"""

from django.contrib import admin
from .models import (
    ExtractionProject, AnalyzedPage, ContentSelector, SelectionSession,
    SiteFieldSelector, SelectorTestResult, FieldSelectionSession, AIPreparationRecord
)

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

@admin.register(AIPreparationRecord)
class AIPreparationRecordAdmin(admin.ModelAdmin):
    """Admin interface for AI Preparation Records."""
    
    list_display = (
        'session_id', 'field_name', 'instance_index', 
        'content_preview', 'content_type', 'confidence_level', 
        'validation_status', 'extraction_timestamp'
    )
    list_filter = (
        'content_type', 'confidence_level', 'validation_status', 
        'extraction_method', 'extraction_timestamp'
    )
    search_fields = ('session_id', 'field_name', 'extracted_content', 'user_comment')
    readonly_fields = ('extraction_timestamp', 'created_at', 'updated_at', 'content_preview')
    
    fieldsets = (
        ('Identification', {
            'fields': ('session_id', 'source_url', 'extraction_timestamp')
        }),
        ('Content', {
            'fields': ('field_name', 'instance_index', 'extracted_content', 'content_type')
        }),
        ('Selectors', {
            'fields': ('xpath_used', 'css_selector_used'),
            'classes': ('collapse',)
        }),
        ('AI Context', {
            'fields': ('user_comment', 'extraction_method', 'confidence_level')
        }),
        ('Processing', {
            'fields': ('validation_status', 'preprocessing_notes'),
            'classes': ('collapse',)
        }),
        ('Relationships', {
            'fields': ('parent_record',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        """Display content preview in admin list."""
        return obj.content_preview
    content_preview.short_description = 'Content Preview'
    
    def get_queryset(self, request):
        """Optimize queryset for admin display."""
        return super().get_queryset(request).select_related('parent_record')
