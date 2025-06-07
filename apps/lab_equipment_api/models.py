"""
Lab Equipment API v2 Models - Core models for API operations tracking.

Created by: Quantum Gecko
Date: 2025-01-19
Project: Triad Docker Base
"""

import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class APIRequest(models.Model):
    """Track all API requests for monitoring and analytics."""
    
    REQUEST_METHODS = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    endpoint = models.CharField(max_length=200)
    method = models.CharField(max_length=10, choices=REQUEST_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Request metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_size = models.PositiveIntegerField(null=True, blank=True)
    
    # Timing information
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    response_status_code = models.PositiveIntegerField(null=True, blank=True)
    response_size = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['endpoint', 'status']),
            models.Index(fields=['created_at', 'status']),
        ]
        
    def __str__(self):
        return f"{self.method} {self.endpoint} - {self.status}"
    
    @property
    def duration(self):
        """Calculate request duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class BatchOperation(models.Model):
    """Track batch operations for lab equipment processing."""
    
    OPERATION_TYPES = [
        ('create', 'Create Equipment'),
        ('update', 'Update Equipment'),
        ('delete', 'Delete Equipment'),
        ('validate', 'Validate Data'),
        ('migrate', 'Migrate Data'),
    ]
    
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('partial', 'Partially Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    api_request = models.OneToOneField(APIRequest, on_delete=models.CASCADE, related_name='batch_operation')
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    
    # Operation details
    total_items = models.PositiveIntegerField(default=0)
    processed_items = models.PositiveIntegerField(default=0)
    successful_items = models.PositiveIntegerField(default=0)
    failed_items = models.PositiveIntegerField(default=0)
    
    # Progress tracking
    current_item_index = models.PositiveIntegerField(default=0)
    progress_percentage = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Results and errors
    result_summary = models.JSONField(default=dict, blank=True)
    error_details = models.JSONField(default=list, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['operation_type', 'status']),
        ]
        
    def __str__(self):
        return f"{self.operation_type} batch ({self.total_items} items) - {self.status}"
    
    def update_progress(self):
        """Update progress percentage based on processed items."""
        if self.total_items > 0:
            self.progress_percentage = (self.processed_items / self.total_items) * 100
        else:
            self.progress_percentage = 0.0
        self.save(update_fields=['progress_percentage'])


class ValidationResult(models.Model):
    """Store validation outcomes for data quality tracking."""
    
    VALIDATION_TYPES = [
        ('equipment', 'Equipment Data'),
        ('tags', 'Tag Data'),
        ('specifications', 'Specification Data'),
        ('models', 'Model Data'),
        ('images', 'Image Data'),
        ('batch', 'Batch Operation'),
    ]
    
    RESULT_LEVELS = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    api_request = models.ForeignKey(APIRequest, on_delete=models.CASCADE, related_name='validation_results')
    validation_type = models.CharField(max_length=20, choices=VALIDATION_TYPES)
    result_level = models.CharField(max_length=10, choices=RESULT_LEVELS)
    
    # Validation details
    field_name = models.CharField(max_length=100, blank=True)
    error_code = models.CharField(max_length=50, blank=True)
    message = models.TextField()
    suggested_fix = models.TextField(blank=True)
    
    # Context information
    item_id = models.CharField(max_length=100, blank=True)
    item_type = models.CharField(max_length=50, blank=True)
    validation_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at', 'result_level']
        indexes = [
            models.Index(fields=['api_request', 'result_level']),
            models.Index(fields=['validation_type', 'result_level']),
        ]
        
    def __str__(self):
        return f"{self.validation_type} {self.result_level}: {self.message[:50]}"


class APIConfiguration(models.Model):
    """Store API configuration settings for flexible behavior."""
    
    CONFIG_TYPES = [
        ('validation', 'Validation Rules'),
        ('processing', 'Processing Settings'),
        ('limits', 'Rate Limits'),
        ('features', 'Feature Flags'),
        ('integration', 'Integration Settings'),
    ]
    
    key = models.CharField(max_length=100, unique=True)
    config_type = models.CharField(max_length=20, choices=CONFIG_TYPES)
    value = models.JSONField()
    description = models.TextField(blank=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['config_type', 'key']
        indexes = [
            models.Index(fields=['config_type', 'is_active']),
            models.Index(fields=['key', 'is_active']),
        ]
        
    def __str__(self):
        return f"{self.config_type}: {self.key}"


class ErrorLog(models.Model):
    """Comprehensive error tracking for API operations."""
    
    ERROR_TYPES = [
        ('validation', 'Validation Error'),
        ('processing', 'Processing Error'),
        ('external', 'External Service Error'),
        ('database', 'Database Error'),
        ('permission', 'Permission Error'),
        ('system', 'System Error'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    api_request = models.ForeignKey(APIRequest, on_delete=models.CASCADE, related_name='error_logs')
    error_type = models.CharField(max_length=20, choices=ERROR_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    
    # Error details
    error_code = models.CharField(max_length=50, blank=True)
    message = models.TextField()
    stack_trace = models.TextField(blank=True)
    context_data = models.JSONField(default=dict, blank=True)
    
    # Resolution tracking
    is_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at', '-severity']
        indexes = [
            models.Index(fields=['error_type', 'severity']),
            models.Index(fields=['is_resolved', 'created_at']),
            models.Index(fields=['api_request', 'error_type']),
        ]
        
    def __str__(self):
        return f"{self.error_type} ({self.severity}): {self.message[:50]}" 