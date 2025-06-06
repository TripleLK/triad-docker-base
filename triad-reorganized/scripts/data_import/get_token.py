#!/usr/bin/env python
"""
Script to get or create an API token for testing.
"""
import os
import django
import sys

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.base_site.models import APIToken

# Get an API token or create a test one if needed
token = APIToken.objects.filter(is_active=True).first()
if not token:
    # Create a test token
    token = APIToken.objects.create(
        name="Test Token",
        token="test_token_123456",
        description="Created for API testing"
    )
    print(token.token)
else:
    print(token.token) 