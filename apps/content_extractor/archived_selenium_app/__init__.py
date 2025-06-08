"""
Selenium Downloadable App for Content Extraction

Standalone Python application that can be packaged and distributed
for content extraction with integration back to Django admin.

Created by: Quantum Bear
Date: 2025-01-22
Project: Triad Docker Base
"""

from .app import ContentExtractorApp
from .gui import ContentExtractorGUI
from .cli import ContentExtractorCLI

__version__ = "1.0.0"
__all__ = ['ContentExtractorApp', 'ContentExtractorGUI', 'ContentExtractorCLI'] 