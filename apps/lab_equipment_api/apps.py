"""
Django app configuration for Lab Equipment API v2.

Created by: Quantum Gecko
Date: 2025-01-19
Project: Triad Docker Base
"""

from django.apps import AppConfig


class LabEquipmentApiConfig(AppConfig):
    """Configuration for the Lab Equipment API v2 application."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.lab_equipment_api'
    verbose_name = 'Lab Equipment API v2'
    
    def ready(self):
        """Initialize app when Django starts."""
        # Import signal handlers when app is ready
        try:
            from . import signals  # noqa
        except ImportError:
            pass 