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
    
    // **NEW AI PREPARATION SYSTEM**: Open XPath Editor after selection
    setTimeout(() => {
        console.log('🔧 Opening XPath Editor for AI preparation system');
        
        // Check if XPath editor is available
        if (window.ContentExtractorXPathEditor && window.ContentExtractorXPathEditor.openEditor) {
            window.ContentExtractorXPathEditor.openEditor(element, fieldName, selection.xpath);
        } else {
            console.warn('⚠️ XPath Editor not loaded - falling back to basic selection');
            
            // Show fallback notification
            const fallbackNotice = document.createElement('div');
            fallbackNotice.className = 'content-extractor-ui';
            fallbackNotice.style.cssText = `
                position: fixed;
                top: 30%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: #ffc107;
                color: #212529;
                padding: 12px 20px;
                border-radius: 8px;
                z-index: 10003;
                font-size: 14px;
                font-weight: bold;
                text-align: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            `;
            fallbackNotice.innerHTML = `
                ⚠️ XPath Editor Unavailable<br>
                <small>Using basic selection mode</small>
            `;
            
            document.body.appendChild(fallbackNotice);
            setTimeout(() => fallbackNotice.remove(), 3000);
        }
    }, 100);
    
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

// Multi-element instance management functions
window.createNewInstance = function(fieldName) {
    console.log(`➕ Creating new instance for ${fieldName}`);
    
    // Initialize instanceSelections if not exists
    if (!window.contentExtractorData.instanceSelections) {
        window.contentExtractorData.instanceSelections = {};
    }
    
    if (!window.contentExtractorData.instanceSelections[fieldName]) {
        window.contentExtractorData.instanceSelections[fieldName] = [];
    }
    
    // Create new instance
    const newInstance = {
        instance_index: window.contentExtractorData.instanceSelections[fieldName].length,
        created_at: Date.now(),
        subfields: {}
    };
    
    window.contentExtractorData.instanceSelections[fieldName].push(newInstance);
    
    console.log(`✅ Created new instance ${fieldName}[${newInstance.instance_index}]`);
    
    // Refresh the instance management menu
    createInstanceManagementMenu(fieldName);
    
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
    feedback.textContent = `✅ New ${fieldName} instance created!`;
    
    document.body.appendChild(feedback);
    setTimeout(() => feedback.remove(), 2000);
};

window.openInstanceSubfields = function(fieldName, instanceIndex) {
    console.log(`⚙️ Opening subfields for ${fieldName}[${instanceIndex}]`);
    
    // Close instance menu and show subfields menu
    const menu = document.getElementById('content-extractor-instance-menu');
    if (menu) {
        menu.remove();
    }
    
    createInstanceSubfieldsMenu(fieldName, instanceIndex);
};

