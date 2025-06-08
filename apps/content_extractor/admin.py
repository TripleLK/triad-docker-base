"""
Django Admin configuration for Content Extractor models.

Note: Site Configuration and Field Configuration models are now managed 
as Wagtail snippets in wagtail_hooks.py, not Django admin.

Created by: Silver Raven
Date: 2025-01-22
Project: Triad Docker Base - Site Configuration System
"""

from django.contrib import admin
from .models import SiteConfiguration, FieldConfiguration

# The new models (SiteConfiguration, FieldConfiguration) are registered 
# as Wagtail snippets in wagtail_hooks.py and do not need Django admin registration.

# All previous models (ExtractionProject, AnalyzedPage, ContentSelector, etc.) 
# have been removed as part of the model redesign.
