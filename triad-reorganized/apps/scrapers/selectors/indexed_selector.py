#!/usr/bin/env python3
# apps/scrapers/selectors/indexed_selector.py

import logging
from typing import Union

from .base import Selector, Selected, SelectedType

log = logging.getLogger(__name__)

class IndexedSelector(Selector):
    """
    A selector that extracts a specific element from a Multiple Selected.
    
    This selector takes an index n and returns the nth element from the input
    Selected Multiple collection.
    """
    
    def __init__(self, index: Union[int, slice]):
        """
        Initialize an IndexedSelector.
        
        Args:
            index: The index to extract, or a slice object for extracting a range
        """
        self.expected_selected = SelectedType.MULTIPLE
        
        # Support both integer indices and slices
        if not isinstance(index, (int, slice)):
            raise TypeError("Index must be an integer or slice object")
            
        self.index = index

    def select(self, selected):
        """
        Extract the element at specified index from a MULTIPLE Selected.
        
        Args:
            selected: A Selected of type MULTIPLE
            
        Returns:
            If index is int: The Selected at position index
            If index is slice: A Selected MULTIPLE containing the sliced elements
        """
        super().select(selected)
        
        # Ensure value is a list
        if not isinstance(selected.value, list):
            raise TypeError("IndexedSelector requires a list value in the Selected Multiple object")
            
        try:
            # Handle both integer index and slice
            if isinstance(self.index, int):
                # For integer index, return the single element
                return selected.value[self.index]
            else:
                # For slice, return a MULTIPLE of the sliced elements
                return Selected(selected.value[self.index], SelectedType.MULTIPLE)
        except IndexError:
            # Provide a helpful error message
            raise IndexError(f"Index {self.index} out of bounds for list of length {len(selected.value)}")

    def toYamlDict(self):
        """Convert to YAML dictionary representation."""
        result = {'index': self.index}
        # If index is a slice, we need special handling
        if isinstance(self.index, slice):
            # Convert slice to a format that can be serialized and parsed
            result = {
                'slice': {
                    'start': self.index.start,
                    'stop': self.index.stop,
                    'step': self.index.step
                }
            }
        return {'indexed_selector': result}

    @staticmethod
    def fromYamlDict(yaml_dict):
        """
        Create an IndexedSelector from a YAML dictionary.
        
        Args:
            yaml_dict: Dictionary containing 'index' or 'slice'
            
        Returns:
            A new IndexedSelector instance
        """
        if 'index' in yaml_dict:
            index = yaml_dict['index']
            if not isinstance(index, int):
                raise TypeError("IndexedSelector 'index' must be an integer")
            return IndexedSelector(index)
        elif 'slice' in yaml_dict:
            # Parse slice parameters
            slice_dict = yaml_dict['slice']
            if not isinstance(slice_dict, dict):
                raise TypeError("IndexedSelector 'slice' must be a dictionary")
                
            # Create a slice object
            slice_obj = slice(
                slice_dict.get('start'),
                slice_dict.get('stop'),
                slice_dict.get('step')
            )
            return IndexedSelector(slice_obj)
        else:
            raise ValueError("IndexedSelector YAML requires an 'index' or 'slice' key") 