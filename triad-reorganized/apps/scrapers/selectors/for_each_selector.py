#!/usr/bin/env python3
# apps/scrapers/selectors/for_each_selector.py

import logging
from typing import Optional

from .base import Selector, Selected, SelectedType

log = logging.getLogger(__name__)

class ForEachSelector(Selector):
    """
    Applies a selector to each element in a MULTIPLE.
    
    This selector takes another selector and applies it to each element in the
    input MULTIPLE, returning a new MULTIPLE with the results.
    """
    
    def __init__(self, selector: Selector, skip_on_fail: bool = False):
        """
        Initialize a ForEachSelector.
        
        Args:
            selector: The Selector to apply to each element
            skip_on_fail: If True, skip elements that cause errors; if False, raise the error
        """
        self.expected_selected = SelectedType.MULTIPLE
        
        if not isinstance(selector, Selector):
            raise TypeError("ForEachSelector requires a Selector instance")
            
        self.selector = selector
        self.skip_on_fail = skip_on_fail

    def select(self, selected):
        """
        Apply the selector to each element in the MULTIPLE.
        
        Args:
            selected: A Selected of type MULTIPLE
            
        Returns:
            A new Selected of type MULTIPLE containing the results
        """
        super().select(selected)
        
        # Ensure value is a list
        if not isinstance(selected.value, list):
            raise TypeError("ForEachSelector input must have a list value")
            
        results = []
        for i, item in enumerate(selected.value):
            # Ensure each item is a Selected
            if not isinstance(item, Selected):
                err_msg = f"Item at index {i} in ForEachSelector input is not a Selected (type: {type(item)})"
                if self.skip_on_fail:
                    log.warning(f"Skipping: {err_msg}")
                    continue
                else:
                    raise TypeError(err_msg)
            
            # Apply the selector to this item
            try:
                result = self.selector.select(item)
                results.append(result)
            except Exception as e:
                if self.skip_on_fail:
                    log.warning(f"Error processing item at index {i}, skipping: {e}", exc_info=True)
                else:
                    # Add context to the error
                    raise RuntimeError(f"Error at index {i} in ForEachSelector: {e}") from e
                    
        return Selected(results, SelectedType.MULTIPLE)

    def toYamlDict(self):
        """Convert to YAML dictionary representation."""
        result = {
            'selector': self.selector.toYamlDict()
        }
        
        # Only include skip_on_fail if it's True
        if self.skip_on_fail:
            result['skip_on_fail'] = True
            
        return {'for_each_selector': result}

    @staticmethod
    def fromYamlDict(yaml_dict):
        """
        Create a ForEachSelector from a YAML dictionary.
        
        Args:
            yaml_dict: Dictionary containing 'selector' and optionally 'skip_on_fail'
            
        Returns:
            A new ForEachSelector instance
        """
        if 'selector' not in yaml_dict:
            raise ValueError("ForEachSelector YAML requires a 'selector' key")
            
        # Import the factory function here to avoid circular imports
        from .base import Selector
        
        # Parse the selector
        try:
            selector = Selector.fromYamlDict(yaml_dict['selector'])
        except Exception as e:
            raise ValueError(f"Error parsing selector in ForEachSelector: {e}") from e
            
        # Get skip_on_fail option
        skip_on_fail = yaml_dict.get('skip_on_fail', False)
        if not isinstance(skip_on_fail, bool):
            raise TypeError("'skip_on_fail' must be a boolean")
            
        return ForEachSelector(selector, skip_on_fail=skip_on_fail)
