#!/usr/bin/env python3
# apps/scrapers/selectors/file_selector.py

import logging
import os

from .base import Selector, Selected

log = logging.getLogger(__name__)

class FileSelector(Selector):
    """
    Loads a selector from a file and uses it.
    
    This allows breaking complex selectors into reusable files. It loads
    the selector definition from the specified YAML file and applies it.
    """
    
    def __init__(self, file_path):
        """
        Initialize a FileSelector.
        
        Args:
            file_path: Path to the YAML file containing a selector definition
        """
        # FileSelector accepts any input type that the loaded selector accepts
        self.expected_selected = None
        
        if not isinstance(file_path, str):
            raise TypeError("file_path must be a string")
            
        if not file_path:
            raise ValueError("file_path cannot be empty")
            
        self.file_path = file_path
        self._selector = None  # Lazy-loaded

    @property
    def selector(self):
        """
        Get the selector loaded from the file.
        
        This property lazily loads the selector when first accessed.
        
        Returns:
            The loaded Selector instance
        """
        if self._selector is None:
            # Import here to avoid circular imports
            from .base import Selector
            
            try:
                self._selector = Selector.fromFilePath(self.file_path)
                if self._selector is None:
                    raise ValueError(f"Failed to load selector from file: {self.file_path}")
            except Exception as e:
                # Add context to the error
                raise RuntimeError(f"Error loading selector from file '{self.file_path}': {e}") from e
                
            # Inherit expected_selected from the loaded selector
            self.expected_selected = self._selector.expected_selected
                
        return self._selector

    def select(self, selected):
        """
        Apply the loaded selector to the input.
        
        Args:
            selected: A Selected object matching the expected type of the loaded selector
            
        Returns:
            The result of applying the loaded selector
        """
        return self.selector.select(selected)

    def toYamlDict(self):
        """Convert to YAML dictionary representation."""
        return {'file_selector': {'file_path': self.file_path}}

    @staticmethod
    def fromYamlDict(yaml_dict):
        """
        Create a FileSelector from a YAML dictionary.
        
        Args:
            yaml_dict: Dictionary containing 'file_path' key
            
        Returns:
            A new FileSelector instance
        """
        if 'file_path' not in yaml_dict:
            raise ValueError("FileSelector YAML requires a 'file_path' key")
            
        file_path = yaml_dict['file_path']
        if not isinstance(file_path, str) or not file_path:
            raise ValueError("file_path must be a non-empty string")
            
        return FileSelector(file_path)
