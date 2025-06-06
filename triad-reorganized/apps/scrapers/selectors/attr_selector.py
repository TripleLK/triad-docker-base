#!/usr/bin/env python3
# apps/scrapers/selectors/attr_selector.py

import logging
import bs4

from .base import Selector, Selected, SelectedType

log = logging.getLogger(__name__)

class AttrSelector(Selector):
    """
    Extracts an attribute from a Selected Single element.
    
    This selector takes an attribute name and returns the value of that attribute
    from the input element as a Value.
    """
    
    def __init__(self, attr):
        """
        Initialize an AttrSelector.
        
        Args:
            attr: The name of the attribute to extract (e.g., 'href', 'class', 'id')
        """
        self.expected_selected = SelectedType.SINGLE
        
        if not isinstance(attr, str) or not attr:
            raise ValueError("Attribute name must be a non-empty string")
            
        self.attr = attr

    def select(self, selected):
        """
        Extract the specified attribute from a SINGLE Selected.
        
        Args:
            selected: A Selected of type SINGLE (BeautifulSoup object)
            
        Returns:
            A Selected of type VALUE containing the attribute value
        """
        super().select(selected)
        
        # Ensure selected.value is a Tag object, as NavigableString, etc., don't have attrs
        if not isinstance(selected.value, bs4.element.Tag):
            raise TypeError(f"AttrSelector requires a bs4.element.Tag, but received {type(selected.value)}")
            
        try:
            # Use .get() for safer access, returning None if attr doesn't exist
            attr_value = selected.value.get(self.attr)
            return Selected(attr_value, SelectedType.VALUE)
        except Exception as e:
            raise RuntimeError(f"Error extracting attribute '{self.attr}': {e}") from e

    def toYamlDict(self):
        """Convert to YAML dictionary representation."""
        return {'attr_selector': {'attr': self.attr}}

    @staticmethod
    def fromYamlDict(yaml_dict):
        """
        Create an AttrSelector from a YAML dictionary.
        
        Args:
            yaml_dict: Dictionary containing 'attr' key
            
        Returns:
            A new AttrSelector instance
        """
        if 'attr' not in yaml_dict:
            raise ValueError("AttrSelector YAML requires an 'attr' key")
            
        if not isinstance(yaml_dict['attr'], str) or not yaml_dict['attr']:
            raise ValueError("AttrSelector 'attr' must be a non-empty string")
            
        return AttrSelector(yaml_dict['attr'])
