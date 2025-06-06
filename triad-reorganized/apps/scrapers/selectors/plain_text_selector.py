#!/usr/bin/env python3
# apps/scrapers/selectors/plain_text_selector.py

import logging

from .base import Selector, Selected, SelectedType

log = logging.getLogger(__name__)

class PlainTextSelector(Selector):
    """
    Returns a fixed text value.
    
    This selector ignores its input and always returns the same text value.
    Useful for adding constants or fixed parts to the output.
    """
    
    def __init__(self, text):
        """
        Initialize a PlainTextSelector.
        
        Args:
            text: The text value to return
        """
        # This selector accepts any input type since it ignores it
        self.expected_selected = None
        
        # Convert to string to ensure we always have a string value
        self.text = str(text)

    def select(self, selected):
        """
        Return the fixed text value.
        
        Args:
            selected: Any Selected object (ignored)
            
        Returns:
            A Selected of type VALUE containing the fixed text
        """
        # No need to validate input type as we accept any type
        return Selected(self.text, SelectedType.VALUE)

    def toYamlDict(self):
        """Convert to YAML dictionary representation."""
        return {'plain_text_selector': {'text': self.text}}

    @staticmethod
    def fromYamlDict(yaml_dict):
        """
        Create a PlainTextSelector from a YAML dictionary.
        
        Args:
            yaml_dict: Dictionary containing 'text' key
            
        Returns:
            A new PlainTextSelector instance
        """
        if 'text' not in yaml_dict:
            raise ValueError("PlainTextSelector YAML requires a 'text' key")
            
        # Always cast to string
        return PlainTextSelector(str(yaml_dict['text']))
