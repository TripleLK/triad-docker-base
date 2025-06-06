#!/usr/bin/env python3
# apps/scrapers/selectors/regex_selector.py

import re
import logging
from typing import Optional, Union, List
from bs4 import BeautifulSoup
from .base import Selector, Selected, SelectedType

log = logging.getLogger(__name__)

class RegexSelector(Selector):
    """
    A selector that applies a regex pattern to extract content from text.
    
    This selector accepts both SINGLE and VALUE types, converts them to string representation
    if needed, applies the regex pattern, and extracts the specified capture group.
    """
    
    def __init__(self, pattern: str, group: int = 0):
        """
        Initialize a RegexSelector with a regex pattern and group number.
        
        Args:
            pattern: The regex pattern to apply
            group: The capture group to extract (default: 0 - entire match)
        """
        self.pattern = pattern
        self.group = group
        # Accept both SINGLE and VALUE input types
        self.expected_selected = [SelectedType.SINGLE, SelectedType.VALUE]

    def select(self, selected: Selected) -> Selected:
        """
        Apply regex pattern to extract content from the input.
        
        Args:
            selected: A Selected object of type SINGLE or VALUE
            
        Returns:
            A Selected of type VALUE containing the extracted text or None if no match
        """
        # Log detailed input information
        log.debug(f"RegexSelector input: {selected}")
        log.debug(f"RegexSelector pattern: {self.pattern}, group: {self.group}")
        
        try:
            super().select(selected)
        except Exception as e:
            log.error(f"RegexSelector type validation error: {str(e)}")
            # Gracefully handle type mismatch by returning None
            return Selected(None, SelectedType.VALUE)
        
        # Convert input to string based on its type
        if selected.selected_type == SelectedType.SINGLE:
            try:
                # Handle BeautifulSoup objects
                if isinstance(selected.value, BeautifulSoup) or hasattr(selected.value, 'decode'):
                    input_text = str(selected.value)
                    log.debug(f"RegexSelector converting BeautifulSoup to string, length: {len(input_text)}")
                else:
                    # For regular Tag objects, get HTML representation
                    input_text = str(selected.value)
                    log.debug(f"RegexSelector converting Tag to string, length: {len(input_text)}")
            except AttributeError as e:
                log.warning(f"RegexSelector could not convert SINGLE to string: {e}")
                return Selected(None, SelectedType.VALUE)
        else:  # VALUE type
            input_text = str(selected.value) if selected.value is not None else ""
            log.debug(f"RegexSelector processing VALUE type, input: '{input_text[:100]}{'...' if len(input_text) > 100 else ''}'")
        
        # Apply the regex pattern
        try:
            log.debug(f"RegexSelector applying pattern: {self.pattern}")
            matches = re.search(self.pattern, input_text, re.DOTALL)
            if matches:
                result = matches.group(self.group).strip()
                log.debug(f"RegexSelector match found, result: '{result[:100]}{'...' if len(result) > 100 else ''}'")
                return Selected(result, SelectedType.VALUE)
            else:
                log.debug(f"RegexSelector no match found for pattern: {self.pattern}")
                return Selected(None, SelectedType.VALUE)
        except (re.error, IndexError) as e:
            log.error(f"RegexSelector regex error with pattern '{self.pattern}': {e}")
            return Selected(None, SelectedType.VALUE)
        except Exception as e:
            log.error(f"RegexSelector unexpected error: {e}")
            return Selected(None, SelectedType.VALUE)

    def toYamlDict(self):
        """Convert to YAML representation."""
        return {
            'regex_selector': {
                'pattern': self.pattern,
                'group': self.group
            }
        }

    @classmethod
    def fromYamlDict(cls, yaml_dict):
        """
        Create a RegexSelector from YAML.
        
        Args:
            yaml_dict: Dictionary containing 'pattern' and optional 'group'
            
        Returns:
            A new RegexSelector instance
        """
        if isinstance(yaml_dict, dict):
            pattern = yaml_dict.get('pattern')
            group = yaml_dict.get('group', 0)
            
            if not pattern:
                raise ValueError("RegexSelector requires 'pattern' parameter")
                
            return cls(pattern=pattern, group=group)
        else:
            raise ValueError(f"Expected dict for RegexSelector, got {type(yaml_dict)}") 