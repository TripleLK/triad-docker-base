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
        // Start direct selection for simple fields
        startSelection(fieldName);
    }
}

// Start element selection
function startSelection(fieldName) {
    window.contentExtractorData.isSelectionMode = true;
    window.contentExtractorData.activeField = fieldName;
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
        padding: 10px 15px;
        border-radius: 8px;
        z-index: 9999;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    `;
    indicator.innerHTML = `🎯 Selecting: <strong>${fieldName}</strong><br><small>Click elements to select</small>`;
    document.body.appendChild(indicator);
    
    // Show selection manager
    createSelectionManager(fieldName);
    
    document.addEventListener('click', handleElementClick, true);
    document.addEventListener('mouseover', handleMouseOver, true);
    document.addEventListener('mouseout', handleMouseOut, true);
}

// Handle element click during selection
function handleElementClick(event) {
    if (!window.contentExtractorData.isSelectionMode) return;
    
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
    window.contentExtractorData.fieldSelections[fieldName].push(selection);
    
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
    
    // Stop selection for single-value fields
    const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
    if (field && field.type === 'single') {
        setTimeout(() => stopSelection(), 500); // Small delay to show feedback
    }
}

// Handle mouse over during selection
function handleMouseOver(event) {
    if (!window.contentExtractorData.isSelectionMode) return;
    
    const element = event.target;
    if (!window.contentExtractorData.selectedDOMElements.has(element)) {
        element.style.outline = '2px dashed ' + getFieldColor(window.contentExtractorData.activeField);
        element.style.outlineOffset = '1px';
    }
}

// Handle mouse out during selection
function handleMouseOut(event) {
    if (!window.contentExtractorData.isSelectionMode) return;
    
    const element = event.target;
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