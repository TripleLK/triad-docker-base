"""
Content Extractor URL Configuration

URL patterns for the content extractor app, including endpoints for
site configuration integration with the interactive selector.

Created by: Cosmic Phoenix
Date: 2025-01-22
Project: Triad Docker Base - Site Configuration Integration
"""

from django.urls import path
from . import views

app_name = 'content_extractor'

urlpatterns = [
    # Site Configuration API endpoints
    path('save-configuration/', views.save_xpath_configuration, name='save_xpath_configuration'),
    path('get-site-configuration/', views.get_site_configuration, name='get_site_configuration'),
    path('delete-configuration/', views.delete_xpath_configuration, name='delete_xpath_configuration'),
] 