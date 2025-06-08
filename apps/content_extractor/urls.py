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
    path('get-configuration/', views.get_site_configuration, name='get_site_configuration'),
    
    # Multi-URL Testing API endpoints
    path('add-test-url/', views.add_test_url_view, name='add_test_url'),
    path('switch-url/<str:direction>/', views.switch_url_view, name='switch_url'),
    path('get-test-urls/', views.get_test_urls_view, name='get_test_urls'),
] 