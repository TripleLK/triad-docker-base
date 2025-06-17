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

// Field selection handler - SWIFT PHOENIX: Direct XPath selection workflow
function selectField(fieldName) {
    const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
    if (!field) return;
    
    // SWIFT PHOENIX: Skip method menu completely - direct to selections interface
    // User feedback: "The 'how to set' menu can be skipped; everything will be xpaths"
    console.log(`🎯 Swift Phoenix: Direct XPath selection for ${fieldName} - bypassing method menu`);
    startSelection(fieldName);
}

// Load existing selectors for the current domain
async function loadExistingSelectors() {
    const domain = window.location.hostname;
    const apiUrl = `${window.contentExtractorData.baseUrl}/content-extractor/get-site-configuration/?domain=${encodeURIComponent(domain)}`;
    
    try {
        console.log('📥 Loading existing selectors for domain:', domain);
        
        const response = await fetch(apiUrl, {
            method: 'GET',
            headers: {
                'Authorization': 'Token ' + (window.contentExtractorData.apiToken || 'PLACEHOLDER_TOKEN_NEEDS_DYNAMIC_GENERATION')
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // Check if we have successful response with field mappings
        if (result.success && result.field_mappings && Object.keys(result.field_mappings).length > 0) {
            console.log('✅ Found existing configuration for domain:', domain);
            console.log('📋 Field mappings:', result.field_mappings);
            
            // Apply existing selectors to the page
            applyExistingSelectors(result.field_mappings);
            
            // Show notification that existing selectors were loaded
            showExistingSelectorNotification(Object.keys(result.field_mappings).length, domain);
            
            return result.field_mappings;
        } else {
            console.log('📝 No existing configuration found for domain:', domain);
            return {};
        }
    } catch (error) {
        console.error('❌ Error loading existing selectors:', error);
        return {};
    }
}

// Apply existing selectors to the page
function applyExistingSelectors(fieldMappings) {
    if (!fieldMappings || Object.keys(fieldMappings).length === 0) {
        console.log('ℹ️ No field mappings to apply');
        return;
    }
    
    console.log('🎯 Applying existing selectors to page...');
    
    // SWIFT PHOENIX: Initialize fieldComments if not already done
    if (!window.contentExtractorData.fieldComments) {
        window.contentExtractorData.fieldComments = {};
    }
    
    Object.keys(fieldMappings).forEach(fieldName => {
        const config = fieldMappings[fieldName];
        const xpathSelectors = config.xpath_selectors || [];
        const fieldComment = config.comment || '';
        
        // SWIFT PHOENIX: Load field comment from backend configuration
        if (fieldComment && fieldComment !== `Auto-generated from interactive selector on ${window.location.hostname}`) {
            window.contentExtractorData.fieldComments[fieldName] = fieldComment;
            console.log(`💬 Loaded comment for ${fieldName}: "${fieldComment}"`);
        }
        
        if (xpathSelectors.length > 0) {
            // ARCTIC STORM: Fix selector multiplication bug
            // Initialize field selections if not already done
            if (!window.contentExtractorData.fieldSelections[fieldName]) {
                window.contentExtractorData.fieldSelections[fieldName] = [];
            }
            
            // Try to find elements using the stored XPath selectors
            xpathSelectors.forEach((xpath, index) => {
                try {
                    console.log(`🔍 STELLAR HAWK: Testing XPath for ${fieldName}: ${xpath}`);
                    const result = document.evaluate(
                        xpath, 
                        document, 
                        null, 
                        XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, 
                        null
                    );
                    
                    console.log(`📊 STELLAR HAWK: XPath result count: ${result.snapshotLength}`);
                    
                    // ARCTIC STORM: Only create one selection object per XPath, regardless of matches
                    // Check if this XPath is already in the field selections to prevent duplication
                    const existingSelection = window.contentExtractorData.fieldSelections[fieldName].find(
                        sel => sel.xpath === xpath
                    );
                    
                    if (!existingSelection && result.snapshotLength > 0) {
                        // Use the first matched element for the selection data
                        const firstElement = result.snapshotItem(0);
                        
                        // Create ONE selection object for this XPath
                        const selection = {
                            field_name: fieldName,
                            xpath: xpath,
                            css_selector: getElementCSSSelector(firstElement),
                            selected_text: firstElement.textContent.trim(),
                            context_path: window.contentExtractorData.contextPath,
                            depth: window.contentExtractorData.currentDepth,
                            timestamp: Date.now(),
                            element_id: generateElementId(),
                            is_existing: true, // Mark as existing selector
                            match_count: result.snapshotLength // Track how many elements this XPath matches
                        };
                        
                        // Add ONLY ONE selection object per XPath
                        window.contentExtractorData.fieldSelections[fieldName].push(selection);
                        console.log(`✅ ARCTIC STORM: Added single selector for ${fieldName}: ${xpath} (matches ${result.snapshotLength} elements)`);
                    }
                    
                    // Still highlight ALL matched elements for visual feedback
                    for (let i = 0; i < result.snapshotLength; i++) {
                        const element = result.snapshotItem(i);
                        console.log(`✨ STELLAR HAWK: Highlighting element ${i + 1}/${result.snapshotLength}:`, element);
                        
                        // Highlight the element with a special style for existing selectors
                        highlightExistingElement(element, getFieldColor(fieldName), fieldName);
                        window.contentExtractorData.selectedDOMElements.add(element);
                    }
                    
                } catch (xpathError) {
                    console.warn(`⚠️ XPath selector failed for ${fieldName}: ${xpath}`, xpathError);
                }
            });
        }
    });
    
    console.log('🎉 Finished applying existing selectors');
    
    // QUANTUM VAULT: Fix UI synchronization - refresh field menus after loading existing selectors
    // This ensures that if a field menu is currently open, it updates to show the correct field counts
    if (typeof refreshFieldMenus === 'function') {
        console.log('🔄 Refreshing field menus after loading existing selectors');
        refreshFieldMenus();
        console.log('✅ Field menus refreshed with newly loaded selector data');
    }
}

// STELLAR HAWK: Add missing highlightElement function
// This function is called by highlightExistingElement but was not defined globally
function highlightElement(element, color) {
    element.style.setProperty('outline', `3px solid ${color}`, 'important');
    element.style.setProperty('outline-offset', '2px', 'important');
    element.style.setProperty('box-shadow', `0 0 0 1px ${color}20`, 'important');
}

// Highlight existing selector elements with special styling
function highlightExistingElement(element, fieldColor, fieldName) {
    // Apply base highlight
    highlightElement(element, fieldColor);
    
    // Add additional styling to indicate this is a pre-existing selector
    element.style.setProperty('border', '2px dashed ' + fieldColor, 'important');
    element.style.setProperty('background-color', fieldColor + '15', 'important'); // Light background
    
    // Add a special badge for existing selectors
    const badge = document.createElement('div');
    badge.className = 'content-extractor-ui existing-selector-badge';
    badge.setAttribute('data-field-name', fieldName);
    badge.style.cssText = `
        position: absolute;
        top: -12px;
        left: -2px;
        background: ${fieldColor};
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: bold;
        z-index: 9998;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        pointer-events: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        border: 1px solid rgba(255,255,255,0.3);
    `;
    badge.textContent = `✓ ${fieldName}`;
    
    // Position the badge relative to the element
    const rect = element.getBoundingClientRect();
    if (rect.top < 20) {
        // If element is near top of page, put badge below
        badge.style.top = '100%';
        badge.style.marginTop = '2px';
    }
    
    element.style.position = 'relative';
    element.appendChild(badge);
}

// Show notification that existing selectors were loaded
function showExistingSelectorNotification(count, domain) {
    const notification = document.createElement('div');
    notification.className = 'content-extractor-ui';
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        left: 20px;
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
        padding: 15px 20px;
        border-radius: 12px;
        z-index: 10001;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        border: 2px solid rgba(255,255,255,0.3);
        backdrop-filter: blur(10px);
        max-width: 350px;
    `;
    
    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
            <span style="font-size: 18px;">✨</span>
            <div>
                <div style="font-weight: bold; font-size: 16px;">Existing Selectors Loaded</div>
                <div style="font-size: 12px; opacity: 0.9;">Domain: ${domain}</div>
            </div>
        </div>
        <div style="font-size: 13px; margin-bottom: 10px;">
            Found <strong>${count} configured fields</strong> with existing selectors.
            Elements are highlighted with dashed borders and checkmark badges.
        </div>
        <div style="text-align: right;">
            <button onclick="this.parentElement.remove()" 
                    style="padding: 6px 12px; background: rgba(255,255,255,0.2); 
                           color: white; border: 1px solid rgba(255,255,255,0.4); 
                           border-radius: 6px; cursor: pointer; font-size: 12px;">
                Got it
            </button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 8 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(-100%)';
            notification.style.transition = 'all 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }
    }, 8000);
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
    
    // CRIMSON FALCON: Trigger field menu refresh after selection changes
    // This ensures completion indicators update immediately
    if (typeof refreshFieldMenus === 'function') {
        refreshFieldMenus();
        console.log('🔄 Field menu refreshed after selection');
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

// Stop selection mode and save configurations to backend
window.stopSelection = function() {
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
    if (typeof closeSelectionManager === 'function') {
        closeSelectionManager();
    }
    
    // Clear hover effects
    document.querySelectorAll('*').forEach(el => {
        if (!window.contentExtractorData.selectedDOMElements.has(el)) {
            el.style.outline = '';
            el.style.outlineOffset = '';
        }
    });
    
    console.log('🛑 Selection mode stopped');
    
    // Save configurations to backend if there are selections
    saveConfigurationsToBackend();
};

// Save XPath configurations to the backend
function saveConfigurationsToBackend() {
    const fieldSelections = window.contentExtractorData.fieldSelections || {};
    const fieldComments = window.contentExtractorData.fieldComments || {};
    
    // Check if there are any selections to save
    const hasSelections = Object.keys(fieldSelections).some(fieldName => 
        fieldSelections[fieldName] && fieldSelections[fieldName].length > 0
    );
    
    if (!hasSelections) {
        console.log('📝 No selections to save');
        return;
    }
    
    // Extract domain from current URL
    const domain = window.location.hostname;
    
    // Prepare field mappings for backend
    const field_mappings = {};
    
    Object.keys(fieldSelections).forEach(fieldName => {
        const selections = fieldSelections[fieldName];
        if (selections && selections.length > 0) {
            // Extract XPath selectors (filter out null/undefined values from manual text inputs)
            const xpaths = selections
                .map(selection => selection.xpath)
                .filter(xpath => xpath && xpath.trim());
            
            if (xpaths.length > 0) {
                // SWIFT PHOENIX: Use actual user field comment instead of generic message
                const userComment = fieldComments[fieldName] || '';
                const defaultComment = userComment || `Auto-generated from interactive selector on ${window.location.hostname}`;
                
                // Create proper field mapping object format expected by backend
                field_mappings[fieldName] = {
                    xpath_selectors: xpaths,
                    comment: defaultComment
                };
                
                console.log(`💬 Field ${fieldName}: Using comment "${userComment || '(auto-generated)'}"`);
            }
        }
    });
    
    // Only proceed if we have XPath selectors to save
    if (Object.keys(field_mappings).length === 0) {
        console.log('📝 No XPath selectors to save (manual text entries only)');
        return;
    }
    
    console.log('📡 ARCTIC STORM: Backend will auto-delete missing fields. Sending current fields:', Object.keys(field_mappings));
    
    // Show saving indicator
    const savingIndicator = document.createElement('div');
    savingIndicator.id = 'saving-indicator';
    savingIndicator.className = 'content-extractor-ui';
    savingIndicator.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #007bff;
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        z-index: 10002;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        min-width: 200px;
        text-align: center;
    `;
    savingIndicator.innerHTML = `
        <div style="font-weight: bold; margin-bottom: 5px;">💾 Saving Configuration...</div>
        <div style="font-size: 12px;">Domain: ${domain}</div>
    `;
    document.body.appendChild(savingIndicator);
    
    // Prepare data for backend
    const data = {
        domain: domain,
        site_name: document.title || domain,
        field_mappings: field_mappings
    };
    
    console.log('📡 Saving configuration to backend:', data);
    
    // Send to backend - Use configurable base URL
    const apiUrl = `${window.contentExtractorData.baseUrl}/content-extractor/save-configuration/`;
    console.log('📍 API URL:', apiUrl);
    
    fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            // Use dynamically generated API token from management command
            'Authorization': 'Token ' + (window.contentExtractorData.apiToken || 'PLACEHOLDER_TOKEN_NEEDS_DYNAMIC_GENERATION')
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        console.log('✅ Configuration saved successfully:', result);
        
        // Update indicator with success message
        savingIndicator.style.background = '#28a745';
        savingIndicator.innerHTML = `
            <div style="font-weight: bold; margin-bottom: 5px;">✅ Configuration Saved!</div>
            <div style="font-size: 12px;">
                ${result.total_fields} fields configured for ${domain}
            </div>
            <div style="font-size: 11px; margin-top: 5px;">
                New: ${result.saved_fields?.length || 0}, Updated: ${result.updated_fields?.length || 0}
            </div>
        `;
        
        // Remove success indicator after delay
        setTimeout(() => {
            if (savingIndicator.parentNode) {
                savingIndicator.remove();
            }
        }, 5000);
        
        // Show detailed success notification
        showSaveSuccessDetail(result);
    })
    .catch(error => {
        console.error('❌ Error saving configuration:', error);
        
        // Update indicator with error message
        savingIndicator.style.background = '#dc3545';
        savingIndicator.innerHTML = `
            <div style="font-weight: bold; margin-bottom: 5px;">❌ Save Failed</div>
            <div style="font-size: 12px;">
                Error: ${error.message || 'Network error'}
            </div>
            <div style="font-size: 11px; margin-top: 5px;">
                Check console for details
            </div>
        `;
        
        // Remove error indicator after longer delay
        setTimeout(() => {
            if (savingIndicator.parentNode) {
                savingIndicator.remove();
            }
        }, 8000);
    });
}

// Show detailed success notification
function showSaveSuccessDetail(result) {
    const detailModal = document.createElement('div');
    detailModal.className = 'content-extractor-ui';
    detailModal.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        color: #333;
        padding: 20px;
        border-radius: 12px;
        z-index: 10003;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        max-width: 500px;
        border: 2px solid #28a745;
    `;
    
    const savedFieldsList = result.saved_fields?.map(field => typeof field === 'object' ? field.field : field).join(', ') || '';
    const updatedFieldsList = result.updated_fields?.join(', ') || '';
    const deletedFieldsList = result.deleted_fields?.join(', ') || '';
    
    // ARCTIC STORM: Build sections for different operation types
    let sectionsHTML = '';
    
    if (result.saved_fields?.length > 0) {
        const newCount = result.saved_fields.filter(f => !result.updated_fields?.includes(typeof f === 'object' ? f.field : f)).length;
        if (newCount > 0) {
            sectionsHTML += `
                <div style="margin-bottom: 15px;">
                    <strong>✅ New Fields Configured (${newCount}):</strong>
                    <div style="margin: 5px 0; padding: 8px; background: #d4edda; border-radius: 4px; font-size: 13px;">
                        ${savedFieldsList}
                    </div>
                </div>
            `;
        }
    }
    
    if (result.updated_fields?.length > 0) {
        sectionsHTML += `
            <div style="margin-bottom: 15px;">
                <strong>🔄 Updated Fields (${result.updated_fields.length}):</strong>
                <div style="margin: 5px 0; padding: 8px; background: #d1ecf1; border-radius: 4px; font-size: 13px;">
                    ${updatedFieldsList}
                </div>
            </div>
        `;
    }
    
    if (result.deleted_fields?.length > 0) {
        sectionsHTML += `
            <div style="margin-bottom: 15px;">
                <strong>🗑️ Auto-Deleted Fields (${result.deleted_fields.length}):</strong>
                <div style="margin: 5px 0; padding: 8px; background: #f8d7da; border-radius: 4px; font-size: 13px;">
                    ${deletedFieldsList}
                </div>
                <div style="font-size: 11px; color: #666; margin-top: 5px;">
                    ℹ️ Fields removed because they were cleared in the interface
                </div>
            </div>
        `;
    }
    
    detailModal.innerHTML = `
        <div style="text-align: center; margin-bottom: 15px;">
            <div style="font-size: 18px; font-weight: bold; color: #28a745; margin-bottom: 10px;">
                ✅ Configuration Saved Successfully!
            </div>
            <div style="font-size: 14px; color: #666;">
                Domain: <strong>${result.domain || 'Unknown'}</strong>
            </div>
            <div style="font-size: 12px; color: #888; margin-top: 5px;">
                Total Active Fields: ${result.total_fields || 0}
            </div>
        </div>
        
        ${sectionsHTML}
        
        <div style="text-align: center; margin-top: 20px;">
            <button onclick="this.parentElement.parentElement.remove()" 
                    style="padding: 8px 16px; background: #28a745; color: white; 
                           border: none; border-radius: 6px; cursor: pointer; font-size: 14px;">
                Continue
            </button>
            <button onclick="window.open('/admin/snippets/content_extractor/siteconfiguration/', '_blank')" 
                    style="padding: 8px 16px; background: #007bff; color: white; 
                           border: none; border-radius: 6px; cursor: pointer; font-size: 14px; margin-left: 10px;">
                View in Admin
            </button>
        </div>
    `;
    
    document.body.appendChild(detailModal);
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

// THUNDER CASCADE: Add field comment functionality for simplified approach
window.addFieldComment = function(fieldName) {
    console.log(`💬 Adding comment for ${fieldName}`);
    closeFieldSettingMethodMenu();
    createFieldCommentDialog(fieldName);
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
        // ARCTIC STORM: Clear locally - backend will auto-delete missing fields on save
        window.contentExtractorData.fieldSelections[fieldName] = [];
        
        // Remove highlights for this field
        window.contentExtractorData.selectedDOMElements.forEach(element => {
            removeHighlight(element);
        });
        window.contentExtractorData.selectedDOMElements.clear();
        
        console.log(`🗑️ ARCTIC STORM: Cleared ${fieldName} locally - will be auto-deleted on save`);
        
        // CRIMSON FALCON: Refresh field menus after clearing selections
        if (typeof refreshFieldMenus === 'function') {
            refreshFieldMenus();
            console.log('🔄 Field menu refreshed after clearing selections');
        }
        
        // Refresh the method menu to show updated state
        setTimeout(() => {
            createFieldSettingMethodMenu(fieldName);
        }, 100);
        
        // Update control panel
        if (typeof window.updateControlPanelProgress === 'function') {
            window.updateControlPanelProgress();
        }
        
        // Show local clear feedback
        const feedback = document.createElement('div');
        feedback.className = 'content-extractor-ui';
        feedback.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #17a2b8;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            z-index: 10003;
            font-size: 14px;
            font-weight: bold;
            animation: fadeInOut 3s ease-in-out;
        `;
        feedback.textContent = `🗑️ ${fieldName} cleared - will be removed on "Finish"`;
        
        document.body.appendChild(feedback);
        setTimeout(() => feedback.remove(), 3000);
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
    
    // CRIMSON FALCON: Refresh field menus after text input save
    if (typeof refreshFieldMenus === 'function') {
        refreshFieldMenus();
        console.log('🔄 Field menu refreshed after text input save');
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
    
    // SWIFT PHOENIX: Refresh main menu after instance creation
    // Addresses Priority 2 - Cross-menu communication
    if (typeof refreshFieldMenus === 'function') {
        refreshFieldMenus();
        console.log('🔄 Swift Phoenix: Main menu refreshed after instance creation');
    }
    
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
        
        // SWIFT PHOENIX: Refresh main menu after instance deletion
        // Addresses Priority 2 - Cross-menu communication
        if (typeof refreshFieldMenus === 'function') {
            refreshFieldMenus();
            console.log('🔄 Swift Phoenix: Main menu refreshed after instance deletion');
        }
        
        // Refresh using unified menu system
        if (window.ContentExtractorUnifiedMenu) {
            window.ContentExtractorUnifiedMenu.createInstanceMenu(fieldName);
        } else {
            console.error(`❌ [ERROR] ContentExtractorUnifiedMenu not available`);
            createInstanceManagementMenu(fieldName);
        }
        
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
    // Use unified menu system
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
        // Critical error - unified menu system not available
        console.error(`❌ [ERROR] ContentExtractorUnifiedMenu not available - subfield menu cannot be created`);
        console.error(`💡 [SOLUTION] Include content_extractor_unified_menu.js before this file`);
        return null;
    }
}

// Build subfields menu content HTML with unified field menu styling
function buildSubfieldsMenuContent(field, instanceIndex, instance) {
    // Get fresh completion data for subfields (similar to main field menu)
    let completedSubfields = 0;
    let totalSubfields = field.sub_fields.length;
    let totalSubfieldSelections = 0;
    
    field.sub_fields.forEach(subfield => {
        const subfieldSelections = instance.subfields[subfield.name] || [];
        if (subfieldSelections.length > 0) {
            completedSubfields++;
            totalSubfieldSelections += subfieldSelections.length;
        }
    });
    
    // Build subfield options using the same style as main field menu
    let subfieldsHtml = '';
    field.sub_fields.forEach(subfield => {
        const icon = subfield.type === 'multi-value' ? '📋' : '📝';
        
        // Use direct access like main field menu
        const subfieldSelections = instance.subfields[subfield.name] || [];
        const hasSelections = subfieldSelections.length > 0;
        const selectionCount = subfieldSelections.length;
        
        // Selection indicator - identical to main field menu style
        let selectionIndicator = '';
        if (hasSelections) {
            selectionIndicator = `
                <span style="float: right; background: #28a745; color: white; 
                             padding: 2px 6px; border-radius: 10px; font-size: 11px; font-weight: bold;">
                    ✓ ${selectionCount}
                </span>
            `;
        } else {
            selectionIndicator = `
                <span style="float: right; background: #6c757d; color: white; 
                             padding: 2px 6px; border-radius: 10px; font-size: 11px;">
                    ○
                </span>
            `;
        }
        
        // Button styling based on current selection status - identical to main field menu
        const buttonStyle = hasSelections 
            ? `background: ${subfield.color || field.color}40; border: 2px solid #28a745; box-shadow: 0 2px 4px rgba(40, 167, 69, 0.2);`
            : `background: ${subfield.color || field.color}20; border: 2px solid ${subfield.color || field.color};`;
        
        // Get current XPath for display (like "Last:" in main field menu)
        const lastSelection = hasSelections ? subfieldSelections[subfieldSelections.length - 1] : null;
        const currentXPath = lastSelection ? lastSelection.xpath : '';
        const lastSelectionText = lastSelection ? lastSelection.selected_text || '' : '';
        
        subfieldsHtml += `
            <button onclick="selectSubfield('${field.name}', ${instanceIndex}, '${subfield.name}')" 
                    style="display: block; width: 100%; margin: 8px 0; padding: 12px; 
                           ${buttonStyle}
                           border-radius: 8px; cursor: pointer; text-align: left;
                           font-size: 14px; transition: all 0.2s; position: relative;"
                    onmouseover="this.style.transform='scale(1.02)'; this.style.boxShadow='0 4px 8px rgba(0,0,0,0.1)'"
                    onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='${hasSelections ? '0 2px 4px rgba(40, 167, 69, 0.2)' : 'none'}'">
                ${selectionIndicator}
                ${icon} <strong>${subfield.label}</strong><br>
                <small style="color: #666;">${subfield.description || subfield.type}</small>
                ${hasSelections && lastSelectionText ? `<br><small style="color: #28a745; font-weight: bold;">Last: "${lastSelectionText.substring(0, 30)}${lastSelectionText.length > 30 ? '...' : ''}"</small>` : ''}
                ${hasSelections && currentXPath ? `<br><small style="color: #007bff; font-weight: bold;">XPath: ${currentXPath.substring(0, 40)}${currentXPath.length > 40 ? '...' : ''}</small>` : ''}
            </button>
        `;
    });
    
    // Selection summary - using same style as main field menu
    const summaryHtml = totalSubfieldSelections > 0 ? `
        <div style="margin: 15px 0; padding: 10px; background: #e8f5e8; border-radius: 6px; text-align: center;">
            <strong style="color: #28a745;">📊 Progress: ${completedSubfields}/${totalSubfields} subfields completed</strong><br>
            <small style="color: #666;">Total selections: ${totalSubfieldSelections}</small>
        </div>
    ` : '';
    
    return summaryHtml + subfieldsHtml;
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
        // Critical error - unified menu system not available
        console.error(`❌ [ERROR] ContentExtractorUnifiedMenu not available - subfield menu cannot be created`);
        alert('Error: Menu system not properly loaded. Please refresh the page.');
        return;
    }
};

