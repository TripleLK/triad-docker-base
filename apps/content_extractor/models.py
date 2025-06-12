"""
Content Extractor Models - Site Configuration System

Site-level configuration models for managing XPath selectors 
per LabEquipmentPage field per site domain.

Created by: Silver Raven
Date: 2025-01-22
Modified by: Cosmic Forge - Added SiteURL model for URL management
Project: Triad Docker Base - Site Configuration System
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class SiteConfiguration(models.Model):
    """
    Configuration for a specific site domain.
    Stores site-level settings and metadata for content extraction.
    """
    site_domain = models.CharField(
        max_length=255, 
        unique=True,
        help_text="Site domain (e.g., 'airscience.com', 'example-lab-supplier.com')"
    )
    site_name = models.CharField(
        max_length=255,
        help_text="Human-readable site name for identification"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this site configuration is active for extraction"
    )
    notes = models.TextField(
        blank=True,
        help_text="Notes about this site configuration"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="User who created this configuration"
    )
    
    class Meta:
        ordering = ['site_name', 'site_domain']
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configurations"
        
    def __str__(self):
        return f"{self.site_name} ({self.site_domain})"
    
    @property
    def configured_fields_count(self):
        """Return the number of fields configured for this site."""
        return self.field_configs.count()
    
    @property
    def active_field_configs_count(self):
        """Return the number of active field configurations for this site."""
        return self.field_configs.filter(is_active=True).count()

    @property
    def urls_count(self):
        """Return the total number of URLs configured for this site."""
        return self.urls.count()
    
    @property
    def active_urls_count(self):
        """Return the number of active URLs for this site."""
        return self.urls.filter(status='active').count()


class SiteURL(models.Model):
    """
    URL management for each site configuration.
    Stores URLs to be processed for content extraction with status tracking.
    """
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('disabled', 'Disabled'),
    ]
    
    PROCESSING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    site_config = models.ForeignKey(
        SiteConfiguration,
        on_delete=models.CASCADE,
        related_name='urls',
        help_text="Site configuration this URL belongs to"
    )
    url = models.URLField(
        max_length=500,
        help_text="Full URL to be processed for content extraction"
    )
    page_title = models.CharField(
        max_length=255,
        blank=True,
        help_text="Auto-populated page title from scraped content"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Whether this URL is active for processing"
    )
    last_processed = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of last successful processing"
    )
    processing_status = models.CharField(
        max_length=20,
        choices=PROCESSING_STATUS_CHOICES,
        default='pending',
        help_text="Current processing status for AI JSON generation"
    )
    notes = models.TextField(
        blank=True,
        help_text="Notes about this URL or processing results"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="User who added this URL"
    )
    
    class Meta:
        ordering = ['site_config__site_name', 'url']
        unique_together = ['site_config', 'url']
        verbose_name = "Site URL"
        verbose_name_plural = "Site URLs"
        
    def __str__(self):
        return f"{self.site_config.site_name} - {self.url}"
    
    def mark_processing(self):
        """Mark this URL as currently being processed."""
        self.processing_status = 'processing'
        self.save(update_fields=['processing_status', 'updated_at'])
    
    def mark_completed(self):
        """Mark this URL as successfully processed."""
        self.processing_status = 'completed'
        self.last_processed = timezone.now()
        self.save(update_fields=['processing_status', 'last_processed', 'updated_at'])
    
    def mark_failed(self, error_note=None):
        """Mark this URL as failed processing."""
        self.processing_status = 'failed'
        if error_note:
            self.notes = f"{self.notes}\n\nError: {error_note}" if self.notes else f"Error: {error_note}"
        self.save(update_fields=['processing_status', 'notes', 'updated_at'])


class FieldConfiguration(models.Model):
    """
    XPath selector configuration for a specific LabEquipmentPage field on a specific site.
    Each record represents the extraction configuration for one field on one site.
    """
    
    # Lab Equipment Page Model Fields (based on actual model structure)
    LAB_EQUIPMENT_FIELD_CHOICES = [
        ('title', 'Title'),
        ('short_description', 'Short Description'),
        ('full_description', 'Full Description'),
        ('models', 'Models'),
        ('model_name', 'Model Name'),
        ('name', 'Name (Generic)'),
        ('features', 'Features'),
        ('accessories', 'Accessories'),
        ('categorized_tags', 'Categorized Tags'),
        ('gallery_images', 'Gallery Images'),
        ('spec_groups', 'Specification Groups'),
        ('specification_group_names', 'Specification Group Names'),
        ('source_url', 'Source URL'),
        ('specification_confidence', 'Specification Confidence'),
        ('needs_review', 'Needs Review'),
        ('data_completeness', 'Data Completeness'),
        ('source_type', 'Source Type'),
        ('meta_title', 'Meta Title'),
        ('meta_description', 'Meta Description'),
        ('meta_keywords', 'Meta Keywords'),
        ('seo_content', 'SEO Content'),
        ('target_keywords', 'Target Keywords'),
        ('related_keywords', 'Related Keywords'),
        ('technical_keywords', 'Technical Keywords'),
        ('structured_data', 'Structured Data'),
        ('alt_text_suggestions', 'Alt Text Suggestions'),
        ('page_content_sections', 'Page Content Sections'),
        ('applications', 'Applications'),
        ('slug', 'URL Slug'),
    ]
    
    site_config = models.ForeignKey(
        SiteConfiguration,
        on_delete=models.CASCADE,
        related_name='field_configs',
        help_text="Site configuration this field belongs to"
    )
    lab_equipment_field = models.CharField(
        max_length=100,
        choices=LAB_EQUIPMENT_FIELD_CHOICES,
        help_text="LabEquipmentPage model field this configuration targets"
    )
    
    # XPath Configuration
    xpath_selectors = models.JSONField(
        default=list,
        blank=True,
        help_text="List of XPath strings to try for extracting this field content"
    )
    
    # AI Context
    comment = models.TextField(
        blank=True,
        help_text="Context comment for AI processing - explains what this field should contain"
    )
    
    # Configuration Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this field configuration is active for extraction"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="User who created this field configuration"
    )
    
    class Meta:
        ordering = ['site_config__site_name', 'lab_equipment_field']
        unique_together = ['site_config', 'lab_equipment_field']
        verbose_name = "Field Configuration"
        verbose_name_plural = "Field Configurations"
        
    def __str__(self):
        return f"{self.site_config.site_name} - {self.get_lab_equipment_field_display()}"
    
    @property
    def xpath_count(self):
        """Return the number of XPath selectors configured for this field."""
        return len(self.xpath_selectors) if self.xpath_selectors else 0
    
    def add_xpath_selector(self, xpath):
        """Add an XPath selector to this field configuration."""
        if not self.xpath_selectors:
            self.xpath_selectors = []
        if xpath not in self.xpath_selectors:
            self.xpath_selectors.append(xpath)
            self.save()
    
    def remove_xpath_selector(self, xpath):
        """Remove an XPath selector from this field configuration."""
        if self.xpath_selectors and xpath in self.xpath_selectors:
            self.xpath_selectors.remove(xpath)
            self.save()
    
    def get_primary_xpath(self):
        """Return the first (primary) XPath selector, or None if none configured."""
        return self.xpath_selectors[0] if self.xpath_selectors else None


class AIJSONRecord(models.Model):
    """
    Generated AI-ready JSON data for each processed URL.
    Stores the combined scraped content, XPath configurations, and metadata.
    """
    
    site_url = models.ForeignKey(
        SiteURL,
        on_delete=models.CASCADE,
        related_name='ai_json_records',
        help_text="Site URL this JSON was generated from"
    )
    json_data = models.JSONField(
        help_text="Complete AI-ready JSON combining scraped content and XPath configurations"
    )
    generation_timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When this JSON was generated"
    )
    content_hash = models.CharField(
        max_length=64,
        help_text="SHA256 hash of the scraped content for change detection"
    )
    processing_duration = models.DurationField(
        null=True,
        blank=True,
        help_text="Time taken to generate this JSON"
    )
    
    # Status tracking
    is_current = models.BooleanField(
        default=True,
        help_text="Whether this is the most recent JSON for this URL"
    )
    
    class Meta:
        ordering = ['-generation_timestamp']
        verbose_name = "AI JSON Record"
        verbose_name_plural = "AI JSON Records"
        
    def __str__(self):
        return f"{self.site_url.site_config.site_name} - {self.site_url.url} ({self.generation_timestamp})"
    
    @property
    def json_size_kb(self):
        """Return the approximate size of the JSON data in KB."""
        import json
        return len(json.dumps(self.json_data)) / 1024 if self.json_data else 0
    
    def mark_as_outdated(self):
        """Mark this record as no longer current (when new JSON is generated)."""
        self.is_current = False
        self.save(update_fields=['is_current'])
