from django.db import models
from django.utils import timezone


class BatchURLProcessingRequest(models.Model):
    """Model to track batch URL processing requests."""
    name = models.CharField(max_length=255, verbose_name="Batch Name")
    css_selectors = models.TextField(
        verbose_name="CSS Selectors",
        blank=True,
        null=True,
        help_text="Optional CSS selectors to filter HTML content (comma-separated)"
    )
    selector_configuration = models.ForeignKey(
        'SelectorConfiguration',
        on_delete=models.SET_NULL,
        related_name='batch_requests',
        null=True,
        blank=True,
        help_text="Selected selector configuration for HTML processing"
    )
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('partial', 'Partially Completed'),
        ],
        default='pending'
    )
    total_urls = models.PositiveIntegerField(default=0)
    processed_urls = models.PositiveIntegerField(default=0)
    successful_urls = models.PositiveIntegerField(default=0)
    failed_urls = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Batch URL Processing Request"
        verbose_name_plural = "Batch URL Processing Requests"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.status})"
    
    def update_status(self):
        """Update the status based on individual URL processing requests."""
        # Count related requests by status
        total = self.url_requests.count()
        processed = self.url_requests.exclude(status='pending').count()
        completed = self.url_requests.filter(status='completed').count()
        failed = self.url_requests.filter(status='failed').count()
        
        # Update counters
        self.total_urls = total
        self.processed_urls = processed
        self.successful_urls = completed
        self.failed_urls = failed
        
        # Calculate the new status
        if total == 0:
            new_status = 'pending'
        elif processed == 0:
            new_status = 'pending'
        elif processed < total:
            new_status = 'processing'
        elif failed == total:
            new_status = 'failed'
        elif completed == total:
            new_status = 'completed'
            self.completed_at = timezone.now()
        else:
            new_status = 'partial'
            
        self.status = new_status
        self.save()
        
        return new_status
    
    @property
    def progress_percentage(self):
        """Calculate the progress percentage for this batch."""
        if self.total_urls == 0:
            return 0
        return int((self.processed_urls / self.total_urls) * 100)


class URLProcessingRequest(models.Model):
    """Model to track URL processing requests sent to AWS Bedrock."""
    url = models.URLField(verbose_name="URL to process")
    name = models.CharField(max_length=255, verbose_name="Name", blank=True, null=True, help_text="Name of the processed entity")
    css_selectors = models.TextField(
        verbose_name="CSS Selectors",
        blank=True,
        null=True,
        help_text="Optional CSS selectors to filter HTML content (comma-separated)"
    )
    selector_configuration = models.ForeignKey(
        'SelectorConfiguration',
        on_delete=models.SET_NULL,
        related_name='url_requests',
        null=True,
        blank=True,
        help_text="Selected selector configuration for HTML processing"
    )
    created_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    error_message = models.TextField(blank=True, null=True)
    response_data = models.JSONField(blank=True, null=True)
    created_page_id = models.IntegerField(blank=True, null=True, help_text="ID of the page created from this request")
    batch = models.ForeignKey(
        BatchURLProcessingRequest,
        on_delete=models.CASCADE,
        related_name='url_requests',
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = "URL Processing Request"
        verbose_name_plural = "URL Processing Requests"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.url} ({self.status})"
    
    def mark_as_processing(self):
        self.status = 'processing'
        self.save(update_fields=['status'])
        
        # Update batch status if part of a batch
        if self.batch:
            self.batch.update_status()
    
    def mark_as_completed(self, response_data):
        self.status = 'completed'
        self.processed_at = timezone.now()
        self.response_data = response_data
        self.save(update_fields=['status', 'processed_at', 'response_data'])
        
        # Update batch status if part of a batch
        if self.batch:
            self.batch.update_status()
    
    def mark_as_failed(self, error_message):
        self.status = 'failed'
        self.processed_at = timezone.now()
        self.error_message = error_message
        self.save(update_fields=['status', 'processed_at', 'error_message'])
        
        # Update batch status if part of a batch
        if self.batch:
            self.batch.update_status()


class SelectorConfiguration(models.Model):
    """Model to store selector configurations for HTML content extraction."""
    name = models.CharField(max_length=255, verbose_name="Configuration Name")
    description = models.TextField(
        verbose_name="Description",
        blank=True,
        help_text="Brief description of what this selector configuration is for"
    )
    selector_config = models.JSONField(
        verbose_name="Selector Configuration",
        help_text="JSON configuration for selectors (list of dictionaries with selector, name, note, and preserve_html fields)"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        related_name='selector_configurations',
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = "Selector Configuration"
        verbose_name_plural = "Selector Configurations"
        ordering = ['name', '-created_at']
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validate the selector_config field."""
        from django.core.exceptions import ValidationError
        import json
        
        # Ensure selector_config is a valid JSON list
        if not isinstance(self.selector_config, list):
            raise ValidationError({
                'selector_config': 'Selector configuration must be a list of dictionaries'
            })
            
        # Validate each item in the list
        for i, item in enumerate(self.selector_config):
            if not isinstance(item, dict):
                raise ValidationError({
                    'selector_config': f'Item at index {i} must be a dictionary'
                })
                
            # Check for required keys
            if 'selector' not in item:
                raise ValidationError({
                    'selector_config': f'Item at index {i} is missing required "selector" field'
                })
                
            if 'name' not in item:
                raise ValidationError({
                    'selector_config': f'Item at index {i} is missing required "name" field'
                })
                
            # Validate types
            if not isinstance(item.get('selector'), str):
                raise ValidationError({
                    'selector_config': f'Selector at index {i} must be a string'
                })
                
            if not isinstance(item.get('name'), str):
                raise ValidationError({
                    'selector_config': f'Name at index {i} must be a string'
                })
                
            if 'note' in item and not isinstance(item.get('note'), str):
                raise ValidationError({
                    'selector_config': f'Note at index {i} must be a string'
                })
                
            if 'preserve_html' in item and not isinstance(item.get('preserve_html'), bool):
                raise ValidationError({
                    'selector_config': f'preserve_html at index {i} must be a boolean'
                }) 