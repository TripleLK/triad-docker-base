"""
Wagtail Admin Integration for Content Extractor - Site Configuration System

Simple snippet registration for site-level configurations and field-level 
XPath selector settings for LabEquipmentPage model integration.

Created by: Silver Raven
Date: 2025-01-22
Modified by: Cosmic Phoenix - Fixed InlinePanel formset error by removing InlinePanel
Enhanced by: Rapid Forge - Added multi-URL testing support
Project: Triad Docker Base - Site Configuration System
"""

from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel, MultiFieldPanel

from .models import SiteConfiguration, FieldConfiguration


# Configure panels for SiteConfiguration with multi-URL testing support
SiteConfiguration.panels = [
    MultiFieldPanel([
        FieldPanel('site_name'),
        FieldPanel('site_domain'),
        FieldPanel('is_active'),
    ], heading="Site Information"),
    
    MultiFieldPanel([
        FieldPanel('test_urls', help_text="Add multiple test URLs to verify selectors work across different pages of this domain. Each URL should be a complete URL (including http/https) that belongs to this domain."),
    ], heading="Multi-URL Testing"),
    
    FieldPanel('notes'),
]

# Configure panels for FieldConfiguration
FieldConfiguration.panels = [
    MultiFieldPanel([
        FieldPanel('site_config'),
        FieldPanel('lab_equipment_field'),
        FieldPanel('is_active'),
    ], heading="Configuration"),
    
    FieldPanel('xpath_selectors', help_text="JSON array of XPath selectors to try in order"),
    FieldPanel('comment', help_text="Context for AI processing - explain what this field should contain"),
]

# Register base models directly (no proxy models, no InlinePanel)
register_snippet(SiteConfiguration)
register_snippet(FieldConfiguration) 