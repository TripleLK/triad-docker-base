#!/usr/bin/env python3
# apps/scrapers/selectors/series_selector.py

import logging
from typing import List

from .base import Selector, Selected, SelectedType

log = logging.getLogger(__name__)

class SeriesSelector(Selector):
    """
    Applies a sequence of selectors in order.
    
    This selector takes a list of other selectors and applies them in sequence,
    with each selector operating on the output of the previous one.
    """
    
    def __init__(self, selectors: List[Selector]):
        """
        Initialize a SeriesSelector.
        
        Args:
            selectors: A list of Selector instances to apply in sequence
        """
        if not isinstance(selectors, list):
            raise TypeError("SeriesSelector requires a list of selectors")
            
        if not all(isinstance(s, Selector) for s in selectors):
            raise TypeError("All items in selectors list must be Selector instances")
            
        self.selectors = selectors
        
        # The expected input type is determined by the first selector in the series
        # If no selectors, accept any input (becomes identity operation)
        if selectors:
            self.expected_selected = selectors[0].expected_selected
        else:
            self.expected_selected = None

    def select(self, selected):
        """
        Apply each selector in sequence.
        
        Args:
            selected: A Selected object that matches the expected type of the first selector
            
        Returns:
            The result of applying all selectors in sequence
        """
        log.debug(f"SeriesSelector starting with input: {selected}")
        
        # Validate initial input if we have an expected type
        if self.expected_selected is not None:
            try:
                super().select(selected)
            except TypeError as e:
                log.error(f"SeriesSelector type validation error: {str(e)}")
                log.error(f"SeriesSelector expected {self.expected_selected} but got {selected.selected_type}")
                raise
        
        # For empty series, return input unchanged
        if not self.selectors:
            log.debug("SeriesSelector has no selectors, returning input unchanged")
            return selected
        
        # Apply selectors in sequence
        current = selected
        for i, selector in enumerate(self.selectors):
            selector_name = type(selector).__name__
            log.debug(f"SeriesSelector step {i+1}/{len(self.selectors)}: applying {selector_name}")
            log.debug(f"  Input to {selector_name}: type={current.selected_type}, value={current}")
            
            try:
                current = selector.select(current)
                log.debug(f"  Output from {selector_name}: type={current.selected_type}, value={current}")
            except Exception as e:
                # Add context about which selector failed
                log.error(f"SeriesSelector error in step {i+1}/{len(self.selectors)} ({selector_name}): {e}")
                raise RuntimeError(f"Error in {selector_name} within SeriesSelector: {e}") from e
        
        log.debug(f"SeriesSelector completed with result: {current}")        
        return current

    def toYamlDict(self):
        """Convert to YAML list representation."""
        return [selector.toYamlDict() for selector in self.selectors]

    @staticmethod
    def fromYamlDict(yaml_dict):
        """
        Create a SeriesSelector from a YAML list.
        
        Args:
            yaml_dict: List of YAML dicts, each representing a selector
            
        Returns:
            A new SeriesSelector instance
        """
        if not isinstance(yaml_dict, list):
            raise TypeError("SeriesSelector YAML must be a list")
            
        # Import the factory function here to avoid circular imports
        from .base import Selector
        
        # Convert each item in the list to a Selector
        selectors = []
        for i, selector_dict in enumerate(yaml_dict):
            try:
                selector = Selector.fromYamlDict(selector_dict)
                selectors.append(selector)
            except Exception as e:
                raise ValueError(f"Error parsing selector at index {i}: {e}") from e
                
        return SeriesSelector(selectors)
