#!/usr/bin/env python3
# apps/scrapers/selectors/br_split_selector.py

import logging
import re
from bs4 import BeautifulSoup
from .base import Selector, Selected, SelectedType

log = logging.getLogger(__name__)

class BrSplitSelector(Selector):
    """
    Splits HTML content by <br/> tags.
    
    This selector specifically handles splitting HTML content by <br/> tags (in various forms)
    and returns each segment as a SINGLE type in a MULTIPLE result, preserving the HTML structure
    for further processing.
    """
    
    def __init__(self, include_empty=False):
        """
        Initialize a BrSplitSelector.
        
        Args:
            include_empty: Whether to include empty segments in the result (default: False)
        """
        # Can only handle SINGLE type (HTML element)
        self.expected_selected = SelectedType.SINGLE
        self.include_empty = include_empty
        # Pattern matches various forms of <br> tags (<br>, <br/>, <br />)
        self.br_pattern = re.compile(r'<br\s*/?>', re.IGNORECASE)

    def select(self, selected):
        """
        Split the HTML content by <br/> tags.
        
        Args:
            selected: A Selected of type SINGLE (HTML content)
            
        Returns:
            A Selected of type MULTIPLE containing SINGLE values for each segment
        """
        super().select(selected)
        
        # Get the HTML representation
        if hasattr(selected.value, 'decode'):
            html_content = str(selected.value)
        else:
            html_content = str(selected.value)
        
        log.debug(f"BrSplitSelector processing HTML: {html_content[:100]}...")
        
        # Split the HTML by <br/> tags
        segments = self.br_pattern.split(html_content)
        log.debug(f"BrSplitSelector found {len(segments)} segments")
        
        # Create a Selected SINGLE for each segment
        result_segments = []
        for i, segment in enumerate(segments):
            if not segment.strip() and not self.include_empty:
                log.debug(f"BrSplitSelector skipping empty segment {i}")
                continue
                
            # Make sure segment has proper HTML structure
            segment = segment.strip()
            
            # Wrap segments without HTML tags in paragraph tags
            if not segment.startswith('<'):
                segment = f"<p>{segment}</p>"
            elif not segment.endswith('>'):
                # Make sure segment ends with HTML tag
                segment = f"{segment}</p>"
            
            # Create a new BeautifulSoup object for each segment
            try:
                soup = BeautifulSoup(segment, 'html.parser')
                result_segments.append(Selected(soup, SelectedType.SINGLE))
                log.debug(f"BrSplitSelector added segment {i}: {segment[:50]}...")
            except Exception as e:
                log.error(f"BrSplitSelector error processing segment {i}: {e}")
                
        return Selected(result_segments, SelectedType.MULTIPLE)

    def toYamlDict(self):
        """Convert to YAML dictionary representation."""
        return {'br_split_selector': {'include_empty': self.include_empty}}

    @staticmethod
    def fromYamlDict(yaml_dict):
        """
        Create a BrSplitSelector from a YAML dictionary.
        
        Args:
            yaml_dict: Dictionary that may contain 'include_empty' key
            
        Returns:
            A new BrSplitSelector instance
        """
        include_empty = False
        if isinstance(yaml_dict, dict):
            include_empty = yaml_dict.get('include_empty', False)
            
        return BrSplitSelector(include_empty=include_empty) 