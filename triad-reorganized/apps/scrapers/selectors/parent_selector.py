#!/usr/bin/env python3
# apps/scrapers/selectors/parent_selector.py

import logging
from typing import Any, Dict, Optional

from apps.scrapers.selectors.base import Selected, SelectedType, Selector

log = logging.getLogger(__name__)

class ParentSelector(Selector):
    """
    A selector that finds the parent element of a selected element.
    
    This selector expects a SINGLE type input (a BeautifulSoup element) and outputs
    the parent element as a SINGLE type.
    """
    
    def __init__(self, levels: int = 1):
        """
        Initialize the ParentSelector.
        
        Args:
            levels: Number of levels to go up in the parent hierarchy. Default is 1.
        """
        self.levels = levels
    
    def select(self, selected: Selected) -> Selected:
        """
        Select the parent element of the input element.
        
        Args:
            selected: A Selected object containing a BeautifulSoup element.
            
        Returns:
            A Selected object containing the parent element.
            
        Raises:
            RuntimeError: If the input is not of type SINGLE.
        """
        if selected.selected_type != SelectedType.SINGLE:
            raise RuntimeError(f"ParentSelector expects input of type SINGLE, but got {selected.selected_type}")
        
        try:
            element = selected.value
            
            # If this is a strong tag, get its direct parent (which should be a paragraph)
            if element.name == 'strong':
                if element.parent:
                    log.debug(f"Found parent of strong tag: {element.parent.name}")
                    return Selected(element.parent, SelectedType.SINGLE)
                else:
                    log.warning("Strong tag has no parent")
            
            # If we have levels specified, go up that many levels in hierarchy
            for i in range(self.levels):
                if element.parent and element.parent.name != '[document]':
                    element = element.parent
                    log.debug(f"Went up to parent: {element.name}")
                else:
                    log.warning(f"Reached the top of the document at level {i}, cannot go up further")
                    break
                    
            return Selected(element, SelectedType.SINGLE)
        except Exception as e:
            raise RuntimeError(f"Error finding parent element: {e}")
    
    @classmethod
    def fromYamlDict(cls, yaml_dict: Dict[str, Any]) -> "ParentSelector":
        """
        Create a ParentSelector from a YAML dictionary.
        
        Args:
            yaml_dict: A dictionary containing the configuration.
            
        Returns:
            A ParentSelector object.
        """
        if isinstance(yaml_dict, str):
            # Simple case: just 'parent_selector'
            return cls()
        
        # Get the number of levels to go up (optional)
        levels = yaml_dict.get("levels", 1)
        return cls(levels=levels)

    def toYamlDict(self) -> Dict[str, Any]:
        """
        Convert this selector to a YAML dictionary.
        
        Returns:
            A dictionary suitable for YAML serialization.
        """
        if self.levels == 1:
            return "parent_selector"
        else:
            return {
                "parent_selector": {
                    "levels": self.levels
                }
            } 