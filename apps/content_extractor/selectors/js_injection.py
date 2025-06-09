"""
JavaScript injection manager for content extractor.

This module handles the injection of JavaScript code into web pages
for interactive content selection. JavaScript code is now organized
into separate files for better maintainability.

Created by: Electric Sentinel  
Date: 2025-01-08
Project: Triad Docker Base
"""

import os
import json
from pathlib import Path
from typing import List
from .selection_context import SelectionField


class JavaScriptInjectionManager:
    """Manages JavaScript injection for interactive content selection."""
    
    def __init__(self):
        # Get the path to the static JavaScript files
        self.js_dir = Path(__file__).parent.parent / 'static' / 'js'
        
        # JavaScript files in load order (dependencies matter)
        self.js_files = [
            'content_extractor_core.js',      # Core utilities and colors
            'content_extractor_unified_menu.js', # Unified menu system (shared by all components)
            'content_extractor_ui.js',        # UI components and menus
            'content_extractor_xpath_editor.js', # XPath editor modal for AI preparation
            'content_extractor_events.js',    # Event handlers
            'content_extractor_selection.js'  # Selection management and initialization
        ]
    
    def _load_javascript_file(self, filename: str) -> str:
        """Load JavaScript content from a file."""
        file_path = self.js_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"JavaScript file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            raise RuntimeError(f"Failed to load JavaScript file {filename}: {e}")
    
    def _load_all_javascript(self) -> str:
        """Load and concatenate all JavaScript files in correct order."""
        js_parts = []
        
        for filename in self.js_files:
            try:
                content = self._load_javascript_file(filename)
                js_parts.append(f"// === {filename} ===")
                js_parts.append(content)
                js_parts.append("")  # Add blank line between files
            except Exception as e:
                print(f"Warning: Could not load {filename}: {e}")
                # Continue loading other files even if one fails
                continue
        
        return "\n".join(js_parts)

    def get_selection_javascript(self, current_fields: List[SelectionField], 
                               current_depth: int, depth_color: str, 
                               breadcrumbs: List[str], base_url: str = 'http://localhost:8000', api_token: str = None) -> str:
        """
        Generate complete JavaScript for content selection interface.
        
        Args:
            current_fields: List of fields available for selection
            current_depth: Current nesting depth
            depth_color: Color for current depth level
            breadcrumbs: Navigation breadcrumb trail
            base_url: Base URL for API calls (defaults to localhost:8000)
            api_token: API token for authentication (optional)
            
        Returns:
            Complete JavaScript code as string
        """
        # Convert fields to JavaScript-compatible format
        field_data = []
        for field in current_fields:
            # Convert sub_fields if they exist
            sub_fields_data = []
            if field.sub_fields:
                for sub_field in field.sub_fields:
                    sub_fields_data.append({
                        'name': sub_field.name,
                        'label': sub_field.label,
                        'description': sub_field.description,
                        'type': sub_field.type,
                        'color': sub_field.color or '#007bff'
                    })
            
            field_data.append({
                'name': field.name,
                'label': field.label, 
                'description': field.description,
                'type': field.type,
                'color': field.color or '#007bff',
                'has_sub_fields': bool(field.sub_fields),
                'sub_fields': sub_fields_data if sub_fields_data else None
            })
        
        # Load all JavaScript files
        try:
            javascript_content = self._load_all_javascript()
        except Exception as e:
            print(f"Error loading JavaScript files: {e}")
            # Fallback to a minimal JavaScript snippet
            javascript_content = """
            console.error('Failed to load Content Extractor JavaScript files');
            alert('Content Extractor: JavaScript files could not be loaded. Please check the installation.');
            """
        
        # Create initialization data with API token
        initialization_js = f"""
        // Initialize Content Extractor Data
        window.contentExtractorData = {{
            fieldOptions: {json.dumps(field_data)},
            currentDepth: {current_depth},
            depthColor: '{depth_color}',
            breadcrumbs: {json.dumps(breadcrumbs)},
            contextPath: window.location.pathname,
            fieldSelections: {{}},
            instanceSelections: {{}},
            selectedDOMElements: new Set(),
            isSelectionMode: false,
            activeField: null,
            activeSubfield: null,
            isSelectionPaused: false,
            pendingAction: null,
            scriptVersion: '3.2.0',
            baseUrl: '{base_url}',
            apiToken: {json.dumps(api_token) if api_token else 'null'}
        }};
        
        console.log('🎯 Content Extractor initialized with', window.contentExtractorData.fieldOptions.length, 'fields');
        console.log('🌐 Base URL set to:', window.contentExtractorData.baseUrl);
        console.log('🔑 API Token configured:', window.contentExtractorData.apiToken ? 'Yes' : 'No');
        
        // Automatically load existing selectors for this domain after initialization
        setTimeout(function() {{
            if (typeof loadExistingSelectors === 'function') {{
                console.log('🔄 Automatically loading existing selectors for domain:', window.location.hostname);
                loadExistingSelectors().then(function(fieldMappings) {{
                    if (fieldMappings && Object.keys(fieldMappings).length > 0) {{
                        console.log('✅ Successfully loaded existing selectors:', Object.keys(fieldMappings));
                    }} else {{
                        console.log('📝 No existing selectors found for this domain');
                    }}
                }}).catch(function(error) {{
                    console.error('❌ Error auto-loading existing selectors:', error);
                }});
            }} else {{
                console.warn('⚠️ loadExistingSelectors function not available');
            }}
        }}, 1000); // Wait 1 second for all functions to be loaded
        """
        
        # Combine initialization with loaded JavaScript
        return initialization_js + "\n\n" + javascript_content

    # Legacy methods kept for backward compatibility but now just return empty strings
    # since the functionality has been moved to separate JavaScript files
    
    def _get_color_definitions(self) -> str:
        """Legacy method - functionality moved to content_extractor_core.js"""
        return ""
    
    def _get_core_functions(self) -> str:
        """Legacy method - functionality moved to content_extractor_core.js"""
        return ""
    
    def _get_ui_components(self) -> str:
        """Legacy method - functionality moved to content_extractor_ui.js"""
        return ""
    
    def _get_event_handlers(self) -> str:
        """Legacy method - functionality moved to content_extractor_events.js"""
        return ""
    
    def _get_nested_navigation(self) -> str:
        """Legacy method - functionality moved to content_extractor_selection.js"""
        return ""
    
    def _get_control_panel_enhanced(self) -> str:
        """Legacy method - functionality moved to content_extractor_selection.js"""
        return "" 