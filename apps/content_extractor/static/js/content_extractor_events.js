/**
 * Content Extractor Event Handlers
 * 
 * This file contains event handling functions for element selection,
 * mouse interactions, and user interface interactions.
 * 
 * Created by: Electric Sentinel
 * Date: 2025-01-08
 * Project: Triad Docker Base
 */

// Field selection handler
function selectField(fieldName) {
    const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
    if (!field) return;
    
    if (field.has_sub_fields) {
        // Show instance management menu for nested fields
        createInstanceManagementMenu(fieldName);
    } else {
        // Show field setting method menu for simple fields
        createFieldSettingMethodMenu(fieldName);
    }
}

// Start element selection
function startSelection(fieldName) {
    window.contentExtractorData.isSelectionMode = true;
    window.contentExtractorData.activeField = fieldName;
    window.contentExtractorData.isSelectionPaused = false; // Add pause state
    closeFieldMenu();
    
    // Add selection mode indicator
    const indicator = document.createElement('div');
    indicator.id = 'selection-mode-indicator';
    indicator.className = 'content-extractor-ui'; // Mark as our UI
    indicator.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${getFieldColor(fieldName)};
        color: white;
        padding: 15px;
        border-radius: 12px;
        z-index: 9999;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        border: 2px solid rgba(255,255,255,0.3);
        min-width: 200px;
    `;
    
    updateSelectionIndicator(indicator, fieldName);
    document.body.appendChild(indicator);
    
    // Show selection manager
    createSelectionManager(fieldName);
    
    document.addEventListener('click', handleElementClick, true);
    document.addEventListener('mouseover', handleMouseOver, true);
    document.addEventListener('mouseout', handleMouseOut, true);
}

// Update selection mode indicator content
function updateSelectionIndicator(indicator, fieldName) {
    const isPaused = window.contentExtractorData.isSelectionPaused;
    const bgColor = isPaused ? '#6c757d' : getFieldColor(fieldName);
    const statusIcon = isPaused ? '⏸️' : '🎯';
    const statusText = isPaused ? 'PAUSED' : 'ACTIVE';
    const interactionText = isPaused ? 'Normal page interaction' : 'Click elements to select';
    
    indicator.style.background = bgColor;
    indicator.innerHTML = `
        <div style="text-align: center; margin-bottom: 10px;">
            <div style="font-size: 16px; font-weight: bold;">
                ${statusIcon} Selecting: <span style="text-decoration: underline;">${fieldName}</span>
            </div>
            <div style="font-size: 12px; opacity: 0.9; margin: 5px 0;">
                Status: <strong>${statusText}</strong>
            </div>
            <div style="font-size: 11px; opacity: 0.8;">
                ${interactionText}
            </div>
        </div>
        <div style="text-align: center;">
            <button onclick="toggleSelectionMode()" 
                    style="padding: 6px 12px; margin: 2px; background: rgba(255,255,255,0.2); 
                           color: white; border: 1px solid rgba(255,255,255,0.4); border-radius: 6px; 
                           cursor: pointer; font-size: 12px; transition: all 0.2s;"
                    onmouseover="this.style.background='rgba(255,255,255,0.3)'"
                    onmouseout="this.style.background='rgba(255,255,255,0.2)'">
                ${isPaused ? '▶️ Resume' : '⏸️ Pause'}
            </button>
            <button onclick="window.stopSelection()" 
                    style="padding: 6px 12px; margin: 2px; background: rgba(255,255,255,0.2); 
                           color: white; border: 1px solid rgba(255,255,255,0.4); border-radius: 6px; 
                           cursor: pointer; font-size: 12px; transition: all 0.2s;"
                    onmouseover="this.style.background='rgba(255,255,255,0.3)'"
                    onmouseout="this.style.background='rgba(255,255,255,0.2)'">
                ✅ Finish
            </button>
        </div>
    `;
}

// Toggle selection mode (pause/resume)
window.toggleSelectionMode = function() {
    window.contentExtractorData.isSelectionPaused = !window.contentExtractorData.isSelectionPaused;
    
    // Update the indicator
    const indicator = document.getElementById('selection-mode-indicator');
    if (indicator && window.contentExtractorData.activeField) {
        updateSelectionIndicator(indicator, window.contentExtractorData.activeField);
    }
    
    // Clear any existing hover effects when pausing
    if (window.contentExtractorData.isSelectionPaused) {
        document.querySelectorAll('*').forEach(el => {
            if (!window.contentExtractorData.selectedDOMElements.has(el)) {
                el.style.outline = '';
                el.style.outlineOffset = '';
            }
        });
        console.log('⏸️ Selection mode paused - normal page interaction enabled');
    } else {
        console.log('▶️ Selection mode resumed - click elements to select');
    }
};

// Handle element click during selection
function handleElementClick(event) {
    if (!window.contentExtractorData.isSelectionMode || window.contentExtractorData.isSelectionPaused) {
        return; // Allow normal page interaction when paused
    }
    
    const element = event.target;
    
    // Ignore clicks on our own injected UI elements
    const injectedElementIds = [
        'content-extractor-control-panel',
        'content-extractor-field-menu', 
        'content-extractor-instance-menu',
        'content-extractor-selection-manager',
        'selection-mode-indicator'
    ];
    
    // Check if clicked element or any parent is an injected element
    let currentElement = element;
    while (currentElement && currentElement !== document.body) {
        if (injectedElementIds.includes(currentElement.id) || 
            currentElement.classList.contains('content-extractor-ui')) {
            console.log('🚫 Ignoring click on injected UI element:', currentElement.id || currentElement.className);
            return; // Ignore clicks on our UI
        }
        currentElement = currentElement.parentElement;
    }
    
    event.preventDefault();
    event.stopPropagation();
    
    const fieldName = window.contentExtractorData.activeField;
    
    // Create selection data
    const selection = {
        field_name: fieldName,
        xpath: getElementXPath(element),
        css_selector: getElementCSSSelector(element),
        selected_text: element.textContent.trim(),
        context_path: window.contentExtractorData.contextPath,
        depth: window.contentExtractorData.currentDepth,
        timestamp: Date.now(),
        element_id: generateElementId()
    };
    
    // Add to selections
    if (!window.contentExtractorData.fieldSelections[fieldName]) {
        window.contentExtractorData.fieldSelections[fieldName] = [];
    }
    
    // For single-value fields, replace the previous selection
    const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
    if (field && field.type === 'single' && window.contentExtractorData.fieldSelections[fieldName].length > 0) {
        // Remove highlight from previous selection
        window.contentExtractorData.selectedDOMElements.forEach(el => {
            // Simple way to check if this element was selected for this field
            removeHighlight(el);
        });
        window.contentExtractorData.selectedDOMElements.clear();
        
        // Replace the selection array with the new selection
        window.contentExtractorData.fieldSelections[fieldName] = [selection];
        console.log(`🔄 Replaced previous selection for single-value field ${fieldName}`);
    } else {
        // Add to existing selections for multi-value fields
        window.contentExtractorData.fieldSelections[fieldName].push(selection);
    }
    
    // Highlight selected element
    highlightElement(element, getFieldColor(fieldName));
    window.contentExtractorData.selectedDOMElements.add(element);
    
    // Update progress displays
    if (typeof window.updateControlPanelProgress === 'function') {
        window.updateControlPanelProgress();
    }
    
    // Update selection manager if open
    if (typeof window.updateSelectionManager === 'function') {
        window.updateSelectionManager();
    }
    
    // Show visual feedback for the selection
    const feedback = document.createElement('div');
    feedback.className = 'content-extractor-ui'; // Mark as our UI
    feedback.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: #28a745;
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        z-index: 10001;
        font-size: 14px;
        pointer-events: none;
        animation: fadeInOut 1.5s ease-in-out;
    `;
    feedback.textContent = `✓ ${fieldName} selected!`;
    
    // Add CSS animation
    if (!document.getElementById('selection-feedback-style')) {
        const style = document.createElement('style');
        style.id = 'selection-feedback-style';
        style.textContent = `
            @keyframes fadeInOut {
                0% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
                20% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
                80% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
                100% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(feedback);
    setTimeout(() => feedback.remove(), 1500);
    
    console.log(`✅ Selected ${fieldName}:`, selection.selected_text.substring(0, 50) + '...');
    
    // For single-value fields, show a notification but don't auto-stop selection
    if (field && field.type === 'single') {
        // Show additional feedback for single-value fields
        const singleFieldNotice = document.createElement('div');
        singleFieldNotice.className = 'content-extractor-ui';
        singleFieldNotice.style.cssText = `
            position: fixed;
            top: 40%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #17a2b8;
            color: white;
            padding: 10px 16px;
            border-radius: 8px;
            z-index: 10002;
            font-size: 13px;
            pointer-events: none;
            animation: fadeInOut 2.5s ease-in-out;
            text-align: center;
            max-width: 300px;
        `;
        singleFieldNotice.innerHTML = `
            <strong>Single-value field</strong><br>
            <small>Select another to replace, or click ✅ Finish to complete</small>
        `;
        
        document.body.appendChild(singleFieldNotice);
        setTimeout(() => singleFieldNotice.remove(), 2500);
        
        console.log(`ℹ️ Single-value field ${fieldName} - selection can be replaced`);
    }
}

// Handle mouse over during selection
function handleMouseOver(event) {
    if (!window.contentExtractorData.isSelectionMode || window.contentExtractorData.isSelectionPaused) {
        return; // No hover effects when paused
    }
    
    const element = event.target;
    
    // Ignore hover effects on our own injected UI elements
    const injectedElementIds = [
        'content-extractor-control-panel',
        'content-extractor-field-menu', 
        'content-extractor-instance-menu',
        'content-extractor-selection-manager',
        'selection-mode-indicator'
    ];
    
    // Check if hovered element or any parent is an injected element
    let currentElement = element;
    while (currentElement && currentElement !== document.body) {
        if (injectedElementIds.includes(currentElement.id) || 
            currentElement.classList.contains('content-extractor-ui')) {
            return; // Ignore hover effects on our UI
        }
        currentElement = currentElement.parentElement;
    }
    
    if (!window.contentExtractorData.selectedDOMElements.has(element)) {
        element.style.outline = '2px dashed ' + getFieldColor(window.contentExtractorData.activeField);
        element.style.outlineOffset = '1px';
    }
}

// Handle mouse out during selection
function handleMouseOut(event) {
    if (!window.contentExtractorData.isSelectionMode || window.contentExtractorData.isSelectionPaused) {
        return; // No hover effects when paused
    }
    
    const element = event.target;
    
    // Ignore hover effects on our own injected UI elements
    const injectedElementIds = [
        'content-extractor-control-panel',
        'content-extractor-field-menu', 
        'content-extractor-instance-menu',
        'content-extractor-selection-manager',
        'selection-mode-indicator'
    ];
    
    // Check if hovered element or any parent is an injected element
    let currentElement = element;
    while (currentElement && currentElement !== document.body) {
        if (injectedElementIds.includes(currentElement.id) || 
            currentElement.classList.contains('content-extractor-ui')) {
            return; // Ignore hover effects on our UI
        }
        currentElement = currentElement.parentElement;
    }
    
    if (!window.contentExtractorData.selectedDOMElements.has(element)) {
        element.style.outline = '';
        element.style.outlineOffset = '';
    }
}

// Stop selection mode
function stopSelection() {
    window.contentExtractorData.isSelectionMode = false;
    window.contentExtractorData.activeField = null;
    
    // Remove event listeners
    document.removeEventListener('click', handleElementClick, true);
    document.removeEventListener('mouseover', handleMouseOver, true);
    document.removeEventListener('mouseout', handleMouseOut, true);
    
    // Remove selection indicator
    const indicator = document.getElementById('selection-mode-indicator');
    if (indicator) {
        indicator.remove();
    }
    
    // Close selection manager
    closeSelectionManager();
    
    // Clear hover effects
    document.querySelectorAll('*').forEach(el => {
        if (!window.contentExtractorData.selectedDOMElements.has(el)) {
            el.style.outline = '';
            el.style.outlineOffset = '';
        }
    });
    
    console.log('🛑 Selection mode stopped');
}

// Field setting method handlers
window.startPageSelection = function(fieldName) {
    console.log(`🖱️ Starting page selection for ${fieldName}`);
    closeFieldSettingMethodMenu();
    startSelection(fieldName); // Use existing selection functionality
};

window.startTextInput = function(fieldName) {
    console.log(`✏️ Starting text input for ${fieldName}`);
    closeFieldSettingMethodMenu();
    createTextInputDialog(fieldName);
};

window.startFileImport = function(fieldName) {
    console.log(`📁 File import for ${fieldName} - Coming soon`);
    alert('File import feature coming soon!');
};

window.startAIExtraction = function(fieldName) {
    console.log(`🤖 AI extraction for ${fieldName} - Coming soon`);
    alert('AI-powered extraction feature coming soon!');
};

window.closeFieldSettingMethodMenu = function() {
    console.log('❌ closeFieldSettingMethodMenu called - returning to field menu');
    const menu = document.getElementById('content-extractor-method-menu');
    if (menu) {
        menu.remove();
    }
    // Return to field menu when method menu closes
    setTimeout(() => {
        window.showFieldMenu();
    }, 100);
};

window.clearFieldSelections = function(fieldName) {
    if (confirm(`Clear all selections for "${fieldName}"?`)) {
        window.contentExtractorData.fieldSelections[fieldName] = [];
        
        // Remove highlights for this field
        window.contentExtractorData.selectedDOMElements.forEach(element => {
            removeHighlight(element);
        });
        window.contentExtractorData.selectedDOMElements.clear();
        
        console.log(`🗑️ Cleared all selections for ${fieldName}`);
        
        // Refresh the method menu to show updated state
        setTimeout(() => {
            createFieldSettingMethodMenu(fieldName);
        }, 100);
        
        // Update control panel
        if (typeof window.updateControlPanelProgress === 'function') {
            window.updateControlPanelProgress();
        }
    }
};

window.saveTextInput = function(fieldName) {
    const textarea = document.getElementById('text-input-field');
    if (!textarea) return;
    
    const inputValue = textarea.value.trim();
    if (!inputValue) {
        alert('Please enter a value before saving.');
        return;
    }
    
    const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
    if (!field) return;
    
    // Clear existing selections for this field
    window.contentExtractorData.fieldSelections[fieldName] = [];
    
    if (field.type === 'multi-value') {
        // Split by lines and filter out empty lines
        const values = inputValue.split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0);
        
        values.forEach((value, index) => {
            const selection = {
                field_name: fieldName,
                xpath: null, // No XPath for manually entered text
                css_selector: null, // No CSS selector for manually entered text  
                selected_text: value,
                context_path: window.contentExtractorData.contextPath,
                depth: window.contentExtractorData.currentDepth,
                timestamp: Date.now(),
                element_id: `manual-text-${Date.now()}-${index}`,
                input_method: 'manual_text'
            };
            window.contentExtractorData.fieldSelections[fieldName].push(selection);
        });
        
        console.log(`✅ Saved ${values.length} text values for ${fieldName}:`, values);
    } else {
        // Single value
        const selection = {
            field_name: fieldName,
            xpath: null, // No XPath for manually entered text
            css_selector: null, // No CSS selector for manually entered text
            selected_text: inputValue,
            context_path: window.contentExtractorData.contextPath,
            depth: window.contentExtractorData.currentDepth,
            timestamp: Date.now(),
            element_id: `manual-text-${Date.now()}`,
            input_method: 'manual_text'
        };
        window.contentExtractorData.fieldSelections[fieldName].push(selection);
        
        console.log(`✅ Saved text value for ${fieldName}:`, inputValue);
    }
    
    // Close the dialog
    const dialog = document.getElementById('content-extractor-text-dialog');
    if (dialog) {
        dialog.remove();
    }
    
    // Show success feedback
    const feedback = document.createElement('div');
    feedback.className = 'content-extractor-ui';
    feedback.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: #28a745;
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        z-index: 10003;
        font-size: 14px;
        font-weight: bold;
        pointer-events: none;
        animation: fadeInOut 2s ease-in-out;
    `;
    feedback.textContent = `✅ ${fieldName} saved successfully!`;
    
    document.body.appendChild(feedback);
    setTimeout(() => feedback.remove(), 2000);
    
    // Update control panel progress
    if (typeof window.updateControlPanelProgress === 'function') {
        window.updateControlPanelProgress();
    }
    
    // Return to field menu
    setTimeout(() => {
        window.showFieldMenu();
    }, 500);
};

window.cancelTextInput = function(fieldName) {
    console.log(`❌ Cancelled text input for ${fieldName}`);
    
    // Close the dialog
    const dialog = document.getElementById('content-extractor-text-dialog');
    if (dialog) {
        dialog.remove();
    }
    
    // Return to method selection menu
    setTimeout(() => {
        createFieldSettingMethodMenu(fieldName);
    }, 100);
}; 