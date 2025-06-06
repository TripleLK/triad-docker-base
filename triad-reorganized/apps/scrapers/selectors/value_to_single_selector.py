#!/usr/bin/env python3
# apps/scrapers/selectors/value_to_single_selector.py

import logging
from typing import Any, Dict, Optional

from bs4 import BeautifulSoup

from apps.scrapers.selectors.base import Selected, SelectedType, Selector

log = logging.getLogger(__name__)

class ValueToSingleSelector(Selector):
    """
    Selector that converts a VALUE type to a SINGLE type.
    
    This is useful for bridging between selectors that produce VALUE types
    and selectors that expect SINGLE types.
    """
    
    def __init__(self, parser: str = "html.parser"):
        """
        Initialize the ValueToSingleSelector.
        
        Args:
            parser: The HTML parser to use. Default is "html.parser".
        """
        self.parser = parser
    
    def select(self, selected: Selected) -> Selected:
        """
        Convert a VALUE type to a SINGLE type by wrapping it in a BeautifulSoup object.
        
        Args:
            selected: A Selected object containing a value.
            
        Returns:
            A Selected object containing a BeautifulSoup object (SINGLE type).
            
        Raises:
            RuntimeError: If the input is not of type VALUE.
        """
        if selected.selected_type != SelectedType.VALUE:
            raise RuntimeError(f"ValueToSingleSelector expects input of type VALUE, but got {selected.selected_type}")
        
        try:
            value = selected.value
            if isinstance(value, str):
                # Wrap string in a BeautifulSoup object
                soup = BeautifulSoup(f"<div>{value}</div>", self.parser)
                return Selected(soup.div, SelectedType.SINGLE)
            else:
                # For non-string values, convert to string first
                soup = BeautifulSoup(f"<div>{str(value)}</div>", self.parser)
                return Selected(soup.div, SelectedType.SINGLE)
        except Exception as e:
            raise RuntimeError(f"Error converting VALUE to SINGLE: {e}")
    
    @classmethod
    def fromYamlDict(cls, yaml_dict: Dict[str, Any]) -> "ValueToSingleSelector":
        """
        Create a ValueToSingleSelector from a YAML dictionary.
        
        Args:
            yaml_dict: A dictionary containing the configuration.
            
        Returns:
            A ValueToSingleSelector object.
        """
        if isinstance(yaml_dict, str):
            # Simple case: just 'value_to_single_selector'
            return cls()
        
        # Get the parser (optional)
        parser = yaml_dict.get("parser", "html.parser")
        return cls(parser=parser)
    
    def toYamlDict(self) -> Dict[str, Any]:
        """
        Convert this selector to a YAML dictionary.
        
        Returns:
            A dictionary suitable for YAML serialization.
        """
        if self.parser == "html.parser":
            return "value_to_single_selector"
        else:
            return {
                "value_to_single_selector": {
                    "parser": self.parser
                }
            } 