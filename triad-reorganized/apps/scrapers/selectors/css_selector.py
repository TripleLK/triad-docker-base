#!/usr/bin/env python3
# apps/scrapers/selectors/css_selector.py

import logging
from typing import Optional

from .base import Selector, Selected, SelectedType
from .indexed_selector import IndexedSelector

log = logging.getLogger(__name__)

class CSSSelector(Selector):
    """
    Uses BeautifulSoup's CSS selector capability to extract elements from HTML.
    
    This selector takes a CSS selector string and optionally an index.
    If an index is provided, it returns the element at that index as a SINGLE.
    Otherwise, it returns all matching elements as a MULTIPLE.
    """
    
    def __init__(self, css_selector: str, index: Optional[int] = None):
        """
        Initialize a CSS selector.
        
        Args:
            css_selector: A CSS selector string (e.g., 'div.content > p.main')
            index: Optional index to return only one element from the results
        """
        self.expected_selected = SelectedType.SINGLE  # Expects a single Tag/Soup object
        if not isinstance(css_selector, str):
            raise TypeError("CSS selector must be a string")
        if index is not None and not isinstance(index, int):
            raise TypeError("Index must be an integer if provided")
            
        self.css_selector_text = css_selector
        self.index = index

    def select(self, selected):
        """
        Apply the CSS selector to the input Selected object.
        
        Args:
            selected: A Selected object of type SINGLE (a BeautifulSoup object)
            
        Returns:
            If index is None: A Selected MULTIPLE containing all matching elements
            If index is provided: A Selected SINGLE containing the element at that index
        """
        log.debug(f"CSSSelector '{self.css_selector_text}' input: type={selected.selected_type}")
        
        # Validate input type
        try:
            super().select(selected)
        except TypeError as e:
            log.error(f"CSSSelector type validation error: {str(e)}")
            log.error(f"CSSSelector expected SINGLE but got {selected.selected_type}")
            raise
        
        # BeautifulSoup's select() method returns a list of matching elements
        try:
            matching_elements = selected.value.select(self.css_selector_text)
            log.debug(f"CSSSelector '{self.css_selector_text}' found {len(matching_elements)} matching elements")
        except Exception as e:
            log.error(f"CSSSelector error applying selector '{self.css_selector_text}': {e}")
            raise RuntimeError(f"Error applying CSS selector '{self.css_selector_text}': {e}") from e
            
        # Wrap each element in a Selected SINGLE
        selected_elements = [Selected(element, SelectedType.SINGLE) for element in matching_elements]
        
        # If no elements found, return an empty MULTIPLE
        if not selected_elements:
            log.debug(f"CSSSelector '{self.css_selector_text}' found no matching elements")
            
        # Return all elements as a MULTIPLE, or apply index if specified
        multiple_result = Selected(selected_elements, SelectedType.MULTIPLE)
        
        if self.index is not None:
            log.debug(f"CSSSelector applying index {self.index} to {len(selected_elements)} elements")
            # Import locally to avoid circular imports
            try:
                indexed_result = IndexedSelector(self.index).select(multiple_result)
                log.debug(f"CSSSelector indexed result: {indexed_result}")
                return indexed_result
            except IndexError as e:
                log.error(f"CSSSelector index error: {e}")
                # Handle index out of bounds gracefully
                raise IndexError(f"Index {self.index} out of bounds for CSS selector '{self.css_selector_text}' (found {len(selected_elements)} elements)")
        
        log.debug(f"CSSSelector returning MULTIPLE with {len(selected_elements)} elements")
        return multiple_result

    def toYamlDict(self):
        """Convert to YAML dictionary representation."""
        result = {"css_selector": self.css_selector_text}
        if self.index is not None:
            result["index"] = self.index
        return {"css_selector": result}

    @staticmethod
    def fromYamlDict(yaml_dict):
        """
        Create a CSSSelector from a YAML dictionary.
        
        Args:
            yaml_dict: Dictionary containing 'css_selector' and optionally 'index'
            
        Returns:
            A new CSSSelector instance
        """
        if isinstance(yaml_dict, str):
            # Handle legacy format if needed
            return CSSSelector(yaml_dict)
            
        # Check for required css_selector key
        if "css_selector" not in yaml_dict:
            raise ValueError("CSS selector YAML requires a 'css_selector' key")
            
        # Handle case where css_selector might be the value directly or nested
        css_selector = yaml_dict["css_selector"]
        if isinstance(css_selector, str):
            # Simple format: {"css_selector": "div.content"}
            return CSSSelector(css_selector, index=yaml_dict.get("index"))
        elif isinstance(css_selector, dict):
            # Nested format: {"css_selector": {"css_selector": "div.content", "index": 0}}
            return CSSSelector(
                css_selector["css_selector"],
                index=css_selector.get("index")
            )
        else:
            raise TypeError(f"Invalid CSS selector format: {yaml_dict}") 