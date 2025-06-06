#!/usr/bin/env python3
# apps/scrapers/selectors/base.py

import bs4
from bs4 import BeautifulSoup
from enum import Enum
from abc import ABC, abstractmethod
from copy import deepcopy
import re
import yaml
import logging # Use logging
from typing import Any, Dict, List, Optional, Union

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# --- Core Data Structures ---

class SelectedType(Enum):
    """Defines the type of data held by a Selected object."""
    VALUE = 0    # Terminal value (e.g., string, dict, list, number, None)
    SINGLE = 1   # A single BeautifulSoup Tag or the root BeautifulSoup object
    MULTIPLE = 2 # A list of Selected objects

class Selected:
    """Wraps the result of a Selector operation, indicating its type."""
    def __init__(self, value, selected_type):
        if not isinstance(selected_type, SelectedType):
            raise TypeError("selected_type must be an instance of SelectedType Enum")
        self.value = value
        self.selected_type = selected_type
        self._validate_selected_type()

    @property
    def collapsed_value(self):
        """Recursively collapses MULTIPLE Selecteds to a list of values, otherwise returns the value."""
        if self.selected_type == SelectedType.MULTIPLE:
            # Ensure the value is actually a list before trying to iterate
            if not isinstance(self.value, list):
                 # This indicates an internal inconsistency if validation passed/was skipped
                 log.warning(f"Selected of type MULTIPLE has non-list value: {type(self.value)}. Returning raw value.")
                 return self.value
            return [sub_selected.collapsed_value for sub_selected in self.value if isinstance(sub_selected, Selected)]
        elif self.selected_type == SelectedType.SINGLE:
             # Decide how to collapse SINGLE: text? html? raw object?
             # Let's default to text for now, but this could be configurable or context-dependent.
             if isinstance(self.value, (bs4.element.Tag, BeautifulSoup)):
                 return self.value.get_text(strip=True)
             return str(self.value) # Fallback for NavigableString etc.
        else: # VALUE type
            return self.value

    # Keep __str__ simple for basic representation
    def __str__(self):
         # Limit length for readability
        str_val = str(self.value)
        max_len = 100
        if len(str_val) > max_len:
             str_val = str_val[:max_len] + "..."
        return f"Selected({self.selected_type.name}, value='{str_val}')"

    # __repr__ is often more useful for debugging
    def __repr__(self):
        return f"Selected(value={repr(self.value)}, selected_type=SelectedType.{self.selected_type.name})"

    def _validate_selected_type(self):
        """Validate that the value is appropriate for the declared type."""
        if self.selected_type == SelectedType.MULTIPLE:
            if not isinstance(self.value, list):
                raise TypeError(f"MULTIPLE Selected must have a list value, got {type(self.value)}")
                
            if not all(isinstance(item, Selected) for item in self.value):
                raise TypeError("MULTIPLE Selected must contain only Selected objects")
                
        # Add more validation for SINGLE type if needed
        

# --- Abstract Base Selector ---