window.deleteInstance = function(fieldName, instanceIndex) {
    console.log(`🗑️ Deleting instance ${fieldName}[${instanceIndex}]`);
    
    if (confirm(`Are you sure you want to delete ${fieldName}[${instanceIndex + 1}]? This will remove all subfield data for this instance.`)) {
        // Remove the instance
        if (window.contentExtractorData.instanceSelections[fieldName]) {
            window.contentExtractorData.instanceSelections[fieldName].splice(instanceIndex, 1);
            
            // Update instance indices for remaining instances
            window.contentExtractorData.instanceSelections[fieldName].forEach((instance, index) => {
                instance.instance_index = index;
            });
        }
        
        console.log(`✅ Deleted instance ${fieldName}[${instanceIndex}]`);
        
        // Refresh the instance management menu
        createInstanceManagementMenu(fieldName);
        
        // Show success feedback
        const feedback = document.createElement('div');
        feedback.className = 'content-extractor-ui';
        feedback.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #dc3545;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            z-index: 10003;
            font-size: 14px;
            font-weight: bold;
            pointer-events: none;
            animation: fadeInOut 2s ease-in-out;
        `;
        feedback.textContent = `🗑️ ${fieldName} instance deleted!`;
        
        document.body.appendChild(feedback);
        setTimeout(() => feedback.remove(), 2000);
    }
};

function createInstanceSubfieldsMenu(fieldName, instanceIndex) {
    // Use unified menu system if available
    if (window.ContentExtractorUnifiedMenu) {
        const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
        if (!field || !field.sub_fields) return;
        
        const instance = window.contentExtractorData.instanceSelections[fieldName][instanceIndex];
        if (!instance) return;
        
        const config = {
            id: 'content-extractor-subfields-menu',
            title: `⚙️ ${field.label}[${instanceIndex + 1}] Subfields`,
            subtitle: 'Configure subfields for this instance',
            type: 'subfield',
            color: field.color,
            content: buildSubfieldsMenuContent(field, instanceIndex, instance),
            buttons: [
                { label: '⬅️ Back to Instances', type: 'secondary', onClick: `returnToInstanceManagement('${fieldName}')` },
                { label: '🏠 Main Menu', type: 'primary', onClick: 'returnToFieldMenu()' }
            ],
            breadcrumbs: ['Fields', field.label, `Instance ${instanceIndex + 1}`]
        };
        
        return window.ContentExtractorUnifiedMenu.createMenu(config);
    } else {
        // Legacy subfields menu creation (fallback)
        return createLegacyInstanceSubfieldsMenu(fieldName, instanceIndex);
    }
}

// Build subfields menu content HTML with XPath editing capabilities
function buildSubfieldsMenuContent(field, instanceIndex, instance) {
    let subfieldsHtml = `
        <div style="margin: 15px 0;">
            <h4 style="margin: 0 0 10px 0; color: ${field.color}; font-size: 14px;">
                Subfields with XPath Configuration:
            </h4>
            <div style="max-height: 300px; overflow-y: auto;">
    `;
    
    field.sub_fields.forEach((subfield, index) => {
        const subfieldSelections = instance.subfields[subfield.name] || [];
        const hasSelections = subfieldSelections.length > 0;
        const progressText = hasSelections ? ` (${subfieldSelections.length} selected)` : '';
        const statusColor = hasSelections ? '#28a745' : '#6c757d';
        
        // Get current XPath if available
        const lastSelection = hasSelections ? subfieldSelections[subfieldSelections.length - 1] : null;
        const currentXPath = lastSelection ? lastSelection.xpath : '';
        
        subfieldsHtml += `
            <div style="margin: 8px 0; padding: 12px; background: ${subfield.color || '#f8f9fa'}10; 
                       border: 1px solid ${subfield.color || '#dee2e6'}; border-radius: 6px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div style="flex: 1;">
                        <div style="font-weight: bold; color: ${subfield.color || '#333'};">
                            ${subfield.label}${progressText}
                        </div>
                        <div style="font-size: 12px; color: #666; margin-top: 2px;">
                            ${subfield.description || subfield.type}
                        </div>
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <button onclick="selectSubfield('${field.name}', ${instanceIndex}, '${subfield.name}')" 
                                style="padding: 8px 16px; background: ${statusColor}; color: white; 
                                       border: none; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: bold;"
                                onmouseover="this.style.opacity='0.8'"
                                onmouseout="this.style.opacity='1'">
                            ${hasSelections ? '✅ Set' : '⚙️ Set'}
                        </button>
                        ${hasSelections ? `
                            <button onclick="openSubfieldXPathEditor('${field.name}', ${instanceIndex}, '${subfield.name}')" 
                                    style="padding: 8px 12px; background: #007bff; color: white; 
                                           border: none; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: bold;"
                                    onmouseover="this.style.opacity='0.8'"
                                    onmouseout="this.style.opacity='1'"
                                    title="Edit XPath for this subfield">
                                🔧
                            </button>
                        ` : ''}
                    </div>
                </div>
                ${currentXPath ? `
                    <div style="margin-top: 8px; padding: 6px 8px; background: #f8f9fa; border-radius: 4px; font-family: monospace; font-size: 11px; color: #666;">
                        <strong>XPath:</strong> ${currentXPath}
                    </div>
                ` : ''}
            </div>
        `;
    });
    
    subfieldsHtml += `
            </div>
        </div>
    `;
    
    return subfieldsHtml;
}

// Legacy subfields menu creation (kept for backward compatibility)
function createLegacyInstanceSubfieldsMenu(fieldName, instanceIndex) {
    const menuId = 'content-extractor-subfields-menu';
    let existingMenu = document.getElementById(menuId);
    if (existingMenu) {
        existingMenu.remove();
    }
    
    const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
    if (!field || !field.sub_fields) return;
    
    const instance = window.contentExtractorData.instanceSelections[fieldName][instanceIndex];
    if (!instance) return;
    
    const menu = document.createElement('div');
    menu.id = menuId;
    menu.className = 'content-extractor-ui';
    menu.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        border: 3px solid ${field.color};
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        z-index: 10000;
        max-width: 600px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        cursor: move;
    `;
    
    // Add draggable functionality
    let isDragging = false;
    let dragOffset = { x: 0, y: 0 };
    
    menu.addEventListener('mousedown', function(e) {
        if (e.target.closest('.menu-header') || e.target === menu) {
            isDragging = true;
            const rect = menu.getBoundingClientRect();
            dragOffset.x = e.clientX - rect.left;
            dragOffset.y = e.clientY - rect.top;
            menu.style.cursor = 'grabbing';
            e.preventDefault();
        }
    });
    
    document.addEventListener('mousemove', function(e) {
        if (isDragging) {
            menu.style.left = (e.clientX - dragOffset.x) + 'px';
            menu.style.top = (e.clientY - dragOffset.y) + 'px';
            menu.style.transform = 'none';
        }
    });
    
    document.addEventListener('mouseup', function() {
        if (isDragging) {
            isDragging = false;
            menu.style.cursor = 'move';
        }
    });
    
    // Header
    const headerHtml = `
        <div class="menu-header" style="text-align: center; margin-bottom: 20px; cursor: grab; padding: 5px; border-radius: 6px;"
             onmousedown="this.style.cursor='grabbing'" onmouseup="this.style.cursor='grab'">
            <h3 style="margin: 0; color: ${field.color};">
                ⚙️ ${field.label}[${instanceIndex + 1}] Subfields
            </h3>
            <small style="color: #666;">Configure subfields for this instance</small>
        </div>
    `;
    
    // Breadcrumb
    const breadcrumbHtml = `
        <div style="margin-bottom: 15px; padding: 8px 12px; background: #f8f9fa; border-radius: 6px; font-size: 14px; color: #6c757d;">
            📍 Fields → ${field.label} → Instance ${instanceIndex + 1}
        </div>
    `;
    
    // Subfields list
    let subfieldsHtml = `
        <div style="margin: 15px 0;">
            <h4 style="margin: 0 0 10px 0; color: ${field.color}; font-size: 14px;">
                Subfields:
            </h4>
            <div style="max-height: 300px; overflow-y: auto;">
    `;
    
    field.sub_fields.forEach((subfield, index) => {
        const subfieldSelections = instance.subfields[subfield.name] || [];
        const hasSelections = subfieldSelections.length > 0;
        const progressText = hasSelections ? ` (${subfieldSelections.length} selected)` : '';
        const statusColor = hasSelections ? '#28a745' : '#6c757d';
        
        subfieldsHtml += `
            <div style="margin: 8px 0; padding: 12px; background: ${subfield.color || '#f8f9fa'}10; 
                       border: 1px solid ${subfield.color || '#dee2e6'}; border-radius: 6px; 
                       display: flex; justify-content: space-between; align-items: center;">
                <div style="flex: 1;">
                    <div style="font-weight: bold; color: ${subfield.color || '#333'};">
                        ${subfield.label}${progressText}
                    </div>
                    <div style="font-size: 12px; color: #666; margin-top: 2px;">
                        ${subfield.description || subfield.type}
                    </div>
                </div>
                <div>
                    <button onclick="selectSubfield('${field.name}', ${instanceIndex}, '${subfield.name}')" 
                            style="padding: 8px 16px; background: ${statusColor}; color: white; 
                                   border: none; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: bold;"
                            onmouseover="this.style.opacity='0.8'"
                            onmouseout="this.style.opacity='1'">
                        ${hasSelections ? '✅ Set' : '⚙️ Set'}
                    </button>
                </div>
            </div>
        `;
    });
    
    subfieldsHtml += `
            </div>
        </div>
    `;
    
    // Navigation buttons
    const navigationHtml = `
        <div style="text-align: center; margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee;">
            <button onclick="returnToInstanceManagement('${fieldName}')" 
                    style="padding: 8px 16px; margin: 0 5px; background: #6c757d; color: white; 
                           border: none; border-radius: 6px; cursor: pointer; transition: all 0.2s;"
                    onmouseover="this.style.background='#5a6268'"
                    onmouseout="this.style.background='#6c757d'">
                ⬅️ Back to Instances
            </button>
            <button onclick="returnToFieldMenu()" 
                    style="padding: 8px 16px; margin: 0 5px; background: #007bff; color: white; 
                           border: none; border-radius: 6px; cursor: pointer; transition: all 0.2s;"
                    onmouseover="this.style.background='#0056b3'"
                    onmouseout="this.style.background='#007bff'">
                🏠 Main Menu
            </button>
        </div>
    `;
    
    menu.innerHTML = headerHtml + breadcrumbHtml + subfieldsHtml + navigationHtml;
    document.body.appendChild(menu);
    
    return menu;
}

// Subfield selection handler - now works like main field selection
window.selectSubfield = function(fieldName, instanceIndex, subfieldName) {
    console.log(`🎯 Selecting subfield: ${fieldName}[${instanceIndex}].${subfieldName}`);
    
    const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
    if (!field) return;
    
    const subfield = field.sub_fields.find(sf => sf.name === subfieldName);
    if (!subfield) return;
    
    // Use unified menu system for subfield method selection
    if (window.ContentExtractorUnifiedMenu) {
        // Get existing selections
        const instance = window.contentExtractorData.instanceSelections[fieldName][instanceIndex];
        const subfieldSelections = instance.subfields[subfieldName] || [];
        const hasSelections = subfieldSelections.length > 0;
        
        // Build current value display
        let currentValueHtml = '';
        if (hasSelections) {
            const lastSelection = subfieldSelections[subfieldSelections.length - 1];
            const valuePreview = lastSelection.selected_text.length > 60 
                ? lastSelection.selected_text.substring(0, 60) + '...'
                : lastSelection.selected_text;
            const currentXPath = lastSelection.xpath || 'No XPath set';
            
            currentValueHtml = `
                <div style="margin: 15px 0; padding: 10px; background: ${subfield.color || '#007bff'}10; border: 1px solid ${subfield.color || '#007bff'}40; border-radius: 6px;">
                    <div style="font-size: 12px; color: #666; margin-bottom: 5px;">
                        Current Value${subfield.type === 'multi-value' ? ` (${subfieldSelections.length} items)` : ''}:
                    </div>
                    <div style="font-weight: bold; color: ${subfield.color || '#007bff'}; margin-bottom: 8px;">
                        "${valuePreview}"
                    </div>
                    <div style="font-family: monospace; font-size: 11px; color: #666; background: #f8f9fa; padding: 6px; border-radius: 4px;">
                        <strong>XPath:</strong> ${currentXPath}
                    </div>
                </div>
            `;
        }
        
        const config = {
            id: 'content-extractor-subfield-method-menu',
            title: `🎯 Set "${subfield.label}"`,
            subtitle: `Configure ${field.label}[${instanceIndex + 1}] subfield`,
            type: 'method',
            color: subfield.color || '#007bff',
            content: `
                <div style="margin-bottom: 15px; padding: 8px 12px; background: #f8f9fa; border-radius: 6px; font-size: 14px;">
                    <strong>${field.label}[${instanceIndex + 1}].${subfield.label}</strong> (${subfield.type})<br>
                    <small style="color: #666;">${subfield.description || 'Subfield configuration'}</small>
                </div>
                
                ${currentValueHtml}
                
                <div style="margin: 15px 0;">
                    <button onclick="startSubfieldPageSelection('${fieldName}', ${instanceIndex}, '${subfieldName}')" 
                            style="display: block; width: 100%; margin: 8px 0; padding: 15px; 
                                   background: #007bff; color: white; border: none; border-radius: 8px; 
                                   cursor: pointer; text-align: left; font-size: 14px; transition: all 0.2s;"
                            onmouseover="this.style.background='#0056b3'; this.style.transform='scale(1.02)'"
                            onmouseout="this.style.background='#007bff'; this.style.transform='scale(1)'">
                        🖱️ <strong>Select from Page Elements</strong><br>
                        <small style="opacity: 0.9;">Click elements on the webpage to extract content</small>
                    </button>
                    
                    <button onclick="startSubfieldTextInput('${fieldName}', ${instanceIndex}, '${subfieldName}')" 
                            style="display: block; width: 100%; margin: 8px 0; padding: 15px; 
                                   background: #28a745; color: white; border: none; border-radius: 8px; 
                                   cursor: pointer; text-align: left; font-size: 14px; transition: all 0.2s;"
                            onmouseover="this.style.background='#1e7e34'; this.style.transform='scale(1.02)'"
                            onmouseout="this.style.background='#28a745'; this.style.transform='scale(1)'">
                        ✏️ <strong>Enter Text Manually</strong><br>
                        <small style="opacity: 0.9;">Type or paste the value directly</small>
                    </button>
                </div>
            `,
            buttons: [
                { label: '⬅️ Back to Subfields', type: 'secondary', onClick: `returnToSubfieldsList('${fieldName}', ${instanceIndex})` },
                ...(hasSelections ? [
                    { label: '🔧 Edit XPath', type: 'info', onClick: `openSubfieldXPathEditor('${fieldName}', ${instanceIndex}, '${subfieldName}')` },
                    { label: '🗑️ Clear Value', type: 'warning', onClick: `clearSubfieldSelections('${fieldName}', ${instanceIndex}, '${subfieldName}')` }
                ] : [])
            ],
            breadcrumbs: ['Fields', field.label, `Instance ${instanceIndex + 1}`, subfield.label]
        };
        
        window.ContentExtractorUnifiedMenu.createMenu(config);
    } else {
        // Fallback to legacy system
        const subfieldConfig = {
            parentField: fieldName,
            instanceIndex: instanceIndex,
            subfieldName: subfieldName,
            label: subfield.label,
            type: subfield.type,
            description: subfield.description,
            color: subfield.color
        };
        createSubfieldMethodMenu(subfieldConfig);
    }
};

// Helper function to open XPath editor for subfields
window.openSubfieldXPathEditor = function(fieldName, instanceIndex, subfieldName) {
    console.log(`🔧 Opening XPath editor for subfield: ${fieldName}[${instanceIndex}].${subfieldName}`);
    
    const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
    if (!field) return;
    
    const subfield = field.sub_fields.find(sf => sf.name === subfieldName);
    if (!subfield) return;
    
    const instance = window.contentExtractorData.instanceSelections[fieldName][instanceIndex];
    const subfieldSelections = instance.subfields[subfieldName] || [];
    
    // Get the last XPath if available
    const lastSelection = subfieldSelections.length > 0 ? subfieldSelections[subfieldSelections.length - 1] : null;
    const currentXPath = lastSelection ? lastSelection.xpath : '';
    
    // Create a pseudo-element for XPath generation if we have a selection
    let targetElement = null;
    if (lastSelection && lastSelection.element_path) {
        // Try to find the element by XPath if we have it
        try {
            const result = document.evaluate(
                lastSelection.xpath || lastSelection.element_path,
                document,
                null,
                XPathResult.FIRST_ORDERED_NODE_TYPE,
                null
            );
            targetElement = result.singleNodeValue;
        } catch (error) {
            console.warn('Could not find target element for XPath editor:', error);
        }
    }
    
    // Set up XPath editor context for subfield
    if (window.ContentExtractorXPathEditor) {
        window.ContentExtractorXPathEditor.currentSubfieldContext = {
            fieldName: fieldName,
            instanceIndex: instanceIndex,
            subfieldName: subfieldName
        };
    }
    
    // Use unified menu system for XPath editor
    const fieldDisplayName = `${field.label}[${instanceIndex + 1}].${subfield.label}`;
    
    if (window.ContentExtractorUnifiedMenu) {
        window.ContentExtractorUnifiedMenu.createXPathEditor(targetElement, fieldDisplayName, currentXPath);
    } else {
        // Fallback
        window.openXPathEditor(targetElement, fieldDisplayName);
    }
};

function createSubfieldMethodMenu(subfieldConfig) {
    const menuId = 'content-extractor-subfield-method-menu';
    let existingMenu = document.getElementById(menuId);
    if (existingMenu) {
        existingMenu.remove();
    }
    
    const menu = document.createElement('div');
    menu.id = menuId;
    menu.className = 'content-extractor-ui';
    menu.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        border: 3px solid ${subfieldConfig.color || '#007bff'};
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        z-index: 10000;
        max-width: 500px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        cursor: move;
    `;
    
    // Add draggable functionality (same as other menus)
    let isDragging = false;
    let dragOffset = { x: 0, y: 0 };
    
    menu.addEventListener('mousedown', function(e) {
        if (e.target.closest('.menu-header') || e.target === menu) {
            isDragging = true;
            const rect = menu.getBoundingClientRect();
            dragOffset.x = e.clientX - rect.left;
            dragOffset.y = e.clientY - rect.top;
            menu.style.cursor = 'grabbing';
            e.preventDefault();
        }
    });
    
    document.addEventListener('mousemove', function(e) {
        if (isDragging) {
            menu.style.left = (e.clientX - dragOffset.x) + 'px';
            menu.style.top = (e.clientY - dragOffset.y) + 'px';
            menu.style.transform = 'none';
        }
    });
    
    document.addEventListener('mouseup', function() {
        if (isDragging) {
            isDragging = false;
            menu.style.cursor = 'move';
        }
    });
    
    // Get existing selections for this subfield
    const instance = window.contentExtractorData.instanceSelections[subfieldConfig.parentField][subfieldConfig.instanceIndex];
    const subfieldSelections = instance.subfields[subfieldConfig.subfieldName] || [];
    const hasSelections = subfieldSelections.length > 0;
    
    // Current value display
    let currentValueHtml = '';
    if (hasSelections) {
        const lastSelection = subfieldSelections[subfieldSelections.length - 1];
        const valuePreview = lastSelection.selected_text.length > 60 
            ? lastSelection.selected_text.substring(0, 60) + '...'
            : lastSelection.selected_text;
        currentValueHtml = `
            <div style="margin: 15px 0; padding: 10px; background: ${subfieldConfig.color || '#007bff'}10; border: 1px solid ${subfieldConfig.color || '#007bff'}40; border-radius: 6px;">
                <div style="font-size: 12px; color: #666; margin-bottom: 5px;">
                    Current Value${subfieldConfig.type === 'multi-value' ? ` (${subfieldSelections.length} items)` : ''}:
                </div>
                <div style="font-weight: bold; color: ${subfieldConfig.color || '#007bff'};">
                    "${valuePreview}"
                </div>
            </div>
        `;
    }
    
    menu.innerHTML = `
        <div class="menu-header" style="text-align: center; margin-bottom: 20px; cursor: grab; padding: 5px; border-radius: 6px;"
             onmousedown="this.style.cursor='grabbing'" onmouseup="this.style.cursor='grab'">
            <h3 style="margin: 0; color: ${subfieldConfig.color || '#007bff'};">
                🎯 Set "${subfieldConfig.label}"
            </h3>
            <small style="color: #666;">Choose your input method</small>
        </div>
        
        <div style="margin-bottom: 15px; padding: 8px 12px; background: #f8f9fa; border-radius: 6px; font-size: 14px;">
            <strong>${subfieldConfig.parentField}[${subfieldConfig.instanceIndex + 1}].${subfieldConfig.label}</strong> (${subfieldConfig.type})<br>
            <small style="color: #666;">${subfieldConfig.description || 'Subfield'}</small>
        </div>
        
        ${currentValueHtml}
        
        <div style="margin: 15px 0;">
            <button onclick="startSubfieldPageSelection('${subfieldConfig.parentField}', ${subfieldConfig.instanceIndex}, '${subfieldConfig.subfieldName}')" 
                    style="display: block; width: 100%; margin: 8px 0; padding: 15px; 
                           background: #007bff; color: white; border: none; border-radius: 8px; 
                           cursor: pointer; text-align: left; font-size: 14px; transition: all 0.2s;"
                    onmouseover="this.style.background='#0056b3'; this.style.transform='scale(1.02)'"
                    onmouseout="this.style.background='#007bff'; this.style.transform='scale(1)'">
                🖱️ <strong>Select from Page Elements</strong><br>
                <small style="opacity: 0.9;">Click elements on the webpage to extract content</small>
            </button>
            
            <button onclick="startSubfieldTextInput('${subfieldConfig.parentField}', ${subfieldConfig.instanceIndex}, '${subfieldConfig.subfieldName}')" 
                    style="display: block; width: 100%; margin: 8px 0; padding: 15px; 
                           background: #28a745; color: white; border: none; border-radius: 8px; 
                           cursor: pointer; text-align: left; font-size: 14px; transition: all 0.2s;"
                    onmouseover="this.style.background='#1e7e34'; this.style.transform='scale(1.02)'"
                    onmouseout="this.style.background='#28a745'; this.style.transform='scale(1)'">
                ✏️ <strong>Enter Text Manually</strong><br>
                <small style="opacity: 0.9;">Type or paste the value directly</small>
            </button>
        </div>
        
        <div style="text-align: center; margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee;">
            <button onclick="returnToSubfieldsList('${subfieldConfig.parentField}', ${subfieldConfig.instanceIndex})" 
                    style="padding: 8px 16px; margin: 0 5px; background: #dc3545; color: white; 
                           border: none; border-radius: 6px; cursor: pointer; transition: all 0.2s;"
                    onmouseover="this.style.background='#c82333'"
                    onmouseout="this.style.background='#dc3545'">
                ⬅️ Back to Subfields
            </button>
            ${hasSelections ? `
                <button onclick="clearSubfieldSelections('${subfieldConfig.parentField}', ${subfieldConfig.instanceIndex}, '${subfieldConfig.subfieldName}')" 
                        style="padding: 8px 16px; margin: 0 5px; background: #ffc107; color: #212529; 
                               border: none; border-radius: 6px; cursor: pointer; transition: all 0.2s;"
                        onmouseover="this.style.background='#e0a800'"
                        onmouseout="this.style.background='#ffc107'">
                    🗑️ Clear Value
                </button>
            ` : ''}
        </div>
    `;
    
    document.body.appendChild(menu);
    return menu;
}

// Navigation helper functions
window.returnToInstanceManagement = function(fieldName) {
    console.log(`⬅️ Returning to instance management for ${fieldName}`);
    const menu = document.getElementById('content-extractor-subfields-menu');
    if (menu) {
        menu.remove();
    }
    createInstanceManagementMenu(fieldName);
};

window.returnToFieldMenu = function() {
    console.log('🏠 Returning to main field menu');
    const subfieldsMenu = document.getElementById('content-extractor-subfields-menu');
    const methodMenu = document.getElementById('content-extractor-subfield-method-menu');
    if (subfieldsMenu) subfieldsMenu.remove();
    if (methodMenu) methodMenu.remove();
    window.showFieldMenu();
};

window.returnToSubfieldsList = function(fieldName, instanceIndex) {
    console.log(`⬅️ Returning to subfields list for ${fieldName}[${instanceIndex}]`);
    const menu = document.getElementById('content-extractor-subfield-method-menu');
    if (menu) {
        menu.remove();
    }
    createInstanceSubfieldsMenu(fieldName, instanceIndex);
};

// Subfield selection handlers
window.startSubfieldPageSelection = function(fieldName, instanceIndex, subfieldName) {
    console.log(`🖱️ Starting page selection for subfield ${fieldName}[${instanceIndex}].${subfieldName}`);
    
    // Set up selection context for subfield
    window.contentExtractorData.activeSubfield = {
        fieldName: fieldName,
        instanceIndex: instanceIndex,
        subfieldName: subfieldName
    };
    
    // Close method menu
    const menu = document.getElementById('content-extractor-subfield-method-menu');
    if (menu) {
        menu.remove();
    }
    
    // Start selection mode
    startSubfieldSelection(fieldName, instanceIndex, subfieldName);
};

window.startSubfieldTextInput = function(fieldName, instanceIndex, subfieldName) {
    console.log(`✏️ Starting text input for subfield ${fieldName}[${instanceIndex}].${subfieldName}`);
    
    // Close method menu
    const menu = document.getElementById('content-extractor-subfield-method-menu');
    if (menu) {
        menu.remove();
    }
    
    // Create text input dialog for subfield
    createSubfieldTextInputDialog(fieldName, instanceIndex, subfieldName);
};

function startSubfieldSelection(fieldName, instanceIndex, subfieldName) {
    // Similar to startSelection but for subfields
    window.contentExtractorData.isSelectionMode = true;
    window.contentExtractorData.activeField = `${fieldName}[${instanceIndex}].${subfieldName}`;
    window.contentExtractorData.isSelectionPaused = false;
    
    // Add selection mode indicator
    const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
    const subfield = field.sub_fields.find(sf => sf.name === subfieldName);
    const subfieldColor = subfield.color || field.color;
    
    const indicator = document.createElement('div');
    indicator.id = 'selection-mode-indicator';
    indicator.className = 'content-extractor-ui';
    indicator.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${subfieldColor};
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
    
    updateSubfieldSelectionIndicator(indicator, fieldName, instanceIndex, subfieldName);
    document.body.appendChild(indicator);
    
    document.addEventListener('click', handleSubfieldElementClick, true);
    document.addEventListener('mouseover', handleMouseOver, true);
    document.addEventListener('mouseout', handleMouseOut, true);
}

function updateSubfieldSelectionIndicator(indicator, fieldName, instanceIndex, subfieldName) {
    const isPaused = window.contentExtractorData.isSelectionPaused;
    const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
    const subfield = field.sub_fields.find(sf => sf.name === subfieldName);
    const bgColor = isPaused ? '#6c757d' : (subfield.color || field.color);
    const statusIcon = isPaused ? '⏸️' : '🎯';
    const statusText = isPaused ? 'PAUSED' : 'ACTIVE';
    const interactionText = isPaused ? 'Normal page interaction' : 'Click elements to select';
    
    indicator.style.background = bgColor;
    indicator.innerHTML = `
        <div style="text-align: center; margin-bottom: 10px;">
            <div style="font-size: 16px; font-weight: bold;">
                ${statusIcon} Selecting: <span style="text-decoration: underline;">${fieldName}[${instanceIndex + 1}].${subfieldName}</span>
            </div>
            <div style="font-size: 12px; opacity: 0.9; margin: 5px 0;">
                Status: <strong>${statusText}</strong>
            </div>
            <div style="font-size: 11px; opacity: 0.8;">
                ${interactionText}
            </div>
        </div>
        <div style="text-align: center;">
            <button onclick="toggleSubfieldSelectionMode()" 
                    style="padding: 6px 12px; margin: 2px; background: rgba(255,255,255,0.2); 
                           color: white; border: 1px solid rgba(255,255,255,0.4); border-radius: 6px; 
                           cursor: pointer; font-size: 12px; transition: all 0.2s;"
                    onmouseover="this.style.background='rgba(255,255,255,0.3)'"
                    onmouseout="this.style.background='rgba(255,255,255,0.2)'">
                ${isPaused ? '▶️ Resume' : '⏸️ Pause'}
            </button>
            <button onclick="finishSubfieldSelection()" 
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

window.toggleSubfieldSelectionMode = function() {
    window.contentExtractorData.isSelectionPaused = !window.contentExtractorData.isSelectionPaused;
    
    const indicator = document.getElementById('selection-mode-indicator');
    if (indicator && window.contentExtractorData.activeSubfield) {
        const { fieldName, instanceIndex, subfieldName } = window.contentExtractorData.activeSubfield;
        updateSubfieldSelectionIndicator(indicator, fieldName, instanceIndex, subfieldName);
    }
    
    if (window.contentExtractorData.isSelectionPaused) {
        document.querySelectorAll('*').forEach(el => {
            if (!window.contentExtractorData.selectedDOMElements.has(el)) {
                el.style.outline = '';
                el.style.outlineOffset = '';
            }
        });
        console.log('⏸️ Subfield selection mode paused');
    } else {
        console.log('▶️ Subfield selection mode resumed');
    }
};

window.finishSubfieldSelection = function() {
    console.log('✅ Finishing subfield selection');
    
    // Stop selection mode
    window.contentExtractorData.isSelectionMode = false;
    const activeSubfield = window.contentExtractorData.activeSubfield;
    window.contentExtractorData.activeSubfield = null;
    
    // Remove event listeners
    document.removeEventListener('click', handleSubfieldElementClick, true);
    document.removeEventListener('mouseover', handleMouseOver, true);
    document.removeEventListener('mouseout', handleMouseOut, true);
    
    // Remove selection indicator
    const indicator = document.getElementById('selection-mode-indicator');
    if (indicator) {
        indicator.remove();
    }
    
    // Clear hover effects
    document.querySelectorAll('*').forEach(el => {
        if (!window.contentExtractorData.selectedDOMElements.has(el)) {
            el.style.outline = '';
            el.style.outlineOffset = '';
        }
    });
    
    // Return to subfields list
    if (activeSubfield) {
        createInstanceSubfieldsMenu(activeSubfield.fieldName, activeSubfield.instanceIndex);
    }
};

function handleSubfieldElementClick(event) {
    if (!window.contentExtractorData.isSelectionMode || window.contentExtractorData.isSelectionPaused) {
        return;
    }
    
    const element = event.target;
    
    // Same UI filtering as regular element clicks
    const injectedElementIds = [
        'content-extractor-control-panel',
        'content-extractor-field-menu', 
        'content-extractor-instance-menu',
        'content-extractor-subfields-menu',
        'content-extractor-subfield-method-menu',
        'content-extractor-selection-manager',
        'selection-mode-indicator'
    ];
    
    let currentElement = element;
    while (currentElement && currentElement !== document.body) {
        if (injectedElementIds.includes(currentElement.id) || 
            currentElement.classList.contains('content-extractor-ui')) {
            console.log('🚫 Ignoring click on injected UI element:', currentElement.id || currentElement.className);
            return;
        }
        currentElement = currentElement.parentElement;
    }
    
    event.preventDefault();
    event.stopPropagation();
    
    const activeSubfield = window.contentExtractorData.activeSubfield;
    if (!activeSubfield) return;
    
    const { fieldName, instanceIndex, subfieldName } = activeSubfield;
    
    // Create selection data
    const selection = {
        field_name: `${fieldName}[${instanceIndex}].${subfieldName}`,
        xpath: getElementXPath(element),
        css_selector: getElementCSSSelector(element),
        selected_text: element.textContent.trim(),
        context_path: window.contentExtractorData.contextPath,
        depth: window.contentExtractorData.currentDepth,
        timestamp: Date.now(),
        element_id: generateElementId(),
        input_method: 'page_selection'
    };
    
    // Store in instance subfields
    const instance = window.contentExtractorData.instanceSelections[fieldName][instanceIndex];
    if (!instance.subfields[subfieldName]) {
        instance.subfields[subfieldName] = [];
    }
    
    // Check if this is a single-value subfield
    const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
    const subfield = field.sub_fields.find(sf => sf.name === subfieldName);
    
    if (subfield && subfield.type === 'single' && instance.subfields[subfieldName].length > 0) {
        // Replace previous selection for single-value subfields
        window.contentExtractorData.selectedDOMElements.forEach(el => {
            removeHighlight(el);
        });
        window.contentExtractorData.selectedDOMElements.clear();
        
        instance.subfields[subfieldName] = [selection];
        console.log(`🔄 Replaced previous selection for single-value subfield ${fieldName}[${instanceIndex}].${subfieldName}`);
    } else {
        // Add to existing selections for multi-value subfields
        instance.subfields[subfieldName].push(selection);
    }
    
    // Highlight selected element
    const subfieldColor = subfield.color || field.color;
    highlightElement(element, subfieldColor);
    window.contentExtractorData.selectedDOMElements.add(element);
    
    console.log(`✅ Selected element for ${fieldName}[${instanceIndex}].${subfieldName}:`, element.textContent.trim());
}

function createSubfieldTextInputDialog(fieldName, instanceIndex, subfieldName) {
    const dialogId = 'content-extractor-subfield-text-dialog';
    let existingDialog = document.getElementById(dialogId);
    if (existingDialog) {
        existingDialog.remove();
    }
    
    const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
    const subfield = field.sub_fields.find(sf => sf.name === subfieldName);
    if (!subfield) return;
    
    const dialog = document.createElement('div');
    dialog.id = dialogId;
    dialog.className = 'content-extractor-ui';
    dialog.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        border: 3px solid ${subfield.color || field.color};
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        z-index: 10001;
        max-width: 500px;
        width: 90%;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    `;
    
    const textareaHeight = subfield.type === 'multi-value' ? '120px' : '80px';
    const placeholder = subfield.type === 'multi-value' 
        ? 'Enter multiple values, one per line...' 
        : 'Enter the value...';
    
    dialog.innerHTML = `
        <div style="text-align: center; margin-bottom: 20px;">
            <h3 style="margin: 0; color: ${subfield.color || field.color};">
                ✏️ Enter "${subfield.label}"
            </h3>
            <small style="color: #666;">Manual text input</small>
        </div>
        
        <div style="margin-bottom: 15px; padding: 8px 12px; background: #f8f9fa; border-radius: 6px; font-size: 14px;">
            <strong>${fieldName}[${instanceIndex + 1}].${subfield.label}</strong> (${subfield.type})<br>
            <small style="color: #666;">${subfield.description || 'Subfield'}</small>
        </div>
        
        <div style="margin: 15px 0;">
            <textarea id="subfield-text-input-field" 
                      placeholder="${placeholder}"
                      style="width: 100%; height: ${textareaHeight}; padding: 12px; 
                             border: 2px solid #dee2e6; border-radius: 6px; 
                             font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                             font-size: 14px; resize: vertical; box-sizing: border-box;"
                      onkeydown="if(event.key==='Enter' && !event.shiftKey && '${subfield.type}' === 'single') { event.preventDefault(); saveSubfieldTextInput('${fieldName}', ${instanceIndex}, '${subfieldName}'); }"></textarea>
        </div>
        
        <div style="text-align: center; margin-top: 20px;">
            <button onclick="saveSubfieldTextInput('${fieldName}', ${instanceIndex}, '${subfieldName}')" 
                    style="padding: 10px 20px; margin: 0 5px; background: #28a745; color: white; 
                           border: none; border-radius: 6px; cursor: pointer; font-weight: bold;"
                    onmouseover="this.style.background='#218838'"
                    onmouseout="this.style.background='#28a745'">
                ✅ Save
            </button>
            <button onclick="cancelSubfieldTextInput('${fieldName}', ${instanceIndex}, '${subfieldName}')" 
                    style="padding: 10px 20px; margin: 0 5px; background: #6c757d; color: white; 
                           border: none; border-radius: 6px; cursor: pointer;"
                    onmouseover="this.style.background='#5a6268'"
                    onmouseout="this.style.background='#6c757d'">
                ❌ Cancel
            </button>
        </div>
    `;
    
    document.body.appendChild(dialog);
    
    // Focus the textarea
    setTimeout(() => {
        const textarea = document.getElementById('subfield-text-input-field');
        if (textarea) {
            textarea.focus();
        }
    }, 100);
    
    return dialog;
}

window.saveSubfieldTextInput = function(fieldName, instanceIndex, subfieldName) {
    const textarea = document.getElementById('subfield-text-input-field');
    if (!textarea) return;
    
    const inputValue = textarea.value.trim();
    if (!inputValue) {
        alert('Please enter a value before saving.');
        return;
    }
    
    const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
    const subfield = field.sub_fields.find(sf => sf.name === subfieldName);
    if (!subfield) return;
    
    const instance = window.contentExtractorData.instanceSelections[fieldName][instanceIndex];
    if (!instance.subfields[subfieldName]) {
        instance.subfields[subfieldName] = [];
    }
    
    // Clear existing selections for this subfield
    instance.subfields[subfieldName] = [];
    
    if (subfield.type === 'multi-value') {
        // Split by lines and filter out empty lines
        const values = inputValue.split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0);
        
        values.forEach((value, index) => {
            const selection = {
                field_name: `${fieldName}[${instanceIndex}].${subfieldName}`,
                xpath: null,
                css_selector: null,
                selected_text: value,
                context_path: window.contentExtractorData.contextPath,
                depth: window.contentExtractorData.currentDepth,
                timestamp: Date.now(),
                element_id: `manual-subfield-text-${Date.now()}-${index}`,
                input_method: 'manual_text'
            };
            instance.subfields[subfieldName].push(selection);
        });
        
        console.log(`✅ Saved ${values.length} text values for ${fieldName}[${instanceIndex}].${subfieldName}:`, values);
    } else {
        // Single value
        const selection = {
            field_name: `${fieldName}[${instanceIndex}].${subfieldName}`,
            xpath: null,
            css_selector: null,
            selected_text: inputValue,
            context_path: window.contentExtractorData.contextPath,
            depth: window.contentExtractorData.currentDepth,
            timestamp: Date.now(),
            element_id: `manual-subfield-text-${Date.now()}`,
            input_method: 'manual_text'
        };
        instance.subfields[subfieldName].push(selection);
        
        console.log(`✅ Saved text value for ${fieldName}[${instanceIndex}].${subfieldName}:`, inputValue);
    }
    
    // Close the dialog
    const dialog = document.getElementById('content-extractor-subfield-text-dialog');
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
    feedback.textContent = `✅ ${fieldName}[${instanceIndex + 1}].${subfieldName} saved!`;
    
    document.body.appendChild(feedback);
    setTimeout(() => feedback.remove(), 2000);
    
    // Return to subfields list
    setTimeout(() => {
        createInstanceSubfieldsMenu(fieldName, instanceIndex);
    }, 500);
};

window.cancelSubfieldTextInput = function(fieldName, instanceIndex, subfieldName) {
    console.log(`❌ Cancelled text input for ${fieldName}[${instanceIndex}].${subfieldName}`);
    
    // Close the dialog
    const dialog = document.getElementById('content-extractor-subfield-text-dialog');
    if (dialog) {
        dialog.remove();
    }
    
    // Return to subfield method selection
    setTimeout(() => {
        const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
        const subfield = field.sub_fields.find(sf => sf.name === subfieldName);
        
        const subfieldConfig = {
            ...subfield,
            name: `${fieldName}[${instanceIndex}].${subfieldName}`,
            isSubfield: true,
            parentField: fieldName,
            instanceIndex: instanceIndex,
            subfieldName: subfieldName
        };
        
        createSubfieldMethodMenu(subfieldConfig);
    }, 100);
};

window.clearSubfieldSelections = function(fieldName, instanceIndex, subfieldName) {
    if (confirm(`Clear all selections for "${fieldName}[${instanceIndex + 1}].${subfieldName}"?`)) {
        const instance = window.contentExtractorData.instanceSelections[fieldName][instanceIndex];
        instance.subfields[subfieldName] = [];
        
        console.log(`🗑️ Cleared all selections for ${fieldName}[${instanceIndex}].${subfieldName}`);
        
        // Refresh the subfield method menu
        setTimeout(() => {
            const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
            const subfield = field.sub_fields.find(sf => sf.name === subfieldName);
            
            const subfieldConfig = {
                ...subfield,
                name: `${fieldName}[${instanceIndex}].${subfieldName}`,
                isSubfield: true,
                parentField: fieldName,
                instanceIndex: instanceIndex,
                subfieldName: subfieldName
            };
            
            createSubfieldMethodMenu(subfieldConfig);
        }, 100);
    }
}; 