#!/usr/bin/env python3
# apps/scrapers/selectors/zip_selector.py

import logging
from copy import deepcopy

from .base import Selector, Selected, SelectedType

log = logging.getLogger(__name__)

class ZipSelector(Selector):
    """
    Creates a dictionary by zipping keys and values from two selectors.
    
    This selector takes two selectors:
    1. A keys selector that returns a MULTIPLE of VALUES
    2. A vals selector that returns a MULTIPLE of VALUES
    
    It applies both selectors to the input and creates a dictionary mapping
    the keys to the corresponding values.
    """
    
    def __init__(self, keys_selector, vals_selector):
        """
        Initialize a ZipSelector.
        
        Args:
            keys_selector: A Selector that returns a MULTIPLE of VALUES to use as keys
            vals_selector: A Selector that returns a MULTIPLE of VALUES to use as values
        """
        # This selector can accept any input type, as it depends on the sub-selectors
        self.expected_selected = None
        
        if not isinstance(keys_selector, Selector):
            raise TypeError("keys_selector must be a Selector instance")
            
        if not isinstance(vals_selector, Selector):
            raise TypeError("vals_selector must be a Selector instance")
            
        self.keys_selector = keys_selector
        self.vals_selector = vals_selector

    def select(self, selected):
        """
        Apply both selectors and create a dictionary by zipping their results.
        
        Args:
            selected: Any Selected object accepted by both sub-selectors
            
        Returns:
            A Selected of type VALUE containing the resulting dictionary
        """
        # Apply selectors to get keys and values
        # Use deepcopy to prevent side effects between selectors
        keys_result = self.keys_selector.select(deepcopy(selected))
        vals_result = self.vals_selector.select(deepcopy(selected))
        
        # Verify both results are MULTIPLE type
        if keys_result.selected_type != SelectedType.MULTIPLE:
            raise TypeError(f"keys_selector must return a MULTIPLE, but returned {keys_result.selected_type}")
            
        if vals_result.selected_type != SelectedType.MULTIPLE:
            raise TypeError(f"vals_selector must return a MULTIPLE, but returned {vals_result.selected_type}")
            
        # Get the lists of keys and values
        keys = keys_result.value
        vals = vals_result.value
        
        # Verify lists have the same length
        if len(keys) != len(vals):
            raise ValueError(f"keys and vals must have the same length, but got {len(keys)} keys and {len(vals)} vals")
            
        # Extract the collapsed values
        key_values = []
        for i, key in enumerate(keys):
            if not isinstance(key, Selected):
                raise TypeError(f"Item at index {i} in keys is not a Selected (type: {type(key)})")
                
            # Keys must be hashable
            try:
                key_value = key.collapsed_value
                # Try to hash the key to ensure it's usable as a dictionary key
                hash(key_value)
                key_values.append(key_value)
            except Exception as e:
                raise TypeError(f"Key at index {i} is not hashable: {e}") from e
                
        val_values = []
        for i, val in enumerate(vals):
            if not isinstance(val, Selected):
                raise TypeError(f"Item at index {i} in vals is not a Selected (type: {type(val)})")
                
            val_values.append(val.collapsed_value)
            
        # Create the dictionary
        result = dict(zip(key_values, val_values))
        
        return Selected(result, SelectedType.VALUE)

    def toYamlDict(self):
        """Convert to YAML dictionary representation."""
        return {
            'zip_selector': {
                'keys': self.keys_selector.toYamlDict(),
                'vals': self.vals_selector.toYamlDict()
            }
        }

    @staticmethod
    def fromYamlDict(yaml_dict):
        """
        Create a ZipSelector from a YAML dictionary.
        
        Args:
            yaml_dict: Dictionary containing 'keys' and 'vals' keys
            
        Returns:
            A new ZipSelector instance
        """
        if 'keys' not in yaml_dict or 'vals' not in yaml_dict:
            raise ValueError("ZipSelector YAML requires 'keys' and 'vals' keys")
            
        # Import the factory function here to avoid circular imports
        from .base import Selector
        
        # Parse the selectors
        try:
            keys_selector = Selector.fromYamlDict(yaml_dict['keys'])
        except Exception as e:
            raise ValueError(f"Error parsing keys selector: {e}") from e
            
        try:
            vals_selector = Selector.fromYamlDict(yaml_dict['vals'])
        except Exception as e:
            raise ValueError(f"Error parsing vals selector: {e}") from e
            
        return ZipSelector(keys_selector, vals_selector)