// Helper function to open XPath editor for subfields
window.openSubfieldXPathEditor = function(fieldName, instanceIndex, subfieldName) {
    console.log(`🔧 [DEBUG] Opening XPath editor for subfield: ${fieldName}[${instanceIndex}].${subfieldName}`);
    
    const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
    if (!field) {
        console.error(`❌ [ERROR] Field not found: ${fieldName}`);
        return;
    }
    
    const subfield = field.sub_fields.find(sf => sf.name === subfieldName);
    if (!subfield) {
        console.error(`❌ [ERROR] Subfield not found: ${subfieldName} in field ${fieldName}`);
        return;
    }
    
    const instance = window.contentExtractorData.instanceSelections[fieldName][instanceIndex];
    if (!instance) {
        console.error(`❌ [ERROR] Instance not found: ${fieldName}[${instanceIndex}]`);
        return;
    }
    
    const subfieldSelections = instance.subfields[subfieldName] || [];
    console.log(`📊 [DEBUG] Found ${subfieldSelections.length} subfield selections`);
    
    // Get the last XPath if available
    const lastSelection = subfieldSelections.length > 0 ? subfieldSelections[subfieldSelections.length - 1] : null;
    const currentXPath = lastSelection ? lastSelection.xpath : '';
    console.log(`📋 [DEBUG] Current XPath: ${currentXPath || 'None'}`);
    
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
            console.log(`🎯 [DEBUG] Found target element:`, targetElement);
        } catch (error) {
            console.warn('⚠️ [WARN] Could not find target element for XPath editor:', error);
        }
    }
    
    // Set up XPath editor context for subfield - CRITICAL FIX
    if (window.ContentExtractorXPathEditor) {
        console.log(`📝 [DEBUG] Setting subfield context in XPath editor`);
        window.ContentExtractorXPathEditor.currentSubfieldContext = {
            fieldName: fieldName,
            instanceIndex: instanceIndex,
            subfieldName: subfieldName
        };
        console.log(`✅ [DEBUG] Subfield context set:`, window.ContentExtractorXPathEditor.currentSubfieldContext);
    } else {
        console.error(`❌ [ERROR] ContentExtractorXPathEditor not available`);
        return;
    }
    
    // Use unified menu system for XPath editor
    const fieldDisplayName = `${field.label}[${instanceIndex + 1}].${subfield.label}`;
    console.log(`🖥️ [DEBUG] Opening XPath editor with field name: ${fieldDisplayName}`);
    
    if (window.ContentExtractorUnifiedMenu) {
        console.log(`🚀 [DEBUG] Using unified menu system to create XPath editor`);
        window.ContentExtractorUnifiedMenu.createXPathEditor(targetElement, fieldDisplayName, currentXPath);
    } else {
        console.error(`❌ [ERROR] ContentExtractorUnifiedMenu not available`);
        // Fallback
        window.openXPathEditor(targetElement, fieldDisplayName);
    }
    
    console.log(`✅ [DEBUG] XPath editor setup complete for subfield`);
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
    
    // Close any open menus
    const parentMenu = document.getElementById('content-extractor-parent-selector-menu');
    if (parentMenu) {
        parentMenu.remove();
    }
    
    const subfieldMenu = document.getElementById('content-extractor-subfields-menu');
    if (subfieldMenu) {
        subfieldMenu.remove();
    }
    
    // Always use unified menu system
    if (window.ContentExtractorUnifiedMenu) {
        window.ContentExtractorUnifiedMenu.createInstanceMenu(fieldName);
    } else {
        console.error(`❌ [ERROR] ContentExtractorUnifiedMenu not available`);
        // Fallback to old system
        createInstanceManagementMenu(fieldName);
    }
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
    
    // STELLAR NEXUS: Check parent container scoping
    const instance = window.contentExtractorData.instanceSelections[fieldName][instanceIndex];
    if (instance.parentContainer && instance.parentContainer.xpath) {
        // Find parent container element
        const parentElement = findElementByXPath(instance.parentContainer.xpath);
        if (parentElement) {
            // Check if selected element is within parent container
            if (!parentElement.contains(element)) {
                console.log('🚫 Element outside parent container scope:', element);
                showParentScopeWarning(fieldName, instanceIndex, subfieldName);
                return;
            }
            console.log('✅ Element within parent container scope');
        } else {
            console.warn('⚠️ Parent container element not found on page');
        }
    }
    
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
        input_method: 'page_selection',
        parentRelative: instance.parentContainer ? true : false // Mark as parent-scoped
    };
    
    // If parent container exists, create relative XPath
    if (instance.parentContainer && instance.parentContainer.xpath) {
        const parentElement = findElementByXPath(instance.parentContainer.xpath);
        if (parentElement) {
            selection.xpath = getRelativeXPath(element, parentElement);
            selection.parentXPath = instance.parentContainer.xpath;
            console.log('🎯 Created parent-relative XPath:', selection.xpath);
        }
    }
    
    // Store in instance subfields
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
    
    // SWIFT PHOENIX: Refresh main menu after subfield selection
    // Addresses Priority 2 - Cross-menu communication
    if (typeof refreshFieldMenus === 'function') {
        refreshFieldMenus();
        console.log('🔄 Swift Phoenix: Main menu refreshed after subfield element selection');
    }
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
    
    // SWIFT PHOENIX: Refresh main menu after subfield text input save
    // Addresses Priority 2 - Cross-menu communication
    if (typeof refreshFieldMenus === 'function') {
        refreshFieldMenus();
        console.log('🔄 Swift Phoenix: Main menu refreshed after subfield text input save');
    }
    
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
        
        // SWIFT PHOENIX: Refresh main menu after subfield clearing
        // Addresses Priority 2 - Cross-menu communication
        if (typeof refreshFieldMenus === 'function') {
            refreshFieldMenus();
            console.log('🔄 Swift Phoenix: Main menu refreshed after subfield clearing');
        }
        
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

