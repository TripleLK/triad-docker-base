"""
Django admin configuration for Lab Equipment API v2.

Created by: Quantum Gecko
Date: 2025-01-19
Project: Triad Docker Base
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import APIRequest, BatchOperation, ValidationResult, APIConfiguration, ErrorLog


@admin.register(APIRequest)
class APIRequestAdmin(admin.ModelAdmin):
    """Admin interface for API requests."""
    
    list_display = [
        'id', 'method', 'endpoint', 'user', 'status', 
        'response_status_code', 'created_at', 'duration_display'
    ]
    list_filter = ['method', 'status', 'response_status_code', 'created_at']
    search_fields = ['endpoint', 'user__username', 'ip_address']
    readonly_fields = ['id', 'created_at', 'duration_display']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Request Info', {
            'fields': ('id', 'endpoint', 'method', 'user')
        }),
        ('Status & Timing', {
            'fields': ('status', 'created_at', 'started_at', 'completed_at', 'duration_display')
        }),
        ('Request Details', {
            'fields': ('ip_address', 'user_agent', 'request_size')
        }),
        ('Response Details', {
            'fields': ('response_status_code', 'response_size', 'error_message')
        }),
    )
    
    def duration_display(self, obj):
        """Display request duration in human-readable format."""
        duration = obj.duration
        if duration is not None:
            if duration < 1:
                return f"{duration * 1000:.0f}ms"
            else:
                return f"{duration:.2f}s"
        return "N/A"
    duration_display.short_description = "Duration"


@admin.register(BatchOperation)
class BatchOperationAdmin(admin.ModelAdmin):
    """Admin interface for batch operations."""
    
    list_display = [
        'id', 'operation_type', 'status', 'progress_percentage',
        'total_items', 'successful_items', 'failed_items', 'created_at'
    ]
    list_filter = ['operation_type', 'status', 'created_at']
    search_fields = ['id', 'api_request__endpoint']
    readonly_fields = ['id', 'created_at', 'progress_bar_display']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Operation Info', {
            'fields': ('id', 'api_request', 'operation_type', 'status')
        }),
        ('Progress', {
            'fields': ('progress_percentage', 'progress_bar_display', 'current_item_index')
        }),
        ('Item Counts', {
            'fields': ('total_items', 'processed_items', 'successful_items', 'failed_items')
        }),
        ('Timing', {
            'fields': ('created_at', 'started_at', 'completed_at')
        }),
        ('Results', {
            'fields': ('result_summary', 'error_details'),
            'classes': ('collapse',)
        }),
    )
    
    def progress_bar_display(self, obj):
        """Display progress as a visual bar."""
        percentage = obj.progress_percentage
        color = 'green' if percentage == 100 else 'blue' if percentage > 50 else 'orange'
        return format_html(
            '<div style="width: 200px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; '
            'text-align: center; line-height: 20px; color: white;">{:.1f}%</div></div>',
            percentage, color, percentage
        )
    progress_bar_display.short_description = "Progress"


@admin.register(ValidationResult)
class ValidationResultAdmin(admin.ModelAdmin):
    """Admin interface for validation results."""
    
    list_display = [
        'id', 'validation_type', 'result_level', 'field_name', 
        'error_code', 'message_preview', 'created_at'
    ]
    list_filter = ['validation_type', 'result_level', 'error_code', 'created_at']
    search_fields = ['field_name', 'error_code', 'message', 'item_id']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at', 'result_level']
    
    def message_preview(self, obj):
        """Show truncated message."""
        return obj.message[:100] + "..." if len(obj.message) > 100 else obj.message
    message_preview.short_description = "Message"


@admin.register(APIConfiguration)
class APIConfigurationAdmin(admin.ModelAdmin):
    """Admin interface for API configuration."""
    
    list_display = ['key', 'config_type', 'is_active', 'updated_at', 'created_by']
    list_filter = ['config_type', 'is_active', 'created_at']
    search_fields = ['key', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['config_type', 'key']
    
    fieldsets = (
        ('Configuration', {
            'fields': ('key', 'config_type', 'value', 'description')
        }),
        ('Status', {
            'fields': ('is_active', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    """Admin interface for error logs."""
    
    list_display = [
        'id', 'error_type', 'severity', 'message_preview', 
        'is_resolved', 'created_at'
    ]
    list_filter = ['error_type', 'severity', 'is_resolved', 'created_at']
    search_fields = ['error_code', 'message', 'api_request__endpoint']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at', '-severity']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Error Info', {
            'fields': ('id', 'api_request', 'error_type', 'severity', 'error_code')
        }),
        ('Details', {
            'fields': ('message', 'stack_trace', 'context_data')
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolution_notes', 'resolved_at', 'resolved_by')
        }),
        ('Timing', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def message_preview(self, obj):
        """Show truncated error message."""
        return obj.message[:100] + "..." if len(obj.message) > 100 else obj.message
    message_preview.short_description = "Message"
    
    actions = ['mark_resolved']
    
    def mark_resolved(self, request, queryset):
        """Mark selected errors as resolved."""
        from django.utils import timezone
        updated = queryset.update(
            is_resolved=True,
            resolved_at=timezone.now(),
            resolved_by=request.user
        )
        self.message_user(request, f'{updated} error(s) marked as resolved.')
    mark_resolved.short_description = "Mark selected errors as resolved" 