class Selector(ABC):
    """Abstract base class for all selector operations."""
    expected_selected: Optional[Union[SelectedType, List[SelectedType]]] = None

    def validate_selected_type(self, selected):
        """Checks if the input Selected object's type matches expectations."""
        if self.expected_selected is None:
            return # None means any type is accepted

        allowed_types = self.expected_selected
        if not isinstance(allowed_types, list):
            allowed_types = [allowed_types] # Make it a list for uniform checking

        if selected.selected_type not in allowed_types:
            expected_names = " or ".join([st.name for st in allowed_types])
            raise TypeError(
                f"{type(self).__name__} expects input of type {expected_names}, "
                f"but received {selected.selected_type.name}."
            )

    # Make select the primary method users override
    @abstractmethod
    def select(self, selected: Selected) -> Selected:
        """Performs the selection logic on the input Selected object."""
        # Basic validation happens first
        self.validate_selected_type(selected)
        # Subclasses will implement the core logic here
        pass # This method MUST be overridden

    # __call__ provides a convenient way to use selector instances
    def __call__(self, selected: Selected) -> Selected:
        """Allows calling the selector instance like a function."""
        # Add logging for entry/exit?
        # log.debug(f"Calling {type(self).__name__} on {selected}")
        result = self.select(selected)
        # log.debug(f"{type(self).__name__} returned {result}")
        return result

    # --- YAML Loading Factory Methods ---

    @classmethod
    def fromYamlDict(cls, yaml_dict):
        """
        Create a selector from a YAML dictionary.

        This function recursively creates a selector from a YAML dictionary, by dispatching
        to the appropriate selector class based on the keys in the dictionary or the string
        value.
        """
        from apps.scrapers.selectors.css_selector import CSSSelector
        from apps.scrapers.selectors.text_selector import TextSelector
        from apps.scrapers.selectors.html_selector import HtmlSelector
        from apps.scrapers.selectors.indexed_selector import IndexedSelector
        from apps.scrapers.selectors.mapping_selector import MappingSelector
        from apps.scrapers.selectors.for_each_selector import ForEachSelector
        from apps.scrapers.selectors.plain_text_selector import PlainTextSelector
        from apps.scrapers.selectors.series_selector import SeriesSelector
        from apps.scrapers.selectors.split_selector import SplitSelector
        from apps.scrapers.selectors.br_split_selector import BrSplitSelector
        from apps.scrapers.selectors.value_to_single_selector import ValueToSingleSelector
        from apps.scrapers.selectors.zip_selector import ZipSelector
        from apps.scrapers.selectors.parent_selector import ParentSelector
        from apps.scrapers.selectors.regex_selector import RegexSelector
        from apps.scrapers.selectors.file_selector import FileSelector
        from apps.scrapers.selectors.concat_selector import ConcatSelector
        from apps.scrapers.selectors.attr_selector import AttrSelector
        from apps.scrapers.selectors.categorized_tag_page_selector import CategorizedTagPageSelector
        from apps.scrapers.selectors.print_selector import PrintSelector

        if yaml_dict is None:
            return None
        elif isinstance(yaml_dict, dict):
            # Check if there's exactly one key
            if len(yaml_dict) != 1:
                raise ValueError(f"Expected exactly one key in selector dict, got {len(yaml_dict)} keys: {list(yaml_dict.keys())}")

            # Get the key and value
            key = list(yaml_dict.keys())[0]
            value = yaml_dict[key]

            # Dispatch to the appropriate class based on the key
            if key == "css_selector":
                return CSSSelector.fromYamlDict(value)
            elif key == "text_selector":
                return TextSelector.fromYamlDict(value)
            elif key == "html_selector":
                return HtmlSelector.fromYamlDict(value)
            elif key == "indexed_selector":
                return IndexedSelector.fromYamlDict(value)
            elif key == "mapping_selector":
                return MappingSelector.fromYamlDict(value)
            elif key == "for_each_selector":
                return ForEachSelector.fromYamlDict(value)
            elif key == "plain_text_selector":
                return PlainTextSelector.fromYamlDict(value)
            elif key == "series_selector":
                return SeriesSelector.fromYamlDict(value)
            elif key == "split_selector":
                return SplitSelector.fromYamlDict(value)
            elif key == "br_split_selector":
                return BrSplitSelector.fromYamlDict(value)
            elif key == "value_to_single_selector":
                return ValueToSingleSelector.fromYamlDict(value)
            elif key == "zip_selector":
                return ZipSelector.fromYamlDict(value)
            elif key == "parent_selector":
                return ParentSelector.fromYamlDict(value)
            elif key == "regex_selector":
                return RegexSelector.fromYamlDict(value)
            elif key == "file_selector":
                return FileSelector.fromYamlDict(value)
            elif key == "concat_selector":
                return ConcatSelector.fromYamlDict(value)
            elif key == "print_selector":
                return PrintSelector.fromYamlDict(value)
            elif key == "attr_selector":
                return AttrSelector.fromYamlDict(value)
            elif key == "categorized_tag_page_selector":
                return CategorizedTagPageSelector.fromYamlDict(value)
            else:
                raise ValueError(f"Unknown selector type: {key}")
        elif isinstance(yaml_dict, str):
            # Handle simple string selectors
            string_specs_dict = {
                "text_selector": TextSelector,
                "html_selector": HtmlSelector,
                "value_to_single_selector": ValueToSingleSelector,
                "parent_selector": ParentSelector
            }
            if yaml_dict in string_specs_dict:
                # Call the specific class's fromYamlDict (which might just return an instance)
                return string_specs_dict[yaml_dict].fromYamlDict(yaml_dict)
            else:
                raise ValueError(f"Unknown string-based selector type: {yaml_dict}")
        elif isinstance(yaml_dict, list):
            # Lists are treated as a series of selectors to be applied in order
            return SeriesSelector.fromYamlDict(yaml_dict)
        else:
            raise ValueError(f"Unknown YAML dict type: {type(yaml_dict)}")

    @staticmethod
    def fromFilePath(file_path):
        """Loads a Selector configuration from a YAML file path."""
        try:
            with open(file_path, 'r') as file:
                yaml_content = file.read()
            # Use safe_load to prevent arbitrary code execution
            yaml_dict = yaml.safe_load(yaml_content)
            if yaml_dict is None:
                # Handle empty file case gracefully
                log.warning(f"YAML file is empty: {file_path}")
                raise ValueError(f"YAML file is empty: {file_path}") # Raise error instead of returning None

        except FileNotFoundError:
            log.error(f"YAML file not found: {file_path}")
            raise # Re-raise the specific error
        except yaml.YAMLError as e:
            log.error(f"Error parsing YAML file {file_path}: {e}")
            raise ValueError(f"Invalid YAML format in {file_path}") from e
        except Exception as e:
            # Catch other potential errors during file reading or initial parsing
            log.error(f"An unexpected error occurred while loading YAML from {file_path}: {e}", exc_info=True)
            raise RuntimeError(f"Failed to load selector from {file_path}") from e # Use RuntimeError for unexpected issues

        # Once loaded, delegate to the dictionary-based factory method
        try:
             return Selector.fromYamlDict(yaml_dict)
        except Exception as e:
             # Catch errors during Selector construction from the loaded dict
             log.error(f"Error constructing selector from loaded YAML in {file_path}: {e}", exc_info=True)
             # Re-raise the error, possibly adding file context
             raise Exception(f"Error processing selector definition in {file_path}: {e}") from e


    # --- YAML Saving Method ---
    # Needs to be implemented by each subclass

    @abstractmethod
    def toYamlDict(self):
        """Returns the YAML dictionary representation of the selector."""
        pass # Must be implemented by subclasses
