#!/usr/bin/env python3
# apps/scrapers/selectors/html_selector.py

import logging
import bs4
from bs4 import BeautifulSoup

from .base import Selector, Selected, SelectedType

log = logging.getLogger(__name__)

class HtmlSelector(Selector):
    """
    Extracts the HTML content from a Single element.
    
    This selector takes a Single element and returns its HTML representation
    as a Value string.
    """
    
    def __init__(self):
        """Initialize an HtmlSelector with no parameters."""
        self.expected_selected = SelectedType.SINGLE

    def select(self, selected):
        """
        Extract HTML from a SINGLE Selected.
        
        Args:
            selected: A Selected of type SINGLE (BeautifulSoup object)
            
        Returns:
            A Selected of type VALUE containing the HTML as a string
        """
        log.debug(f"HtmlSelector input: type={selected.selected_type}, value_type={type(selected.value)}")
        
        try:
            super().select(selected)
        except TypeError as e:
            log.error(f"HtmlSelector type validation error: {str(e)}")
            log.error(f"HtmlSelector input details: type={selected.selected_type}, value={selected}")
            # Re-raise the error since this is a critical type mismatch
            raise
        
        # Get the HTML content
        try:
            # Check if the value is a Tag or BeautifulSoup object before calling prettify
            if isinstance(selected.value, (bs4.element.Tag, BeautifulSoup)):
                html_content = selected.value.prettify()
                log.debug(f"HtmlSelector prettified HTML content, length: {len(html_content)}")
            else:
                # Handle cases like NavigableString - just convert to string
                html_content = str(selected.value)
                log.debug(f"HtmlSelector converted non-Tag to string, length: {len(html_content)}")
                
            result = Selected(html_content.strip(), SelectedType.VALUE)
            log.debug(f"HtmlSelector output: {result}")
            return result
        except Exception as e:
            log.error(f"HtmlSelector error extracting HTML: {e}")
            raise RuntimeError(f"Error extracting HTML: {e}") from e

    def toYamlDict(self):
        """Convert to YAML representation (simple string)."""
        return 'html_selector'

    @staticmethod
    def fromYamlDict(yaml_dict):
        """
        Create an HtmlSelector from YAML.
        
        Args:
            yaml_dict: Can be ignored as HtmlSelector takes no parameters
            
        Returns:
            A new HtmlSelector instance
        """
        return HtmlSelector()
