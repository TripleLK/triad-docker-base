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