// Parent selection functions - Stellar Nexus Implementation
window.setParentContainer = function(fieldName, instanceIndex) {
    console.log(`🎯 Setting parent container for ${fieldName}[${instanceIndex}]`);
    
    if (window.ContentExtractorUnifiedMenu) {
        window.ContentExtractorUnifiedMenu.createParentSelectionMenu(fieldName, instanceIndex);
    } else {
        console.error(`❌ [ERROR] ContentExtractorUnifiedMenu not available`);
    }
};

window.startParentSelection = function(fieldName, instanceIndex) {
    console.log(`🎯 Starting parent element selection for ${fieldName}[${instanceIndex}]`);
    
    // Store selection context
    window.contentExtractorData.parentSelectionContext = {
        fieldName: fieldName,
        instanceIndex: instanceIndex,
        active: true
    };
    
    // Close parent selection menu
    const parentMenu = document.getElementById('content-extractor-parent-selector-menu');
    if (parentMenu) {
        parentMenu.remove();
    }
    
    // Add parent selection overlay similar to field selection
    addParentSelectionOverlay();
    
    // Enable parent selection mode
    enableParentSelectionMode();
    
    // Show selection indicator
    showParentSelectionIndicator(fieldName, instanceIndex);
};

function addParentSelectionOverlay() {
    // Remove any existing overlays
    const existingOverlays = document.querySelectorAll('.content-extractor-ui.parent-selection-overlay');
    existingOverlays.forEach(overlay => overlay.remove());
    
    // Create parent selection overlay
    const overlay = document.createElement('div');
    overlay.className = 'content-extractor-ui parent-selection-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.1);
        z-index: 9999;
        pointer-events: none;
        backdrop-filter: blur(1px);
    `;
    
    document.body.appendChild(overlay);
    console.log('🎯 Parent selection overlay added');
}

function enableParentSelectionMode() {
    // Remove existing event listeners
    document.removeEventListener('click', handleElementClick, true);
    document.removeEventListener('mouseover', handleMouseOver, true);
    document.removeEventListener('mouseout', handleMouseOut, true);
    
    // Add parent selection event listeners
    document.addEventListener('click', handleParentElementClick, true);
    document.addEventListener('mouseover', handleParentMouseOver, true);
    document.addEventListener('mouseout', handleParentMouseOut, true);
    
    console.log('🎯 Parent selection mode enabled');
}

function handleParentElementClick(event) {
    // Prevent default behavior
    event.preventDefault();
    event.stopPropagation();
    
    const target = event.target;
    
    // Skip content extractor UI elements
    if (target.closest('.content-extractor-ui')) {
        console.log('🎯 Skipping content extractor UI element');
        return;
    }
    
    const context = window.contentExtractorData.parentSelectionContext;
    if (!context || !context.active) {
        console.log('🎯 Parent selection context not active');
        return;
    }
    
    console.log(`🎯 Parent element clicked for ${context.fieldName}[${context.instanceIndex}]`, target);
    
    // Get element details
    const xpath = getElementXPath(target);
    const selectedText = target.textContent.trim();
    
    // Create parent container data
    const parentContainer = {
        xpath: xpath,
        selected_text: selectedText,
        timestamp: Date.now()
    };
    
    // Store parent container in instance
    const instance = window.contentExtractorData.instanceSelections[context.fieldName][context.instanceIndex];
    if (instance) {
        instance.parentContainer = parentContainer;
        console.log(`✅ Parent container saved for ${context.fieldName}[${context.instanceIndex}]:`, parentContainer);
        
        // Highlight the selected parent element
        highlightParentElement(target, getFieldColor(context.fieldName));
        
        // Disable parent selection mode
        disableParentSelectionMode();
        
        // Show success feedback
        showParentSelectionSuccess(context.fieldName, context.instanceIndex, selectedText);
        
        // Return to instance management menu
        setTimeout(() => {
            returnToInstanceManagement(context.fieldName);
        }, 1500);
    } else {
        console.error(`❌ Instance not found: ${context.fieldName}[${context.instanceIndex}]`);
    }
    
    // Clear selection context
    window.contentExtractorData.parentSelectionContext = null;
}

function handleParentMouseOver(event) {
    const target = event.target;
    
    // Skip content extractor UI elements
    if (target.closest('.content-extractor-ui')) {
        return;
    }
    
    // Add hover highlight for potential parent selection
    target.style.setProperty('outline', '3px solid #007bff', 'important');
    target.style.setProperty('outline-offset', '2px', 'important');
    target.style.setProperty('background-color', 'rgba(0, 123, 255, 0.1)', 'important');
    target.style.setProperty('cursor', 'crosshair', 'important');
}

function handleParentMouseOut(event) {
    const target = event.target;
    
    // Skip content extractor UI elements
    if (target.closest('.content-extractor-ui')) {
        return;
    }
    
    // Remove hover highlight
    target.style.removeProperty('outline');
    target.style.removeProperty('outline-offset');
    target.style.removeProperty('background-color');
    target.style.removeProperty('cursor');
}

function disableParentSelectionMode() {
    // Remove parent selection event listeners
    document.removeEventListener('click', handleParentElementClick, true);
    document.removeEventListener('mouseover', handleParentMouseOver, true);
    document.removeEventListener('mouseout', handleParentMouseOut, true);
    
    // Remove overlay
    const overlay = document.querySelector('.content-extractor-ui.parent-selection-overlay');
    if (overlay) {
        overlay.remove();
    }
    
    // Remove selection indicator
    const indicator = document.querySelector('.content-extractor-ui.parent-selection-indicator');
    if (indicator) {
        indicator.remove();
    }
    
    console.log('🎯 Parent selection mode disabled');
}

function highlightParentElement(element, color) {
    // Apply parent container highlighting
    element.style.setProperty('border', '3px solid ' + color, 'important');
    element.style.setProperty('background-color', color + '20', 'important');
    element.style.setProperty('box-shadow', '0 0 10px ' + color + '80', 'important');
    
    // Add parent container badge
    const badge = document.createElement('div');
    badge.className = 'content-extractor-ui parent-container-badge';
    badge.style.cssText = `
        position: absolute;
        top: -15px;
        left: -3px;
        background: ${color};
        color: white;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: bold;
        z-index: 9998;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        pointer-events: none;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        border: 2px solid white;
    `;
    badge.textContent = '🎯 PARENT CONTAINER';
    
    element.style.position = 'relative';
    element.appendChild(badge);
    
    console.log('🎯 Parent element highlighted with badge');
}

function showParentSelectionIndicator(fieldName, instanceIndex) {
    const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
    if (!field) return;
    
    const indicator = document.createElement('div');
    indicator.className = 'content-extractor-ui parent-selection-indicator';
    indicator.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: linear-gradient(135deg, ${field.color}, ${field.color}dd);
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        z-index: 10001;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        font-weight: bold;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        border: 2px solid white;
        text-align: center;
        animation: slideDown 0.3s ease-out;
    `;
    indicator.innerHTML = `
        <div>🎯 Select Parent Container</div>
        <div style="font-size: 12px; margin-top: 4px; opacity: 0.9;">
            ${field.label}[${instanceIndex + 1}] - Click on parent element
        </div>
    `;
    
    document.body.appendChild(indicator);
}

