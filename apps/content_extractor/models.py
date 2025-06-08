"""
Content Extractor Models - Site Configuration System

Site-level configuration models for managing XPath selectors 
per LabEquipmentPage field per site domain.

Created by: Silver Raven
Date: 2025-01-22
Enhanced by: Rapid Forge (Multi-URL Testing Support)
Project: Triad Docker Base - Site Configuration System
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core import validators


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
    
    # Multi-URL Testing Support
    test_urls = models.JSONField(
        default=list,
        blank=True,
        help_text="List of test URLs to verify selectors work across different pages of this domain"
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
    def test_urls_count(self):
        """Return the number of test URLs configured for this site."""
        return len(self.test_urls) if self.test_urls else 0
    
    def add_test_url(self, url):
        """Add a test URL to this site configuration."""
        if not self.test_urls:
            self.test_urls = []
        
        # Validate URL belongs to this domain
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if self.site_domain not in parsed.netloc:
            raise ValueError(f"URL {url} does not belong to domain {self.site_domain}")
        
        if url not in self.test_urls:
            self.test_urls.append(url)
            self.save()
    
    def remove_test_url(self, url):
        """Remove a test URL from this site configuration."""
        if self.test_urls and url in self.test_urls:
            self.test_urls.remove(url)
            self.save()
    
    def get_valid_test_urls(self):
        """Return list of test URLs that are properly formatted and belong to this domain."""
        if not self.test_urls:
            return []
        
        from urllib.parse import urlparse
        valid_urls = []
        
        for url in self.test_urls:
            try:
                parsed = urlparse(url)
                if parsed.scheme in ['http', 'https'] and self.site_domain in parsed.netloc:
                    valid_urls.append(url)
            except Exception:
                continue  # Skip invalid URLs
        
        return valid_urls


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
