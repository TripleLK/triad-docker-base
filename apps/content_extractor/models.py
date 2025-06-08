"""
Content Extractor Models

Data models for managing content extraction projects, analyzed pages,
and the selectors generated through human-in-the-loop analysis.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class ExtractionProject(models.Model):
    """
    A project for extracting content from a specific website/domain.
    Groups related pages and their analysis together.
    """
    name = models.CharField(max_length=255, help_text="Descriptive name for this extraction project")
    domain = models.URLField(help_text="Base domain being analyzed")
    description = models.TextField(blank=True, help_text="Project description and goals")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Project status
    STATUS_CHOICES = [
        ('setup', 'Setup - Adding Pages'),
        ('selecting', 'Human Selection In Progress'),
        ('analyzing', 'Analyzing Selectors'),
        ('complete', 'Complete - Selectors Ready'),
        ('archived', 'Archived'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='setup')
    
    class Meta:
        ordering = ['-updated_at']
        
    def __str__(self):
        return f"{self.name} ({self.domain})"


class AnalyzedPage(models.Model):
    """
    A single page that has been analyzed for content extraction.
    Stores the original HTML and processed representation.
    """
    project = models.ForeignKey(ExtractionProject, on_delete=models.CASCADE, related_name='pages')
    url = models.URLField(help_text="Full URL of the analyzed page")
    title = models.CharField(max_length=500, blank=True, help_text="Page title extracted from HTML")
    
    # HTML storage and processing
    original_html = models.TextField(help_text="Original HTML content")
    processed_dom = models.JSONField(help_text="Simplified DOM structure as JSON")
    
    # Analysis metadata
    analyzed_at = models.DateTimeField(default=timezone.now)
    content_hash = models.CharField(max_length=64, help_text="Hash of processed content for change detection")
    
    class Meta:
        ordering = ['url']
        unique_together = ['project', 'url']
        
    def __str__(self):
        return f"{self.title or 'Untitled'} - {self.url}"


class ContentSelector(models.Model):
    """
    A selector (XPath/CSS) that identifies specific content across pages.
    Generated through human-in-the-loop analysis and pattern detection.
    """
    project = models.ForeignKey(ExtractionProject, on_delete=models.CASCADE, related_name='selectors')
    label = models.CharField(max_length=100, help_text="Human-readable label for this content type")
    
    # Selector details
    xpath = models.TextField(help_text="XPath selector for this content")
    css_selector = models.TextField(blank=True, help_text="CSS selector alternative (if applicable)")
    
    # Validation and confidence
    confidence_score = models.FloatField(
        default=1.0, 
        help_text="Confidence score (0-1) based on cross-page validation"
    )
    pages_matched = models.ManyToManyField(
        AnalyzedPage, 
        blank=True,
        help_text="Pages where this selector successfully extracts content"
    )
    
    # Pattern information
    is_generalized = models.BooleanField(
        default=False,
        help_text="Whether this selector was generalized from patterns"
    )
    base_pattern = models.TextField(
        blank=True,
        help_text="Base pattern used for generalization"
    )
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    created_by_human = models.BooleanField(
        default=True,
        help_text="Whether this selector was created by human selection or algorithm"
    )
    
    class Meta:
        ordering = ['label', '-confidence_score']
        unique_together = ['project', 'label']
        
    def __str__(self):
        return f"{self.project.name} - {self.label}"


class SelectionSession(models.Model):
    """
    Records a human selection session for tracking progress and allowing resumption.
    """
    project = models.ForeignKey(ExtractionProject, on_delete=models.CASCADE, related_name='sessions')
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Session state
    current_page_index = models.IntegerField(default=0)
    selections_made = models.JSONField(
        default=dict,
        help_text="Temporary storage for selections during active session"
    )
    
    class Meta:
        ordering = ['-started_at']
        
    def __str__(self):
        status = "Complete" if self.completed_at else "In Progress"
        return f"{self.project.name} Session - {status}"


class SiteFieldSelector(models.Model):
    """
    Site-specific selectors for LabEquipmentPage fields.
    Stores working selectors per site domain for specific model fields.
    """
    # Site identification
    domain = models.CharField(max_length=255, help_text="Site domain (e.g., 'airscience.com')")
    site_name = models.CharField(max_length=100, help_text="Human-readable site name")
    
    # Field mapping to LabEquipmentPage model
    FIELD_CHOICES = [
        ('title', 'Title'),
        ('short_description', 'Short Description'),
        ('full_description', 'Full Description'),
        ('models', 'Models'),
        ('features', 'Features'),
        ('accessories', 'Accessories'),
        ('categorized_tags', 'Categorized Tags'),
        ('gallery_images', 'Gallery Images'),
        ('spec_groups', 'Specification Groups'),
        ('source_url', 'Source URL'),
        ('specification_confidence', 'Specification Confidence'),
        ('needs_review', 'Needs Review'),
        ('data_completeness', 'Data Completeness'),
        ('source_type', 'Source Type'),
    ]
    field_name = models.CharField(max_length=50, choices=FIELD_CHOICES, help_text="LabEquipmentPage field name")
    
    # Selector details
    xpath = models.TextField(help_text="XPath selector for this field")
    css_selector = models.TextField(blank=True, help_text="CSS selector alternative")
    
    # Field handling
    requires_manual_input = models.BooleanField(
        default=False,
        help_text="If True, this field requires manual input rather than selection"
    )
    manual_input_note = models.TextField(
        blank=True,
        help_text="Instructions for manual input (if required)"
    )
    
    # Testing and validation
    success_rate = models.FloatField(
        default=0.0,
        help_text="Success rate (0-1) from cross-page testing"
    )
    pages_tested = models.IntegerField(
        default=0,
        help_text="Number of pages this selector has been tested on"
    )
    pages_successful = models.IntegerField(
        default=0,
        help_text="Number of pages where selector worked"
    )
    last_tested = models.DateTimeField(null=True, blank=True)
    
    # Creation metadata
    created_from_url = models.URLField(help_text="URL where this selector was originally created")
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Usage tracking
    times_used = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['domain', 'field_name', '-success_rate']
        unique_together = ['domain', 'field_name']
        
    def __str__(self):
        manual_indicator = " (Manual)" if self.requires_manual_input else ""
        return f"{self.domain} - {self.get_field_name_display()}{manual_indicator}"

    def update_success_rate(self):
        """Update success rate based on testing data"""
        if self.pages_tested > 0:
            self.success_rate = self.pages_successful / self.pages_tested
        else:
            self.success_rate = 0.0
        self.save()


class SelectorTestResult(models.Model):
    """
    Records results of testing a selector on different pages.
    Tracks which selectors work across different pages on the same site.
    """
    selector = models.ForeignKey(SiteFieldSelector, on_delete=models.CASCADE, related_name='test_results')
    test_url = models.URLField(help_text="URL where selector was tested")
    
    # Test results
    SUCCESS_CHOICES = [
        ('success', 'Success - Content Found'),
        ('no_match', 'No Match - Selector Found Nothing'),
        ('error', 'Error - Selector Failed'),
        ('invalid_content', 'Invalid Content - Wrong Content Type'),
    ]
    result = models.CharField(max_length=20, choices=SUCCESS_CHOICES)
    
    # Content details
    extracted_content = models.TextField(blank=True, help_text="Content extracted by selector")
    content_preview = models.CharField(
        max_length=200, 
        blank=True,
        help_text="First 200 chars of extracted content"
    )
    
    # Testing metadata
    tested_at = models.DateTimeField(default=timezone.now)
    test_duration = models.FloatField(help_text="Time taken to test selector (seconds)")
    error_message = models.TextField(blank=True, help_text="Error message if test failed")
    
    class Meta:
        ordering = ['-tested_at']
        unique_together = ['selector', 'test_url']
        
    def __str__(self):
        return f"{self.selector.domain}/{self.selector.field_name} on {self.test_url} - {self.get_result_display()}"

    def save(self, *args, **kwargs):
        # Auto-generate content preview
        if self.extracted_content and not self.content_preview:
            self.content_preview = self.extracted_content[:200]
        super().save(*args, **kwargs)
        
        # Update selector success statistics
        self.selector.pages_tested = self.selector.test_results.count()
        self.selector.pages_successful = self.selector.test_results.filter(result='success').count()
        self.selector.last_tested = timezone.now()
        self.selector.update_success_rate()


class FieldSelectionSession(models.Model):
    """
    Tracks field selection sessions for specific sites and field completion progress.
    """
    domain = models.CharField(max_length=255, help_text="Site domain being worked on")
    session_name = models.CharField(max_length=100, help_text="Descriptive session name")
    
    # Field completion tracking
    completed_fields = models.JSONField(
        default=list,
        help_text="List of field names that have been completed"
    )
    current_field = models.CharField(
        max_length=50,
        blank=True,
        help_text="Currently active field being selected"
    )
    
    # Session management
    started_at = models.DateTimeField(default=timezone.now)
    last_activity = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Progress tracking
    total_fields = models.IntegerField(default=14, help_text="Total LabEquipmentPage fields")
    
    class Meta:
        ordering = ['-last_activity']
        
    def __str__(self):
        progress = f"{len(self.completed_fields)}/{self.total_fields}"
        status = "Complete" if self.completed_at else "In Progress" 
        return f"{self.domain} - {self.session_name} ({progress}) - {status}"
    
    @property
    def completion_percentage(self):
        """Calculate completion percentage"""
        if self.total_fields == 0:
            return 0
        return (len(self.completed_fields) / self.total_fields) * 100
    
    def mark_field_complete(self, field_name):
        """Mark a field as completed"""
        if field_name not in self.completed_fields:
            self.completed_fields.append(field_name)
            self.save()
            
        # Check if all fields are complete
        if len(self.completed_fields) >= self.total_fields:
            self.completed_at = timezone.now()
            self.is_active = False
            self.save()
    
    def get_remaining_fields(self):
        """Get list of fields that still need to be completed"""
        all_field_choices = [choice[0] for choice in SiteFieldSelector.FIELD_CHOICES]
        return [field for field in all_field_choices if field not in self.completed_fields]


class AIPreparationRecord(models.Model):
    """
    Store extracted content optimized for AI processing.
    
    This model represents the new direction for content extraction focused on 
    AI preparation rather than direct LabEquipmentPage model population.
    All fields are designed for flexible AI consumption with context-rich data.
    
    Created by: Silver Phoenix
    Date: 2025-01-08
    Project: Triad Docker Base - AI Preparation System
    """
    
    # Identification
    session_id = models.CharField(
        max_length=255,
        help_text="Unique identifier for grouping related extractions"
    )
    source_url = models.URLField(help_text="Source URL where content was extracted")
    extraction_timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When this extraction was performed"
    )
    
    # Content Fields (All TextField for AI flexibility)
    field_name = models.CharField(
        max_length=255,
        help_text="Name of the field being extracted (e.g., 'title', 'description')"
    )
    extracted_content = models.TextField(
        help_text="The actual extracted text content"
    )
    xpath_used = models.TextField(
        help_text="XPath selector that extracted this content"
    )
    css_selector_used = models.TextField(
        blank=True,
        help_text="CSS selector alternative (if applicable)"
    )
    
    # AI Context Fields
    user_comment = models.TextField(
        blank=True,
        help_text="User-provided context for AI processing"
    )
    extraction_method = models.CharField(
        max_length=50,
        choices=[
            ('page_selection', 'Selected from page'),
            ('text_input', 'Manual text input'),
            ('xpath_edit', 'Edited XPath selection'),
        ],
        default='page_selection',
        help_text="Method used to extract this content"
    )
    confidence_level = models.CharField(
        max_length=20,
        choices=[
            ('high', 'High Confidence'),
            ('medium', 'Medium Confidence'),
            ('low', 'Low Confidence'),
        ],
        default='medium',
        help_text="Confidence level in extraction accuracy"
    )
    
    # Metadata for AI Processing
    content_type = models.CharField(
        max_length=100,
        choices=[
            ('text', 'Plain Text'),
            ('list', 'List of Items'),
            ('nested_data', 'Nested/Structured Data'),
            ('html', 'HTML Content'),
            ('number', 'Numeric Data'),
            ('url', 'URL/Link'),
        ],
        default='text',
        help_text="Type of content for AI processing optimization"
    )
    preprocessing_notes = models.TextField(
        blank=True,
        help_text="Technical notes for AI processing"
    )
    validation_status = models.CharField(
        max_length=20,
        choices=[
            ('valid', 'Valid'),
            ('needs_review', 'Needs Review'),
            ('error', 'Error - Needs Fixing'),
        ],
        default='valid',
        help_text="Validation status of extracted content"
    )
    
    # Relationships and Organization
    parent_record = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text="Parent record for nested content structures"
    )
    instance_index = models.IntegerField(
        default=0,
        help_text="Instance number for multi-instance fields (0 for single instance)"
    )
    
    # Creation tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['session_id', 'field_name', 'instance_index']
        unique_together = ['session_id', 'field_name', 'instance_index']
        indexes = [
            models.Index(fields=['session_id', 'field_name']),
            models.Index(fields=['source_url', 'extraction_timestamp']),
            models.Index(fields=['validation_status']),
        ]
        
    def __str__(self):
        instance_str = f"[{self.instance_index}]" if self.instance_index > 0 else ""
        return f"{self.session_id} - {self.field_name}{instance_str}"
    
    @property
    def content_preview(self):
        """Return first 100 characters of extracted content for display."""
        if not self.extracted_content:
            return "(No content)"
        return (self.extracted_content[:100] + "...") if len(self.extracted_content) > 100 else self.extracted_content
    
    def save(self, *args, **kwargs):
        """Auto-set content_type based on extracted content if not specified."""
        if not self.content_type or self.content_type == 'text':
            # Simple heuristics for content type detection
            content = self.extracted_content.strip()
            if content.startswith('<') and content.endswith('>'):
                self.content_type = 'html'
            elif content.startswith('http'):
                self.content_type = 'url'
            elif '\n' in content and any(marker in content for marker in ['•', '-', '*', '1.', '2.']):
                self.content_type = 'list'
            elif content.replace('.', '').replace(',', '').isdigit():
                self.content_type = 'number'
        
        super().save(*args, **kwargs)


class AIContextBuilder:
    """
    Format extracted content and comments for AI consumption.
    
    Utility class for exporting AIPreparationRecord data in formats
    optimized for AI model consumption.
    """
    
    @staticmethod
    def build_context(session_id):
        """Build complete context dictionary for a session."""
        from .models import AIPreparationRecord
        
        records = AIPreparationRecord.objects.filter(session_id=session_id).order_by('field_name', 'instance_index')
        
        if not records.exists():
            return None
            
        first_record = records.first()
        context = {
            'session_id': session_id,
            'source_url': first_record.source_url,
            'extraction_timestamp': first_record.extraction_timestamp.isoformat(),
            'total_fields': records.count(),
            'fields': {}
        }
        
        for record in records:
            field_key = record.field_name
            if record.instance_index > 0:
                field_key = f"{record.field_name}[{record.instance_index}]"
                
            context['fields'][field_key] = {
                'content': record.extracted_content,
                'user_comment': record.user_comment,
                'extraction_method': record.extraction_method,
                'xpath': record.xpath_used,
                'confidence': record.confidence_level,
                'content_type': record.content_type,
                'validation_status': record.validation_status,
            }
        
        return context
    
    @staticmethod
    def export_for_ai(session_id, format='json'):
        """Export in format optimized for AI model consumption."""
        import json
        
        context = AIContextBuilder.build_context(session_id)
        if not context:
            return None
            
        if format == 'json':
            return json.dumps(context, indent=2)
        elif format == 'prompt':
            return AIContextBuilder._format_as_prompt(context)
        elif format == 'structured':
            return AIContextBuilder._format_as_structured_data(context)
        else:
            return context
    
    @staticmethod
    def _format_as_prompt(context):
        """Format context as AI prompt text."""
        prompt_parts = [
            f"Content Extraction Session: {context['session_id']}",
            f"Source: {context['source_url']}",
            f"Extracted: {context['extraction_timestamp']}",
            "",
            "Extracted Fields:"
        ]
        
        for field_name, field_data in context['fields'].items():
            prompt_parts.append(f"\n{field_name.upper()}:")
            prompt_parts.append(f"Content: {field_data['content']}")
            if field_data['user_comment']:
                prompt_parts.append(f"Context: {field_data['user_comment']}")
            prompt_parts.append(f"Confidence: {field_data['confidence']}")
            prompt_parts.append("")
        
        return "\n".join(prompt_parts)
    
    @staticmethod
    def _format_as_structured_data(context):
        """Format context as structured data for AI processing."""
        structured = {
            'metadata': {
                'session_id': context['session_id'],
                'source_url': context['source_url'],
                'extraction_timestamp': context['extraction_timestamp'],
                'total_fields': context['total_fields']
            },
            'content': {}
        }
        
        for field_name, field_data in context['fields'].items():
            structured['content'][field_name] = {
                'value': field_data['content'],
                'context': field_data['user_comment'],
                'confidence': field_data['confidence'],
                'type': field_data['content_type']
            }
        
        return structured
