#!/usr/bin/env python3
# apps/scrapers/selectors/__init__.py

"""
Selectors Package

This package provides a collection of selectors for extracting and transforming data 
from HTML documents using BeautifulSoup.

The selector system is designed to be:
1. Composable - Selectors can be combined and chained together
2. Serializable - Selectors can be saved to and loaded from YAML files
3. Type-safe - Selectors validate their input and output types
"""

# Export base classes and enums
from .base import Selector, Selected, SelectedType

# Export all selector implementations
from .css_selector import CSSSelector
from .text_selector import TextSelector 
from .indexed_selector import IndexedSelector
from .html_selector import HtmlSelector
from .attr_selector import AttrSelector
from .split_selector import SplitSelector
from .br_split_selector import BrSplitSelector
from .series_selector import SeriesSelector
from .for_each_selector import ForEachSelector
from .mapping_selector import MappingSelector
from .plain_text_selector import PlainTextSelector
from .concat_selector import ConcatSelector
from .print_selector import PrintSelector
from .file_selector import FileSelector
from .zip_selector import ZipSelector
from .value_to_single_selector import ValueToSingleSelector
from .regex_selector import RegexSelector

__all__ = [
    # Base classes
    'Selector', 'Selected', 'SelectedType',
    
    # Core selectors
    'CSSSelector', 'TextSelector', 'IndexedSelector', 
    
    # Additional selectors
    'HtmlSelector', 'AttrSelector', 'SplitSelector', 'BrSplitSelector',
    'SeriesSelector', 'ForEachSelector', 'MappingSelector', 
    'PlainTextSelector', 'ConcatSelector', 'PrintSelector', 
    'FileSelector', 'ZipSelector', 'ValueToSingleSelector',
    'RegexSelector'
]
