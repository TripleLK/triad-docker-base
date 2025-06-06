#!/usr/bin/env python3
# apps/scrapers/selectors/text_selector.py

import logging
from .base import Selector, Selected, SelectedType

log = logging.getLogger(__name__)

class TextSelector(Selector):
    """
    A selector that extracts the text content from a Single element.
    
    This is one of the simplest selector types, as it simply calls get_text()
    on the BeautifulSoup element and returns that text as a VALUE.
    """
    
    def __init__(self):
        """Initialize a TextSelector with no parameters."""
        self.expected_selected = SelectedType.SINGLE

    def select(self, selected):
        """
        Extract text from a SINGLE Selected.
        
        Args:
            selected: A Selected of type SINGLE (BeautifulSoup object)
            
        Returns:
            A Selected of type VALUE containing the extracted text
        """
        super().select(selected)
        
        # Get and clean the text
        try:
            text = selected.value.get_text(strip=True)
        except AttributeError:
            # Fallback for non-Tag objects
            text = str(selected.value).strip()
            
        return Selected(text, SelectedType.VALUE)

    def toYamlDict(self):
        """Convert to YAML representation (simple string)."""
        return 'text_selector'

    @staticmethod
    def fromYamlDict(yaml_dict):
        """
        Create a TextSelector from YAML.
        
        Args:
            yaml_dict: Can be ignored as TextSelector takes no parameters
            
        Returns:
            A new TextSelector instance
        """
        return TextSelector() 