#!/usr/bin/env python3
# apps/scrapers/selectors/print_selector.py

import logging

from .base import Selector, Selected, SelectedType

log = logging.getLogger(__name__)

class PrintSelector(Selector):
    """
    Prints information for debugging purposes.
    
    This selector takes a message and optionally prints the input Selected object's
    value. It passes through the input unchanged, making it useful for debugging
    selector chains.
    """
    
    def __init__(self, message, print_selected=False):
        """
        Initialize a PrintSelector.
        
        Args:
            message: The message to print
            print_selected: If True, also print information about the Selected object
        """
        # This selector accepts any input type
        self.expected_selected = None
        
        self.message = str(message)
        self.print_selected = bool(print_selected)

    def select(self, selected):
        """
        Print the message and optionally the selected object, then return the input.
        
        Args:
            selected: Any Selected object
            
        Returns:
            The same Selected object that was passed in
        """
        # Log the message
        log.info(f"PrintSelector: {self.message}")
        
        # If requested, also log information about the Selected object
        if self.print_selected:
            try:
                # Handle different selected types
                if selected.selected_type == SelectedType.MULTIPLE:
                    length = len(selected.value) if isinstance(selected.value, list) else "unknown"
                    log.info(f"  Selected type: MULTIPLE, count: {length}")
                    
                    # For MULTIPLE, show a preview of the first few items
                    if isinstance(selected.value, list) and selected.value:
                        max_preview = 3
                        for i, item in enumerate(selected.value[:max_preview]):
                            log.info(f"  Item {i}: {type(item).__name__}")
                        if len(selected.value) > max_preview:
                            log.info(f"  ... ({len(selected.value) - max_preview} more items)")
                            
                elif selected.selected_type == SelectedType.SINGLE:
                    tag_name = getattr(selected.value, 'name', None)
                    tag_info = f", tag: {tag_name}" if tag_name else ""
                    log.info(f"  Selected type: SINGLE{tag_info}")
                    
                    # For SINGLE, show a preview of the HTML
                    preview = str(selected.value)[:100]
                    if len(preview) == 100:
                        preview += "..."
                    log.info(f"  Value preview: {preview}")
                    
                else:  # VALUE
                    value_type = type(selected.value).__name__
                    log.info(f"  Selected type: VALUE, value type: {value_type}")
                    
                    # For VALUE, show the value directly
                    preview = str(selected.value)[:100]
                    if len(preview) == 100:
                        preview += "..."
                    log.info(f"  Value: {preview}")
                    
            except Exception as e:
                # Don't let logging errors disrupt the selector chain
                log.warning(f"Error printing Selected info: {e}")
                
        # Pass through the input unchanged
        return selected

    def toYamlDict(self):
        """Convert to YAML dictionary representation."""
        result = {'message': self.message}
        
        # Only include print_selected if it's True
        if self.print_selected:
            result['print_selected'] = True
            
        return {'print_selector': result}

    @staticmethod
    def fromYamlDict(yaml_dict):
        """
        Create a PrintSelector from a YAML dictionary.
        
        Args:
            yaml_dict: Dictionary containing:
                - 'message': The message to print
                - 'print_selected' (optional): Whether to print the Selected info
            
        Returns:
            A new PrintSelector instance
        """
        if 'message' not in yaml_dict:
            raise ValueError("PrintSelector YAML requires a 'message' key")
            
        message = yaml_dict['message']
        print_selected = yaml_dict.get('print_selected', False)
        
        return PrintSelector(message, print_selected=print_selected)
