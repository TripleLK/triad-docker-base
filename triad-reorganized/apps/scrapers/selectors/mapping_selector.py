#!/usr/bin/env python3
# apps/scrapers/selectors/mapping_selector.py

import logging
from typing import Dict, Optional, Literal
from copy import deepcopy

from .base import Selector, Selected, SelectedType

log = logging.getLogger(__name__)

class MappingSelector(Selector):
    """
    Creates a dictionary by applying multiple selectors to the same input.
    
    This selector takes a dictionary of key names to selectors. It applies each
    selector to the input and creates a dictionary with the keys mapping to the
    results of the corresponding selectors.
    """
    
    VALID_ERROR_STRATEGIES = ["raise", "mark_none", "skip"]
    
    def __init__(self, mapping: Dict[str, Selector], error_strategy: Literal["raise", "mark_none", "skip"] = "raise"):
        """
        Initialize a MappingSelector.
        
        Args:
            mapping: Dictionary mapping key names to Selector instances
            error_strategy: How to handle errors:
                - "raise": Re-raise any errors that occur
                - "mark_none": Set the key's value to None if an error occurs
                - "skip": Skip the entire mapping operation if any selector errors
        """
        self.expected_selected = SelectedType.SINGLE
        
        # Validate mapping
        if not isinstance(mapping, dict):
            raise TypeError("MappingSelector requires a dictionary")
            
        for key, value in mapping.items():
            if not isinstance(key, str):
                raise TypeError(f"MappingSelector keys must be strings, got {type(key)}")
                
            if not isinstance(value, Selector):
                raise TypeError(f"MappingSelector values must be Selectors, got {type(value)} for key '{key}'")
                
        # Validate error strategy
        if error_strategy not in self.VALID_ERROR_STRATEGIES:
            raise ValueError(f"Invalid error_strategy: {error_strategy}. Must be one of {self.VALID_ERROR_STRATEGIES}")
                
        self.mapping = mapping
        self.error_strategy = error_strategy

    def select(self, selected):
        """
        Apply each selector in the mapping to the input.
        
        Args:
            selected: A Selected object that matches the expected input type
            
        Returns:
            A Selected of type VALUE containing a dictionary
        """
        super().select(selected)
        
        result = {}
        for key, selector in self.mapping.items():
            try:
                # Use deepcopy to ensure selector doesn't modify the input for other selectors
                selector_result = selector.select(deepcopy(selected))
                result[key] = selector_result.collapsed_value
            except Exception as e:
                if self.error_strategy == "raise":
                    # Add context to the error
                    raise RuntimeError(f"Error applying selector for key '{key}' in MappingSelector: {e}") from e
                elif self.error_strategy == "mark_none":
                    log.warning(f"Error for key '{key}' in MappingSelector, setting to None: {e}", exc_info=True)
                    result[key] = None
                elif self.error_strategy == "skip":
                    log.warning(f"Error for key '{key}' in MappingSelector, skipping entire mapping: {e}", exc_info=True)
                    raise RuntimeError(f"MappingSelector failed with 'skip' strategy due to error for key '{key}': {e}") from e
                    
        return Selected(result, SelectedType.VALUE)

    def toYamlDict(self):
        """Convert to YAML dictionary representation."""
        mapping_dict = {}
        
        # Add each selector to the mapping
        for key, selector in self.mapping.items():
            mapping_dict[key] = selector.toYamlDict()
            
        result = {
            'mapping': mapping_dict
        }
        
        # Only include error_strategy if it's not the default
        if self.error_strategy != "raise":
            result['error_strategy'] = self.error_strategy
            
        return {'mapping_selector': result}

    @staticmethod
    def fromYamlDict(yaml_dict):
        """
        Create a MappingSelector from a YAML dictionary.
        
        Args:
            yaml_dict: Dictionary containing:
                - 'mapping': Dictionary of key names to selector YAML
                - 'error_strategy' (optional): Error handling strategy
            
        Returns:
            A new MappingSelector instance
        """
        # Ensure mapping key exists
        if 'mapping' not in yaml_dict:
            raise ValueError("MappingSelector YAML requires a 'mapping' key")
            
        mapping_dict = yaml_dict['mapping']
        if not isinstance(mapping_dict, dict):
            raise TypeError("MappingSelector 'mapping' must be a dictionary")
            
        # Import the factory function here to avoid circular imports
        from .base import Selector
        
        # Parse selectors in the mapping
        mapping = {}
        for key, selector_dict in mapping_dict.items():
            try:
                selector = Selector.fromYamlDict(selector_dict)
                mapping[key] = selector
            except Exception as e:
                raise ValueError(f"Error parsing selector for key '{key}': {e}") from e
                
        # Get error strategy
        error_strategy = yaml_dict.get('error_strategy', 'raise')
        if error_strategy not in MappingSelector.VALID_ERROR_STRATEGIES:
            raise ValueError(f"Invalid error_strategy: {error_strategy}. Must be one of {MappingSelector.VALID_ERROR_STRATEGIES}")
            
        return MappingSelector(mapping, error_strategy=error_strategy)
