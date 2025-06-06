#!/usr/bin/env python3
# apps/scrapers/selectors/soup_selector.py

import logging
from typing import Dict, Any

from .css_selector import CSSSelector

log = logging.getLogger(__name__)

class SoupSelector(CSSSelector):
    """
    Legacy SoupSelector redirects to CSSSelector for backward compatibility.
    
    This is a thin wrapper around CSSSelector that converts old SoupSelector syntax
    to the new CSS selector syntax.
    """
    
    @staticmethod
    def fromYamlDict(yaml_dict: Any) -> CSSSelector:
        """
        Convert old soup_selector YAML format to use CSS selector format.
        
        Args:
            yaml_dict: Can be:
                - Dict with {'tag': str, 'attrs': Dict}
                - Dict with {'css_selector': str}
                - Dict with {'css_selector': Dict}
        
        Returns:
            A CSSSelector instance
        """
        if isinstance(yaml_dict, dict) and 'tag' in yaml_dict:
            # Old format used {'tag': 'div', 'attrs': {'class': 'content'}}
            # Convert to CSS selector format
            tag = yaml_dict.get('tag', '')
            attrs = yaml_dict.get('attrs', {})
            
            # Build a CSS selector from the tag and attributes
            selector_parts = [tag]
            for attr_name, attr_value in attrs.items():
                if attr_name == 'class':
                    # Handle class specially
                    classes = attr_value.split() if isinstance(attr_value, str) else attr_value
                    if isinstance(classes, list):
                        selector_parts.extend([f".{cls}" for cls in classes])
                    else:
                        selector_parts.append(f".{attr_value}")
                else:
                    # Handle other attributes
                    selector_parts.append(f"[{attr_name}='{attr_value}']")
            
            css_selector = ''.join(selector_parts)
            index = yaml_dict.get('index')
            
            log.warning(f"Using deprecated SoupSelector format. Please migrate to CSSSelector. "
                        f"Converted '{yaml_dict}' to CSS selector: '{css_selector}'")
            
            return CSSSelector(css_selector, index=index)
        else:
            # If it doesn't have 'tag', just pass it to CSSSelector
            log.warning(f"Using deprecated SoupSelector. Please use CSSSelector directly.")
            return CSSSelector.fromYamlDict(yaml_dict)
