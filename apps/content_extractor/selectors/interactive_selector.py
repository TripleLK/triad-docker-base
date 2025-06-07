"""
Interactive Selector for Content Extraction

Uses Selenium to display web pages and capture user selections
for generating robust content selectors with field-specific assignment.
Enhanced with floating field selection menu for LabEquipmentPage model.

Created by: Phoenix Velocity
Date: 2025-01-08
Enhanced by: Quantum Catalyst  
Date: 2025-01-08
Project: Triad Docker Base
"""

import time
import json
from typing import Dict, List, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import logging

logger = logging.getLogger(__name__)


class InteractiveSelector:
    """Manages Selenium-based interactive element selection with field-specific assignment"""
    
    # LabEquipmentPage fields available for selection
    FIELD_OPTIONS = [
        {'name': 'title', 'label': 'Title', 'type': 'single', 'description': 'Equipment main title'},
        {'name': 'short_description', 'label': 'Short Description', 'type': 'single', 'description': 'Brief equipment summary'},
        {'name': 'full_description', 'label': 'Full Description', 'type': 'single', 'description': 'Detailed equipment description'},
        {'name': 'specification_confidence', 'label': 'Specification Confidence', 'type': 'single', 'description': 'Confidence level (low/medium/high)'},
        {'name': 'needs_review', 'label': 'Needs Review', 'type': 'single', 'description': 'Review flag indicator'},
        {'name': 'source_url', 'label': 'Source URL', 'type': 'single', 'description': 'Original product page URL'},
        {'name': 'source_type', 'label': 'Source Type', 'type': 'single', 'description': 'New/Used/Refurbished indicator'},
        {'name': 'data_completeness', 'label': 'Data Completeness', 'type': 'single', 'description': 'Completeness score'},
        {'name': 'models', 'label': 'Models', 'type': 'multi-value', 'description': 'Product model variations'},
        {'name': 'features', 'label': 'Features', 'type': 'multi-value', 'description': 'Equipment features list'},
        {'name': 'accessories', 'label': 'Accessories', 'type': 'multi-value', 'description': 'Related accessories/parts'},
        {'name': 'categorized_tags', 'label': 'Categorized Tags', 'type': 'multi-value', 'description': 'Category and tag assignments'},
        {'name': 'gallery_images', 'label': 'Gallery Images', 'type': 'multi-value', 'description': 'Product image gallery'},
        {'name': 'spec_groups', 'label': 'Specification Groups', 'type': 'multi-value', 'description': 'Technical specifications with nested specs'}
    ]
    
    def __init__(self, headless: bool = False):
        """
        Initialize the interactive selector.
        
        Args:
            headless: Whether to run browser in headless mode
        """
        self.headless = headless
        self.driver = None
        self.selected_elements = []
        self.selection_session_data = {
            'active_field': None,
            'field_selections': {},  # field_name -> [selections]
            'multi_value_examples': {}  # field_name -> [example1, example2]
        }
    
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
        """Inject enhanced JavaScript for field-specific element selection"""
        # Create field options JavaScript array
        field_options_js = json.dumps(self.FIELD_OPTIONS)
        
        selection_js = f"""
        window.contentExtractorData = {{
            selectedElements: [],
            selectedDOMElements: new Set(),
            isSelectionMode: false,
            currentLabel: '',
            activeField: null,
            fieldSelections: {{}},
            multiValueExamples: {{}},
            fieldOptions: {field_options_js}
        }};
        
        // Field-specific highlight colors
        const FIELD_COLORS = {{
            'title': '#ff6b6b',
            'short_description': '#4ecdc4', 
            'full_description': '#45b7d1',
            'specification_confidence': '#96ceb4',
            'needs_review': '#ffeaa7',
            'source_url': '#dda0dd',
            'source_type': '#98d8c8',
            'data_completeness': '#f7dc6f',
            'models': '#bb8fce',
            'features': '#85c1e9',
            'accessories': '#f8c471',
            'categorized_tags': '#82e0aa',
            'gallery_images': '#f1948a',
            'spec_groups': '#aed6f1'
        }};
        
        // Get field color or default
        function getFieldColor(fieldName) {{
            return FIELD_COLORS[fieldName] || '#007bff';
        }}
        
        // Highlight element on hover (enhanced visibility)
        function highlightElement(element) {{
            if (!window.contentExtractorData.selectedDOMElements.has(element)) {{
                const color = getFieldColor(window.contentExtractorData.activeField);
                element.style.outline = `4px solid ${{color}}`;
                element.style.backgroundColor = `${{color}}44`;
                element.style.boxShadow = `0 0 8px ${{color}}88`;
                element.style.zIndex = '9999';
                element.style.position = 'relative';
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
            }}
        }}
        
        // Mark element as selected with enhanced persistent styling
        function markAsSelected(element, fieldName) {{
            window.contentExtractorData.selectedDOMElements.add(element);
            const color = getFieldColor(fieldName);
            element.style.outline = `4px solid ${{color}}`;
            element.style.backgroundColor = `${{color}}66`;
            element.style.boxShadow = `0 0 12px ${{color}}aa`;
            element.style.position = 'relative';
            element.style.zIndex = '9998';
            element.setAttribute('data-content-extractor-selected', 'true');
            element.setAttribute('data-field-name', fieldName);
            
            // Add a small indicator badge
            const badge = document.createElement('div');
            badge.setAttribute('data-selection-badge', fieldName);
            badge.setAttribute('data-content-extractor-ui', 'true');
            badge.style.cssText = `
                position: absolute !important;
                top: -8px !important;
                right: -8px !important;
                background: ${{color}} !important;
                color: white !important;
                border-radius: 50% !important;
                width: 20px !important;
                height: 20px !important;
                font-size: 10px !important;
                font-weight: bold !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                z-index: 10000 !important;
                border: 2px solid white !important;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3) !important;
                font-family: 'Segoe UI', Arial, sans-serif !important;
            `;
            badge.textContent = '✓';
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
        
        // Create floating field selection menu
        function createFieldSelectionMenu() {{
            const menu = document.createElement('div');
            menu.id = 'field-selection-menu';
            menu.setAttribute('data-content-extractor-ui', 'true');
            menu.style.cssText = `
                position: fixed !important;
                top: 20px !important;
                left: 20px !important;
                background: linear-gradient(135deg, #2c3e50, #34495e) !important;
                color: white !important;
                padding: 25px !important;
                border-radius: 12px !important;
                z-index: 10001 !important;
                font-family: 'Segoe UI', Arial, sans-serif !important;
                font-size: 14px !important;
                max-width: 380px !important;
                box-shadow: 0 8px 24px rgba(0,0,0,0.5) !important;
                max-height: 85vh !important;
                overflow-y: auto !important;
                border: 2px solid #3498db !important;
            `;
            
            let menuHTML = `
                <div style="border-bottom: 2px solid #3498db !important; padding-bottom: 18px !important; margin-bottom: 18px !important;">
                    <h3 style="margin: 0 !important; color: #ecf0f1 !important; font-size: 18px !important; font-weight: 600 !important; font-family: 'Segoe UI', Arial, sans-serif !important;">🎯 Field Selection</h3>
                    <p style="margin: 8px 0 0 0 !important; font-size: 13px !important; color: #bdc3c7 !important; line-height: 1.4 !important; font-family: 'Segoe UI', Arial, sans-serif !important;">Choose which LabEquipmentPage field you want to select content for:</p>
                </div>
                <div id="field-options">
            `;
            
            // Get current field selections for status indicators
            const currentSelections = window.contentExtractorData.fieldSelections;
            
            // Group fields by type
            const singleFields = window.contentExtractorData.fieldOptions.filter(f => f.type === 'single');
            const multiFields = window.contentExtractorData.fieldOptions.filter(f => f.type === 'multi-value');
            
            // Single value fields
            menuHTML += `<div style="margin-bottom: 25px !important;">
                <h4 style="margin: 0 0 12px 0 !important; color: #3498db !important; font-size: 15px !important; font-weight: 600 !important; font-family: 'Segoe UI', Arial, sans-serif !important;">📄 Single Value Fields</h4>
            `;
            singleFields.forEach(field => {{
                const color = getFieldColor(field.name);
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
            
            // Multi-value fields
            menuHTML += `<div>
                <h4 style="margin: 0 0 12px 0 !important; color: #e74c3c !important; font-size: 15px !important; font-weight: 600 !important; font-family: 'Segoe UI', Arial, sans-serif !important;">📋 Multi-Value Fields</h4>
                <p style="font-size: 11px !important; color: #95a5a6 !important; margin: 0 0 12px 0 !important; padding: 8px !important; background: rgba(231,76,60,0.1) !important; border-radius: 6px !important; border-left: 3px solid #e74c3c !important; font-family: 'Segoe UI', Arial, sans-serif !important;">💡 Select 2+ examples for pattern generation</p>
            `;
            multiFields.forEach(field => {{
                const color = getFieldColor(field.name);
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
            
            // Summary section
            const completedCount = Object.keys(currentSelections).filter(k => currentSelections[k].length > 0).length;
            const totalFields = window.contentExtractorData.fieldOptions.length;
            
            menuHTML += `</div>
                <div style="margin-top: 25px !important; border-top: 2px solid #34495e !important; padding-top: 18px !important;">
                    <div style="background: rgba(52,152,219,0.1) !important; padding: 12px !important; border-radius: 8px !important; margin-bottom: 15px !important; border-left: 4px solid #3498db !important;">
                        <div style="font-size: 13px !important; font-weight: 600 !important; color: #3498db !important;">Progress: ${{completedCount}}/${{totalFields}} fields completed</div>
                        <div style="font-size: 11px !important; color: #bdc3c7 !important; margin-top: 4px !important;">Fields with at least one selection</div>
                    </div>
                    <div style="display: flex !important; gap: 10px !important;">
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
                        <button id="clear-all-selections" style="
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
                        " onmouseover="this.style.backgroundColor='#7f8c8d'" onmouseout="this.style.backgroundColor='#95a5a6'">Clear All</button>
                    </div>
                </div>
            `;
            
            menu.innerHTML = menuHTML;
            return menu;
        }}
        
        // Show field selection menu
        window.showFieldMenu = function() {{
            // Remove existing menu if present
            const existingMenu = document.getElementById('field-selection-menu');
            if (existingMenu) {{
                existingMenu.remove();
            }}
            
            const menu = createFieldSelectionMenu();
            document.body.appendChild(menu);
            
            // Add event listeners to prevent interference
            menu.addEventListener('mouseenter', function(e) {{ e.stopPropagation(); }});
            menu.addEventListener('mouseleave', function(e) {{ e.stopPropagation(); }});
            menu.addEventListener('click', function(e) {{ e.stopPropagation(); }});
            
            // Add event listeners for field selection
            menu.querySelectorAll('.field-option').forEach(button => {{
                button.addEventListener('click', function() {{
                    const fieldName = this.getAttribute('data-field');
                    selectField(fieldName);
                }});
            }});
            
            // Close menu button
            document.getElementById('close-field-menu').addEventListener('click', function() {{
                menu.remove();
            }});
            
            // Clear all selections button
            document.getElementById('clear-all-selections').addEventListener('click', function() {{
                if (confirm('Clear all field selections? This cannot be undone.')) {{
                    window.clearSelections();
                    menu.remove();
                    window.showFieldMenu(); // Refresh menu to show updated status
                }}
            }});
        }};
        
        // Select a field and start content selection
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
            
            // Create floating menu toggle button
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
            
            const toggle = document.createElement('div');
            toggle.id = 'field-menu-toggle';
            toggle.setAttribute('data-content-extractor-ui', 'true');
            toggle.style.cssText = `
                position: fixed !important;
                bottom: 20px !important;
                left: 20px !important;
                background: linear-gradient(135deg, #3498db, #2980b9) !important;
                color: white !important;
                padding: 12px 16px !important;
                border-radius: 50px !important;
                z-index: 10002 !important;
                font-family: 'Segoe UI', Arial, sans-serif !important;
                font-size: 14px !important;
                font-weight: 600 !important;
                cursor: pointer !important;
                box-shadow: 0 4px 12px rgba(52,152,219,0.4) !important;
                border: 2px solid white !important;
                transition: all 0.3s ease !important;
                user-select: none !important;
            `;
            
            toggle.innerHTML = `
                <div style="display: flex !important; align-items: center !important; gap: 8px !important;">
                    <span>📋</span>
                    <div style="display: flex !important; flex-direction: column !important; align-items: flex-start !important;">
                        <span style="font-size: 12px !important; opacity: 0.8 !important; color: white !important;">Current Field:</span>
                        <span style="font-size: 13px !important; font-weight: 700 !important; color: white !important;">${{window.contentExtractorData.activeField || 'None'}}</span>
                    </div>
                </div>
            `;
            
            // Add click handler to show field menu
            toggle.addEventListener('click', function(e) {{
                e.stopPropagation();
                window.showFieldMenu();
                // Keep the toggle visible for easy access
            }});
            
            // Add event listeners to prevent interference
            toggle.addEventListener('mouseenter', function(e) {{ 
                e.stopPropagation();
                this.style.transform = 'translateY(-2px)';
                this.style.boxShadow = '0 6px 16px rgba(52,152,219,0.6)';
                this.style.background = 'linear-gradient(135deg, #2980b9, #3498db)';
            }});
            
            toggle.addEventListener('mouseleave', function(e) {{ 
                e.stopPropagation();
                this.style.transform = 'translateY(0)';
                this.style.boxShadow = '0 4px 12px rgba(52,152,219,0.4)';
                this.style.background = 'linear-gradient(135deg, #3498db, #2980b9)';
            }});
            
            document.body.appendChild(toggle);
        }}
        
        // Remove floating menu toggle
        function removeFloatingMenuToggle() {{
            const toggle = document.getElementById('field-menu-toggle');
            if (toggle) {{
                toggle.remove();
            }}
        }}
        
        // Start field-specific selection mode
        window.startFieldSelection = function(fieldName) {{
            window.contentExtractorData.isSelectionMode = true;
            window.contentExtractorData.activeField = fieldName;
            
            // Find field info
            const fieldInfo = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
            
            document.addEventListener('mouseover', handleMouseOver);
            document.addEventListener('mouseout', handleMouseOut);
            document.addEventListener('click', handleClick);
            
            // Show field-specific instructions
            showFieldInstructions(fieldInfo);
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
                
                // Handle multi-value field logic
                const fieldInfo = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
                if (fieldInfo && fieldInfo.type === 'multi-value') {{
                    handleMultiValueSelection(fieldName, selection);
                }}
            }}
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
                    <div style="font-weight: 600 !important; margin-bottom: 6px !important; color: white !important;">📍 How to select:</div>
                    <div style="color: white !important;">• <strong>Hover</strong> over elements to preview</div>
                    <div style="color: white !important;">• <strong>Click</strong> elements to select them</div>
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
        """
        
        self.driver.execute_script(selection_js)
    
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
            
            logger.info(f"Successfully loaded page: {url}")
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
        
        Returns:
            True if menu displayed successfully
        """
        if not self.driver:
            logger.error("Driver not initialized")
            return False
        
        try:
            self.driver.execute_script("window.showFieldMenu();")
            logger.info("Field selection menu displayed")
            return True
        except WebDriverException as e:
            logger.error(f"Failed to show field menu: {e}")
            return False
    
    def start_field_selection(self, field_name: str) -> bool:
        """
        Start field-specific selection mode for a LabEquipmentPage field.
        
        Args:
            field_name: Name of the field to select content for
            
        Returns:
            True if field selection started successfully
        """
        if not self.driver:
            logger.error("Driver not initialized")
            return False
        
        # Validate field name
        valid_fields = [field['name'] for field in self.FIELD_OPTIONS]
        if field_name not in valid_fields:
            logger.error(f"Invalid field name: {field_name}. Valid fields: {valid_fields}")
            return False
        
        try:
            self.driver.execute_script(f"window.startFieldSelection('{field_name}');")
            self.selection_session_data['active_field'] = field_name
            logger.info(f"Started field selection for: {field_name}")
            return True
        except WebDriverException as e:
            logger.error(f"Failed to start field selection: {e}")
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