function showParentSelectionSuccess(fieldName, instanceIndex, selectedText) {
    const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
    if (!field) return;
    
    const success = document.createElement('div');
    success.className = 'content-extractor-ui parent-selection-success';
    success.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
        padding: 20px 30px;
        border-radius: 12px;
        z-index: 10003;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        font-weight: bold;
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        border: 3px solid white;
        text-align: center;
        animation: scaleIn 0.3s ease-out;
    `;
    success.innerHTML = `
        <div style="font-size: 16px; margin-bottom: 8px;">✅ Parent Container Set!</div>
        <div style="font-size: 12px; opacity: 0.9; margin-bottom: 6px;">
            ${field.label}[${instanceIndex + 1}]
        </div>
        <div style="font-size: 11px; background: rgba(255,255,255,0.2); padding: 6px; border-radius: 4px;">
            "${selectedText.substring(0, 60)}${selectedText.length > 60 ? '...' : ''}"
        </div>
    `;
    
    document.body.appendChild(success);
    
    setTimeout(() => {
        success.remove();
    }, 1500);
}

// Add new instance and refresh unified menu
window.addNewInstance = function(fieldName) {
    console.log(`➕ Adding new instance for ${fieldName}`);
    
    if (!window.contentExtractorData.instanceSelections[fieldName]) {
        window.contentExtractorData.instanceSelections[fieldName] = [];
    }
    
    // Create new instance with proper structure 
    const newInstance = {
        instance_index: window.contentExtractorData.instanceSelections[fieldName].length,
        xpath: '',
        selected_text: '',
        timestamp: new Date().toISOString(),
        subfields: {}
    };
    
    // Initialize subfields structure
    const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
    if (field && field.sub_fields) {
        field.sub_fields.forEach(subfield => {
            newInstance.subfields[subfield.name] = [];
        });
    }
    
    window.contentExtractorData.instanceSelections[fieldName].push(newInstance);
    console.log(`✅ Created new instance ${fieldName}[${newInstance.instance_index}]`);
    
    // SWIFT PHOENIX: Refresh main menu after instance creation
    // Addresses Priority 2 - Cross-menu communication
    if (typeof refreshFieldMenus === 'function') {
        refreshFieldMenus();
        console.log('🔄 Swift Phoenix: Main menu refreshed after instance creation');
    }
    
    // Refresh using unified menu system
    if (window.ContentExtractorUnifiedMenu) {
        window.ContentExtractorUnifiedMenu.createInstanceMenu(fieldName);
    } else {
        console.error(`❌ [ERROR] ContentExtractorUnifiedMenu not available`);
        createInstanceManagementMenu(fieldName);
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
    feedback.textContent = `✅ New ${fieldName} instance created!`;
    
    document.body.appendChild(feedback);
    setTimeout(() => feedback.remove(), 2000);
};

// Helper functions for parent scoping - Stellar Nexus Implementation
function findElementByXPath(xpath) {
    try {
        const result = document.evaluate(
            xpath, 
            document, 
            null, 
            XPathResult.FIRST_ORDERED_NODE_TYPE, 
            null
        );
        return result.singleNodeValue;
    } catch (error) {
        console.error('Error finding element by XPath:', xpath, error);
        return null;
    }
}

function getRelativeXPath(element, parentElement) {
    if (!element || !parentElement) {
        return getElementXPath(element);
    }
    
    try {
        // Get full XPath of element
        const fullXPath = getElementXPath(element);
        
        // Get XPath of parent
        const parentXPath = getElementXPath(parentElement);
        
        // If element's XPath starts with parent's XPath, create relative path
        if (fullXPath.startsWith(parentXPath)) {
            // Remove parent path and leading slash
            let relativePath = fullXPath.substring(parentXPath.length);
            if (relativePath.startsWith('/')) {
                relativePath = '.' + relativePath;
            } else {
                relativePath = './' + relativePath;
            }
            
            console.log(`🎯 Relative XPath: ${relativePath} (from parent: ${parentXPath})`);
            return relativePath;
        } else {
            console.warn('⚠️ Element not properly contained in parent, using absolute XPath');
            return fullXPath;
        }
    } catch (error) {
        console.error('Error creating relative XPath:', error);
        return getElementXPath(element);
    }
}

function showParentScopeWarning(fieldName, instanceIndex, subfieldName) {
    const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
    if (!field) return;
    
    const warning = document.createElement('div');
    warning.className = 'content-extractor-ui parent-scope-warning';
    warning.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: linear-gradient(135deg, #dc3545, #c82333);
        color: white;
        padding: 20px 30px;
        border-radius: 12px;
        z-index: 10005;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        font-weight: bold;
        box-shadow: 0 6px 20px rgba(0,0,0,0.4);
        border: 3px solid white;
        text-align: center;
        animation: shakeWarning 0.5s ease-in-out;
        max-width: 400px;
    `;
    warning.innerHTML = `
        <div style="font-size: 18px; margin-bottom: 10px;">🚫 Outside Parent Scope!</div>
        <div style="font-size: 13px; margin-bottom: 8px; opacity: 0.9;">
            ${field.label}[${instanceIndex + 1}].${subfieldName}
        </div>
        <div style="font-size: 12px; background: rgba(255,255,255,0.2); padding: 8px; border-radius: 6px; line-height: 1.4;">
            Selected element is not within the parent container.<br>
            Please select elements inside the parent scope only.
        </div>
    `;
    
    // Add shake animation if not exists
    if (!document.getElementById('parent-scope-warning-style')) {
        const style = document.createElement('style');
        style.id = 'parent-scope-warning-style';
        style.textContent = `
            @keyframes shakeWarning {
                0%, 100% { transform: translate(-50%, -50%) rotate(0deg); }
                25% { transform: translate(-50%, -50%) rotate(1deg); }
                75% { transform: translate(-50%, -50%) rotate(-1deg); }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(warning);
    
    // Remove after delay
    setTimeout(() => {
        warning.remove();
    }, 3000);
    
    console.log(`🚫 Parent scope warning shown for ${fieldName}[${instanceIndex}].${subfieldName}`);
}

// CRIMSON PHOENIX: Missing button event handlers for unified menu system
window.configureSubfields = function(fieldName, instanceIndex) {
    console.log(`⚙️ Configuring subfields for ${fieldName}[${instanceIndex}]`);
    
    const instance = window.contentExtractorData.instanceSelections[fieldName][instanceIndex];
    if (!instance) {
        console.error(`❌ Instance ${fieldName}[${instanceIndex}] not found`);
        return;
    }
    
    // Check if parent container is set
    const hasParent = instance.parentContainer && instance.parentContainer.xpath;
    if (!hasParent) {
        console.warn(`⚠️ No parent container set for ${fieldName}[${instanceIndex}]`);
        // Show warning and redirect to parent selection
        alert('Please set a parent container first before configuring subfields.');
        window.setParentContainer(fieldName, instanceIndex);
        return;
    }
    
    // Open subfields menu
    createInstanceSubfieldsMenu(fieldName, instanceIndex);
};

window.editInstance = function(fieldName, instanceIndex) {
    console.log(`✏️ Editing instance ${fieldName}[${instanceIndex}]`);
    
    // For now, redirect to existing openInstanceSubfields functionality
    // This maintains backward compatibility while using unified menu system
    openInstanceSubfields(fieldName, instanceIndex);
};

// THUNDER CASCADE: Field comment save/cancel functions
window.saveFieldComment = function(fieldName) {
    const textarea = document.getElementById('comment-input-field');
    if (!textarea) return;
    
    const commentValue = textarea.value.trim();
    
    // Initialize fieldComments if not exists
    if (!window.contentExtractorData.fieldComments) {
        window.contentExtractorData.fieldComments = {};
    }
    
    // Save comment (even if empty to clear existing)
    window.contentExtractorData.fieldComments[fieldName] = commentValue;
    
    console.log(`💾 Saved comment for ${fieldName}:`, commentValue || '(empty)');
    
    // Close the dialog
    const dialog = document.getElementById('content-extractor-comment-dialog');
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
        background: #17a2b8;
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        z-index: 10003;
        font-size: 14px;
        font-weight: bold;
        pointer-events: none;
        animation: fadeInOut 2s ease-in-out;
    `;
    feedback.textContent = `💬 Comment ${commentValue ? 'saved' : 'cleared'} for ${fieldName}!`;
    
    document.body.appendChild(feedback);
    setTimeout(() => feedback.remove(), 2000);
    
    // Return to method selection menu
    setTimeout(() => {
        createFieldSettingMethodMenu(fieldName);
    }, 500);
};

window.cancelFieldComment = function(fieldName) {
    console.log(`❌ Cancelled comment input for ${fieldName}`);
    
    // Close the dialog
    const dialog = document.getElementById('content-extractor-comment-dialog');
    if (dialog) {
        dialog.remove();
    }
    
    // Return to method selection menu
    setTimeout(() => {
        createFieldSettingMethodMenu(fieldName);
    }, 100);
};