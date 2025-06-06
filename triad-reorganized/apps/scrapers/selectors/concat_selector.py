#!/usr/bin/env python3
# apps/scrapers/selectors/concat_selector.py

import logging
from copy import deepcopy

from .base import Selector, Selected, SelectedType

log = logging.getLogger(__name__)

class ConcatSelector(Selector):
    """
    Concatenates the results of two selectors.
    
    This selector takes two selectors, applies both to the input, and returns
    the concatenation of their results as a string.
    """
    
    def __init__(self, first, second):
        """
        Initialize a ConcatSelector.
        
        Args:
            first: The first Selector to apply
            second: The second Selector to apply
        """
        # This selector can accept any input type, as it depends on the sub-selectors
        self.expected_selected = None
        
        if not isinstance(first, Selector):
            raise TypeError("first must be a Selector instance")
            
        if not isinstance(second, Selector):
            raise TypeError("second must be a Selector instance")
            
        self.first = first
        self.second = second

    def select(self, selected):
        """
        Apply both selectors and concatenate their results.
        
        Args:
            selected: Any Selected object accepted by both sub-selectors
            
        Returns:
            A Selected of type VALUE containing the concatenated results
        """
        # We need to use deepcopy to avoid any side effects from the first selector
        # affecting the second selector's input
        first_result = self.first.select(deepcopy(selected))
        second_result = self.second.select(deepcopy(selected))
        
        # Extract string values from the results
        # Use collapsed_value to handle different result types
        first_value = str(first_result.collapsed_value) if first_result.collapsed_value is not None else ""
        second_value = str(second_result.collapsed_value) if second_result.collapsed_value is not None else ""
        
        # Concatenate the results
        result = first_value + second_value
        
        return Selected(result, SelectedType.VALUE)

    def toYamlDict(self):
        """Convert to YAML dictionary representation."""
        return {
            'concat_selector': {
                'first': self.first.toYamlDict(),
                'second': self.second.toYamlDict()
            }
        }

    @staticmethod
    def fromYamlDict(yaml_dict):
        """
        Create a ConcatSelector from a YAML dictionary.
        
        Args:
            yaml_dict: Dictionary containing 'first' and 'second' keys
            
        Returns:
            A new ConcatSelector instance
        """
        if 'first' not in yaml_dict or 'second' not in yaml_dict:
            raise ValueError("ConcatSelector YAML requires 'first' and 'second' keys")
            
        # Import the factory function here to avoid circular imports
        from .base import Selector
        
        # Parse the selectors
        try:
            first = Selector.fromYamlDict(yaml_dict['first'])
        except Exception as e:
            raise ValueError(f"Error parsing first selector: {e}") from e
            
        try:
            second = Selector.fromYamlDict(yaml_dict['second'])
        except Exception as e:
            raise ValueError(f"Error parsing second selector: {e}") from e
            
        return ConcatSelector(first, second)
