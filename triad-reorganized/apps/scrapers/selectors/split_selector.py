#!/usr/bin/env python3
# apps/scrapers/selectors/split_selector.py

import logging

from .base import Selector, Selected, SelectedType

log = logging.getLogger(__name__)

class SplitSelector(Selector):
    """
    Splits a string value by a delimiter.
    
    This selector takes a delimiter string and splits the input value by that delimiter,
    returning a MULTIPLE of VALUE elements.
    """
    
    def __init__(self, delimiter):
        """
        Initialize a SplitSelector.
        
        Args:
            delimiter: The string to split by (e.g., ',', '\n', ' ')
        """
        # Can handle both VALUE type (direct string) and SINGLE type (element that can be converted to text)
        self.expected_selected = [SelectedType.VALUE, SelectedType.SINGLE]
        
        if not isinstance(delimiter, str):
            raise TypeError("Delimiter must be a string")
            
        self.delimiter = delimiter

    def select(self, selected):
        """
        Split the input by the delimiter.
        
        Args:
            selected: A Selected of type VALUE (string) or SINGLE (can be converted to string)
            
        Returns:
            A Selected of type MULTIPLE containing Selected VALUEs for each split part
        """
        super().select(selected)
        
        # Get the text representation
        if selected.selected_type == SelectedType.SINGLE:
            # Use .get_text() for BeautifulSoup elements or str() for others
            try:
                text = selected.value.get_text()
            except AttributeError:
                text = str(selected.value)
        else:  # VALUE type
            text = str(selected.value)
        
        # Split the text
        split_parts = text.split(self.delimiter)
        
        # Create a Selected VALUE for each non-empty part
        parts = [Selected(part.strip(), SelectedType.VALUE) 
                for part in split_parts 
                if part.strip()]
                
        return Selected(parts, SelectedType.MULTIPLE)

    def toYamlDict(self):
        """Convert to YAML dictionary representation."""
        return {'split_selector': {'delimiter': self.delimiter}}

    @staticmethod
    def fromYamlDict(yaml_dict):
        """
        Create a SplitSelector from a YAML dictionary.
        
        Args:
            yaml_dict: Dictionary containing 'delimiter' key
            
        Returns:
            A new SplitSelector instance
        """
        if 'delimiter' not in yaml_dict:
            raise ValueError("SplitSelector YAML requires a 'delimiter' key")
            
        if not isinstance(yaml_dict['delimiter'], str):
            raise TypeError("SplitSelector 'delimiter' must be a string")
            
        return SplitSelector(yaml_dict['delimiter'])
