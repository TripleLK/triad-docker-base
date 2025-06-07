from django.contrib import admin
from .models import URLProcessingRequest, SelectorConfiguration
from django.utils.html import format_html


@admin.register(URLProcessingRequest)
class URLProcessingRequestAdmin(admin.ModelAdmin):
    list_display = ('url', 'status', 'created_at', 'processed_at')
    list_filter = ('status',)
    search_fields = ('url', 'error_message')
    readonly_fields = ('created_at', 'processed_at', 'response_data')
    fieldsets = (
        (None, {
            'fields': ('url', 'status')
        }),
        ('Timing', {
            'fields': ('created_at', 'processed_at')
        }),
        ('Response', {
            'fields': ('response_data', 'error_message')
        }),
    )


@admin.register(SelectorConfiguration)
class SelectorConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'description_preview', 'created_by', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'selector_config')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )
    
    def description_preview(self, obj):
        """Return a truncated description."""
        if obj.description and len(obj.description) > 50:
            return obj.description[:50] + "..."
        return obj.description
    
    description_preview.short_description = 'Description'
    
    def save_model(self, request, obj, form, change):
        """Set the created_by field to the current user if not already set."""
        if not change and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change) 