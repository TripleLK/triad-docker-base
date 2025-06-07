"""
UI Components for Interactive Selector

Handles JavaScript injection, menu generation, and browser UI interactions
for the content extraction system.

Created by: Swift Navigator
Date: 2025-01-08
Project: Triad Docker Base
"""

import json
from typing import Dict, List, Optional


class UIComponentManager:
    """Manages UI components and JavaScript injection for interactive selection"""
    
    def __init__(self, nested_manager=None):
        """Initialize UI component manager with nested selection context"""
        self.nested_manager = nested_manager
    
    def generate_selection_javascript(self) -> str:
        """Generate the complete JavaScript for element selection and UI interaction"""
        
        # Get current fields from nested manager if available
        current_fields = []
        current_depth = 0
        depth_color = '#3498db'
        breadcrumbs = ['Root']
        
        if self.nested_manager:
            current_fields = self.nested_manager.get_current_fields()
            current_depth = self.nested_manager.get_current_depth()
            depth_color = self.nested_manager.get_depth_color()
            breadcrumbs = self.nested_manager.get_breadcrumbs()
        
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
        
        return f"""
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
            nestedContexts: {{}}
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
        
        {self._get_field_menu_javascript()}
        
        {self._get_instance_management_javascript()}
        
        {self._get_event_handlers_javascript()}
        """
    
    def _get_field_menu_javascript(self) -> str:
        """Generate JavaScript for the field selection menu"""
        return """
        // Create enhanced field selection menu with nested context support
        function createFieldSelectionMenu() {
            const menu = document.createElement('div');
            menu.id = 'field-selection-menu';
            menu.setAttribute('data-content-extractor-ui', 'true');
            menu.style.cssText = `
                position: fixed !important;
                top: 20px !important;
                right: 20px !important;
                background: rgba(44, 62, 80, 0.95) !important;
                border: 2px solid ${getDepthColor(window.contentExtractorData.currentDepth)} !important;
                border-radius: 12px !important;
                padding: 16px !important;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
                backdrop-filter: blur(10px) !important;
                z-index: 10000 !important;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
                width: 320px !important;
                max-height: 80vh !important;
                overflow-y: auto !important;
            `;
            
            // Add breadcrumb navigation
            menu.innerHTML = createBreadcrumbNavigation();
            
            // Add field options
            const fieldOptionsHTML = createFieldOptionsHTML();
            menu.innerHTML += fieldOptionsHTML;
            
            // Add control buttons
            const controlButtonsHTML = createControlButtonsHTML();
            menu.innerHTML += controlButtonsHTML;
            
            return menu;
        }
        
        // Create field options HTML
        function createFieldOptionsHTML() {
            const fields = window.contentExtractorData.fieldOptions;
            const currentDepth = window.contentExtractorData.currentDepth;
            
            let html = `
                <div style="margin-bottom: 16px !important;">
                    <div style="color: #ecf0f1 !important; font-size: 14px !important; font-weight: 600 !important; margin-bottom: 12px !important;">
                        🎯 Select Field Type
                    </div>
                    <div style="display: grid !important; gap: 8px !important;">
            `;
            
            fields.forEach(field => {
                const isNested = field.has_sub_fields;
                const icon = isNested ? '🏗️' : (field.type === 'multi-value' ? '📋' : '📄');
                
                html += `
                    <button 
                        onclick="selectField('${field.name}')" 
                        style="
                            background: linear-gradient(135deg, rgba(52, 152, 219, 0.8), rgba(52, 152, 219, 0.6)) !important;
                            border: 1px solid rgba(52, 152, 219, 0.4) !important;
                            color: white !important;
                            padding: 12px 16px !important;
                            border-radius: 8px !important;
                            cursor: pointer !important;
                            transition: all 0.2s ease !important;
                            font-size: 13px !important;
                            text-align: left !important;
                            width: 100% !important;
                            display: flex !important;
                            align-items: center !important;
                            gap: 8px !important;
                        "
                        onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(52,152,219,0.4)'"
                        onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'"
                    >
                        <span style="font-size: 16px !important;">${icon}</span>
                        <div style="flex: 1 !important;">
                            <div style="font-weight: 600 !important;">${field.label}</div>
                            <div style="font-size: 11px !important; opacity: 0.8 !important; margin-top: 2px !important;">
                                ${field.description}
                            </div>
                        </div>
                        ${isNested ? '<span style="font-size: 12px !important; opacity: 0.7 !important;">Nested →</span>' : ''}
                    </button>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
            
            return html;
        }
        
        // Create control buttons HTML
        function createControlButtonsHTML() {
            const currentDepth = window.contentExtractorData.currentDepth;
            
            let html = `
                <div style="border-top: 1px solid rgba(255,255,255,0.1) !important; padding-top: 12px !important; display: flex !important; gap: 8px !important; flex-wrap: wrap !important;">
            `;
            
            // Parent navigation button (if not at root)
            if (currentDepth > 0) {
                html += `
                    <button 
                        onclick="navigateToParent()" 
                        style="
                            background: rgba(231, 76, 60, 0.8) !important;
                            border: 1px solid rgba(231, 76, 60, 0.4) !important;
                            color: white !important;
                            padding: 8px 12px !important;
                            border-radius: 6px !important;
                            cursor: pointer !important;
                            font-size: 12px !important;
                            transition: all 0.2s ease !important;
                            flex: 1 !important;
                        "
                        onmouseover="this.style.backgroundColor='rgba(231, 76, 60, 1)'"
                        onmouseout="this.style.backgroundColor='rgba(231, 76, 60, 0.8)'"
                    >
                        ⬆️ Parent
                    </button>
                `;
            }
            
            // Close menu button
            html += `
                <button 
                    onclick="closeFieldMenu()" 
                    style="
                        background: rgba(149, 165, 166, 0.8) !important;
                        border: 1px solid rgba(149, 165, 166, 0.4) !important;
                        color: white !important;
                        padding: 8px 12px !important;
                        border-radius: 6px !important;
                        cursor: pointer !important;
                        font-size: 12px !important;
                        transition: all 0.2s ease !important;
                        flex: 1 !important;
                    "
                    onmouseover="this.style.backgroundColor='rgba(149, 165, 166, 1)'"
                    onmouseout="this.style.backgroundColor='rgba(149, 165, 166, 0.8)'"
                >
                    ❌ Close
                </button>
            `;
            
            html += `</div>`;
            return html;
        }
        """
    
    def _get_instance_management_javascript(self) -> str:
        """Generate JavaScript for instance management (NEW for 3-level hierarchy)"""
        return """
        // NEW: Show instance management menu (Level 2 in 3-level hierarchy)
        function showInstanceManagementMenu(fieldName) {
            // Remove existing menu
            const existingMenu = document.getElementById('field-selection-menu');
            if (existingMenu) {
                existingMenu.remove();
            }
            
            const menu = document.createElement('div');
            menu.id = 'field-selection-menu';
            menu.setAttribute('data-content-extractor-ui', 'true');
            menu.style.cssText = `
                position: fixed !important;
                top: 20px !important;
                right: 20px !important;
                background: rgba(44, 62, 80, 0.95) !important;
                border: 2px solid ${getDepthColor(1)} !important;
                border-radius: 12px !important;
                padding: 16px !important;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
                backdrop-filter: blur(10px) !important;
                z-index: 10000 !important;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
                width: 320px !important;
                max-height: 80vh !important;
                overflow-y: auto !important;
            `;
            
            // Instance management HTML
            let html = `
                <div style="
                    background: rgba(52,73,94,0.95) !important;
                    padding: 8px 12px !important;
                    border-radius: 6px !important;
                    margin-bottom: 12px !important;
                    border-left: 4px solid ${getDepthColor(1)} !important;
                ">
                    <div style="font-size: 11px !important; color: #bdc3c7 !important; margin-bottom: 4px !important;">Navigation Path (Depth: 1)</div>
                    <div style="display: flex !important; align-items: center !important; gap: 4px !important;">
                        <span style="color: #ecf0f1 !important; font-size: 12px !important; cursor: pointer !important;" onclick="navigateToDepth(0)">Root</span>
                        <span style="color: #7f8c8d !important; font-size: 10px !important;">→</span>
                        <span style="color: #3498db !important; font-weight: 600 !important; font-size: 12px !important;">${fieldName}</span>
                    </div>
                </div>
                
                <div style="margin-bottom: 16px !important;">
                    <div style="color: #ecf0f1 !important; font-size: 14px !important; font-weight: 600 !important; margin-bottom: 12px !important;">
                        📋 Manage ${fieldName} Instances
                    </div>
                    <div style="display: grid !important; gap: 8px !important;" id="instance-buttons-container">
                        <!-- Instance buttons will be populated here -->
                    </div>
                </div>
                
                <div style="border-top: 1px solid rgba(255,255,255,0.1) !important; padding-top: 12px !important; display: flex !important; gap: 8px !important;">
                    <button 
                        onclick="navigateToDepth(0)" 
                        style="
                            background: rgba(231, 76, 60, 0.8) !important;
                            border: 1px solid rgba(231, 76, 60, 0.4) !important;
                            color: white !important;
                            padding: 8px 12px !important;
                            border-radius: 6px !important;
                            cursor: pointer !important;
                            font-size: 12px !important;
                            flex: 1 !important;
                        "
                    >⬆️ Parent</button>
                    <button 
                        onclick="closeFieldMenu()" 
                        style="
                            background: rgba(149, 165, 166, 0.8) !important;
                            border: 1px solid rgba(149, 165, 166, 0.4) !important;
                            color: white !important;
                            padding: 8px 12px !important;
                            border-radius: 6px !important;
                            cursor: pointer !important;
                            font-size: 12px !important;
                            flex: 1 !important;
                        "
                    >❌ Close</button>
                </div>
            `;
            
            menu.innerHTML = html;
            document.body.appendChild(menu);
            
            // Populate instance buttons
            populateInstanceButtons(fieldName);
        }
        
        // NEW: Populate instance buttons for a field
        function populateInstanceButtons(fieldName) {
            const container = document.getElementById('instance-buttons-container');
            if (!container) return;
            
            // For now, show existing instances (this should be populated from backend data)
            // This is a placeholder - actual implementation should get instance data from Python
            const existingInstances = getExistingInstances(fieldName);
            
            let buttonsHTML = '';
            
            // Add existing instance buttons
            existingInstances.forEach((instance, index) => {
                buttonsHTML += `
                    <button 
                        onclick="enterSpecificInstance('${fieldName}', ${index})" 
                        style="
                            background: linear-gradient(135deg, rgba(52, 152, 219, 0.8), rgba(52, 152, 219, 0.6)) !important;
                            border: 1px solid rgba(52, 152, 219, 0.4) !important;
                            color: white !important;
                            padding: 12px 16px !important;
                            border-radius: 8px !important;
                            cursor: pointer !important;
                            transition: all 0.2s ease !important;
                            font-size: 13px !important;
                            text-align: left !important;
                            width: 100% !important;
                        "
                    >
                        📄 ${fieldName}[${index}]
                    </button>
                `;
            });
            
            // Add "Add New Instance" button
            buttonsHTML += `
                <button 
                    onclick="addNewInstance('${fieldName}')" 
                    style="
                        background: linear-gradient(135deg, rgba(243, 156, 18, 0.8), rgba(243, 156, 18, 0.6)) !important;
                        border: 1px solid rgba(243, 156, 18, 0.4) !important;
                        color: white !important;
                        padding: 12px 16px !important;
                        border-radius: 8px !important;
                        cursor: pointer !important;
                        transition: all 0.2s ease !important;
                        font-size: 13px !important;
                        text-align: center !important;
                        width: 100% !important;
                        border-style: dashed !important;
                    "
                    onmouseover="this.style.transform='translateY(-2px)'"
                    onmouseout="this.style.transform='translateY(0)'"
                >
                    ➕ Add New ${fieldName} Instance
                </button>
            `;
            
            container.innerHTML = buttonsHTML;
        }
        
        // Helper function to get existing instances (placeholder)
        function getExistingInstances(fieldName) {
            // This should query the backend for existing instances
            // For now, return a default single instance
            return [{}]; // Represents one existing instance
        }
        
        // NEW: Enter specific instance for editing
        function enterSpecificInstance(fieldName, instanceIndex) {
            // Trigger backend to enter specific instance
            const event = new CustomEvent('enterNestedField', {
                detail: { fieldName: fieldName, instanceIndex: instanceIndex }
            });
            document.dispatchEvent(event);
        }
        
        // NEW: Add new instance
        function addNewInstance(fieldName) {
            // Trigger backend to add new instance
            const event = new CustomEvent('addNewInstance', {
                detail: { fieldName: fieldName }
            });
            document.dispatchEvent(event);
        }
        """
    
    def _get_event_handlers_javascript(self) -> str:
        """Generate JavaScript for event handlers"""
        return """
        // Field selection handler
        window.selectField = function(fieldName) {
            // Check if field has sub-fields (nested)
            const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
            
            if (field && field.has_sub_fields) {
                // NEW: Show instance management menu instead of direct entry
                showInstanceManagementMenu(fieldName);
            } else {
                // Direct field selection for non-nested fields
                const event = new CustomEvent('fieldSelected', {
                    detail: { fieldName: fieldName }
                });
                document.dispatchEvent(event);
            }
        };
        
        // Navigate to parent context
        window.navigateToParent = function() {
            const event = new CustomEvent('navigateToParent', {
                detail: {}
            });
            document.dispatchEvent(event);
        };
        
        // Close field menu
        window.closeFieldMenu = function() {
            const menu = document.getElementById('field-selection-menu');
            if (menu) {
                menu.remove();
            }
        };
        
        // Add instance management button
        window.addInstanceButton = function() {
            const event = new CustomEvent('addInstance', {
                detail: {}
            });
            document.dispatchEvent(event);
        };
        """
    
    def get_instance_button_html(self) -> str:
        """Generate HTML for the Add Instance button"""
        return """
        <div id="add-instance-container" style="
            position: fixed !important;
            bottom: 20px !important;
            right: 20px !important;
            z-index: 9999 !important;
        ">
            <button 
                id="add-instance-btn"
                onclick="addInstanceButton()"
                style="
                    background: linear-gradient(135deg, #f39c12, #e67e22) !important;
                    border: none !important;
                    color: white !important;
                    padding: 12px 20px !important;
                    border-radius: 25px !important;
                    cursor: pointer !important;
                    font-size: 14px !important;
                    font-weight: 600 !important;
                    box-shadow: 0 4px 15px rgba(243, 156, 18, 0.4) !important;
                    transition: all 0.3s ease !important;
                    font-family: 'Segoe UI', Arial, sans-serif !important;
                    display: none !important;
                "
                onmouseover="this.style.transform='translateY(-2px) scale(1.05)'; this.style.boxShadow='0 6px 20px rgba(243, 156, 18, 0.6)'"
                onmouseout="this.style.transform='translateY(0) scale(1)'; this.style.boxShadow='0 4px 15px rgba(243, 156, 18, 0.4)'"
            >
                ➕ Add Instance
            </button>
        </div>
        """ 