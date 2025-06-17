/**
 * Content Extractor Selection Management
 * 
 * This file contains selection management, navigation, control panel,
 * and global interface initialization functions.
 * 
 * Created by: Electric Sentinel
 * Date: 2025-01-08
 * Project: Triad Docker Base
 */

// Navigate to parent level
function navigateToParent() {
    window.contentExtractorData.pendingAction = {
        type: 'navigate_to_parent'
    };
    closeFieldMenu();
    closeInstanceMenu();
}

// Enter nested field context
function enterNestedField(fieldName, instanceIndex = 0) {
    window.contentExtractorData.pendingAction = {
        type: 'enter_nested_field',
        field_name: fieldName,
        instance_index: instanceIndex
    };
    closeFieldMenu();
    closeInstanceMenu();
}

// Instance management functions
function enterInstanceContext(fieldName, instanceIndex) {
    window.contentExtractorData.pendingAction = {
        type: 'enter_instance_context',
        field_name: fieldName,
        instance_index: instanceIndex
    };
    closeInstanceMenu();
}

function addNewInstance(fieldName) {
    window.contentExtractorData.pendingAction = {
        type: 'add_new_instance',
        field_name: fieldName
    };
}

// Menu management functions - explicitly attached to window
window.showFieldMenu = function() {
    console.log('📋 showFieldMenu called');
    
    // CRIMSON FALCON: Ensure menu shows current field state data
    // This guarantees fresh completion indicators every time menu opens
    console.log('🔄 Ensuring fresh field state data before showing menu');
    
    window.createFieldMenu();
};

window.createFieldMenu = createFieldMenu; // Attach to window

window.closeFieldMenu = function() {
    console.log('❌ closeFieldMenu called');
    const menu = document.getElementById('content-extractor-field-menu');
    if (menu) {
        menu.remove();
    }
};

window.closeInstanceMenu = function() {
    console.log('❌ closeInstanceMenu called - returning to field menu');
    const menu = document.getElementById('content-extractor-instance-menu');
    if (menu) {
        menu.remove();
    }
    // Return to field menu when instance menu closes
    setTimeout(() => {
        window.showFieldMenu();
    }, 100);
};

