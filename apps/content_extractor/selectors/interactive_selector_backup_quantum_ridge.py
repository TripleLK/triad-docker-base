"""
Interactive Selector for Content Extraction

Uses Selenium to display web pages and capture user selections
for generating robust content selectors with field-specific assignment.
Enhanced with floating field selection menu for LabEquipmentPage model.
Now includes site-specific selector storage and cross-page testing.
Enhanced with nested object selection architecture for recursive hierarchical data.

Created by: Phoenix Velocity
Date: 2025-01-08
Enhanced by: Quantum Catalyst  
Date: 2025-01-08
Enhanced by: Crimson Phoenix
Date: 2025-01-08
Enhanced by: Quantum Horizon (Nested Selection Architecture)
Date: 2025-01-08
Project: Triad Docker Base
"""

import time
import json
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import logging

# Django imports for model integration
from django.utils import timezone
from apps.content_extractor.models import SiteFieldSelector, SelectorTestResult, FieldSelectionSession

# Import nested selection architecture
from .selection_context import NestedSelectionManager, SelectionField

logger = logging.getLogger(__name__)


class InteractiveSelector:
    """Manages Selenium-based interactive element selection with field-specific assignment, site-specific storage, and nested object selection"""
    
    # Legacy field options for backward compatibility
    FIELD_OPTIONS = [
        {'name': 'title', 'label': 'Title', 'type': 'single', 'description': 'Equipment main title'},
        {'name': 'short_description', 'label': 'Short Description', 'type': 'single', 'description': 'Brief equipment summary'},
        {'name': 'full_description', 'label': 'Full Description', 'type': 'single', 'description': 'Detailed equipment description'},
        {'name': 'source_url', 'label': 'Source URL', 'type': 'single', 'description': 'Original product page URL'},
        {'name': 'source_type', 'label': 'Source Type', 'type': 'single', 'description': 'New/Used/Refurbished indicator'},
        {'name': 'models', 'label': 'Models', 'type': 'multi-value', 'description': 'Product model variations'},
        {'name': 'features', 'label': 'Features', 'type': 'multi-value', 'description': 'Equipment features list'},
        {'name': 'accessories', 'label': 'Accessories', 'type': 'multi-value', 'description': 'Related accessories/parts'},
        {'name': 'categorized_tags', 'label': 'Categorized Tags', 'type': 'multi-value', 'description': 'Category and tag assignments'},
        {'name': 'gallery_images', 'label': 'Gallery Images', 'type': 'multi-value', 'description': 'Product image gallery'},
        {'name': 'spec_groups', 'label': 'Specification Groups', 'type': 'multi-value', 'description': 'Technical specifications with nested specs'}
    ]
    
    def __init__(self, headless: bool = False, session_name: str = None):
        """
        Initialize the interactive selector.
        
        Args:
            headless: Whether to run browser in headless mode
            session_name: Optional session name for tracking progress
        """
        self.headless = headless
        self.driver = None
        self.selected_elements = []
        self.current_url = None
        self.current_domain = None
        self.session_name = session_name or f"Session_{int(time.time())}"
        
        # Initialize nested selection manager
        self.nested_manager = NestedSelectionManager()
        
        # Legacy selection session data for backward compatibility
        self.selection_session_data = {
            'active_field': None,
            'field_selections': {},  # field_name -> [selections]
            'multi_value_examples': {}  # field_name -> [example1, example2]
        }
        
        # Field selection session for progress tracking
        self.field_session = None
    
    def setup_driver(self):
        """Set up Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Set window size for consistency
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Inject our enhanced selection JavaScript
            self._inject_selection_js()
            
            logger.info("WebDriver setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup WebDriver: {e}")
            return False
    
    def _inject_selection_js(self):
        """Inject enhanced JavaScript for nested object selection with recursive contexts"""
        # Get current fields from nested manager
        current_fields = self.nested_manager.get_current_fields()
        field_options_js = json.dumps([
            {
                'name': field.name,
                'label': field.label,
                'type': field.type,
                'description': field.description,
                'color': field.color,
                'has_sub_fields': field.sub_fields is not None
            }
            for field in current_fields
        ])
        
        # Get current context information
        current_depth = self.nested_manager.get_current_depth()
        depth_color = self.nested_manager.get_depth_color()
        breadcrumbs = self.nested_manager.get_breadcrumbs()
        
        selection_js = f"""
        window.contentExtractorData = {{
            selectedElements: [],
            selectedDOMElements: new Set(),
            isSelectionMode: false,
            currentLabel: '',
            activeField: null,
            fieldSelections: {{}},
            multiValueExamples: {{}},
            fieldOptions: {field_options_js},
            // Nested selection state
            currentDepth: {current_depth},
            depthColor: '{depth_color}',
            breadcrumbs: {json.dumps(breadcrumbs)},
            contextPath: '',
            nestedContexts: {{}},
            // Instance management for 3-level hierarchy
            instanceData: {{}}
        }};
        
        // Depth-based colors for visual hierarchy
        const DEPTH_COLORS = [
            '#3498db',  // Blue - root level
            '#e74c3c',  // Red - first nesting  
            '#f39c12',  // Orange - second nesting
            '#27ae60',  // Green - third nesting
            '#9b59b6',  // Purple - fourth nesting
            '#34495e'   // Dark gray - deeper nesting
        ];
        
        // Get depth color
        function getDepthColor(depth) {{
            return DEPTH_COLORS[Math.min(depth, DEPTH_COLORS.length - 1)];
        }}
        
        // Field-specific highlight colors (legacy support)
        const FIELD_COLORS = {{
            'title': '#ff6b6b',
            'short_description': '#4ecdc4', 
            'full_description': '#45b7d1',
            'source_url': '#dda0dd',
            'source_type': '#98d8c8',
            'models': '#bb8fce',
            'features': '#85c1e9',
            'accessories': '#f8c471',
            'categorized_tags': '#82e0aa',
            'gallery_images': '#f1948a',
            'spec_groups': '#aed6f1'
        }};
        
        // Get field color with depth override
        function getFieldColor(fieldName) {{
            if (window.contentExtractorData.currentDepth > 0) {{
                // Use depth color for nested contexts
                return getDepthColor(window.contentExtractorData.currentDepth);
            }}
            return FIELD_COLORS[fieldName] || '#007bff';
        }}
        
        // Enhanced highlight element with depth indication
        function highlightElement(element) {{
            if (!window.contentExtractorData.selectedDOMElements.has(element)) {{
                const color = getFieldColor(window.contentExtractorData.activeField);
                const depth = window.contentExtractorData.currentDepth;
                const borderWidth = 2 + (depth * 2); // Increase border width with depth
                
                element.style.outline = `${{borderWidth}}px solid ${{color}}`;
                element.style.backgroundColor = `${{color}}44`;
                element.style.boxShadow = `0 0 ${{8 + depth * 4}}px ${{color}}88`;
                element.style.zIndex = `${{9999 + depth}}`;
                element.style.position = 'relative';
                
                // Add depth pattern for visual hierarchy
                if (depth > 0) {{
                    element.style.borderStyle = depth === 1 ? 'dashed' : depth === 2 ? 'dotted' : 'solid';
                }}
            }}
        }}
        
        // Remove highlight (only if not already selected)
        function removeHighlight(element) {{
            if (!window.contentExtractorData.selectedDOMElements.has(element)) {{
                element.style.outline = '';
                element.style.backgroundColor = '';
                element.style.boxShadow = '';
                element.style.zIndex = '';
                element.style.position = '';
                element.style.borderStyle = '';
            }}
        }}
        
        // Mark element as selected with enhanced depth styling
        function markAsSelected(element, fieldName) {{
            window.contentExtractorData.selectedDOMElements.add(element);
            const color = getFieldColor(fieldName);
            const depth = window.contentExtractorData.currentDepth;
            const borderWidth = 3 + (depth * 2);
            
            element.style.outline = `${{borderWidth}}px solid ${{color}}`;
            element.style.backgroundColor = `${{color}}66`;
            element.style.boxShadow = `0 0 ${{12 + depth * 4}}px ${{color}}aa`;
            element.style.position = 'relative';
            element.style.zIndex = `${{9998 + depth}}`;
            element.setAttribute('data-content-extractor-selected', 'true');
            element.setAttribute('data-field-name', fieldName);
            element.setAttribute('data-selection-depth', depth);
            
            // Enhanced depth styling
            if (depth > 0) {{
                element.style.borderStyle = depth === 1 ? 'dashed' : depth === 2 ? 'dotted' : 'solid';
            }}
            
            // Add enhanced indicator badge with depth info
            const badge = document.createElement('div');
            badge.setAttribute('data-selection-badge', fieldName);
            badge.setAttribute('data-content-extractor-ui', 'true');
            badge.style.cssText = `
                position: absolute !important;
                top: -${{8 + depth * 2}}px !important;
                right: -${{8 + depth * 2}}px !important;
                background: ${{color}} !important;
                color: white !important;
                border-radius: 50% !important;
                width: ${{20 + depth * 4}}px !important;
                height: ${{20 + depth * 4}}px !important;
                font-size: ${{10 + depth}}px !important;
                font-weight: bold !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                z-index: ${{10000 + depth}} !important;
                border: 2px solid white !important;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3) !important;
                font-family: 'Segoe UI', Arial, sans-serif !important;
            `;
            badge.textContent = depth > 0 ? depth : '✓';
            element.appendChild(badge);
        }}
        
        // Generate XPath for element
        function getXPath(element) {{
            if (element.id !== '') {{
                return `//*[@id="${{element.id}}"]`;
            }}
            if (element === document.body) {{
                return '/html/body';
            }}
            
            let ix = 0;
            let siblings = element.parentNode.childNodes;
            for (let i = 0; i < siblings.length; i++) {{
                let sibling = siblings[i];
                if (sibling === element) {{
                    return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                }}
                if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {{
                    ix++;
                }}
            }}
        }}
        
        // Generate CSS selector for element
        function getCSSSelector(element) {{
            if (element.id) {{
                return '#' + element.id;
            }}
            
            let path = '';
            while (element.parentNode) {{
                let selector = element.tagName.toLowerCase();
                if (element.className) {{
                    selector += '.' + element.className.trim().split(/\\s+/).join('.');
                }}
                
                let sibling = element;
                let nth = 1;
                while (sibling.previousElementSibling) {{
                    sibling = sibling.previousElementSibling;
                    if (sibling.tagName.toLowerCase() === selector.split('.')[0]) {{
                        nth++;
                    }}
                }}
                if (nth > 1) {{
                    selector += ':nth-of-type(' + nth + ')';
                }}
                
                path = selector + (path ? ' > ' + path : '');
                element = element.parentNode;
                
                if (element === document.body) {{
                    break;
                }}
            }}
            return path;
        }}
        
        // Create breadcrumb navigation
        function createBreadcrumbNavigation() {{
            const breadcrumbs = window.contentExtractorData.breadcrumbs || ['Root'];
            const currentDepth = window.contentExtractorData.currentDepth;
            
            let breadcrumbHTML = `
                <div style="
                    background: rgba(52,73,94,0.95) !important;
                    padding: 8px 12px !important;
                    border-radius: 6px !important;
                    margin-bottom: 12px !important;
                    border-left: 4px solid ${{getDepthColor(currentDepth)}} !important;
                ">
                    <div style="font-size: 11px !important; color: #bdc3c7 !important; margin-bottom: 4px !important;">Navigation Path (Depth: ${{currentDepth}})</div>
                    <div style="display: flex !important; align-items: center !important; gap: 4px !important; flex-wrap: wrap !important;">
            `;
            
            breadcrumbs.forEach((crumb, index) => {{
                const isLast = index === breadcrumbs.length - 1;
                const isClickable = index < breadcrumbs.length - 1;
                
                breadcrumbHTML += `
                    <span style="
                        color: ${{isLast ? '#3498db' : '#ecf0f1'}} !important;
                        font-weight: ${{isLast ? '600' : '400'}} !important;
                        font-size: 12px !important;
                        cursor: ${{isClickable ? 'pointer' : 'default'}} !important;
                        padding: 2px 6px !important;
                        border-radius: 3px !important;
                        background: ${{isLast ? 'rgba(52,152,219,0.2)' : 'transparent'}} !important;
                        transition: all 0.2s !important;
                    " 
                    ${{isClickable ? `onclick="navigateToDepth(${{index}})" onmouseover="this.style.backgroundColor='rgba(52,152,219,0.3)'" onmouseout="this.style.backgroundColor='transparent'"` : ''}}
                    >${{crumb}}</span>
                `;
                
                if (!isLast) {{
                    breadcrumbHTML += `<span style="color: #7f8c8d !important; font-size: 10px !important;">→</span>`;
                }}
            }});
            
            breadcrumbHTML += `
                    </div>
                </div>
            `;
            
            return breadcrumbHTML;
        }}
        
        // Navigate to specific depth level
        window.navigateToDepth = function(targetDepth) {{
            // This would trigger Python callback to navigate to specific depth
            const event = new CustomEvent('nestedNavigate', {{ 
                detail: {{ targetDepth: targetDepth }}
            }});
            document.dispatchEvent(event);
        }};
        
        // Create enhanced field selection menu with nested context support
        function createFieldSelectionMenu() {{
            const menu = document.createElement('div');
            menu.id = 'field-selection-menu';
            menu.setAttribute('data-content-extractor-ui', 'true');
            
            const currentDepth = window.contentExtractorData.currentDepth;
            const depthColor = getDepthColor(currentDepth);
            
            menu.style.cssText = `
                position: fixed !important;
                top: 20px !important;
                left: 20px !important;
                background: linear-gradient(135deg, #2c3e50, #34495e) !important;
                color: white !important;
                padding: 25px !important;
                border-radius: 12px !important;
                z-index: ${{10001 + currentDepth}} !important;
                font-family: 'Segoe UI', Arial, sans-serif !important;
                font-size: 14px !important;
                max-width: 420px !important;
                box-shadow: 0 8px 24px rgba(0,0,0,0.5) !important;
                max-height: 85vh !important;
                overflow-y: auto !important;
                border: 3px solid ${{depthColor}} !important;
            `;
            
            let menuHTML = createBreadcrumbNavigation();
            
            menuHTML += `
                <div style="border-bottom: 2px solid ${{depthColor}} !important; padding-bottom: 18px !important; margin-bottom: 18px !important;">
                    <h3 style="margin: 0 !important; color: #ecf0f1 !important; font-size: 18px !important; font-weight: 600 !important; font-family: 'Segoe UI', Arial, sans-serif !important;">
                        🎯 Field Selection
                        <span style="font-size: 14px !important; color: ${{depthColor}} !important; margin-left: 8px !important;">(Depth ${{currentDepth}})</span>
                    </h3>
                    <p style="margin: 8px 0 0 0 !important; font-size: 13px !important; color: #bdc3c7 !important; line-height: 1.4 !important; font-family: 'Segoe UI', Arial, sans-serif !important;">
                        Choose field for current context level:
                    </p>
                </div>
                <div id="field-options">
            `;
            
            // Get current field selections for status indicators
            const currentSelections = window.contentExtractorData.fieldSelections;
            
            // Group fields by type
            const singleFields = window.contentExtractorData.fieldOptions.filter(f => f.type === 'single');
            const multiFields = window.contentExtractorData.fieldOptions.filter(f => f.type === 'multi-value');
            const nestedFields = window.contentExtractorData.fieldOptions.filter(f => f.type === 'nested');
            
            // Single value fields
            if (singleFields.length > 0) {{
                menuHTML += `<div style="margin-bottom: 25px !important;">
                    <h4 style="margin: 0 0 12px 0 !important; color: #3498db !important; font-size: 15px !important; font-weight: 600 !important; font-family: 'Segoe UI', Arial, sans-serif !important;">📄 Single Value Fields</h4>
                `;
                
                singleFields.forEach(field => {{
                    const color = field.color;
                    const selectionCount = (currentSelections[field.name] || []).length;
                    const isComplete = selectionCount > 0;
                    const statusIcon = isComplete ? '✅' : '⭕';
                    const completionText = isComplete ? `(${{selectionCount}} selected)` : '(none)';
                    
                    menuHTML += `
                        <button class="field-option" data-field="${{field.name}}" style="
                            display: block !important;
                            width: 100% !important;
                            margin: 6px 0 !important;
                            padding: 12px 15px !important;
                            background: ${{isComplete ? color + '44' : color + '22'}} !important;
                            border: 2px solid ${{color}} !important;
                            border-radius: 8px !important;
                            color: white !important;
                            cursor: pointer !important;
                            text-align: left !important;
                            font-size: 13px !important;
                            font-family: 'Segoe UI', Arial, sans-serif !important;
                            transition: all 0.3s ease !important;
                            position: relative !important;
                            ${{isComplete ? 'box-shadow: 0 0 8px ' + color + '66 !important;' : ''}}
                        " onmouseover="this.style.backgroundColor='${{color}}66'; this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(0,0,0,0.3)'" 
                           onmouseout="this.style.backgroundColor='${{isComplete ? color + '44' : color + '22'}}'; this.style.transform='translateY(0)'; this.style.boxShadow='${{isComplete ? '0 0 8px ' + color + '66' : 'none'}}'">
                            <div style="display: flex !important; justify-content: space-between !important; align-items: center !important;">
                                <div style="font-weight: 600 !important; color: white !important;">${{field.label}}</div>
                                <div style="font-size: 16px !important;">${{statusIcon}}</div>
                            </div>
                            <div style="font-size: 11px !important; opacity: 0.9 !important; margin-top: 4px !important; color: white !important;">${{field.description}}</div>
                            <div style="font-size: 10px !important; opacity: 0.7 !important; margin-top: 2px !important; color: #ecf0f1 !important;">${{completionText}}</div>
                        </button>
                    `;
                }});
                menuHTML += `</div>`;
            }}
            
            // Multi-value fields
            if (multiFields.length > 0) {{
                menuHTML += `<div style="margin-bottom: 25px !important;">
                    <h4 style="margin: 0 0 12px 0 !important; color: #e74c3c !important; font-size: 15px !important; font-weight: 600 !important; font-family: 'Segoe UI', Arial, sans-serif !important;">📋 Multi-Value Fields</h4>
                    <p style="font-size: 11px !important; color: #95a5a6 !important; margin: 0 0 12px 0 !important; padding: 8px !important; background: rgba(231,76,60,0.1) !important; border-radius: 6px !important; border-left: 3px solid #e74c3c !important; font-family: 'Segoe UI', Arial, sans-serif !important;">💡 Select 2+ examples for pattern generation</p>
                `;
                
                multiFields.forEach(field => {{
                    const color = field.color;
                    const selectionCount = (currentSelections[field.name] || []).length;
                    const isComplete = selectionCount > 0;
                    const readyForGeneration = selectionCount >= 2;
                    let statusIcon = '⭕';
                    let statusText = '(none)';
                    
                    if (readyForGeneration) {{
                        statusIcon = '🎯';
                        statusText = `(${{selectionCount}} - ready for pattern)`;
                    }} else if (isComplete) {{
                        statusIcon = '⚠️';
                        statusText = `(${{selectionCount}} - need more examples)`;
                    }}
                    
                    menuHTML += `
                        <button class="field-option" data-field="${{field.name}}" style="
                            display: block !important;
                            width: 100% !important;
                            margin: 6px 0 !important;
                            padding: 12px 15px !important;
                            background: ${{isComplete ? color + '44' : color + '22'}} !important;
                            border: 2px solid ${{color}} !important;
                            border-radius: 8px !important;
                            color: white !important;
                            cursor: pointer !important;
                            text-align: left !important;
                            font-size: 13px !important;
                            font-family: 'Segoe UI', Arial, sans-serif !important;
                            transition: all 0.3s ease !important;
                            position: relative !important;
                            ${{readyForGeneration ? 'box-shadow: 0 0 12px ' + color + '88 !important;' : isComplete ? 'box-shadow: 0 0 6px ' + color + '44 !important;' : ''}}
                        " onmouseover="this.style.backgroundColor='${{color}}66'; this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(0,0,0,0.3)'" 
                           onmouseout="this.style.backgroundColor='${{isComplete ? color + '44' : color + '22'}}'; this.style.transform='translateY(0)'; this.style.boxShadow='${{readyForGeneration ? '0 0 12px ' + color + '88' : isComplete ? '0 0 6px ' + color + '44' : 'none'}}'">
                            <div style="display: flex !important; justify-content: space-between !important; align-items: center !important;">
                                <div style="font-weight: 600 !important; color: white !important;">${{field.label}}</div>
                                <div style="font-size: 16px !important;">${{statusIcon}}</div>
                            </div>
                            <div style="font-size: 11px !important; opacity: 0.9 !important; margin-top: 4px !important; color: white !important;">${{field.description}}</div>
                            <div style="font-size: 10px !important; opacity: 0.7 !important; margin-top: 2px !important; color: #ecf0f1 !important;">${{statusText}}</div>
                        </button>
                    `;
                }});
                menuHTML += `</div>`;
            }}
            
            // Nested fields (NEW)
            if (nestedFields.length > 0) {{
                menuHTML += `<div style="margin-bottom: 25px !important;">
                    <h4 style="margin: 0 0 12px 0 !important; color: #9b59b6 !important; font-size: 15px !important; font-weight: 600 !important; font-family: 'Segoe UI', Arial, sans-serif !important;">🏗️ Nested Object Fields</h4>
                    <p style="font-size: 11px !important; color: #95a5a6 !important; margin: 0 0 12px 0 !important; padding: 8px !important; background: rgba(155,89,182,0.1) !important; border-radius: 6px !important; border-left: 3px solid #9b59b6 !important; font-family: 'Segoe UI', Arial, sans-serif !important;">🔗 Select to enter nested context with sub-fields</p>
                `;
                
                nestedFields.forEach(field => {{
                    const color = field.color;
                    const selectionCount = (currentSelections[field.name] || []).length;
                    const hasSubContexts = Object.keys(window.contentExtractorData.nestedContexts).some(key => key.startsWith(field.name));
                    const statusIcon = hasSubContexts ? '🔗' : '📂';
                    const statusText = hasSubContexts ? '(has nested contexts)' : '(click to enter)';
                    
                    menuHTML += `
                        <button class="field-option nested-field" data-field="${{field.name}}" style="
                            display: block !important;
                            width: 100% !important;
                            margin: 6px 0 !important;
                            padding: 12px 15px !important;
                            background: ${{color}}33 !important;
                            border: 2px solid ${{color}} !important;
                            border-style: dashed !important;
                            border-radius: 8px !important;
                            color: white !important;
                            cursor: pointer !important;
                            text-align: left !important;
                            font-size: 13px !important;
                            font-family: 'Segoe UI', Arial, sans-serif !important;
                            transition: all 0.3s ease !important;
                            position: relative !important;
                            ${{hasSubContexts ? 'box-shadow: 0 0 8px ' + color + '66 !important;' : ''}}
                        " onmouseover="this.style.backgroundColor='${{color}}55'; this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(155,89,182,0.4)'" 
                           onmouseout="this.style.backgroundColor='${{color}}33'; this.style.transform='translateY(0)'; this.style.boxShadow='${{hasSubContexts ? '0 0 8px ' + color + '66' : 'none'}}'">
                            <div style="display: flex !important; justify-content: space-between !important; align-items: center !important;">
                                <div style="font-weight: 600 !important; color: white !important;">${{field.label}}</div>
                                <div style="font-size: 16px !important;">${{statusIcon}}</div>
                            </div>
                            <div style="font-size: 11px !important; opacity: 0.9 !important; margin-top: 4px !important; color: white !important;">${{field.description}}</div>
                            <div style="font-size: 10px !important; opacity: 0.7 !important; margin-top: 2px !important; color: #ecf0f1 !important;">${{statusText}}</div>
                        </button>
                    `;
                }});
                menuHTML += `</div>`;
            }}
            
            // Summary and controls
            const allFields = [...singleFields, ...multiFields, ...nestedFields];
            const completedCount = Object.keys(currentSelections).filter(k => currentSelections[k] && currentSelections[k].length > 0).length;
            const totalFields = allFields.length;
            
            menuHTML += `</div>
                <div style="margin-top: 25px !important; border-top: 2px solid #34495e !important; padding-top: 18px !important;">
                    <div style="background: rgba(52,152,219,0.1) !important; padding: 12px !important; border-radius: 8px !important; margin-bottom: 15px !important; border-left: 4px solid ${{depthColor}} !important;">
                        <div style="font-size: 13px !important; font-weight: 600 !important; color: ${{depthColor}} !important;">Context: ${{window.contentExtractorData.breadcrumbs[window.contentExtractorData.breadcrumbs.length - 1]}}</div>
                        <div style="font-size: 11px !important; color: #bdc3c7 !important; margin-top: 4px !important;">Depth ${{currentDepth}} • ${{completedCount}}/${{totalFields}} fields with selections</div>
                    </div>
                    <div style="display: flex !important; gap: 10px !important;">
                        ${{currentDepth > 0 ? 
                            `<button id="navigate-parent" style="
                                background: #95a5a6 !important;
                                color: white !important;
                                border: none !important;
                                padding: 10px 18px !important;
                                border-radius: 6px !important;
                                cursor: pointer !important;
                                font-size: 13px !important;
                                font-weight: 600 !important;
                                font-family: 'Segoe UI', Arial, sans-serif !important;
                                transition: all 0.2s !important;
                                flex: 1 !important;
                            " onmouseover="this.style.backgroundColor='#7f8c8d'" onmouseout="this.style.backgroundColor='#95a5a6'">⬆️ Parent</button>` 
                            : ''
                        }}
                        ${{currentDepth > 0 ? 
                            `<button id="add-instance-btn" style="
                                background: #f39c12 !important;
                                color: white !important;
                                border: none !important;
                                padding: 10px 18px !important;
                                border-radius: 6px !important;
                                cursor: pointer !important;
                                font-size: 13px !important;
                                font-weight: 600 !important;
                                font-family: 'Segoe UI', Arial, sans-serif !important;
                                transition: all 0.2s !important;
                                flex: 1 !important;
                            " onmouseover="this.style.backgroundColor='#e67e22'" onmouseout="this.style.backgroundColor='#f39c12'">➕ Add Instance</button>` 
                            : ''
                        }}
                        <button id="close-field-menu" style="
                            background: #e74c3c !important;
                            color: white !important;
                            border: none !important;
                            padding: 10px 18px !important;
                            border-radius: 6px !important;
                            cursor: pointer !important;
                            font-size: 13px !important;
                            font-weight: 600 !important;
                            font-family: 'Segoe UI', Arial, sans-serif !important;
                            transition: all 0.2s !important;
                            flex: 1 !important;
                        " onmouseover="this.style.backgroundColor='#c0392b'" onmouseout="this.style.backgroundColor='#e74c3c'">Close Menu</button>
                    </div>
                </div>
            `;
            
            menu.innerHTML = menuHTML;
            return menu;
        }}
        
        // Show enhanced field selection menu
        window.showFieldMenu = function() {{
            // Remove existing menu if present
            const existingMenu = document.getElementById('field-selection-menu');
            if (existingMenu) {{
                existingMenu.remove();
            }}
            
            const menu = createFieldSelectionMenu();
            document.body.appendChild(menu);
            
            // DRAGGABLE ENHANCEMENT: Make the field menu draggable
            makeDraggable(menu);
            
            // Add event listeners to prevent interference
            menu.addEventListener('mouseenter', function(e) {{ e.stopPropagation(); }});
            menu.addEventListener('mouseleave', function(e) {{ e.stopPropagation(); }});
            menu.addEventListener('click', function(e) {{ e.stopPropagation(); }});
            
            // Add event listeners for field selection
            menu.querySelectorAll('.field-option').forEach(button => {{
                button.addEventListener('click', function() {{
                    const fieldName = this.getAttribute('data-field');
                    const isNested = this.classList.contains('nested-field');
                    
                    if (isNested) {{
                        enterNestedField(fieldName);
                    }} else {{
                        selectField(fieldName);
                    }}
                }});
            }});
            
            // Parent navigation button
            const parentBtn = document.getElementById('navigate-parent');
            if (parentBtn) {{
                parentBtn.addEventListener('click', function() {{
                    navigateToParent();
                }});
            }}
            
            // Add instance button
            const addInstanceBtn = document.getElementById('add-instance-btn');
            if (addInstanceBtn) {{
                addInstanceBtn.addEventListener('click', function() {{
                    addNestedInstance();
                }});
            }}
            
            // Close menu button
            document.getElementById('close-field-menu').addEventListener('click', function() {{
                menu.remove();
            }});
        }};
        
        // Enter nested field context
        function enterNestedField(fieldName) {{
            // NEW: Show instance management menu instead of directly entering nested field
            showInstanceManagementMenu(fieldName);
        }}
        
        // NEW: Show instance management menu (Level 2)
        function showInstanceManagementMenu(fieldName) {{
            // Remove existing menu
            const existingMenu = document.getElementById('field-selection-menu');
            if (existingMenu) {{
                existingMenu.remove();
            }}
            
            // Create instance management menu
            const menu = document.createElement('div');
            menu.id = 'field-selection-menu';
            menu.setAttribute('data-content-extractor-ui', 'true');
            menu.style.cssText = `
                position: fixed !important;
                top: 50% !important;
                left: 50% !important;
                transform: translate(-50%, -50%) !important;
                background: linear-gradient(135deg, #2c3e50, #34495e) !important;
                color: white !important;
                padding: 25px !important;
                border-radius: 15px !important;
                z-index: 10001 !important;
                font-family: 'Segoe UI', Arial, sans-serif !important;
                font-size: 14px !important;
                box-shadow: 0 15px 35px rgba(0,0,0,0.4) !important;
                border: 3px solid #3498db !important;
                min-width: 400px !important;
                max-width: 500px !important;
                backdrop-filter: blur(10px) !important;
                user-select: none !important;
            `;
            
            // Get existing instances for this field from nested manager
            const instanceData = window.contentExtractorData.instanceData || {{}};
            const fieldInstances = instanceData[fieldName] || [];
            let instanceButtons = '';
            
            // Create buttons for existing instances
            if (fieldInstances.length === 0) {{
                // Default first instance
                instanceButtons = `
                    <button class="instance-btn" data-field="${{fieldName}}" data-index="0" style="
                        background: linear-gradient(135deg, #27ae60, #2ecc71) !important;
                        color: white !important;
                        border: none !important;
                        padding: 12px 20px !important;
                        margin: 6px !important;
                        border-radius: 8px !important;
                        cursor: pointer !important;
                        font-size: 14px !important;
                        font-weight: 600 !important;
                        transition: all 0.2s !important;
                        min-width: 120px !important;
                    " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                        📦 ${{fieldName}}[0]
                    </button>
                `;
            }} else {{
                // Create buttons for each existing instance
                for (let i = 0; i < fieldInstances.length; i++) {{
                    instanceButtons += `
                        <button class="instance-btn" data-field="${{fieldName}}" data-index="${{i}}" style="
                            background: linear-gradient(135deg, #27ae60, #2ecc71) !important;
                            color: white !important;
                            border: none !important;
                            padding: 12px 20px !important;
                            margin: 6px !important;
                            border-radius: 8px !important;
                            cursor: pointer !important;
                            font-size: 14px !important;
                            font-weight: 600 !important;
                            transition: all 0.2s !important;
                            min-width: 120px !important;
                        " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                            📦 ${{fieldName}}[${{i}}]
                        </button>
                    `;
                }}
            }}
            
            menu.innerHTML = `
                <div style="margin-bottom: 20px !important;">
                    <h3 style="margin: 0 0 8px 0 !important; color: #3498db !important; font-size: 18px !important; font-weight: 700 !important;">
                        🏗️ Instance Management
                    </h3>
                    <div style="font-size: 14px !important; color: #bdc3c7 !important; margin-bottom: 8px !important;">
                        Field: <strong>${{fieldName}}</strong>
                    </div>
                    <div style="font-size: 12px !important; color: #95a5a6 !important;">
                        Breadcrumb: Root → ${{fieldName}}
                    </div>
                </div>
                
                <div style="margin-bottom: 20px !important;">
                    <div style="margin-bottom: 12px !important; font-size: 13px !important; color: #ecf0f1 !important; font-weight: 600 !important;">
                        📋 Available Instances:
                    </div>
                    <div style="display: flex !important; flex-wrap: wrap !important; gap: 8px !important; justify-content: center !important;">
                        ${{instanceButtons}}
                        <button id="add-new-instance-btn" data-field="${{fieldName}}" style="
                            background: linear-gradient(135deg, #f39c12, #e67e22) !important;
                            color: white !important;
                            border: none !important;
                            padding: 12px 20px !important;
                            margin: 6px !important;
                            border-radius: 8px !important;
                            cursor: pointer !important;
                            font-size: 14px !important;
                            font-weight: 600 !important;
                            transition: all 0.2s !important;
                            min-width: 120px !important;
                        " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                            ➕ Add New
                        </button>
                    </div>
                </div>
                
                <div style="display: flex !important; gap: 12px !important; justify-content: center !important;">
                    <button id="navigate-parent-instance" style="
                        background: #95a5a6 !important;
                        color: white !important;
                        border: none !important;
                        padding: 12px 20px !important;
                        border-radius: 8px !important;
                        cursor: pointer !important;
                        font-size: 13px !important;
                        font-weight: 600 !important;
                        transition: all 0.2s !important;
                    " onmouseover="this.style.backgroundColor='#7f8c8d'" onmouseout="this.style.backgroundColor='#95a5a6'">
                        ⬆️ Parent
                    </button>
                    <button id="close-instance-menu" style="
                        background: #e74c3c !important;
                        color: white !important;
                        border: none !important;
                        padding: 12px 20px !important;
                        border-radius: 8px !important;
                        cursor: pointer !important;
                        font-size: 13px !important;
                        font-weight: 600 !important;
                        transition: all 0.2s !important;
                    " onmouseover="this.style.backgroundColor='#c0392b'" onmouseout="this.style.backgroundColor='#e74c3c'">
                        Close Menu
                    </button>
                </div>
            `;
            
            document.body.appendChild(menu);
            
            // Make draggable
            makeDraggable(menu);
            
            // Add event listeners for instance buttons
            menu.querySelectorAll('.instance-btn').forEach(button => {{
                button.addEventListener('click', function() {{
                    const fieldName = this.getAttribute('data-field');
                    const instanceIndex = parseInt(this.getAttribute('data-index'));
                    
                    // Enter specific instance (Level 3)
                    enterSpecificInstance(fieldName, instanceIndex);
                }});
            }});
            
            // Add new instance button
            const addNewBtn = menu.querySelector('#add-new-instance-btn');
            if (addNewBtn) {{
                addNewBtn.addEventListener('click', function() {{
                    const fieldName = this.getAttribute('data-field');
                    createNewInstance(fieldName);
                }});
            }};
            
            // Parent navigation
            const parentBtn = menu.querySelector('#navigate-parent-instance');
            if (parentBtn) {{
                parentBtn.addEventListener('click', function() {{
                    navigateToParent();
                }});
            }};
            
            // Close menu
            const closeBtn = menu.querySelector('#close-instance-menu');
            if (closeBtn) {{
                closeBtn.addEventListener('click', function() {{
                    menu.remove();
                }});
            }};
        }}
        
        // Enter specific instance (Level 3)
        function enterSpecificInstance(fieldName, instanceIndex) {{
            // Trigger Python callback to enter specific nested instance
            const event = new CustomEvent('enterNestedField', {{ 
                detail: {{ fieldName: fieldName, instanceIndex: instanceIndex }}
            }});
            document.dispatchEvent(event);
        }}
        
        // Create new instance
        function createNewInstance(fieldName) {{
            // Get current instance count
            const instanceData = window.contentExtractorData.instanceData || {{}};
            const fieldInstances = instanceData[fieldName] || [];
            const nextIndex = fieldInstances.length;
            
            // Trigger Python callback to create new instance
            const event = new CustomEvent('createNewInstance', {{ 
                detail: {{ fieldName: fieldName, newIndex: nextIndex }}
            }});
            document.dispatchEvent(event);
        }}
        
        // Navigate to parent context
        function navigateToParent() {{
            // Trigger Python callback to navigate to parent
            const event = new CustomEvent('navigateToParent', {{}});
            document.dispatchEvent(event);
        }}
        
        // Select a field and start content selection (enhanced for nested contexts)
        function selectField(fieldName) {{
            window.contentExtractorData.activeField = fieldName;
            
            // Remove field menu
            const menu = document.getElementById('field-selection-menu');
            if (menu) {{
                menu.remove();
            }}
            
            // Initialize field selections if not exists
            if (!window.contentExtractorData.fieldSelections[fieldName]) {{
                window.contentExtractorData.fieldSelections[fieldName] = [];
            }}
            
            // Create floating menu toggle
            createFloatingMenuToggle();
            
            // Start selection mode for this field
            window.startFieldSelection(fieldName);
        }}
        
        // Create floating menu toggle
        function createFloatingMenuToggle() {{
            // Remove existing toggle if present
            const existingToggle = document.getElementById('field-menu-toggle');
            if (existingToggle) {{
                existingToggle.remove();
            }}
            
            // Get current field completion status for progress indicator
            const currentSelections = window.contentExtractorData.fieldSelections || {{}};
            const completedCount = Object.keys(currentSelections).filter(k => currentSelections[k] && currentSelections[k].length > 0).length;
            const totalFields = window.contentExtractorData.fieldOptions.length;
            const progressPercentage = Math.round((completedCount / totalFields) * 100);
            
            const controlPanel = document.createElement('div');
            controlPanel.id = 'field-menu-toggle';
            controlPanel.setAttribute('data-content-extractor-ui', 'true');
            controlPanel.style.cssText = `
                position: fixed !important;
                bottom: 20px !important;
                left: 20px !important;
                background: linear-gradient(135deg, #2c3e50, #34495e) !important;
                color: white !important;
                padding: 16px !important;
                border-radius: 12px !important;
                z-index: 10002 !important;
                font-family: 'Segoe UI', Arial, sans-serif !important;
                font-size: 13px !important;
                box-shadow: 0 8px 24px rgba(0,0,0,0.3) !important;
                border: 2px solid #3498db !important;
                transition: all 0.3s ease !important;
                user-select: none !important;
                min-width: 280px !important;
                backdrop-filter: blur(10px) !important;
            `;
            
            controlPanel.innerHTML = `
                <div style="margin-bottom: 12px !important; padding-bottom: 10px !important; border-bottom: 1px solid rgba(255,255,255,0.2) !important;">
                    <div style="display: flex !important; align-items: center !important; gap: 8px !important; margin-bottom: 8px !important;">
                        <span style="font-size: 16px !important;">🎯</span>
                        <div>
                            <div style="font-size: 11px !important; opacity: 0.8 !important; color: white !important;">Current Field:</div>
                            <div style="font-size: 14px !important; font-weight: 700 !important; color: #3498db !important;">${{window.contentExtractorData.activeField || 'None'}}</div>
                        </div>
                    </div>
                    <div style="margin-top: 8px !important;">
                        <div style="display: flex !important; justify-content: space-between !important; align-items: center !important; margin-bottom: 4px !important;">
                            <span style="font-size: 11px !important; color: white !important;">Overall Progress:</span>
                            <span style="font-size: 11px !important; font-weight: 600 !important; color: #3498db !important;">${{completedCount}}/${{totalFields}} (${{progressPercentage}}%)</span>
                        </div>
                        <div style="background: rgba(255,255,255,0.2) !important; height: 6px !important; border-radius: 3px !important; overflow: hidden !important;">
                            <div style="background: linear-gradient(90deg, #27ae60, #2ecc71) !important; height: 100% !important; width: ${{progressPercentage}}% !important; transition: width 0.3s ease !important; border-radius: 3px !important;"></div>
                        </div>
                    </div>
                </div>
                
                <div style="display: grid !important; grid-template-columns: 1fr 1fr !important; gap: 8px !important; margin-bottom: 12px !important;">
                    <button id="control-save-btn" style="
                        background: linear-gradient(135deg, #27ae60, #2ecc71) !important;
                        color: white !important;
                        border: none !important;
                        padding: 10px 12px !important;
                        border-radius: 6px !important;
                        cursor: pointer !important;
                        font-size: 12px !important;
                        font-weight: 600 !important;
                        transition: all 0.2s !important;
                        display: flex !important;
                        align-items: center !important;
                        justify-content: center !important;
                        gap: 4px !important;
                    " onmouseover="this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 8px rgba(39,174,96,0.4)'" 
                       onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'">
                        <span>💾</span>
                        <span>Save</span>
                    </button>
                    
                    <button id="control-test-btn" style="
                        background: linear-gradient(135deg, #f39c12, #e67e22) !important;
                        color: white !important;
                        border: none !important;
                        padding: 10px 12px !important;
                        border-radius: 6px !important;
                        cursor: pointer !important;
                        font-size: 12px !important;
                        font-weight: 600 !important;
                        transition: all 0.2s !important;
                        display: flex !important;
                        align-items: center !important;
                        justify-content: center !important;
                        gap: 4px !important;
                    " onmouseover="this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 8px rgba(243,156,18,0.4)'" 
                       onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'">
                        <span>🧪</span>
                        <span>Test</span>
                    </button>
                </div>
                
                <div style="display: grid !important; grid-template-columns: 1fr 1fr !important; gap: 8px !important; margin-bottom: 12px !important;">
                    <button id="control-navigate-btn" style="
                        background: linear-gradient(135deg, #8e44ad, #9b59b6) !important;
                        color: white !important;
                        border: none !important;
                        padding: 10px 12px !important;
                        border-radius: 6px !important;
                        cursor: pointer !important;
                        font-size: 12px !important;
                        font-weight: 600 !important;
                        transition: all 0.2s !important;
                        display: flex !important;
                        align-items: center !important;
                        justify-content: center !important;
                        gap: 4px !important;
                    " onmouseover="this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 8px rgba(142,68,173,0.4)'" 
                       onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'">
                        <span>🧭</span>
                        <span>Navigate</span>
                    </button>
                    
                    <button id="control-fields-btn" style="
                        background: linear-gradient(135deg, #3498db, #2980b9) !important;
                        color: white !important;
                        border: none !important;
                        padding: 10px 12px !important;
                        border-radius: 6px !important;
                        cursor: pointer !important;
                        font-size: 12px !important;
                        font-weight: 600 !important;
                        transition: all 0.2s !important;
                        display: flex !important;
                        align-items: center !important;
                        justify-content: center !important;
                        gap: 4px !important;
                    " onmouseover="this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 8px rgba(52,152,219,0.4)'" 
                       onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'">
                        <span>📋</span>
                        <span>Fields</span>
                    </button>
                </div>
                
                <div style="border-top: 1px solid rgba(255,255,255,0.2) !important; padding-top: 10px !important; font-size: 10px !important; color: rgba(255,255,255,0.7) !important; text-align: center !important;">
                    <div>💡 <strong>Quick Tips:</strong></div>
                    <div style="margin-top: 4px !important;">Save selections • Test on pages • Navigate URLs</div>
                </div>
            `;
            
            // Add control panel event handlers
            
            // Save button - persist field selections to database
            controlPanel.querySelector('#control-save-btn').addEventListener('click', function(e) {{
                e.stopPropagation();
                handleControlPanelSave();
            }});
            
            // Test button - validate selectors on multiple pages
            controlPanel.querySelector('#control-test-btn').addEventListener('click', function(e) {{
                e.stopPropagation();
                handleControlPanelTest();
            }});
            
            // Navigate button - easy page traversal
            controlPanel.querySelector('#control-navigate-btn').addEventListener('click', function(e) {{
                e.stopPropagation();
                handleControlPanelNavigate();
            }});
            
            // Fields button - show field menu (original functionality)
            controlPanel.querySelector('#control-fields-btn').addEventListener('click', function(e) {{
                e.stopPropagation();
                window.showFieldMenu();
            }});
            
            // Prevent mouse events from interfering with page interaction
            controlPanel.addEventListener('mouseenter', function(e) {{ e.stopPropagation(); }});
            controlPanel.addEventListener('mouseleave', function(e) {{ e.stopPropagation(); }});
            controlPanel.addEventListener('click', function(e) {{ e.stopPropagation(); }});
            
            document.body.appendChild(controlPanel);
            
            // DRAGGABLE ENHANCEMENT: Make the control panel draggable
            makeDraggable(controlPanel);
        }}
        
        // Handle Save button functionality
        function handleControlPanelSave() {{
            const currentSelections = window.contentExtractorData.fieldSelections || {{}};
            const activeField = window.contentExtractorData.activeField;
            
            if (!activeField) {{
                showCustomAlert('❌ No active field selected. Please select a field first.');
                return;
            }}
            
            const fieldSelections = currentSelections[activeField] || [];
            if (fieldSelections.length === 0) {{
                showCustomAlert(`❌ No selections made for field "${{activeField}}". Please select at least one element.`);
                return;
            }}
            
            // Show save confirmation with details
            const selectionCount = fieldSelections.length;
            const fieldInfo = window.contentExtractorData.fieldOptions.find(f => f.name === activeField);
            const isMultiValue = fieldInfo && fieldInfo.type === 'multi-value';
            
            let saveMessage = `💾 Save ${{selectionCount}} selection(s) for "${{activeField}}"?\\n\\n`;
            saveMessage += `Field Type: ${{isMultiValue ? 'Multi-value' : 'Single value'}}\\n`;
            saveMessage += `Domain: ${{window.location.hostname}}\\n`;
            saveMessage += `Current Page: ${{window.location.pathname}}\\n\\n`;
            saveMessage += 'This will save the selector patterns to the database for future use.';
            
            showCustomConfirm(saveMessage, function(confirmed) {{
                if (confirmed) {{
                    // Trigger Python save functionality
                    console.log('🚀 Triggering save for field:', activeField, fieldSelections);
                    window.saveFieldSelections = {{
                        field: activeField,
                        selections: fieldSelections,
                        domain: window.location.hostname,
                        url: window.location.href,
                        timestamp: new Date().toISOString()
                    }};
                    
                    // Visual feedback
                    showTemporaryNotification('💾 Selections saved successfully!', 'success');
                }}
            }});
        }}
        
        // Handle Test button functionality  
        function handleControlPanelTest() {{
            const currentSelections = window.contentExtractorData.fieldSelections || {{}};
            const completedFields = Object.keys(currentSelections).filter(k => currentSelections[k] && currentSelections[k].length > 0);
            
            if (completedFields.length === 0) {{
                showCustomAlert('❌ No field selections to test. Please select elements for at least one field first.');
                return;
            }}
            
            let testMessage = `🧪 Test ${{completedFields.length}} field(s) on multiple pages?\\n\\n`;
            testMessage += `Fields to test: ${{completedFields.join(', ')}}\\n`;
            testMessage += `Current domain: ${{window.location.hostname}}\\n\\n`;
            testMessage += 'This will validate selectors across different pages to ensure reliability.';
            
            showCustomConfirm(testMessage, function(confirmed) {{
                if (confirmed) {{
                    // Trigger Python test functionality
                    console.log('🚀 Triggering cross-page testing for fields:', completedFields);
                    window.testFieldSelections = {{
                        fields: completedFields,
                        domain: window.location.hostname,
                        baseUrl: window.location.href,
                        timestamp: new Date().toISOString()
                    }};
                    
                    // Visual feedback
                    showTemporaryNotification('🧪 Cross-page testing initiated!', 'info');
                }}
            }});
        }}
        
        // Handle Navigate button functionality
        function handleControlPanelNavigate() {{
            const navigationOptions = [
                {{id: '1', label: '🔗 New URL', desc: 'Navigate to a different page for testing'}},
                {{id: '2', label: '🔍 Similar Pages', desc: 'Find similar product pages on this domain'}},
                {{id: '3', label: '📋 Test URLs', desc: 'Navigate to saved test URLs'}},
                {{id: '4', label: '⬅️ Back to Previous', desc: 'Return to previous page'}}
            ];
            
            showCustomSelect(
                '🧭 Navigation Options',
                'Choose how you want to navigate:',
                navigationOptions,
                function(choice) {{
                    handleNavigationChoice(choice);
                }}
            );
        }}
        
        function handleNavigationChoice(choice) {{
            switch(choice) {{
                case '1':
                    // Auto-fill current URL as default
                    const currentUrl = window.location.href;
                    showCustomInput(
                        '🔗 Navigate to URL',
                        'Enter URL to navigate to:',
                        currentUrl,
                        function(newUrl) {{
                            if (newUrl && newUrl.trim()) {{
                                const cleanUrl = newUrl.trim();
                                if (cleanUrl.startsWith('http://') || cleanUrl.startsWith('https://')) {{
                                    window.navigateToUrl = cleanUrl;
                                    showTemporaryNotification(`🧭 Navigating to: ${{cleanUrl}}`, 'info');
                                }} else {{
                                    showCustomAlert('❌ Please enter a complete URL starting with http:// or https://');
                                }}
                            }}
                        }}
                    );
                    break;
                case '2':
                    // Find similar pages functionality
                    console.log('🔍 Finding similar pages on domain:', window.location.hostname);
                    window.findSimilarPages = {{
                        domain: window.location.hostname,
                        currentPath: window.location.pathname,
                        timestamp: new Date().toISOString()
                    }};
                    showTemporaryNotification('🔍 Searching for similar pages...', 'info');
                    break;
                case '3':
                    // Navigate to test URLs
                    console.log('📋 Loading saved test URLs');
                    window.loadTestUrls = {{
                        domain: window.location.hostname,
                        timestamp: new Date().toISOString()
                    }};
                    showTemporaryNotification('📋 Loading test URLs...', 'info');
                    break;
                case '4':
                    // Back to previous page
                    showCustomConfirm('⬅️ Go back to the previous page?', function(confirmed) {{
                        if (confirmed) {{
                            window.history.back();
                        }}
                    }});
                    break;
            }}
        }}
        
        // Custom Alert Modal (replaces alert())
        function showCustomAlert(message) {{
            createModal('Alert', message, [
                {{text: 'OK', primary: true, callback: null}}
            ]);
        }}
        
        // Custom Confirm Modal (replaces confirm())
        function showCustomConfirm(message, callback) {{
            createModal('Confirm', message, [
                {{text: 'Cancel', primary: false, callback: () => callback(false)}},
                {{text: 'OK', primary: true, callback: () => callback(true)}}
            ]);
        }}
        
        // Custom Input Modal (replaces prompt())
        function showCustomInput(title, message, defaultValue = '', callback) {{
            const modalOverlay = document.createElement('div');
            modalOverlay.setAttribute('data-content-extractor-ui', 'true');
            modalOverlay.id = 'custom-input-modal';
            modalOverlay.style.cssText = `
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                width: 100% !important;
                height: 100% !important;
                background: rgba(0, 0, 0, 0.6) !important;
                z-index: 10010 !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                backdrop-filter: blur(3px) !important;
            `;
            
            const modal = document.createElement('div');
            modal.style.cssText = `
                background: white !important;
                border-radius: 12px !important;
                padding: 24px !important;
                max-width: 500px !important;
                width: 90% !important;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3) !important;
                font-family: 'Segoe UI', Arial, sans-serif !important;
                animation: modalSlideIn 0.3s ease-out !important;
            `;
            
            modal.innerHTML = `
                <div style="margin-bottom: 16px !important;">
                    <h3 style="margin: 0 0 8px 0 !important; color: #2c3e50 !important; font-size: 18px !important;">${{title}}</h3>
                    <p style="margin: 0 !important; color: #555 !important; font-size: 14px !important; line-height: 1.4 !important;">${{message}}</p>
                </div>
                <div style="margin-bottom: 20px !important;">
                    <input type="text" id="custom-input-field" value="${{defaultValue}}" style="
                        width: 100% !important;
                        padding: 12px !important;
                        border: 2px solid #ddd !important;
                        border-radius: 6px !important;
                        font-size: 14px !important;
                        font-family: inherit !important;
                        box-sizing: border-box !important;
                    " placeholder="Enter value...">
                </div>
                <div style="display: flex !important; gap: 12px !important; justify-content: flex-end !important;">
                    <button id="custom-input-cancel" style="
                        padding: 10px 20px !important;
                        border: 2px solid #ddd !important;
                        background: white !important;
                        color: #666 !important;
                        border-radius: 6px !important;
                        cursor: pointer !important;
                        font-size: 14px !important;
                        font-weight: 600 !important;
                    ">Cancel</button>
                    <button id="custom-input-ok" style="
                        padding: 10px 20px !important;
                        border: none !important;
                        background: linear-gradient(135deg, #3498db, #2980b9) !important;
                        color: white !important;
                        border-radius: 6px !important;
                        cursor: pointer !important;
                        font-size: 14px !important;
                        font-weight: 600 !important;
                    ">OK</button>
                </div>
            `;
            
            modalOverlay.appendChild(modal);
            document.body.appendChild(modalOverlay);
            
            // Focus and select the input
            const inputField = modal.querySelector('#custom-input-field');
            setTimeout(() => {{
                inputField.focus();
                inputField.select();
            }}, 100);
            
            // Event handlers
            function closeModal() {{
                if (modalOverlay.parentNode) {{
                    modalOverlay.remove();
                }}
            }}
            
            modal.querySelector('#custom-input-cancel').addEventListener('click', function(e) {{
                e.stopPropagation();
                closeModal();
                callback(null);
            }});
            
            modal.querySelector('#custom-input-ok').addEventListener('click', function(e) {{
                e.stopPropagation();
                const value = inputField.value;
                closeModal();
                callback(value);
            }});
            
            // Enter key submits
            inputField.addEventListener('keypress', function(e) {{
                if (e.key === 'Enter') {{
                    const value = inputField.value;
                    closeModal();
                    callback(value);
                }}
            }});
            
            // Escape key cancels
            modalOverlay.addEventListener('keydown', function(e) {{
                if (e.key === 'Escape') {{
                    closeModal();
                    callback(null);
                }}
            }});
            
            // Prevent clicks on modal from closing
            modal.addEventListener('click', function(e) {{
                e.stopPropagation();
            }});
            
            // Click overlay to close
            modalOverlay.addEventListener('click', function(e) {{
                closeModal();
                callback(null);
            }});
        }}
        
        // Custom Select Modal (for navigation options)
        function showCustomSelect(title, message, options, callback) {{
            const modalOverlay = document.createElement('div');
            modalOverlay.setAttribute('data-content-extractor-ui', 'true');
            modalOverlay.id = 'custom-select-modal';
            modalOverlay.style.cssText = `
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                width: 100% !important;
                height: 100% !important;
                background: rgba(0, 0, 0, 0.6) !important;
                z-index: 10010 !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                backdrop-filter: blur(3px) !important;
            `;
            
            const modal = document.createElement('div');
            modal.style.cssText = `
                background: white !important;
                border-radius: 12px !important;
                padding: 24px !important;
                max-width: 500px !important;
                width: 90% !important;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3) !important;
                font-family: 'Segoe UI', Arial, sans-serif !important;
                animation: modalSlideIn 0.3s ease-out !important;
            `;
            
            let optionsHtml = options.map(opt => `
                <div class="select-option" data-value="${{opt.id}}" style="
                    padding: 12px 16px !important;
                    border: 2px solid #e0e0e0 !important;
                    border-radius: 8px !important;
                    margin-bottom: 8px !important;
                    cursor: pointer !important;
                    transition: all 0.2s !important;
                    background: white !important;
                " onmouseover="this.style.background='#f8f9fa'; this.style.borderColor='#3498db';" 
                   onmouseout="this.style.background='white'; this.style.borderColor='#e0e0e0';">
                    <div style="font-size: 14px !important; font-weight: 600 !important; color: #2c3e50 !important; margin-bottom: 4px !important;">${{opt.label}}</div>
                    <div style="font-size: 12px !important; color: #666 !important;">${{opt.desc}}</div>
                </div>
            `).join('');
            
            modal.innerHTML = `
                <div style="margin-bottom: 20px !important;">
                    <h3 style="margin: 0 0 8px 0 !important; color: #2c3e50 !important; font-size: 18px !important;">${{title}}</h3>
                    <p style="margin: 0 !important; color: #555 !important; font-size: 14px !important; line-height: 1.4 !important;">${{message}}</p>
                </div>
                <div id="select-options" style="margin-bottom: 20px !important;">
                    ${{optionsHtml}}
                </div>
                <div style="display: flex !important; justify-content: flex-end !important;">
                    <button id="select-cancel" style="
                        padding: 10px 20px !important;
                        border: 2px solid #ddd !important;
                        background: white !important;
                        color: #666 !important;
                        border-radius: 6px !important;
                        cursor: pointer !important;
                        font-size: 14px !important;
                        font-weight: 600 !important;
                    ">Cancel</button>
                </div>
            `;
            
            modalOverlay.appendChild(modal);
            document.body.appendChild(modalOverlay);
            
            // Event handlers
            function closeModal() {{
                if (modalOverlay.parentNode) {{
                    modalOverlay.remove();
                }}
            }}
            
            // Handle option clicks
            modal.querySelectorAll('.select-option').forEach(option => {{
                option.addEventListener('click', function(e) {{
                    e.stopPropagation();
                    const value = this.getAttribute('data-value');
                    closeModal();
                    callback(value);
                }});
            }});
            
            modal.querySelector('#select-cancel').addEventListener('click', function(e) {{
                e.stopPropagation();
                closeModal();
            }});
            
            // Escape key cancels
            modalOverlay.addEventListener('keydown', function(e) {{
                if (e.key === 'Escape') {{
                    closeModal();
                }}
            }});
            
            // Prevent clicks on modal from closing
            modal.addEventListener('click', function(e) {{
                e.stopPropagation();
            }});
            
            // Click overlay to close
            modalOverlay.addEventListener('click', function(e) {{
                closeModal();
            }});
        }}
        
        // Generic Modal Creator for Alert/Confirm
        function createModal(title, message, buttons) {{
            const modalOverlay = document.createElement('div');
            modalOverlay.setAttribute('data-content-extractor-ui', 'true');
            modalOverlay.id = 'custom-modal';
            modalOverlay.style.cssText = `
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                width: 100% !important;
                height: 100% !important;
                background: rgba(0, 0, 0, 0.6) !important;
                z-index: 10010 !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                backdrop-filter: blur(3px) !important;
            `;
            
            const modal = document.createElement('div');
            modal.style.cssText = `
                background: white !important;
                border-radius: 12px !important;
                padding: 24px !important;
                max-width: 500px !important;  
                width: 90% !important;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3) !important;
                font-family: 'Segoe UI', Arial, sans-serif !important;
                animation: modalSlideIn 0.3s ease-out !important;
            `;
            
            const buttonsHtml = buttons.map((btn, idx) => `
                <button class="modal-btn" data-index="${{idx}}" style="
                    padding: 10px 20px !important;
                    border: ${{btn.primary ? 'none' : '2px solid #ddd'}} !important;
                    background: ${{btn.primary ? 'linear-gradient(135deg, #3498db, #2980b9)' : 'white'}} !important;
                    color: ${{btn.primary ? 'white' : '#666'}} !important;
                    border-radius: 6px !important;
                    cursor: pointer !important;
                    font-size: 14px !important;
                    font-weight: 600 !important;
                    margin-left: 12px !important;
                ">${{btn.text}}</button>
            `).join('');
            
            modal.innerHTML = `
                <div style="margin-bottom: 20px !important;">
                    <h3 style="margin: 0 0 12px 0 !important; color: #2c3e50 !important; font-size: 18px !important;">${{title}}</h3>
                    <p style="margin: 0 !important; color: #555 !important; font-size: 14px !important; line-height: 1.5 !important; white-space: pre-line !important;">${{message}}</p>
                </div>
                <div style="display: flex !important; justify-content: flex-end !important;">
                    ${{buttonsHtml}}
                </div>
            `;
            
            modalOverlay.appendChild(modal);
            document.body.appendChild(modalOverlay);
            
            // Event handlers
            function closeModal() {{
                if (modalOverlay.parentNode) {{
                    modalOverlay.remove();
                }}
            }}
            
            modal.querySelectorAll('.modal-btn').forEach((btn, idx) => {{
                btn.addEventListener('click', function(e) {{
                    e.stopPropagation();
                    closeModal();
                    if (buttons[idx].callback) {{
                        buttons[idx].callback();
                    }}
                }});
            }});
            
            // Escape key closes modal (acts like cancel/first button)
            modalOverlay.addEventListener('keydown', function(e) {{
                if (e.key === 'Escape') {{
                    closeModal();
                    if (buttons[0].callback) {{
                        buttons[0].callback();
                    }}
                }}
            }});
            
            // Prevent clicks on modal from closing
            modal.addEventListener('click', function(e) {{
                e.stopPropagation();
            }});
            
            // Click overlay to close (acts like cancel/first button)
            modalOverlay.addEventListener('click', function(e) {{
                closeModal();
                if (buttons[0].callback) {{
                    buttons[0].callback();
                }}
            }});
        }}
        
        // Check if element is part of content extractor UI
        function isContentExtractorElement(element) {{
            // Check if element or any parent is a content extractor UI element
            let current = element;
            while (current && current !== document.body) {{
                // Check for content extractor IDs
                if (current.id && (
                    current.id === 'field-selection-menu' ||
                    current.id === 'selection-instructions' ||
                    current.id === 'field-menu-toggle'
                )) {{
                    return true;
                }}
                
                // Check for content extractor attributes
                if (current.getAttribute && (
                    current.getAttribute('data-selection-badge') ||
                    current.getAttribute('data-content-extractor-ui')
                )) {{
                    return true;
                }}
                
                // Check for content extractor classes (if any added in future)
                if (current.className && current.className.includes && 
                    current.className.includes('content-extractor')) {{
                    return true;
                }}
                
                current = current.parentElement;
            }}
            return false;
        }}
        
        function handleMultiValueSelection(fieldName, selection) {{
            const fieldSelections = window.contentExtractorData.fieldSelections[fieldName];
            const selectionCount = fieldSelections.length;
            
            // If this is the second selection for a multi-value field, offer generalization
            if (selectionCount === 2) {{
                setTimeout(() => {{
                    if (confirm(`You've selected 2 examples for ${{fieldName}}. Would you like to generate a generalized selector that covers both examples?`)) {{
                        console.log('User wants generalization for:', fieldName);
                        // This will be implemented in next phase - multi-value generalization
                        alert('Generalization feature will be implemented in next phase. For now, you can continue selecting more examples.');
                    }}
                }}, 500);
            }}
        }}
        
        function updateSelectionCounter() {{
            let overlay = document.getElementById('selection-instructions');
            if (overlay) {{
                const fieldName = window.contentExtractorData.activeField;
                const fieldCount = window.contentExtractorData.fieldSelections[fieldName]?.length || 0;
                const totalCount = window.contentExtractorData.selectedElements.length;
                let countDiv = overlay.querySelector('#selection-count');
                if (countDiv) {{
                    countDiv.innerHTML = `
                        <div style="font-weight: 600; font-size: 15px;"><strong>${{fieldName}}</strong>: ${{fieldCount}} selected</div>
                        <div style="font-size: 11px; opacity: 0.8; margin-top: 2px;">Total across all fields: ${{totalCount}}</div>
                    `;
                }}
            }}
        }}
        
        function showFieldInstructions(fieldInfo) {{
            let overlay = document.createElement('div');
            overlay.id = 'selection-instructions';
            overlay.setAttribute('data-content-extractor-ui', 'true');
            const color = getFieldColor(fieldInfo.name);
            overlay.style.cssText = `
                position: fixed !important;
                top: 20px !important;
                right: 20px !important;
                background: linear-gradient(135deg, ${{color}}, ${{color}}dd) !important;
                color: white !important;
                padding: 20px !important;
                border-radius: 12px !important;
                z-index: 10001 !important;
                font-family: 'Segoe UI', Arial, sans-serif !important;
                font-size: 14px !important;
                max-width: 320px !important;
                box-shadow: 0 8px 24px rgba(0,0,0,0.4) !important;
                border: 2px solid white !important;
                backdrop-filter: blur(10px) !important;
            `;
            
            const isMultiValue = fieldInfo.type === 'multi-value';
            const multiValueInstructions = isMultiValue ? 
                '<div style="background: rgba(255,255,255,0.15) !important; padding: 10px !important; border-radius: 8px !important; margin: 10px 0 !important; border-left: 4px solid rgba(255,255,255,0.5) !important;"><strong>💡 Multi-Value Field:</strong><br>Select 2+ examples for best pattern results</div>' : '';
            
            overlay.innerHTML = `
                <div style="border-bottom: 2px solid rgba(255,255,255,0.3) !important; padding-bottom: 12px !important; margin-bottom: 12px !important;">
                    <div style="display: flex !important; align-items: center !important; justify-content: space-between !important;">
                        <strong style="font-size: 16px !important; font-weight: 600 !important; color: white !important;">🎯 ${{fieldInfo.label}}</strong>
                        <div style="background: rgba(255,255,255,0.2) !important; padding: 4px 8px !important; border-radius: 20px !important; font-size: 11px !important; font-weight: 600 !important; color: white !important;">
                            ${{fieldInfo.type === 'multi-value' ? 'MULTI' : 'SINGLE'}}
                        </div>
                    </div>
                    <div style="font-size: 12px !important; opacity: 0.9 !important; margin-top: 6px !important; line-height: 1.3 !important; color: white !important;">${{fieldInfo.description}}</div>
                </div>
                <div id="selection-count" style="background: rgba(255,255,255,0.1) !important; padding: 10px !important; border-radius: 8px !important; margin-bottom: 10px !important; text-align: center !important;">
                    <div style="font-weight: 600 !important; font-size: 15px !important; color: white !important;"><strong>${{fieldInfo.name}}</strong>: 0 selected</div>
                    <div style="font-size: 11px !important; opacity: 0.8 !important; margin-top: 2px !important; color: white !important;">Total across all fields: 0</div>
                </div>
                ${{multiValueInstructions}}
                <div style="background: rgba(255,255,255,0.1) !important; padding: 12px !important; border-radius: 8px !important; margin: 12px 0 !important; font-size: 12px !important; line-height: 1.4 !important; color: white !important;">
                    <div style="font-weight: 600 !important; margin-bottom: 6px !important; color: white !important;">📍 How to interact:</div>
                    <div style="color: white !important;">• <strong>Click</strong> elements to select them</div>
                    <div style="color: white !important;">• <strong>Ctrl+Click</strong> to navigate without selecting</div>
                    <div style="color: white !important;">• <strong>Alt+Click</strong> to preview element info</div>
                    <div style="color: white !important;">• <strong>Hover</strong> to preview selection</div>
                    <div style="color: white !important;">• Selected elements stay highlighted with checkmarks</div>
                </div>
                <div style="display: flex !important; gap: 8px !important; margin-top: 15px !important;">
                    <button onclick="window.stopSelection()" style="
                        flex: 1 !important;
                        padding: 10px 12px !important;
                        background: rgba(255,255,255,0.2) !important;
                        border: 1px solid rgba(255,255,255,0.3) !important;
                        border-radius: 6px !important;
                        color: white !important;
                        cursor: pointer !important;
                        font-size: 12px !important;
                        font-weight: 600 !important;
                        font-family: 'Segoe UI', Arial, sans-serif !important;
                        transition: all 0.2s !important;
                    " onmouseover="this.style.backgroundColor='rgba(255,255,255,0.3)'" onmouseout="this.style.backgroundColor='rgba(255,255,255,0.2)'">
                        ← Back to Fields
                    </button>
                    <button onclick="window.clearFieldSelections('${{fieldInfo.name}}'); updateSelectionCounter();" style="
                        flex: 1 !important;
                        padding: 10px 12px !important;
                        background: #e74c3c !important;
                        color: white !important;
                        border: none !important;
                        border-radius: 6px !important;
                        cursor: pointer !important;
                        font-size: 12px !important;
                        font-weight: 600 !important;
                        font-family: 'Segoe UI', Arial, sans-serif !important;
                        transition: all 0.2s !important;
                    " onmouseover="this.style.backgroundColor='#c0392b'" onmouseout="this.style.backgroundColor='#e74c3c'">
                        Clear Field
                    </button>
                </div>
            `;
            document.body.appendChild(overlay);
            
            // Add event listeners to prevent interference
            overlay.addEventListener('mouseenter', function(e) {{ e.stopPropagation(); }});
            overlay.addEventListener('mouseleave', function(e) {{ e.stopPropagation(); }});
            overlay.addEventListener('click', function(e) {{ e.stopPropagation(); }});
        }}
        
        function hideInstructions() {{
            let overlay = document.getElementById('selection-instructions');
            if (overlay) {{
                overlay.remove();
            }}
        }}
        
        // Get all selected elements
        window.getSelectedElements = function() {{
            return window.contentExtractorData.selectedElements;
        }};
        
        // Get field-specific selections
        window.getFieldSelections = function(fieldName) {{
            return window.contentExtractorData.fieldSelections[fieldName] || [];
        }};
        
        // Get all field selections organized by field
        window.getAllFieldSelections = function() {{
            return window.contentExtractorData.fieldSelections;
        }};
        
        // Clear selections for specific field
        window.clearFieldSelections = function(fieldName) {{
            const fieldSelections = window.contentExtractorData.fieldSelections[fieldName] || [];
            
            // Remove styling from field-specific selected elements
            fieldSelections.forEach(selection => {{
                const elements = document.querySelectorAll(`[data-field-name="${{fieldName}}"]`);
                elements.forEach(element => {{
                    element.style.outline = '';
                    element.style.backgroundColor = '';
                    element.style.boxShadow = '';
                    element.style.zIndex = '';
                    element.style.position = '';
                    element.removeAttribute('data-content-extractor-selected');
                    element.removeAttribute('data-field-name');
                    
                    // Remove selection badge
                    const badge = element.querySelector(`[data-selection-badge="${{fieldName}}"]`);
                    if (badge) {{
                        badge.remove();
                    }}
                    
                    window.contentExtractorData.selectedDOMElements.delete(element);
                }});
            }});
            
            // Clear field-specific data
            window.contentExtractorData.fieldSelections[fieldName] = [];
            
            // Remove from global selections
            window.contentExtractorData.selectedElements = window.contentExtractorData.selectedElements.filter(
                selection => selection.field_name !== fieldName
            );
            
            console.log(`Cleared selections for field: ${{fieldName}}`);
        }};
        
        // Clear all selections
        window.clearSelections = function() {{
            // Remove styling from all selected elements
            window.contentExtractorData.selectedDOMElements.forEach(element => {{
                element.style.outline = '';
                element.style.backgroundColor = '';
                element.style.boxShadow = '';
                element.style.zIndex = '';
                element.style.position = '';
                element.removeAttribute('data-content-extractor-selected');
                element.removeAttribute('data-field-name');
                
                // Remove all selection badges
                const badges = element.querySelectorAll('[data-selection-badge]');
                badges.forEach(badge => badge.remove());
            }});
            
            // Clear all data structures
            window.contentExtractorData.selectedElements = [];
            window.contentExtractorData.selectedDOMElements.clear();
            window.contentExtractorData.fieldSelections = {{}};
            window.contentExtractorData.multiValueExamples = {{}};
            window.contentExtractorData.activeField = null;
            
            // Clean up UI elements
            hideInstructions();
            removeFloatingMenuToggle();
            
            console.log('All selections cleared');
        }};
        
        console.log('Enhanced Field-Specific Content Extractor JavaScript loaded');
        
        // Remove floating menu toggle
        function removeFloatingMenuToggle() {{
            const toggle = document.getElementById('field-menu-toggle');
            if (toggle) {{
                toggle.remove();
            }}
        }}
        
        // Show temporary notification (restored function)
        function showTemporaryNotification(message, type = 'info') {{
            const notification = document.createElement('div');
            notification.setAttribute('data-content-extractor-ui', 'true');
            
            const colors = {{
                success: {{bg: "#27ae60", border: "#2ecc71"}},
                error: {{bg: "#e74c3c", border: "#c0392b"}},
                info: {{bg: "#3498db", border: "#2980b9"}},
                warning: {{bg: "#f39c12", border: "#e67e22"}}
            }};
            
            const color = colors[type] || colors.info;
            
            notification.style.cssText = `
                position: fixed !important;
                top: 20px !important;
                right: 20px !important;
                background: ${{color.bg}} !important;
                color: white !important;
                padding: 12px 20px !important;
                border-radius: 8px !important;
                z-index: 10003 !important;
                font-family: 'Segoe UI', Arial, sans-serif !important;
                font-size: 14px !important;
                font-weight: 600 !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
                border: 2px solid ${{color.border}} !important;
                max-width: 300px !important;
            `;
            
            notification.innerHTML = message;
            document.body.appendChild(notification);
            
            // Auto-remove after 3 seconds
            setTimeout(() => {{
                if (notification.parentNode) {{
                    notification.remove();
                }}
            }}, 3000);
        }}
        
        // Add basic CSS for modal animations
        if (!document.getElementById('content-extractor-animations')) {{
            const style = document.createElement('style');
            style.id = 'content-extractor-animations';
            style.textContent = `
                @keyframes modalSlideIn {{
                    from {{ opacity: 0; transform: scale(0.9); }}
                    to {{ opacity: 1; transform: scale(1); }}
                }}
            `;
            document.head.appendChild(style);
        }}
        
        // Auto-fill functionality for individual fields
        function autoFillCurrentField() {{
            const activeField = window.contentExtractorData.activeField;
            if (!activeField) return;
            
            let autoFilledValue = null;
            
            switch(activeField) {{
                case 'source_url':
                    autoFilledValue = window.location.href;
                    break;
                case 'title':
                    autoFilledValue = document.title || document.querySelector('h1')?.textContent?.trim();
                    break;
                case 'short_description':
                    autoFilledValue = document.querySelector('meta[name="description"]')?.content?.trim();
                    break;
                case 'full_description':
                    // Try common description selectors
                    const descSelectors = [
                        '.description', '.product-description', '.product-details',
                        '#description', '[data-description]', '.content'
                    ];
                    for (const selector of descSelectors) {{
                        const elem = document.querySelector(selector);
                        if (elem && elem.textContent?.trim()) {{
                            autoFilledValue = elem.textContent.trim();
                            break;
                        }}
                    }}
                    break;
                case 'gallery_images':
                    // Find product images
                    const imgSelectors = [
                        '.product-image img', '.gallery img', '.product-gallery img',
                        '[data-image] img', '.image-gallery img'
                    ];
                    for (const selector of imgSelectors) {{
                        const imgs = document.querySelectorAll(selector);
                        if (imgs.length > 0) {{
                            autoFilledValue = `Found ${{imgs.length}} images`;
                            break;
                        }}
                    }}
                    break;
            }}
            
            if (autoFilledValue) {{
                showTemporaryNotification(`🎯 Auto-detected for ${{activeField}}: ${{autoFilledValue.substring(0, 50)}}...`, 'info');
                
                // Show option to use auto-filled value
                showCustomConfirm(
                    `Auto-filled value detected for "${{activeField}}\":\\n\\n${{autoFilledValue.substring(0, 200)}}${{autoFilledValue.length > 200 ? '...' : ''}}\\n\\nUse this auto-detected value?`,
                    function(confirmed) {{
                        if (confirmed) {{
                            // Create a mock selection for the auto-filled value
                            const mockSelection = {{
                                field_name: activeField,
                                label: `${{activeField}}_autofill`,
                                xpath: '//AUTO_FILLED',
                                cssSelector: 'AUTO_FILLED',
                                text: autoFilledValue,
                                tagName: 'auto',
                                attributes: {{}},
                                auto_filled: true
                            }};
                            
                            // Add to selections
                            if (!window.contentExtractorData.fieldSelections[activeField]) {{
                                window.contentExtractorData.fieldSelections[activeField] = [];
                            }}
                            window.contentExtractorData.fieldSelections[activeField].push(mockSelection);
                            window.contentExtractorData.selectedElements.push(mockSelection);
                            
                            showTemporaryNotification(`✅ Auto-filled value saved for ${{activeField}}!`, 'success');
                            updateSelectionCounter();
                        }}
                    }}
                );
            }} else {{
                showTemporaryNotification(`❌ No auto-fill available for ${{activeField}}`, 'warning');
            }}
        }}
        
        // Sub-menu functionality for complex fields
        function showFieldSubMenu(fieldName) {{
            const fieldHierarchies = {{
                'models': [
                    {{id: 'general', label: '📦 All Models', desc: 'Select any model information (recommended)'}},
                    {{id: 'model_name', label: '🏷️ Model Names', desc: 'Specific model names or identifiers'}},
                    {{id: 'model_number', label: '🔢 Model Numbers', desc: 'Part numbers or SKUs'}},
                    {{id: 'specifications', label: '📋 Model Specs', desc: 'Model-specific technical details'}}
                ],
                'categorized_tags': [
                    {{id: 'general', label: '🏷️ All Tags', desc: 'Select any category or tag information (recommended)'}},
                    {{id: 'primary_category', label: '📁 Primary Category', desc: 'Main product category'}},
                    {{id: 'subcategory', label: '📂 Subcategory', desc: 'Product subcategory'}},
                    {{id: 'tags', label: '🏷️ Individual Tags', desc: 'Specific product tags'}}
                ],
                'spec_groups': [
                    {{id: 'general', label: '📊 All Specifications', desc: 'Select any technical specifications (recommended)'}},
                    {{id: 'dimensions', label: '📏 Dimensions', desc: 'Physical measurements'}},
                    {{id: 'weight', label: '⚖️ Weight', desc: 'Product weight information'}},
                    {{id: 'power', label: '⚡ Power Requirements', desc: 'Electrical specifications'}},
                    {{id: 'materials', label: '🧱 Materials', desc: 'Construction materials'}}
                ],
                'features': [
                    {{id: 'general', label: '✨ All Features', desc: 'Select any feature information (recommended)'}},
                    {{id: 'key_features', label: '⭐ Key Features', desc: 'Main product features'}},
                    {{id: 'safety_features', label: '🛡️ Safety Features', desc: 'Safety-related features'}},
                    {{id: 'optional_features', label: '🔧 Optional Features', desc: 'Additional available features'}}
                ],
                'accessories': [
                    {{id: 'general', label: '🔧 All Accessories', desc: 'Select any accessory information (recommended)'}},
                    {{id: 'included_accessories', label: '📦 Included', desc: 'Accessories included with purchase'}},
                    {{id: 'optional_accessories', label: '🛒 Optional', desc: 'Additional available accessories'}},
                    {{id: 'replacement_parts', label: '🔩 Replacement Parts', desc: 'Available replacement components'}}
                ]
            }};
            
            const subFields = fieldHierarchies[fieldName];
            if (!subFields) {{
                // No sub-menu, use regular field selection
                selectField(fieldName);
                return;
            }}
            
            // Show sub-menu selection with enhanced styling
            const fieldLabel = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName)?.label || fieldName;
            
            showCustomSelect(
                `📋 ${{fieldLabel}} Sub-Categories`,
                `Choose how you want to approach selecting "${{fieldLabel}}" content:\\n\\n💡 Tip: "General" options work for most cases and are easier to use.`,
                subFields,
                function(subFieldId) {{
                    if (subFieldId === 'general') {{
                        // User wants to select the parent field generally
                        handleGeneralFieldSelection(fieldName);
                    }} else {{
                        // User wants specific sub-field
                        handleSubFieldSelection(fieldName, subFieldId, subFields.find(f => f.id === subFieldId));
                    }}
                }}
            );
        }}
        
        function handleGeneralFieldSelection(fieldName) {{
            // Set active field to the parent field name
            window.contentExtractorData.activeField = fieldName;
            
            // Initialize field selections if not exists
            if (!window.contentExtractorData.fieldSelections[fieldName]) {{
                window.contentExtractorData.fieldSelections[fieldName] = [];
            }}
            
            // Create floating menu toggle
            createFloatingMenuToggle();
            
            // Start selection mode for the parent field
            window.startFieldSelection(fieldName);
            
            // Show notification about general selection
            showTemporaryNotification(`🎯 Now selecting: ${{fieldName}} (general mode)`, 'info');
        }}
        
        function handleSubFieldSelection(parentField, subFieldId, subFieldInfo) {{
            // Create a compound field name
            const compoundFieldName = `${{parentField}}.${{subFieldId}}`;
            
            // Set active field to the compound name
            window.contentExtractorData.activeField = compoundFieldName;
            
            // Initialize field selections if not exists
            if (!window.contentExtractorData.fieldSelections[compoundFieldName]) {{
                window.contentExtractorData.fieldSelections[compoundFieldName] = [];
            }}
            
            // Create floating menu toggle for sub-field
            createFloatingMenuToggle();
            
            // Start selection mode for sub-field
            window.startFieldSelection(compoundFieldName);
            
            // Show notification about sub-field selection
            showTemporaryNotification(`🎯 Now selecting: ${{subFieldInfo.label}} (${{parentField}})`, 'info');
        }}
        
        // Enhanced control panel with auto-fill button
        function createEnhancedControlPanel() {{
            // This function would modify the control panel to add auto-fill button
            // Called when creating the floating toggle
            const controlPanel = document.getElementById('field-menu-toggle');
            if (!controlPanel) return;
            
            // Add auto-fill button after the main grid
            const autoFillSection = document.createElement('div');
            autoFillSection.style.cssText = `
                margin: 8px 0 !important;
                padding: 8px 0 !important;
                border-top: 1px solid rgba(255,255,255,0.2) !important;
                border-bottom: 1px solid rgba(255,255,255,0.2) !important;
            `;
            
            autoFillSection.innerHTML = `
                <button id="control-autofill-btn" style="
                    width: 100% !important;
                    background: linear-gradient(135deg, #9b59b6, #8e44ad) !important;
                    color: white !important;
                    border: none !important;
                    padding: 10px 12px !important;
                    border-radius: 6px !important;
                    cursor: pointer !important;
                    font-size: 12px !important;
                    font-weight: 600 !important;
                    transition: all 0.2s !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    gap: 6px !important;
                " onmouseover="this.style.backgroundColor='#8e44ad'" 
                   onmouseout="this.style.backgroundColor='#9b59b6'">
                    <span>🎯</span>
                    <span>Auto-Fill Current Field</span>
                </button>
            `;
            
            // Insert before the tips section
            const tipsSection = controlPanel.querySelector('[style*="Quick Tips"]').parentElement;
            controlPanel.insertBefore(autoFillSection, tipsSection);
            
            // Add event handler
            autoFillSection.querySelector('#control-autofill-btn').addEventListener('click', function(e) {{
                e.stopPropagation();
                autoFillCurrentField();
            }});
        }}
        
        // Start field-specific selection mode
        window.startFieldSelection = function(fieldName) {{
            window.contentExtractorData.isSelectionMode = true;
            window.contentExtractorData.activeField = fieldName;
            
            // Check if this is a sub-field (contains dot)
            let fieldInfo;
            if (fieldName.includes('.')) {{
                const [parentField, subField] = fieldName.split('.');
                fieldInfo = {{
                    name: fieldName,
                    label: `${{parentField}} > ${{subField}}`,
                    type: 'single',
                    description: `Sub-field of ${{parentField}}`
                }};
            }} else {{
                fieldInfo = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
            }}
            
            document.addEventListener('mouseover', handleMouseOver);
            document.addEventListener('mouseout', handleMouseOut);
            document.addEventListener('click', handleClick);
            
            // Show field-specific instructions
            showFieldInstructions(fieldInfo);
            
            // Add auto-fill to control panel if it exists
            setTimeout(createEnhancedControlPanel, 100);
        }};
        
        // Stop selection mode
        window.stopSelection = function() {{
            window.contentExtractorData.isSelectionMode = false;
            
            document.removeEventListener('mouseover', handleMouseOver);
            document.removeEventListener('mouseout', handleMouseOut);
            document.removeEventListener('click', handleClick);
            
            hideInstructions();
            removeFloatingMenuToggle(); // Clean up the toggle button
            window.showFieldMenu(); // Return to field menu
        }};
        
        function handleMouseOver(event) {{
            if (window.contentExtractorData.isSelectionMode) {{
                // Ignore events on content extractor UI elements
                if (isContentExtractorElement(event.target)) {{
                    return;
                }}
                highlightElement(event.target);
            }}
        }}
        
        function handleMouseOut(event) {{
            if (window.contentExtractorData.isSelectionMode) {{
                // Ignore events on content extractor UI elements
                if (isContentExtractorElement(event.target)) {{
                    return;
                }}
                removeHighlight(event.target);
            }}
        }}
        
        function handleClick(event) {{
            // NEW: Check for modifier keys
            if (event.ctrlKey || event.metaKey) {{
                // Allow normal page interaction without selecting
                console.log('Ctrl/Cmd+Click detected: Allowing normal navigation without selection');
                return; // Don't prevent default, don't select
            }}
            
            if (event.altKey) {{
                // Preview mode - show element info without selecting
                event.preventDefault();
                event.stopPropagation();
                
                if (!isContentExtractorElement(event.target)) {{
                    let element = event.target;
                    let xpath = getXPath(element);
                    let text = element.textContent.trim().substring(0, 100);
                    
                    // Show preview info
                    console.log('Element Preview:', {{
                        tag: element.tagName.toLowerCase(),
                        text: text,
                        xpath: xpath,
                        classes: element.className
                    }});
                    
                    // Visual feedback for preview
                    element.style.outline = '2px dashed #ffa500';
                    setTimeout(() => {{
                        if (!window.contentExtractorData.selectedDOMElements.has(element)) {{
                            element.style.outline = '';
                        }}
                    }}, 1000);
                }}
                return;
            }}
            
            if (window.contentExtractorData.isSelectionMode) {{
                // Ignore clicks on content extractor UI elements
                if (isContentExtractorElement(event.target)) {{
                    return;
                }}
                
                event.preventDefault();
                event.stopPropagation();
                
                let element = event.target;
                const fieldName = window.contentExtractorData.activeField;
                
                // Check if already selected
                if (window.contentExtractorData.selectedDOMElements.has(element)) {{
                    console.log('Element already selected, skipping...');
                    return;
                }}
                
                let xpath = getXPath(element);
                let cssSelector = getCSSSelector(element);
                let text = element.textContent.trim().substring(0, 200);
                
                let selection = {{
                    field_name: fieldName,
                    label: `${{fieldName}}_selection`,
                    xpath: xpath,
                    cssSelector: cssSelector,
                    text: text,
                    tagName: element.tagName.toLowerCase(),
                    attributes: {{}}
                }};
                
                // Capture key attributes
                for (let attr of element.attributes) {{
                    selection.attributes[attr.name] = attr.value;
                }}
                
                // Add to global and field-specific selections
                window.contentExtractorData.selectedElements.push(selection);
                window.contentExtractorData.fieldSelections[fieldName].push(selection);
                
                // Mark as selected with field-specific styling
                markAsSelected(element, fieldName);
                
                console.log('Element selected for field:', fieldName, selection);
                
                // Update counter in instruction box
                updateSelectionCounter();
                
                // Handle multi-value field logic (only for parent fields, not sub-fields)
                if (!fieldName.includes('.')) {{
                    const fieldInfo = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
                    if (fieldInfo && fieldInfo.type === 'multi-value') {{
                        handleMultiValueSelection(fieldName, selection);
                    }}
                }}
            }}
        }}
        
        // Set up event listeners for nested navigation
        document.addEventListener('enterNestedField', function(event) {{
            const {{ fieldName, instanceIndex }} = event.detail;
            console.log(`Entering nested field: ${{fieldName}} at index ${{instanceIndex}}`);
            
            // This would trigger Python callback through Selenium
            window.pendingNestedAction = {{
                action: 'enter_nested',
                fieldName: fieldName,
                instanceIndex: instanceIndex
            }};
        }});
        
        document.addEventListener('navigateToParent', function(event) {{
            console.log('Navigating to parent context');
            
            // This would trigger Python callback through Selenium
            window.pendingNestedAction = {{
                action: 'navigate_parent'
            }};
        }});
        
        document.addEventListener('nestedNavigate', function(event) {{
            const {{ targetDepth }} = event.detail;
            console.log(`Navigating to depth: ${{targetDepth}}`);
            
            // This would trigger Python callback through Selenium
            window.pendingNestedAction = {{
                action: 'navigate_to_depth',
                targetDepth: targetDepth
            }};
        }});
        
        // Refresh interface after nested context change
        window.refreshNestedInterface = function() {{
            // Remove existing field menu
            const existingMenu = document.getElementById('field-selection-menu');
            if (existingMenu) {{
                existingMenu.remove();
            }}
            
            // Show updated field menu with new context
            window.showFieldMenu();
        }};
        
        // Navigation helper functions
        window.navigateToDepth = function(depth) {{
            document.dispatchEvent(new CustomEvent('nestedNavigate', {{
                detail: {{ targetDepth: depth }}
            }}));
        }};
        
        // Add event listeners after menu is created
        window.attachFieldMenuListeners = function() {{
            // Add event listeners to field option buttons
            document.querySelectorAll('.field-option').forEach(button => {{
                button.addEventListener('click', function(e) {{
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const fieldName = this.getAttribute('data-field');
                    const isNestedField = this.classList.contains('nested-field');
                    
                    console.log('Field option clicked:', fieldName, 'isNested:', isNestedField);
                    
                    if (isNestedField) {{
                        // Handle nested field - enter nested context
                        console.log('Entering nested field:', fieldName);
                        document.dispatchEvent(new CustomEvent('enterNestedField', {{
                            detail: {{ fieldName: fieldName, instanceIndex: 0 }}
                        }}));
                    }} else {{
                        // Handle regular field - start field selection
                        selectField(fieldName);
                    }}
                }});
            }});
            
            // Add event listener to parent navigation button
            const parentBtn = document.getElementById('navigate-parent');
            if (parentBtn) {{
                parentBtn.addEventListener('click', function(e) {{
                    e.preventDefault();
                    e.stopPropagation();
                    console.log('Navigate to parent clicked');
                    document.dispatchEvent(new CustomEvent('navigateToParent'));
                }});
            }}
            
            // Add event listener to close menu button
            const closeBtn = document.getElementById('close-field-menu');
            if (closeBtn) {{
                closeBtn.addEventListener('click', function(e) {{
                    e.preventDefault();
                    e.stopPropagation();
                    document.getElementById('field-selection-menu')?.remove();
                }});
            }}
            
            // Add breadcrumb navigation listeners
            document.querySelectorAll('[onclick*="navigateToDepth"]').forEach(breadcrumb => {{
                breadcrumb.addEventListener('click', function(e) {{
                    e.preventDefault();
                    e.stopPropagation();
                    const onclickAttr = this.getAttribute('onclick');
                    const depth = parseInt(onclickAttr.match(/navigateToDepth\\((\\d+)\\)/)?.[1] || '0');
                    console.log('Breadcrumb clicked, navigating to depth:', depth);
                    window.navigateToDepth(depth);
                }});
            }});
        }};
        
        // Helper function to select a field
        window.selectField = function(fieldName) {{
            // Check if there are sub-menu options for this field
            const hasSubMenu = ['models', 'categorized_tags', 'spec_groups', 'features', 'accessories'].includes(fieldName);
            
            if (hasSubMenu) {{
                showFieldSubMenu(fieldName);
            }} else {{
                // Close field menu
                document.getElementById('field-selection-menu')?.remove();
                
                // Start field selection
                window.contentExtractorData.activeField = fieldName;
                window.contentExtractorData.isSelectionMode = true;
                
                // Initialize field selections array if needed
                if (!window.contentExtractorData.fieldSelections[fieldName]) {{
                    window.contentExtractorData.fieldSelections[fieldName] = [];
                }}
                
                showInstructions(fieldName);
                showTemporaryNotification(`🎯 Now selecting: ${{fieldName}}`, 'info');
                
                console.log('Started field selection for:', fieldName);
            }}
        }};

        // Prevent context menu during dragging
        document.addEventListener('contextmenu', function(e) {{
            if (window.contentExtractorData.dragging && window.contentExtractorData.dragging.isDragging) {{
                e.preventDefault();
            }}
        }});

        // DRAGGABLE FUNCTIONALITY - Properly implemented
        // Initialize dragging state
        window.contentExtractorData.dragging = {{
            isDragging: false,
            element: null,
            startX: 0,
            startY: 0,
            startElementX: 0,
            startElementY: 0
        }};

        // Make element draggable
        function makeDraggable(element) {{
            let isDragging = false;
            let startX, startY, startElementX, startElementY;
            
            element.addEventListener('mousedown', function(e) {{
                // Only drag from header area, not buttons
                if (e.target.tagName === 'BUTTON' || e.target.closest('button')) {{
                    return;
                }}
                
                isDragging = true;
                startX = e.clientX;
                startY = e.clientY;
                
                const rect = element.getBoundingClientRect();
                startElementX = rect.left;
                startElementY = rect.top;
                
                element.style.opacity = '0.9';
                element.style.zIndex = '10999';
                document.body.style.cursor = 'move';
                document.body.style.userSelect = 'none';
                
                e.preventDefault();
                e.stopPropagation();
            }});
            
            document.addEventListener('mousemove', function(e) {{
                if (!isDragging) return;
                
                const deltaX = e.clientX - startX;
                const deltaY = e.clientY - startY;
                
                const newX = startElementX + deltaX;
                const newY = startElementY + deltaY;
                
                // Constrain to viewport
                const maxX = window.innerWidth - element.offsetWidth;
                const maxY = window.innerHeight - element.offsetHeight;
                
                const constrainedX = Math.max(0, Math.min(newX, maxX));
                const constrainedY = Math.max(0, Math.min(newY, maxY));
                
                element.style.left = constrainedX + 'px';
                element.style.top = constrainedY + 'px';
                element.style.position = 'fixed';
            }});
            
            document.addEventListener('mouseup', function(e) {{
                if (!isDragging) return;
                
                isDragging = false;
                element.style.opacity = '';
                element.style.zIndex = element.id === 'field-selection-menu' ? '10001' : '10002';
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
            }});
        }}

        // Element interaction handlers
        document.addEventListener('click', function(e) {{
            if (window.contentExtractorData.isSelectionMode) {{
                e.preventDefault();
                e.stopPropagation();
                
                // Don't select UI elements - check for CSS class
                if (e.target.classList.contains('content-extractor-ui') || e.target.closest('.content-extractor-ui')) {{
                    return;
                }}
                
                let selectedElement = {{
                    xpath: getXPath(e.target),
                    cssSelector: getCSSSelector(e.target),
                    text: e.target.innerText || e.target.textContent || '',
                    tagName: e.target.tagName.toLowerCase(),
                    className: e.target.className,
                    id: e.target.id,
                    coordinates: {{
                        x: e.clientX,
                        y: e.clientY
                    }},
                    timestamp: new Date().toISOString(),
                    fieldName: window.contentExtractorData.activeField,
                    depth: window.contentExtractorData.currentDepth,
                    contextPath: window.contentExtractorData.contextPath
                }};
                
                // Add to selections
                window.contentExtractorData.selectedElements.push(selectedElement);
                
                // Mark as selected visually
                markAsSelected(e.target, window.contentExtractorData.activeField);
                
                // Store in field-specific selection data
                if (!window.contentExtractorData.fieldSelections[window.contentExtractorData.activeField]) {{
                    window.contentExtractorData.fieldSelections[window.contentExtractorData.activeField] = [];
                }}
                window.contentExtractorData.fieldSelections[window.contentExtractorData.activeField].push(selectedElement);
                
                showTemporaryNotification(`✅ Element selected for ${{window.contentExtractorData.activeField}}`, 'success');
                
                console.log('Element selected:', selectedElement);
            }}
        }});

        document.addEventListener('mouseover', function(e) {{
            if (window.contentExtractorData.isSelectionMode && !e.target.classList.contains('content-extractor-ui') && !e.target.closest('.content-extractor-ui')) {{
                highlightElement(e.target);
            }}
        }});

        document.addEventListener('mouseout', function(e) {{
            if (window.contentExtractorData.isSelectionMode && !e.target.classList.contains('content-extractor-ui') && !e.target.closest('.content-extractor-ui')) {{
                removeHighlight(e.target);
            }}
        }});

        // Notification system
        function showTemporaryNotification(message, type = 'info', duration = 3000) {{
            // Remove existing notification
            const existing = document.querySelector('[data-temp-notification]');
            if (existing) {{
                existing.remove();
            }}
            
            const notification = document.createElement('div');
            notification.setAttribute('data-temp-notification', 'true');
            notification.className = 'content-extractor-ui';
            notification.style.cssText = `
                position: fixed !important;
                top: 20px !important;
                right: 20px !important;
                background: ${{type === 'error' ? '#e74c3c' : type === 'success' ? '#27ae60' : '#3498db'}} !important;
                color: white !important;
                padding: 12px 20px !important;
                border-radius: 6px !important;
                z-index: 20000 !important;
                font-family: 'Segoe UI', Arial, sans-serif !important;
                font-size: 14px !important;
                font-weight: 500 !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
                animation: slideInRight 0.3s ease-out !important;
                pointer-events: none !important;
            `;
            notification.textContent = message;
            document.body.appendChild(notification);
            
            // Auto-remove after duration
            setTimeout(() => {{
                if (notification.parentNode) {{
                    notification.style.animation = 'slideOutRight 0.3s ease-in forwards';
                    setTimeout(() => notification.remove(), 300);
                }}
            }}, duration);
        }}

        // Instructions display with enhanced nested context support
        function showInstructions(fieldName) {{
            // Remove existing instructions
            const existing = document.querySelector('[data-instructions-panel]');
            if (existing) {{
                existing.remove();
            }}
            
            const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
            if (!field) return;
            
            const depth = window.contentExtractorData.currentDepth;
            const contextDisplay = depth > 0 ? ` (Level ${{depth + 1}})` : '';
            const depthColor = getDepthColor(depth);
            
            const instructions = document.createElement('div');
            instructions.setAttribute('data-instructions-panel', 'true');
            instructions.className = 'content-extractor-ui';
            instructions.style.cssText = `
                position: fixed !important;
                top: 70px !important;
                left: 20px !important;
                background: white !important;
                border: 3px solid ${{depthColor}} !important;
                border-radius: 8px !important;
                padding: 20px !important;
                z-index: 10003 !important;
                font-family: 'Segoe UI', Arial, sans-serif !important;
                font-size: 14px !important;
                box-shadow: 0 8px 24px rgba(0,0,0,0.2) !important;
                max-width: 400px !important;
                animation: slideInLeft 0.3s ease-out !important;
            `;
            
            instructions.innerHTML = `
                <div style="font-weight: bold; color: ${{depthColor}}; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;">
                    <span style="background: ${{depthColor}}; color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-size: 12px;">
                        ${{depth > 0 ? depth : '✓'}}
                    </span>
                    Selecting: ${{field.label}}${{contextDisplay}}
                </div>
                <div style="color: #666; margin-bottom: 15px; line-height: 1.4;">
                    ${{field.description}}
                </div>
                <div style="color: #444; font-size: 13px; line-height: 1.3;">
                    • Click elements to select them<br>
                    • Elements will be highlighted as you hover<br>
                    • Selected elements get a colored border and badge<br>
                    • Use the control panel to stop selection
                </div>
                <button onclick="this.parentElement.remove()" 
                        style="position: absolute; top: 8px; right: 8px; background: none; border: none; font-size: 18px; cursor: pointer; color: #999;">
                    ×
                </button>
            `;
            
            document.body.appendChild(instructions);
        }}

        // Enhanced field menu with nested context support and breadcrumb navigation
        window.showFieldMenu = function() {{
            // Remove existing menu
            const existing = document.querySelector('#field-selection-menu');
            if (existing) {{
                existing.remove();
            }}
            
            const depth = window.contentExtractorData.currentDepth;
            const depthColor = getDepthColor(depth);
            const breadcrumbs = window.contentExtractorData.breadcrumbs;
            
            const menu = document.createElement('div');
            menu.id = 'field-selection-menu';
            menu.className = 'content-extractor-ui';
            menu.style.cssText = `
                position: fixed !important;
                top: 50px !important;
                right: 50px !important;
                background: white !important;
                border: 3px solid ${{depthColor}} !important;
                border-radius: 12px !important;
                padding: 0 !important;
                z-index: 10001 !important;
                font-family: 'Segoe UI', Arial, sans-serif !important;
                box-shadow: 0 8px 24px rgba(0,0,0,0.5) !important;
                min-width: 300px !important;
                max-width: 400px !important;
                max-height: 80vh !important;
                animation: slideInRight 0.3s ease-out !important;
                display: flex !important;
                flex-direction: column !important;
                overflow: hidden !important;
            `;
            
            // Build breadcrumb navigation
            let breadcrumbHTML = '';
            if (breadcrumbs.length > 0) {{
                breadcrumbHTML = `
                    <div style="margin-bottom: 15px; padding-bottom: 15px; border-bottom: 2px solid #eee;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 8px;">Navigation Path:</div>
                        <div style="display: flex; align-items: center; gap: 5px; flex-wrap: wrap;">
                `;
                
                breadcrumbs.forEach((crumb, index) => {{
                    const isLast = index === breadcrumbs.length - 1;
                    const crumbColor = getDepthColor(index);
                    breadcrumbHTML += `
                        <span onclick="window.navigateToDepth(${{index}})" 
                              style="background: ${{isLast ? crumbColor : '#f8f9fa'}}; 
                                     color: ${{isLast ? 'white' : '#666'}}; 
                                     padding: 4px 8px; 
                                     border-radius: 4px; 
                                     font-size: 11px; 
                                     cursor: ${{isLast ? 'default' : 'pointer'}}; 
                                     border: 1px solid ${{isLast ? crumbColor : '#ddd'}};">
                            ${{crumb}}
                        </span>
                    `;
                    
                    if (!isLast) {{
                        breadcrumbHTML += `<span style="color: #ccc;">→</span>`;
                    }}
                }});
                
                breadcrumbHTML += `
                        </div>
                    </div>
                `;
            }}
            
            // Field selection buttons
            let fieldsHTML = '';
            window.contentExtractorData.fieldOptions.forEach(field => {{
                const fieldColor = field.color || getFieldColor(field.name);
                const hasSubFields = field.has_sub_fields;
                const typeIcon = {{
                    'single': '📄',
                    'multi-value': '📋',
                    'nested': '🏗️'
                }}[field.type] || '❓';
                
                fieldsHTML += `
                    <button onclick="window.startFieldSelection('${{field.name}}')" 
                            style="display: block; 
                                   width: 100%; 
                                   margin: 8px 0; 
                                   padding: 12px; 
                                   background: linear-gradient(135deg, ${{fieldColor}}, ${{fieldColor}}dd); 
                                   color: white; 
                                   border: none; 
                                   border-radius: 6px; 
                                   cursor: pointer; 
                                   font-weight: 500; 
                                   font-size: 13px; 
                                   transition: all 0.2s; 
                                   text-align: left;
                                   position: relative;"
                            onmouseover="this.style.transform='scale(1.02)'; this.style.boxShadow='0 4px 12px rgba(0,0,0,0.2)';"
                            onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='none';">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="font-size: 16px;">${{typeIcon}}</span>
                            <span>${{field.label}}</span>
                            ${{hasSubFields ? '<span style="margin-left: auto; opacity: 0.8;">→</span>' : ''}}
                        </div>
                        <div style="font-size: 11px; opacity: 0.9; margin-top: 4px; line-height: 1.2;">
                            ${{field.description}}
                        </div>
                    </button>
                `;
            }});
            
            menu.innerHTML = `
                <div style="padding: 20px; border-bottom: 1px solid #eee; cursor: move;" class="menu-header">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="background: ${{depthColor}}; color: white; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 12px;">
                            ${{depth > 0 ? depth : '🎯'}}
                        </span>
                        <span style="font-weight: bold; color: #333; font-size: 16px;">
                            Field Selection${{depth > 0 ? ` (Level ${{depth + 1}})` : ''}}
                        </span>
                        <button onclick="document.querySelector('#field-selection-menu').remove()" 
                                style="margin-left: auto; background: none; border: none; font-size: 18px; cursor: pointer; color: #999;">×</button>
                    </div>
                    ${{breadcrumbHTML}}
                </div>
                
                <div style="padding: 20px; overflow-y: auto; flex: 1;">
                    ${{fieldsHTML}}
                    
                    <div style="border-top: 1px solid #eee; padding-top: 15px; margin-top: 15px; font-size: 12px; color: #666;">
                        Click a field to start selecting content for it. Nested fields (🏗️) will open sub-menus.
                    </div>
                </div>
            `;
            
            document.body.appendChild(menu);
            
            // Make the menu draggable
            makeDraggable(menu);
            
            console.log('Field menu displayed with', window.contentExtractorData.fieldOptions.length, 'options at depth', depth);
        }};

        // Navigation functions for nested contexts
        window.navigateToDepth = function(targetDepth) {{
            console.log('Navigating to depth:', targetDepth);
            // This will be handled by Python backend
            window.contentExtractorData.pendingAction = {{
                type: 'navigate_to_depth',
                depth: targetDepth,
                timestamp: Date.now()
            }};
        }};

        window.navigateToParent = function() {{
            console.log('Navigating to parent context');
            // This will be handled by Python backend
            window.contentExtractorData.pendingAction = {{
                type: 'navigate_to_parent',
                timestamp: Date.now()
            }};
        }};

        // Enhanced nested field entry with JavaScript communication
        window.startFieldSelection = function(fieldName) {{
            console.log('Starting field selection for:', fieldName);
            
            // Check if this is a nested field
            const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
            
            if (field && field.has_sub_fields) {{
                console.log('Field has sub-fields, entering nested context');
                
                // Set pending action for backend to handle
                window.contentExtractorData.pendingAction = {{
                    type: 'enter_nested_field',
                    fieldName: fieldName,
                    instanceIndex: 0,
                    timestamp: Date.now()
                }};
                
                showTemporaryNotification(`🔄 Entering nested context: ${{fieldName}}`, 'info');
            }} else {{
                // Regular field selection
                window.contentExtractorData.activeField = fieldName;
                window.contentExtractorData.isSelectionMode = true;
                
                // Initialize field selections array if needed
                if (!window.contentExtractorData.fieldSelections[fieldName]) {{
                    window.contentExtractorData.fieldSelections[fieldName] = [];
                }}
                
                showInstructions(fieldName);
                showTemporaryNotification(`🎯 Now selecting: ${{fieldName}}`, 'info');
                
                console.log('Started field selection for:', fieldName);
            }}
        }};

        // Control panel functions
        window.stopFieldSelection = function() {{
            window.contentExtractorData.isSelectionMode = false;
            window.contentExtractorData.activeField = null;
            
            // Remove instructions
            const instructions = document.querySelector('[data-instructions-panel]');
            if (instructions) {{
                instructions.remove();
            }}
            
            showTemporaryNotification('Selection stopped', 'info');
        }};

        window.clearAllSelections = function() {{
            // Remove all visual selections
            document.querySelectorAll('[data-content-extractor-selected]').forEach(element => {{
                element.style.outline = '';
                element.style.backgroundColor = '';
                element.style.boxShadow = '';
                element.style.position = '';
                element.style.zIndex = '';
                element.removeAttribute('data-content-extractor-selected');
                element.removeAttribute('data-field-name');
                element.removeAttribute('data-selection-depth');
                
                // Remove badge
                const badge = element.querySelector('[data-selection-badge]');
                if (badge) {{
                    badge.remove();
                }}
            }});
            
            // Clear data
            window.contentExtractorData.selectedElements = [];
            window.contentExtractorData.selectedDOMElements = new Set();
            window.contentExtractorData.fieldSelections = {{}};
            
            showTemporaryNotification('All selections cleared', 'info');
        }};

        // Function to refresh nested interface after context changes
        window.refreshNestedInterface = function() {{
            console.log('Refreshing nested interface');
            
            // Close existing menu
            const existingMenu = document.querySelector('#field-selection-menu');
            if (existingMenu) {{
                existingMenu.remove();
            }}
            
            // Show updated menu after a brief delay
            setTimeout(() => {{
                window.showFieldMenu();
            }}, 100);
        }};

        // Export functions for backend access
        window.getSelectedElements = function() {{
            return window.contentExtractorData.selectedElements;
        }};

        window.getFieldSelections = function(fieldName) {{
            return window.contentExtractorData.fieldSelections[fieldName] || [];
        }};

        window.getAllFieldSelections = function() {{
            return window.contentExtractorData.fieldSelections;
        }};

        // CSS animations
        const animationStyles = document.createElement('style');
        animationStyles.textContent = `
            @keyframes slideInRight {{
                from {{ transform: translateX(100%); opacity: 0; }}
                to {{ transform: translateX(0); opacity: 1; }}
            }}
            @keyframes slideOutRight {{
                from {{ transform: translateX(0); opacity: 1; }}
                to {{ transform: translateX(100%); opacity: 0; }}
            }}
            @keyframes slideInLeft {{
                from {{ transform: translateX(-100%); opacity: 0; }}
                to {{ transform: translateX(0); opacity: 1; }}
            }}
        `;
        document.head.appendChild(animationStyles);

        // Floating control panel
        const controlPanel = document.createElement('div');
        controlPanel.id = 'field-menu-toggle';
        controlPanel.className = 'content-extractor-ui';
        controlPanel.style.cssText = `
            position: fixed !important;
            bottom: 30px !important;
            right: 30px !important;
            background: linear-gradient(135deg, #667eea, #764ba2) !important;
            color: white !important;
            border: none !important;
            border-radius: 50px !important;
            padding: 15px 20px !important;
            z-index: 10002 !important;
            font-family: 'Segoe UI', Arial, sans-serif !important;
            font-weight: 600 !important;
            cursor: pointer !important;
            box-shadow: 0 8px 24px rgba(0,0,0,0.3) !important;
            transition: all 0.3s ease !important;
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
        `;

        controlPanel.innerHTML = `
            <span style="font-size: 16px;">🎯</span>
            <span>Field Menu</span>
        `;

        controlPanel.addEventListener('click', function() {{
            window.showFieldMenu();
        }});

        controlPanel.addEventListener('mouseover', function() {{
            this.style.transform = 'scale(1.05)';
            this.style.boxShadow = '0 12px 30px rgba(0,0,0,0.4)';
        }});

        controlPanel.addEventListener('mouseout', function() {{
            this.style.transform = 'scale(1)';
            this.style.boxShadow = '0 8px 24px rgba(0,0,0,0.3)';
        }});

        document.body.appendChild(controlPanel);
        
        // Make control panel draggable too
        makeDraggable(controlPanel);

        console.log('Enhanced nested selection interface initialized with depth support');

        // Navigate to parent context
        function navigateToParent() {{
            // Trigger Python callback to navigate to parent
            const event = new CustomEvent('navigateToParent', {{}});
            document.dispatchEvent(event);
        }}
        
        // Add new instance of current nested field
        function addNestedInstance() {{
            // Get current nested field name from breadcrumbs
            const breadcrumbs = window.contentExtractorData.nestedContext ? window.contentExtractorData.nestedContext.breadcrumbs : [];
            if (breadcrumbs.length < 2) {{
                console.log('No nested context found for adding instance');
                return;
            }}
            
            // Extract field name from last breadcrumb (e.g., "models[0]" -> "models")
            const lastBreadcrumb = breadcrumbs[breadcrumbs.length - 1];
            const bracketIndex = lastBreadcrumb.indexOf('[');
            const fieldName = bracketIndex > 0 ? lastBreadcrumb.substring(0, bracketIndex) : lastBreadcrumb;
            
            // Set pending action for Python to process
            window.contentExtractorData.pendingAction = {{
                type: 'add_instance',
                fieldName: fieldName
            }};
            
            console.log(`Adding new instance for field: ${{fieldName}}`);
        }}
        
        document.addEventListener('navigateToParent', function(event) {{
            console.log('Navigating to parent context');
            
            // This would trigger Python callback through Selenium
            window.pendingNestedAction = {{
                action: 'navigate_parent'
            }};
        }});
        
        document.addEventListener('createNewInstance', function(event) {{
            const {{ fieldName, newIndex }} = event.detail;
            console.log(`Creating new instance: ${{fieldName}} at index ${{newIndex}}`);
            
            // This would trigger Python callback through Selenium
            window.pendingNestedAction = {{
                action: 'create_new_instance',
                fieldName: fieldName,
                newIndex: newIndex
            }};
        }});
    """
        
        try:
            self.driver.execute_script(selection_js)
            logger.info("Enhanced nested selection JavaScript injected successfully")
        except Exception as e:
            logger.error(f"Failed to inject JavaScript: {e}")
            raise

    def enter_nested_field(self, field_name: str, instance_index: int = 0) -> bool:
        """
        Enter a nested field context and refresh the interface.
        
        Args:
            field_name: Name of the nested field to enter
            instance_index: Index for multi-value fields
            
        Returns:
            True if successfully entered nested context
        """
        try:
            # Use nested manager to enter nested context
            success = self.nested_manager.enter_nested_field(field_name, instance_index)
            
            if success:
                logger.info(f"Entered nested field '{field_name}' at index {instance_index}")
                
                # Re-inject JavaScript with updated context
                self._inject_selection_js()
                
                # Refresh the field menu interface
                self.driver.execute_script("window.refreshNestedInterface();")
                
                return True
            else:
                logger.warning(f"Failed to enter nested field '{field_name}' - field may not support nesting")
                return False
                
        except Exception as e:
            logger.error(f"Error entering nested field '{field_name}': {e}")
            return False

    def navigate_to_parent(self) -> bool:
        """
        Navigate back to parent context and refresh the interface.
        
        Returns:
            True if successfully navigated to parent
        """
        try:
            # Use nested manager to navigate to parent
            success = self.nested_manager.navigate_to_parent()
            
            if success:
                logger.info("Navigated to parent context")
                
                # Re-inject JavaScript with updated context
                self._inject_selection_js()
                
                # Refresh the field menu interface
                self.driver.execute_script("window.refreshNestedInterface();")
                
                return True
            else:
                logger.warning("Failed to navigate to parent - already at root level")
                return False
                
        except Exception as e:
            logger.error(f"Error navigating to parent: {e}")
            return False

    def navigate_to_depth(self, target_depth: int) -> bool:
        """
        Navigate to specific depth level in nested hierarchy.
        
        Args:
            target_depth: Target depth level (0 = root)
            
        Returns:
            True if successfully navigated to target depth
        """
        try:
            current_depth = self.nested_manager.get_current_depth()
            
            if target_depth == current_depth:
                return True  # Already at target depth
                
            if target_depth > current_depth:
                logger.warning(f"Cannot navigate to deeper level {target_depth} from current depth {current_depth}")
                return False
                
            # Navigate up to target depth
            while self.nested_manager.get_current_depth() > target_depth:
                if not self.nested_manager.navigate_to_parent():
                    break
                    
            logger.info(f"Navigated to depth {target_depth}")
            
            # Re-inject JavaScript with updated context
            self._inject_selection_js()
            
            # Refresh the field menu interface
            self.driver.execute_script("window.refreshNestedInterface();")
            
            return True
            
        except Exception as e:
            logger.error(f"Error navigating to depth {target_depth}: {e}")
            return False

    def check_for_nested_actions(self) -> bool:
        """
        Check for pending nested navigation actions from JavaScript and handle them.
        
        Returns:
            True if action was handled
        """
        try:
            # Check for pending nested actions in current JavaScript structure
            pending_action = self.driver.execute_script("return window.contentExtractorData.pendingAction;")
            
            if pending_action:
                # Clear the pending action
                self.driver.execute_script("window.contentExtractorData.pendingAction = null;")
                
                action_type = pending_action.get('type')
                
                if action_type == 'enter_nested_field':
                    field_name = pending_action.get('fieldName')
                    instance_index = pending_action.get('instanceIndex', 0)
                    logger.info(f"Processing nested field entry: {field_name} at index {instance_index}")
                    return self.enter_nested_field(field_name, instance_index)
                    
                elif action_type == 'navigate_to_parent':
                    logger.info("Processing navigation to parent context")
                    return self.navigate_to_parent()
                    
                elif action_type == 'navigate_to_depth':
                    target_depth = pending_action.get('depth', 0)
                    logger.info(f"Processing navigation to depth {target_depth}")
                    return self.navigate_to_depth(target_depth)
                    
                elif action_type == 'add_instance':
                    field_name = pending_action.get('fieldName')
                    logger.info(f"Processing add instance for field: {field_name}")
                    return self.add_nested_instance(field_name)
                    
                elif action_type == 'create_new_instance':
                    field_name = pending_action.get('fieldName')
                    new_index = pending_action.get('newIndex', 0)
                    logger.info(f"Processing create new instance for field: {field_name} at index {new_index}")
                    return self.create_new_instance(field_name, new_index)
                    
            return False
            
        except Exception as e:
            logger.error(f"Error checking for nested actions: {e}")
            return False

    def get_nested_selection_hierarchy(self) -> Dict:
        """
        Get the complete nested selection hierarchy.
        
        Returns:
            Dictionary containing the full selection hierarchy
        """
        try:
            return self.nested_manager.export_all_selections()
        except Exception as e:
            logger.error(f"Error exporting nested selection hierarchy: {e}")
            return {}

    def get_current_context_info(self) -> Dict:
        """
        Get information about the current selection context.
        
        Returns:
            Dictionary with current context information
        """
        try:
            return {
                'depth': self.nested_manager.get_current_depth(),
                'breadcrumbs': self.nested_manager.get_breadcrumbs(),
                'depth_color': self.nested_manager.get_depth_color(),
                'available_fields': [
                    {
                        'name': field.name,
                        'label': field.label,
                        'type': field.type,
                        'description': field.description,
                        'has_sub_fields': field.sub_fields is not None
                    }
                    for field in self.nested_manager.get_current_fields()
                ]
            }
        except Exception as e:
            logger.error(f"Error getting current context info: {e}")
            return {}

    def load_page(self, url: str, wait_time: int = 10) -> bool:
        """
        Load a web page and wait for it to be ready.
        
        Args:
            url: URL to load
            wait_time: Maximum time to wait for page load
            
        Returns:
            True if page loaded successfully, False otherwise
        """
        if not self.driver:
            if not self.setup_driver():
                return False
        
        try:
            self.driver.get(url)
            
            # Wait for page to be ready
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Re-inject our JavaScript after page load
            time.sleep(2)  # Give page time to fully render
            self._inject_selection_js()
            
            # Track current URL and domain for site-specific selector storage
            self.current_url = url
            self.current_domain = self._get_domain_from_url(url)
            
            logger.info(f"Successfully loaded page: {url} (domain: {self.current_domain})")
            return True
            
        except TimeoutException:
            logger.error(f"Timeout loading page: {url}")
            return False
        except WebDriverException as e:
            logger.error(f"WebDriver error loading page {url}: {e}")
            return False
    
    def show_field_menu(self) -> bool:
        """
        Display the floating field selection menu for LabEquipmentPage fields.
        Enhanced with nested context support.
        
        Returns:
            True if menu displayed successfully
        """
        if not self.driver:
            logger.error("Driver not initialized")
            return False
        
        try:
            # Check for pending nested actions before showing menu
            self.check_for_nested_actions()
            
            self.driver.execute_script("window.showFieldMenu();")
            logger.info(f"Field selection menu displayed for depth {self.nested_manager.get_current_depth()}")
            return True
        except WebDriverException as e:
            logger.error(f"Failed to show field menu: {e}")
            return False
    
    def start_field_selection(self, field_name: str) -> bool:
        """
        Start field-specific selection mode for a LabEquipmentPage field.
        Enhanced with nested context support.
        
        Args:
            field_name: Name of the field to select content for
            
        Returns:
            True if field selection started successfully
        """
        if not self.driver:
            logger.error("Driver not initialized")
            return False
        
        # Get current available fields (may be different in nested context)
        current_fields = self.nested_manager.get_current_fields()
        valid_field_names = [field.name for field in current_fields]
        
        if field_name not in valid_field_names:
            logger.error(f"Invalid field name: {field_name} for current context. Valid fields: {valid_field_names}")
            return False
        
        try:
            # Check for nested field type
            field_obj = next((f for f in current_fields if f.name == field_name), None)
            
            if field_obj and field_obj.type == 'nested':
                # This is a nested field - enter nested context instead of starting selection
                logger.info(f"Entering nested context for field: {field_name}")
                return self.enter_nested_field(field_name, 0)
            else:
                # Regular field selection
                self.driver.execute_script(f"window.startFieldSelection('{field_name}');")
                self.selection_session_data['active_field'] = field_name
                logger.info(f"Started field selection for: {field_name} at depth {self.nested_manager.get_current_depth()}")
                return True
                
        except WebDriverException as e:
            logger.error(f"Failed to start field selection: {e}")
            return False

    def poll_for_nested_actions(self, timeout: float = 30.0) -> bool:
        """
        Poll for nested navigation actions from the JavaScript interface.
        
        Args:
            timeout: Maximum time to poll in seconds
            
        Returns:
            True if action was handled, False if timeout reached
        """
        if not self.driver:
            return False
            
        start_time = time.time()
        
        try:
            while time.time() - start_time < timeout:
                # Check for nested actions
                action_handled = self.check_for_nested_actions()
                
                if action_handled:
                    return True
                    
                # Small delay to avoid excessive polling
                time.sleep(0.1)
                
            logger.debug("Nested action polling timeout reached")
            return False
            
        except Exception as e:
            logger.error(f"Error during nested action polling: {e}")
            return False

    def start_selection(self, label: str) -> bool:
        """
        Start interactive selection mode for a specific content type.
        DEPRECATED: Use show_field_menu() and start_field_selection() instead.
        
        Args:
            label: Label for the content type being selected
            
        Returns:
            True if selection mode started successfully
        """
        logger.warning("start_selection() is deprecated. Use show_field_menu() for field-specific selection.")
        if not self.driver:
            logger.error("Driver not initialized")
            return False

        try:
            self.driver.execute_script(f"window.startSelection('{label}');")
            logger.info(f"Started selection mode for: {label}")
            return True
        except WebDriverException as e:
            logger.error(f"Failed to start selection mode: {e}")
            return False

    def stop_selection(self) -> List[Dict]:
        """
        Stop selection mode and return selected elements.
        
        Returns:
            List of selected element data
        """
        if not self.driver:
            return []
        
        try:
            # Stop selection mode
            self.driver.execute_script("window.stopSelection();")
            
            # Get selected elements
            selected = self.driver.execute_script("return window.getSelectedElements();")
            
            logger.info(f"Retrieved {len(selected)} selected elements")
            return selected or []
            
        except WebDriverException as e:
            logger.error(f"Failed to stop selection mode: {e}")
            return []
    
    def get_field_selections(self, field_name: str) -> List[Dict]:
        """
        Get selections for a specific field.
        
        Args:
            field_name: Name of the field to get selections for
            
        Returns:
            List of selections for the specified field
        """
        if not self.driver:
            return []
        
        try:
            selected = self.driver.execute_script(f"return window.getFieldSelections('{field_name}');")
            logger.info(f"Retrieved {len(selected)} selections for field: {field_name}")
            return selected or []
        except WebDriverException as e:
            logger.error(f"Failed to get field selections: {e}")
            return []
    
    def get_all_field_selections(self) -> Dict[str, List[Dict]]:
        """
        Get all selections organized by field name.
        
        Returns:
            Dictionary mapping field names to their selections
        """
        if not self.driver:
            return {}
        
        try:
            all_selections = self.driver.execute_script("return window.getAllFieldSelections();")
            logger.info(f"Retrieved selections for {len(all_selections)} fields")
            return all_selections or {}
        except WebDriverException as e:
            logger.error(f"Failed to get all field selections: {e}")
            return {}
    
    def clear_field_selections(self, field_name: str) -> bool:
        """
        Clear selections for a specific field.
        
        Args:
            field_name: Name of the field to clear selections for
            
        Returns:
            True if selections cleared successfully
        """
        if not self.driver:
            return False
        
        try:
            self.driver.execute_script(f"window.clearFieldSelections('{field_name}');")
            logger.info(f"Cleared selections for field: {field_name}")
            return True
        except WebDriverException as e:
            logger.error(f"Failed to clear field selections: {e}")
            return False
    
    def get_field_completion_status(self) -> Dict[str, Dict]:
        """
        Get completion status for all LabEquipmentPage fields.
        
        Returns:
            Dictionary with field completion information
        """
        if not self.driver:
            return {}
        
        try:
            all_selections = self.get_all_field_selections()
            status = {}
            
            for field in self.FIELD_OPTIONS:
                field_name = field['name']
                selections = all_selections.get(field_name, [])
                status[field_name] = {
                    'field_info': field,
                    'selection_count': len(selections),
                    'is_complete': len(selections) > 0,
                    'is_multi_value': field['type'] == 'multi-value',
                    'ready_for_generalization': field['type'] == 'multi-value' and len(selections) >= 2
                }
            
            logger.info(f"Generated completion status for {len(status)} fields")
            return status
            
        except Exception as e:
            logger.error(f"Failed to get field completion status: {e}")
            return {}

    def clear_selections(self):
        """Clear all current selections"""
        if self.driver:
            try:
                self.driver.execute_script("window.clearSelections();")
                self.selection_session_data = {
                    'active_field': None,
                    'field_selections': {},
                    'multi_value_examples': {}
                }
                logger.info("Cleared all selections")
            except WebDriverException as e:
                logger.error(f"Failed to clear selections: {e}")
    
    def get_page_info(self) -> Dict:
        """
        Get basic information about the current page.
        
        Returns:
            Dictionary with page title, URL, and other metadata
        """
        if not self.driver:
            return {}
        
        try:
            return {
                'title': self.driver.title,
                'url': self.driver.current_url,
                'page_source_length': len(self.driver.page_source)
            }
        except WebDriverException as e:
            logger.error(f"Failed to get page info: {e}")
            return {}
    
    def close(self):
        """Clean up and close the browser"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None

    def _get_domain_from_url(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.replace('www.', '')
        except Exception:
            return url

    def _get_or_create_field_session(self, domain: str) -> FieldSelectionSession:
        """Get or create field selection session for this domain"""
        if not self.field_session or self.field_session.domain != domain:
            self.field_session, created = FieldSelectionSession.objects.get_or_create(
                domain=domain,
                session_name=self.session_name,
                is_active=True,
                defaults={
                    'started_at': timezone.now(),
                }
            )
        return self.field_session

    def save_field_selector(self, field_name: str, xpath: str, css_selector: str = "", 
                           requires_manual_input: bool = False, manual_input_note: str = "") -> bool:
        """
        Save a field selector to the database for the current site.
        
        Args:
            field_name: Name of the LabEquipmentPage field
            xpath: XPath selector for the field
            css_selector: Optional CSS selector
            requires_manual_input: Whether this field requires manual input
            manual_input_note: Instructions for manual input
            
        Returns:
            bool: True if saved successfully
        """
        if not self.current_domain or not self.current_url:
            logger.error("No current domain/URL available for saving selector")
            return False
            
        try:
            # Get site name from domain
            site_name = self.current_domain.replace('.com', '').replace('.', ' ').title()
            
            # Create or update the selector
            selector, created = SiteFieldSelector.objects.update_or_create(
                domain=self.current_domain,
                field_name=field_name,
                defaults={
                    'site_name': site_name,
                    'xpath': xpath,
                    'css_selector': css_selector,
                    'requires_manual_input': requires_manual_input,
                    'manual_input_note': manual_input_note,
                    'created_from_url': self.current_url,
                    'created_at': timezone.now(),
                }
            )
            
            # Mark field as complete in session
            field_session = self._get_or_create_field_session(self.current_domain)
            field_session.mark_field_complete(field_name)
            
            action = "Created" if created else "Updated"
            logger.info(f"{action} selector for {self.current_domain}/{field_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save selector: {e}")
            return False

    def test_selector_on_page(self, selector: SiteFieldSelector, test_url: str) -> Dict:
        """
        Test a selector on a specific page and record results.
        
        Args:
            selector: SiteFieldSelector instance to test
            test_url: URL to test the selector on
            
        Returns:
            Dict: Test results with success status and extracted content
        """
        start_time = time.time()
        result = {
            'success': False,
            'result_type': 'error',
            'content': '',
            'error': '',
            'test_duration': 0.0
        }
        
        try:
            # Load the test page
            if not self.load_page(test_url):
                result['error'] = "Failed to load test page"
                return result
                
            # Test the XPath selector
            try:
                elements = self.driver.find_elements(By.XPATH, selector.xpath)
                
                if not elements:
                    result['result_type'] = 'no_match'
                    result['error'] = "Selector found no elements"
                else:
                    # Extract content from first matching element
                    element = elements[0]
                    content = element.text.strip() or element.get_attribute('innerHTML')
                    
                    if content:
                        result['success'] = True
                        result['result_type'] = 'success'
                        result['content'] = content
                    else:
                        result['result_type'] = 'invalid_content'
                        result['error'] = "Element found but contains no text content"
                        
            except Exception as e:
                result['result_type'] = 'error'
                result['error'] = f"XPath execution failed: {str(e)}"
                
        except Exception as e:
            result['error'] = f"Test execution failed: {str(e)}"
            
        finally:
            result['test_duration'] = time.time() - start_time
            
        # Save test result to database
        try:
            SelectorTestResult.objects.create(
                selector=selector,
                test_url=test_url,
                result=result['result_type'],
                extracted_content=result['content'],
                test_duration=result['test_duration'],
                error_message=result['error']
            )
        except Exception as e:
            logger.error(f"Failed to save test result: {e}")
            
        return result

    def test_all_selectors_on_page(self, test_url: str) -> Dict[str, Dict]:
        """
        Test all selectors for the current domain on a new page.
        
        Args:
            test_url: URL to test selectors on
            
        Returns:
            Dict: Results for each field {field_name: test_result}
        """
        if not self.current_domain:
            logger.error("No current domain available for testing")
            return {}
            
        # Get all selectors for this domain
        selectors = SiteFieldSelector.objects.filter(domain=self.current_domain)
        
        results = {}
        for selector in selectors:
            logger.info(f"Testing {selector.field_name} selector on {test_url}")
            results[selector.field_name] = self.test_selector_on_page(selector, test_url)
            
        return results

    def get_saved_selectors(self, domain: str = None) -> List[SiteFieldSelector]:
        """
        Get all saved selectors for a domain.
        
        Args:
            domain: Domain to get selectors for (uses current domain if None)
            
        Returns:
            List of SiteFieldSelector objects
        """
        domain = domain or self.current_domain
        if not domain:
            return []
            
        return list(SiteFieldSelector.objects.filter(domain=domain).order_by('field_name'))

    def get_selector_success_rates(self, domain: str = None) -> Dict[str, float]:
        """
        Get success rates for all selectors in a domain.
        
        Args:
            domain: Domain to get success rates for
            
        Returns:
            Dict: {field_name: success_rate}
        """
        selectors = self.get_saved_selectors(domain)
        return {
            selector.field_name: selector.success_rate 
            for selector in selectors
        }

    def get_manual_input_fields(self, domain: str = None) -> List[Dict]:
        """
        Get fields that require manual input for a domain.
        
        Args:
            domain: Domain to check (uses current domain if None)
            
        Returns:
            List of dicts with field info and manual input instructions
        """
        domain = domain or self.current_domain
        if not domain:
            return []
            
        manual_fields = SiteFieldSelector.objects.filter(
            domain=domain, 
            requires_manual_input=True
        )
        
        return [
            {
                'field_name': field.field_name,
                'field_label': field.get_field_name_display(),
                'manual_input_note': field.manual_input_note,
                'created_from_url': field.created_from_url
            }
            for field in manual_fields
        ]

    def mark_field_as_manual(self, field_name: str, manual_input_note: str) -> bool:
        """
        Mark a field as requiring manual input instead of automatic selection.
        
        Args:
            field_name: Name of the field to mark as manual
            manual_input_note: Instructions for manual input
            
        Returns:
            bool: True if successful
        """
        if not self.current_domain:
            logger.error("No current domain available")
            return False
            
        try:
            selector, created = SiteFieldSelector.objects.update_or_create(
                domain=self.current_domain,
                field_name=field_name,
                defaults={
                    'site_name': self.current_domain.replace('.com', '').replace('.', ' ').title(),
                    'xpath': '',  # No xpath needed for manual input
                    'css_selector': '',
                    'requires_manual_input': True,
                    'manual_input_note': manual_input_note,
                    'created_from_url': self.current_url or '',
                    'created_at': timezone.now(),
                }
            )
            
            # Mark field as complete in session
            field_session = self._get_or_create_field_session(self.current_domain)
            field_session.mark_field_complete(field_name)
            
            logger.info(f"Marked {field_name} as manual input for {self.current_domain}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark field as manual: {e}")
            return False

    def handle_control_panel_actions(self) -> Dict:
        """
        Monitor and handle control panel actions from JavaScript.
        
        Returns:
            Dict: Results of any pending actions
        """
        if not self.driver:
            return {}
            
        results = {}
        
        try:
            # Check for save action
            save_data = self.driver.execute_script("return window.saveFieldSelections;")
            if save_data:
                results['save'] = self._handle_save_action(save_data)
                # Clear the JavaScript variable
                self.driver.execute_script("window.saveFieldSelections = null;")
            
            # Check for test action
            test_data = self.driver.execute_script("return window.testFieldSelections;")
            if test_data:
                results['test'] = self._handle_test_action(test_data)
                # Clear the JavaScript variable
                self.driver.execute_script("window.testFieldSelections = null;")
            
            # Check for navigation action
            navigate_url = self.driver.execute_script("return window.navigateToUrl;")
            if navigate_url:
                results['navigate'] = self._handle_navigate_action(navigate_url)
                # Clear the JavaScript variable
                self.driver.execute_script("window.navigateToUrl = null;")
            
            # Check for similar pages search
            similar_pages_data = self.driver.execute_script("return window.findSimilarPages;")
            if similar_pages_data:
                results['similar_pages'] = self._handle_similar_pages_action(similar_pages_data)
                # Clear the JavaScript variable
                self.driver.execute_script("window.findSimilarPages = null;")
            
            # Check for test URLs loading
            test_urls_data = self.driver.execute_script("return window.loadTestUrls;")
            if test_urls_data:
                results['test_urls'] = self._handle_test_urls_action(test_urls_data)
                # Clear the JavaScript variable
                self.driver.execute_script("window.loadTestUrls = null;")
            
        except Exception as e:
            logger.error(f"Failed to handle control panel actions: {e}")
            results['error'] = str(e)
        
        return results

    def _handle_save_action(self, save_data: Dict) -> Dict:
        """Handle save action from control panel"""
        try:
            field_name = save_data.get('field')
            selections = save_data.get('selections', [])
            
            if not field_name or not selections:
                return {'success': False, 'error': 'Missing field name or selections'}
            
            # Save the most robust selector from the selections
            best_selection = self._choose_best_selector(selections)
            if not best_selection:
                return {'success': False, 'error': 'No valid selectors found'}
            
            success = self.save_field_selector(
                field_name=field_name,
                xpath=best_selection.get('xpath', ''),
                css_selector=best_selection.get('cssSelector', ''),
                requires_manual_input=False,
                manual_input_note=''
            )
            
            return {
                'success': success,
                'field': field_name,
                'selection_count': len(selections),
                'saved_selector': best_selection.get('xpath', '') if success else None
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _handle_test_action(self, test_data: Dict) -> Dict:
        """Handle test action from control panel"""
        try:
            fields = test_data.get('fields', [])
            domain = test_data.get('domain', '')
            
            if not fields:
                return {'success': False, 'error': 'No fields specified for testing'}
            
            # Get saved selectors for these fields
            saved_selectors = self.get_saved_selectors(domain)
            field_selectors = {s.field_name: s for s in saved_selectors if s.field_name in fields}
            
            if not field_selectors:
                return {'success': False, 'error': 'No saved selectors found for specified fields'}
            
            # Test on current page
            test_results = {}
            for field_name, selector in field_selectors.items():
                test_results[field_name] = self.test_selector_on_page(selector, self.current_url)
            
            return {
                'success': True,
                'tested_fields': list(field_selectors.keys()),
                'results': test_results,
                'test_url': self.current_url
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _handle_navigate_action(self, navigate_url: str) -> Dict:
        """Handle navigation action from control panel"""
        try:
            if not navigate_url or not navigate_url.strip():
                return {'success': False, 'error': 'No URL provided'}
            
            url = navigate_url.strip()
            if not (url.startswith('http://') or url.startswith('https://')):
                return {'success': False, 'error': 'Invalid URL format'}
            
            success = self.load_page(url)
            return {
                'success': success,
                'new_url': url,
                'page_title': self.driver.title if success and self.driver else None
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _handle_similar_pages_action(self, similar_data: Dict) -> Dict:
        """Handle similar pages search from control panel"""
        try:
            domain = similar_data.get('domain', '')
            current_path = similar_data.get('currentPath', '')
            
            # This would typically involve web scraping or sitemap analysis
            # For now, provide a basic response with common patterns
            suggested_urls = self._generate_similar_page_suggestions(domain, current_path)
            
            return {
                'success': True,
                'domain': domain,
                'current_path': current_path,
                'suggested_urls': suggested_urls
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _handle_test_urls_action(self, test_urls_data: Dict) -> Dict:
        """Handle test URLs loading from control panel"""
        try:
            domain = test_urls_data.get('domain', '')
            
            # Load test URLs from file system or database
            test_urls = self._load_test_urls_for_domain(domain)
            
            return {
                'success': True,
                'domain': domain,
                'test_urls': test_urls
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _choose_best_selector(self, selections: List[Dict]) -> Dict:
        """Choose the most robust selector from multiple selections"""
        if not selections:
            return {}
        
        # For now, choose the first selection with valid XPath
        for selection in selections:
            if selection.get('xpath') and selection.get('xpath').strip():
                return selection
        
        return selections[0] if selections else {}

    def _generate_similar_page_suggestions(self, domain: str, current_path: str) -> List[str]:
        """Generate suggestions for similar pages on the same domain"""
        base_url = f"https://{domain}"
        suggestions = []
        
        # Common e-commerce patterns
        common_patterns = [
            "/products",
            "/category",
            "/shop",
            "/catalog",
            "/equipment",
            "/instruments",
            "/search"
        ]
        
        for pattern in common_patterns:
            if pattern not in current_path:
                suggestions.append(f"{base_url}{pattern}")
        
        # Add numbered variations if current path has numbers
        import re
        if re.search(r'\d+', current_path):
            base_path = re.sub(r'\d+', '', current_path)
            for i in range(1, 6):
                suggestions.append(f"{base_url}{base_path}{i}")
        
        return suggestions[:10]  # Limit to 10 suggestions

    def _load_test_urls_for_domain(self, domain: str) -> List[str]:
        """Load test URLs for a specific domain"""
        test_urls = []
        
        try:
            # Check for domain-specific test URLs in project management
            import os
            test_urls_dir = ".project_management/test_urls/"
            
            if os.path.exists(test_urls_dir):
                for filename in os.listdir(test_urls_dir):
                    if domain.replace('.', '_') in filename and filename.endswith('.txt'):
                        filepath = os.path.join(test_urls_dir, filename)
                        with open(filepath, 'r') as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith('#') and domain in line:
                                    test_urls.append(line)
        
        except Exception as e:
            logger.error(f"Failed to load test URLs: {e}")
        
        return test_urls[:20]  # Limit to 20 URLs

    def update_control_panel_progress(self) -> bool:
        """Update the control panel progress indicator"""
        if not self.driver:
            return False
        
        try:
            # Get current completion status
            completion_status = self.get_field_completion_status()
            completed_count = sum(1 for status in completion_status.values() if status.get('is_complete', False))
            total_fields = len(self.FIELD_OPTIONS)
            progress_percentage = round((completed_count / total_fields) * 100)
            
            # Update the control panel if it exists
            self.driver.execute_script(f"""
                const controlPanel = document.getElementById('field-menu-toggle');
                if (controlPanel) {{
                    const progressText = controlPanel.querySelector('[style*="Overall Progress"]');
                    const progressBar = controlPanel.querySelector('[style*="background: linear-gradient(90deg, #27ae60, #2ecc71)"]');
                    
                    if (progressText && progressText.nextElementSibling) {{
                        progressText.nextElementSibling.textContent = '{completed_count}/{total_fields} ({progress_percentage}%)';
                    }}
                    
                    if (progressBar) {{
                        progressBar.style.width = '{progress_percentage}%';
                    }}
                }}
            """)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update control panel progress: {e}")
            return False
            return False

    def add_nested_instance(self, field_name: str) -> bool:
        """
        Add a new instance of a nested field (e.g., models[1] after models[0]).
        
        Args:
            field_name: Name of the nested field to add an instance for
            
        Returns:
            True if instance was added successfully
        """
        try:
            # Get current context info to determine the next instance index
            context = self.get_current_context_info()
            breadcrumbs = context.get('breadcrumbs', [])
            
            if len(breadcrumbs) < 2:
                logger.warning("Cannot add instance - not in nested context")
                return False
            
            # Parse current instance from breadcrumb (e.g., "models[0]" -> 0)
            current_breadcrumb = breadcrumbs[-1]
            if '[' not in current_breadcrumb or ']' not in current_breadcrumb:
                logger.warning(f"Cannot parse instance from breadcrumb: {current_breadcrumb}")
                return False
            
            # Extract field name and current index
            bracket_start = current_breadcrumb.find('[')
            bracket_end = current_breadcrumb.find(']')
            current_field = current_breadcrumb[:bracket_start]
            current_index = int(current_breadcrumb[bracket_start+1:bracket_end])
            
            # Verify we're adding an instance of the same field
            if current_field != field_name:
                logger.warning(f"Field mismatch: current={current_field}, requested={field_name}")
                return False
            
            # Navigate back to parent, then enter the new instance
            next_index = current_index + 1
            
            if self.navigate_to_parent():
                success = self.enter_nested_field(field_name, next_index)
                if success:
                    logger.info(f"Added new instance: {field_name}[{next_index}]")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error adding nested instance for '{field_name}': {e}")
            return False

    def create_new_instance(self, field_name: str, new_index: int) -> bool:
        """
        Create a new instance of a nested field (e.g., models[1] after models[0]).
        
        Args:
            field_name: Name of the nested field to add an instance for
            new_index: Index for the new instance
            
        Returns:
            True if instance was added successfully
        """
        try:
            # Get current context info to determine the next instance index
            context = self.get_current_context_info()
            breadcrumbs = context.get('breadcrumbs', [])
            
            if len(breadcrumbs) < 2:
                logger.warning("Cannot add instance - not in nested context")
                return False
            
            # Parse current instance from breadcrumb (e.g., "models[0]" -> 0)
            current_breadcrumb = breadcrumbs[-1]
            if '[' not in current_breadcrumb or ']' not in current_breadcrumb:
                logger.warning(f"Cannot parse instance from breadcrumb: {current_breadcrumb}")
                return False
            
            # Extract field name and current index
            bracket_start = current_breadcrumb.find('[')
            bracket_end = current_breadcrumb.find(']')
            current_field = current_breadcrumb[:bracket_start]
            current_index = int(current_breadcrumb[bracket_start+1:bracket_end])
            
            # Verify we're adding an instance of the same field
            if current_field != field_name:
                logger.warning(f"Field mismatch: current={current_field}, requested={field_name}")
                return False
            
            # Navigate back to parent, then enter the new instance
            next_index = current_index + 1
            
            if self.navigate_to_parent():
                success = self.enter_nested_field(field_name, next_index)
                if success:
                    logger.info(f"Added new instance: {field_name}[{next_index}]")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error adding nested instance for '{field_name}': {e}")
            return False