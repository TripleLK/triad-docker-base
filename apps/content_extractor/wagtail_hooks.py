"""
Wagtail Admin Integration for Content Extractor - Site Configuration System

Enhanced admin interface with URL management and AI JSON generation support.
Includes snippet registration for all models and enhanced admin panels.

Created by: Silver Raven
Date: 2025-01-22
Modified by: Cosmic Phoenix - Fixed InlinePanel formset error by removing InlinePanel
Modified by: Cosmic Forge - Added URL management and AI JSON support
Project: Triad Docker Base - Site Configuration System
"""

from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, FieldRowPanel

from .models import SiteConfiguration, FieldConfiguration, SiteURL, AIJSONRecord


# Configure panels for SiteConfiguration (enhanced with URL summary)
SiteConfiguration.panels = [
    MultiFieldPanel([
        FieldPanel('site_name'),
        FieldPanel('site_domain'),
        FieldPanel('is_active'),
    ], heading="Site Information"),
    
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

# Configure panels for SiteURL (URL management interface)
SiteURL.panels = [
    MultiFieldPanel([
        FieldPanel('site_config'),
        FieldPanel('url'),
        FieldRowPanel([
            FieldPanel('status'),
            FieldPanel('processing_status'),
        ]),
    ], heading="URL Configuration"),
    
    MultiFieldPanel([
        FieldPanel('page_title'),
        FieldPanel('notes'),
    ], heading="Content Information"),
]

# Configure panels for AIJSONRecord (JSON data management)
AIJSONRecord.panels = [
    MultiFieldPanel([
        FieldPanel('site_url'),
        FieldPanel('is_current'),
    ], heading="Record Information"),
    
    FieldPanel('json_data', help_text="Generated AI-ready JSON data"),
    
    MultiFieldPanel([
        FieldPanel('content_hash'),
        FieldPanel('processing_duration'),
    ], heading="Processing Metadata", classname="collapsed"),
]

# Register all models as Wagtail snippets
register_snippet(SiteConfiguration)
register_snippet(FieldConfiguration)
register_snippet(SiteURL)
register_snippet(AIJSONRecord) 