// Control panel integration
window.createControlPanel = function() {
    console.log('🎛️ Creating control panel');
    
    // Remove existing panel if present
    const existingPanel = document.getElementById('content-extractor-control-panel');
    if (existingPanel) {
        existingPanel.remove();
    }
    
    const panel = document.createElement('div');
    panel.id = 'content-extractor-control-panel';
    panel.className = 'content-extractor-ui'; // Mark as our UI
    panel.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        width: 200px;
        background: white;
        border: 2px solid #007bff;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 9998;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 13px;
        cursor: move;
    `;
    
    // Add draggable functionality
    let isDragging = false;
    let dragOffset = { x: 0, y: 0 };
    
    panel.addEventListener('mousedown', function(e) {
        if (e.target === panel || e.target.closest('strong')) {
            isDragging = true;
            const rect = panel.getBoundingClientRect();
            dragOffset.x = e.clientX - rect.left;
            dragOffset.y = e.clientY - rect.top;
            panel.style.cursor = 'grabbing';
            e.preventDefault();
        }
    });
    
    document.addEventListener('mousemove', function(e) {
        if (isDragging) {
            panel.style.left = (e.clientX - dragOffset.x) + 'px';
            panel.style.top = (e.clientY - dragOffset.y) + 'px';
            panel.style.right = 'auto'; // Remove right positioning when dragging
        }
    });
    
    document.addEventListener('mouseup', function() {
        if (isDragging) {
            isDragging = false;
            panel.style.cursor = 'move';
        }
    });
    
    // Progress information
    // QUANTUM VAULT: Fix UI synchronization - use proper completion summary instead of flawed counting
    const summary = getFieldCompletionSummary ? getFieldCompletionSummary() : {
        completedFields: Object.keys(window.contentExtractorData.fieldSelections).filter(fieldName => {
            const selections = window.contentExtractorData.fieldSelections[fieldName];
            return selections && selections.length > 0;
        }).length,
        totalFields: window.contentExtractorData.fieldOptions.length
    };
    
    const progressHtml = summary.totalFields > 0 ? `
        <div class="progress-info" style="margin: 10px 0; padding: 8px; background: #e8f4f8; border-radius: 4px; border-left: 3px solid #17a2b8;">
            <div style="font-size: 11px; color: #666; margin-bottom: 3px;">Progress</div>
            <div style="font-size: 12px; color: #333;">
                ${summary.completedFields}/${summary.totalFields} fields selected
            </div>
            <small style="color: #888; font-size: 10px;">
                ${summary.completedFields === summary.totalFields ? '✅ All fields complete!' : 'Continue selecting...'}
            </small>
        </div>
    ` : '';
    
    panel.innerHTML = `
        <div style="text-align: center; margin-bottom: 10px;">
            <strong>🎯 Content Extractor</strong><br>
            <small style="color: #666;">v${window.contentExtractorData.scriptVersion}</small>
        </div>
        ${progressHtml}
        <button onclick="window.showFieldMenu()" 
                style="display: block; width: 100%; margin: 5px 0; padding: 8px; 
                       background: #007bff; color: white; border: none; 
                       border-radius: 4px; cursor: pointer; transition: all 0.2s;"
                onmouseover="this.style.background='#0056b3'"
                onmouseout="this.style.background='#007bff'">
            📋 Select Fields
        </button>
        <button onclick="window.toggleDebugInfo()" 
                style="display: block; width: 100%; margin: 5px 0; padding: 8px; 
                       background: #6c757d; color: white; border: none; 
                       border-radius: 4px; cursor: pointer; transition: all 0.2s;"
                onmouseover="this.style.background='#5a6268'"
                onmouseout="this.style.background='#6c757d'">
            🔧 Debug Info
        </button>
        <div id="debug-info" style="display: none; margin-top: 10px; font-size: 12px; color: #666; text-align: center; background: #f8f9fa; padding: 8px; border-radius: 4px;">
            <strong>Functions Status:</strong><br>
            showFieldMenu: <span id="func-check-1">❓</span><br>
            createFieldMenu: <span id="func-check-2">❓</span><br>
            <small style="color: #999;">Updates every 2s</small>
        </div>
    `;
    
    document.body.appendChild(panel);
    
    // Update function availability indicators immediately and periodically
    window.updateFunctionStatus = function() {
        const check1 = document.getElementById('func-check-1');
        const check2 = document.getElementById('func-check-2');
        if (check1) check1.textContent = typeof window.showFieldMenu !== 'undefined' ? '✅' : '❌';
        if (check2) check2.textContent = typeof window.createFieldMenu !== 'undefined' ? '✅' : '❌';
    };
    
    setTimeout(window.updateFunctionStatus, 100);
    setInterval(window.updateFunctionStatus, 2000);
    
    return panel;
};

window.toggleDebugInfo = function() {
    console.log('🔧 toggleDebugInfo called');
    const debugInfo = document.getElementById('debug-info');
    if (debugInfo) {
        debugInfo.style.display = debugInfo.style.display === 'none' ? 'block' : 'none';
    }
};

// Function to update control panel progress
window.updateControlPanelProgress = function() {
    const panel = document.getElementById('content-extractor-control-panel');
    if (panel) {
        // Just recreate the panel to show updated progress
        window.createControlPanel();
    }
};

// Initialize the interface
window.initializeInterface = function() {
    console.log('🎬 Initializing Content Extractor interface');
    
    // Create control panel and other interface elements
    window.createControlPanel();
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        if (event.ctrlKey && event.key === 'e') {
            event.preventDefault();
            window.showFieldMenu();
        }
        if (event.key === 'Escape') {
            window.stopSelection();
            window.closeFieldMenu();
            window.closeInstanceMenu();
        }
    });
    
    console.log('✅ Content Extractor interface initialized');
};

// Attach other key functions to window for global access
window.selectField = selectField;
window.startSelection = startSelection;
window.stopSelection = stopSelection;
window.navigateToParent = navigateToParent;
window.enterNestedField = enterNestedField;

// Auto-initialize when script loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', window.initializeInterface);
} else {
    // Use setTimeout to ensure all functions are attached first
    setTimeout(window.initializeInterface, 50);
}

// Selection management menu creation
function createSelectionManager(fieldName) {
    const managerId = 'content-extractor-selection-manager';
    let existingManager = document.getElementById(managerId);
    if (existingManager) {
        existingManager.remove();
    }
    
    const manager = document.createElement('div');
    manager.id = managerId;
    manager.className = 'content-extractor-ui'; // Mark as our UI
    manager.style.cssText = `
        position: fixed;
        top: 20px;
        left: 20px;
        background: white;
        border: 3px solid ${getFieldColor(fieldName)};
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        z-index: 9999;
        max-width: 400px;
        max-height: 60vh;
        overflow-y: auto;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 13px;
        cursor: move;
    `;
    
    // Add draggable functionality
    let isDragging = false;
    let dragOffset = { x: 0, y: 0 };
    
    manager.addEventListener('mousedown', function(e) {
        if (e.target.closest('.manager-header') || e.target === manager) {
            isDragging = true;
            const rect = manager.getBoundingClientRect();
            dragOffset.x = e.clientX - rect.left;
            dragOffset.y = e.clientY - rect.top;
            manager.style.cursor = 'grabbing';
            e.preventDefault();
        }
    });
    
    document.addEventListener('mousemove', function(e) {
        if (isDragging) {
            manager.style.left = (e.clientX - dragOffset.x) + 'px';
            manager.style.top = (e.clientY - dragOffset.y) + 'px';
        }
    });
    
    document.addEventListener('mouseup', function() {
        if (isDragging) {
            isDragging = false;
            manager.style.cursor = 'move';
        }
    });
    
    updateSelectionManagerContent(manager, fieldName);
    document.body.appendChild(manager);
    return manager;
}

// Update selection manager content
function updateSelectionManagerContent(manager, fieldName) {
    const selections = window.contentExtractorData.fieldSelections[fieldName] || [];
    const fieldColor = getFieldColor(fieldName);
    
    let selectionsHtml = '';
    if (selections.length === 0) {
        selectionsHtml = '<div style="text-align: center; color: #666; padding: 20px;">No selections yet<br><small>Click elements on the page to select them</small></div>';
    } else {
        selections.forEach((selection, index) => {
            const shortText = selection.selected_text.length > 50 
                ? selection.selected_text.substring(0, 50) + '...'
                : selection.selected_text;
            
            selectionsHtml += `
                <div style="margin: 8px 0; padding: 8px; background: ${fieldColor}10; border: 1px solid ${fieldColor}40; border-radius: 6px; position: relative;">
                    <div style="font-weight: bold; color: ${fieldColor}; margin-bottom: 4px; display: flex; align-items: center; justify-content: space-between;">
                        <span>Selection ${index + 1}</span>
                        <div style="display: flex; gap: 4px;">
                            <button onclick="editXPathSelector('${fieldName}', ${index})" 
                                    style="background: #007bff; color: white; border: none; 
                                           border-radius: 3px; padding: 2px 6px; font-size: 11px; cursor: pointer;
                                           font-weight: bold;"
                                    title="Edit XPath for AI optimization">
                                >
                            </button>
                            <button onclick="removeSelection('${fieldName}', ${index})" 
                                    style="background: #dc3545; color: white; border: none; 
                                           border-radius: 3px; padding: 2px 6px; font-size: 11px; cursor: pointer;"
                                    title="Remove this selection">
                                ✖
                            </button>
                        </div>
                    </div>
                    <div style="color: #333; margin-bottom: 4px;">"${shortText}"</div>
                    <div style="font-size: 11px; color: #666;">
                        XPath: <code style="background: #f8f9fa; padding: 1px 3px; border-radius: 2px;">${selection.xpath.length > 40 ? selection.xpath.substring(0, 40) + '...' : selection.xpath}</code>
                    </div>
                </div>
            `;
        });
    }
    
    const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
    const fieldType = field ? field.type : 'unknown';
    const isMultiValue = fieldType === 'multi-value';
    
    // SWIFT PHOENIX: Check for existing comment for display in selection manager
    const existingComment = window.contentExtractorData.fieldComments ? 
        window.contentExtractorData.fieldComments[fieldName] || '' : '';
    const hasComment = existingComment.length > 0;
    
    // Current comment display in selection manager
    let currentCommentHtml = '';
    if (hasComment) {
        const commentPreview = existingComment.length > 80 
            ? existingComment.substring(0, 80) + '...'
            : existingComment;
        currentCommentHtml = `
            <div style="margin: 10px 0; padding: 8px; background: #17a2b815; border: 1px solid #17a2b840; border-radius: 6px;">
                <div style="font-size: 11px; color: #666; margin-bottom: 3px;">
                    💬 Current Comment:
                </div>
                <div style="font-style: italic; color: #17a2b8; font-size: 12px;">
                    "${commentPreview}"
                </div>
            </div>
        `;
    }

    manager.innerHTML = `
        <div class="manager-header" style="text-align: center; margin-bottom: 15px; cursor: grab; padding: 5px; border-radius: 6px;"
             onmousedown="this.style.cursor='grabbing'" onmouseup="this.style.cursor='grab'">
            <h4 style="margin: 0; color: ${fieldColor};">
                🎯 ${fieldName} Selections
            </h4>
            <small style="color: #666;">
                ${isMultiValue ? 'Multi-value field' : 'Single-value field'} • ${selections.length} selected
            </small>
        </div>
        
        ${currentCommentHtml}
        
        <div style="max-height: 300px; overflow-y: auto;">
            ${selectionsHtml}
        </div>
        <div style="text-align: center; margin-top: 15px; padding-top: 10px; border-top: 1px solid #eee;">
            <button onclick="addFieldCommentFromSelections('${fieldName}')" 
                    style="padding: 6px 12px; margin: 0 5px; background: #17a2b8; color: white; 
                           border: none; border-radius: 4px; cursor: pointer; font-size: 12px;"
                    title="Add context comment for AI processing">
                💬 ${hasComment ? 'Edit' : 'Add'} Comment
            </button>
            <button onclick="clearAllSelections('${fieldName}')" 
                    style="padding: 6px 12px; margin: 0 5px; background: #ffc107; color: #212529; 
                           border: none; border-radius: 4px; cursor: pointer; font-size: 12px;"
                    ${selections.length === 0 ? 'disabled' : ''}>
                🗑️ Clear All
            </button>
            <button onclick="window.stopSelection()" 
                    style="padding: 6px 12px; margin: 0 5px; background: #28a745; color: white; 
                           border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                ✅ Finish
            </button>
            <button onclick="closeSelectionManager()" 
                    style="padding: 6px 12px; margin: 0 5px; background: #6c757d; color: white; 
                           border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
                ➖ Minimize
            </button>
        </div>
    `;
}

// Selection management functions
window.removeSelection = function(fieldName, index) {
    const selections = window.contentExtractorData.fieldSelections[fieldName] || [];
    if (index >= 0 && index < selections.length) {
        // Remove highlight from the element if possible
        const removedSelection = selections[index];
        console.log(`🗑️ Removing selection ${index + 1} for ${fieldName}:`, removedSelection.selected_text.substring(0, 30) + '...');
        
        // Remove from array
        selections.splice(index, 1);
        
        // CRIMSON FALCON: Refresh field menus after removing selection
        if (typeof refreshFieldMenus === 'function') {
            refreshFieldMenus();
            console.log('🔄 Field menu refreshed after removing selection');
        }
        
        // Update the selection manager display
        window.updateSelectionManager();
        
        // Update control panel progress
        if (typeof window.updateControlPanelProgress === 'function') {
            window.updateControlPanelProgress();
        }
    }
};

window.clearAllSelections = function(fieldName) {
    if (confirm(`Clear all ${window.contentExtractorData.fieldSelections[fieldName]?.length || 0} selections for ${fieldName}?`)) {
        window.contentExtractorData.fieldSelections[fieldName] = [];
        
        // Remove all highlights for this field
        window.contentExtractorData.selectedDOMElements.forEach(element => {
            removeHighlight(element);
        });
        window.contentExtractorData.selectedDOMElements.clear();
        
        console.log(`🗑️ Cleared all selections for ${fieldName}`);
        
        // CRIMSON FALCON: Refresh field menus after clearing all selections
        if (typeof refreshFieldMenus === 'function') {
            refreshFieldMenus();
            console.log('🔄 Field menu refreshed after clearing all selections');
        }
        
        // Update displays
        window.updateSelectionManager();
        if (typeof window.updateControlPanelProgress === 'function') {
            window.updateControlPanelProgress();
        }
    }
};

window.closeSelectionManager = function() {
    const manager = document.getElementById('content-extractor-selection-manager');
    if (manager) {
        manager.remove();
    }
};

window.updateSelectionManager = function() {
    const manager = document.getElementById('content-extractor-selection-manager');
    const activeField = window.contentExtractorData.activeField;
    if (manager && activeField) {
        updateSelectionManagerContent(manager, activeField);
    }
};

// XPath Editor Integration
window.openXPathEditor = function(fieldName, selectionIndex) {
    const selections = window.contentExtractorData.fieldSelections[fieldName] || [];
    if (selectionIndex >= 0 && selectionIndex < selections.length) {
        const selection = selections[selectionIndex];
        
        console.log(`🔧 Opening XPath editor for ${fieldName} selection ${selectionIndex + 1}`);
        
        // Try to find the element on the page using the XPath
        let element = null;
        try {
            const result = document.evaluate(
                selection.xpath,
                document,
                null,
                XPathResult.FIRST_ORDERED_NODE_TYPE,
                null
            );
            element = result.singleNodeValue;
        } catch (error) {
            console.warn('Could not find element using stored XPath:', error);
        }
        
        // If element not found, try to find by text content as fallback
        if (!element && selection.selected_text) {
            const allElements = document.querySelectorAll('*');
            for (let el of allElements) {
                if (el.textContent && el.textContent.trim() === selection.selected_text.trim()) {
                    element = el;
                    break;
                }
            }
        }
        
        // Open XPath editor with the element, field name, and current XPath
        if (window.ContentExtractorXPathEditor && window.ContentExtractorXPathEditor.openEditor) {
            window.ContentExtractorXPathEditor.openEditor(element, fieldName, selection.xpath);
        } else {
            console.error('XPath Editor not available');
            alert('XPath Editor not available. Please ensure the XPath editor script is loaded.');
        }
    }
};

window.editXPathSelector = function(fieldName, index) {
    console.log(`✏️ Swift Phoenix: Edit XPath for ${fieldName}[${index}]`);
    
    const selections = window.contentExtractorData.fieldSelections[fieldName] || [];
    if (index < 0 || index >= selections.length) {
        console.error(`❌ Invalid selection index ${index} for ${fieldName}`);
        alert(`Invalid selection index. Please refresh the page and try again.`);
        return;
    }
    
    const selection = selections[index];
    if (!selection) {
        console.error(`❌ No selection found at index ${index} for ${fieldName}`);
        alert(`Selection not found. Please refresh the page and try again.`);
        return;
    }
    
    console.log(`🎯 Opening XPath editor for selection:`, {
        fieldName: fieldName,
        index: index,
        xpath: selection.xpath,
        text: selection.selected_text?.substring(0, 50) + '...'
    });
                    
    // Try to find the element on the page using the XPath
    let element = null;
                    try {
        const result = document.evaluate(
            selection.xpath,
            document,
            null,
            XPathResult.FIRST_ORDERED_NODE_TYPE,
            null
        );
        element = result.singleNodeValue;
        
        if (element) {
            console.log(`✅ Found element for XPath editing:`, element);
                        } else {
            console.warn(`⚠️ Element not found with XPath: ${selection.xpath}`);
                        }
                    } catch (error) {
        console.warn('⚠️ Error evaluating XPath:', error);
    }
    
    // If element not found, try to find by text content as fallback
    if (!element && selection.selected_text) {
        const textToFind = selection.selected_text.trim();
        const allElements = document.querySelectorAll('*');
        for (let el of allElements) {
            if (el.textContent && el.textContent.trim() === textToFind) {
                element = el;
                console.log(`✅ Found element by text content as fallback:`, element);
                break;
            }
        }
    }
    
    // SWIFT PHOENIX: Fixed XPath editor integration - use correct API
    if (window.ContentExtractorXPathEditor && typeof window.ContentExtractorXPathEditor.openEditor === 'function') {
        console.log(`🔧 Opening XPath editor with element, fieldName: ${fieldName}, xpath: ${selection.xpath}`);
        window.ContentExtractorXPathEditor.openEditor(element, fieldName, selection.xpath);
        
        // Store the selection index for potential updates
        window.ContentExtractorXPathEditor.currentSelectionIndex = index;
        
    } else {
        console.error('❌ XPath Editor not available');
        console.log('Available XPath Editor methods:', Object.keys(window.ContentExtractorXPathEditor || {}));
        alert('XPath Editor not available. Please ensure the XPath editor script is loaded.');
    }
};

// SWIFT PHOENIX: Comment functionality for selections interface
window.addFieldCommentFromSelections = function(fieldName) {
    console.log(`💬 Adding comment for ${fieldName} from selections interface`);
    
    // Create the comment dialog with fromSelections=true (reuse existing function from content_extractor_ui.js)
    if (typeof createFieldCommentDialog === 'function') {
        createFieldCommentDialog(fieldName, true);
    } else {
        console.error('createFieldCommentDialog function not available');
        alert('Comment functionality not available. Please ensure the UI script is loaded.');
    }
};

// SWIFT PHOENIX: Modified comment save function to return to selections instead of method menu
window.saveFieldCommentFromSelections = function(fieldName) {
    const textarea = document.getElementById('comment-input-field');
    if (!textarea) return;
    
    const commentValue = textarea.value.trim();
    
    // Initialize fieldComments if not exists
    if (!window.contentExtractorData.fieldComments) {
        window.contentExtractorData.fieldComments = {};
    }
    
    // Save comment (even if empty to clear existing)
    window.contentExtractorData.fieldComments[fieldName] = commentValue;
    
    console.log(`💾 Saved comment for ${fieldName} from selections:`, commentValue || '(empty)');
    
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
    
    // Update selection manager to show new comment
    window.updateSelectionManager();
};

// SWIFT PHOENIX: Cancel comment function for selections interface
window.cancelFieldCommentFromSelections = function(fieldName) {
    console.log(`❌ Cancelled comment input for ${fieldName} from selections`);
    
    // Close the dialog
    const dialog = document.getElementById('content-extractor-comment-dialog');
    if (dialog) {
        dialog.remove();
    }
    
    // No need to return anywhere - just close the dialog and let user continue with selections
}; 