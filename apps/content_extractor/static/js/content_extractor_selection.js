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
    const panelId = 'content-extractor-control-panel';
    let existingPanel = document.getElementById(panelId);
    if (existingPanel) {
        existingPanel.remove();
    }
    
    const panel = document.createElement('div');
    panel.id = panelId;
    panel.className = 'content-extractor-ui'; // Mark as our UI
    panel.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: white;
        border: 2px solid #007bff;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 9998;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        min-width: 250px;
        max-width: 350px;
    `;
    
    // Calculate selection progress
    const totalSelections = Object.values(window.contentExtractorData.fieldSelections).reduce((sum, selections) => sum + selections.length, 0);
    const completedFields = Object.keys(window.contentExtractorData.fieldSelections).filter(key => window.contentExtractorData.fieldSelections[key].length > 0).length;
    const totalFields = window.contentExtractorData.fieldOptions.length;
    
    // Progress indicator
    const progressHtml = totalSelections > 0 ? `
        <div style="margin: 8px 0; padding: 6px; background: #e8f5e8; border-radius: 4px; text-align: center;">
            <small style="color: #28a745; font-weight: bold;">
                📊 ${completedFields}/${totalFields} fields (${totalSelections} selections)
            </small>
        </div>
    ` : '';
    
    // URL Management section
    const currentDomain = window.location.hostname;
    const urlManagementHtml = `
        <div style="margin: 10px 0; padding: 8px; background: #f8f9fa; border-radius: 4px; border-left: 3px solid #17a2b8;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                <strong style="color: #17a2b8; font-size: 12px;">🌐 URL Testing</strong>
                <span id="url-count" style="font-size: 11px; color: #666;">Loading...</span>
            </div>
            <div style="display: flex; gap: 4px; margin-bottom: 5px;">
                <button onclick="window.switchTestUrl('previous')" 
                        style="flex: 1; padding: 4px 6px; background: #6c757d; color: white; border: none; 
                               border-radius: 3px; cursor: pointer; font-size: 11px; transition: all 0.2s;"
                        onmouseover="this.style.background='#5a6268'"
                        onmouseout="this.style.background='#6c757d'">
                    ⬅️ Prev
                </button>
                <button onclick="window.switchTestUrl('next')" 
                        style="flex: 1; padding: 4px 6px; background: #6c757d; color: white; border: none; 
                               border-radius: 3px; cursor: pointer; font-size: 11px; transition: all 0.2s;"
                        onmouseover="this.style.background='#5a6268'"
                        onmouseout="this.style.background='#6c757d'">
                    Next ➡️
                </button>
            </div>
            <button onclick="window.showAddUrlDialog()" 
                    style="width: 100%; padding: 4px 6px; background: #17a2b8; color: white; border: none; 
                           border-radius: 3px; cursor: pointer; font-size: 11px; transition: all 0.2s;"
                    onmouseover="this.style.background='#138496'"
                    onmouseout="this.style.background='#17a2b8'">
                ➕ Add Test URL
            </button>
        </div>
    `;
    
    panel.innerHTML = `
        <div style="text-align: center; margin-bottom: 10px;">
            <strong>🎯 Content Extractor</strong><br>
            <small style="color: #666;">v${window.contentExtractorData.scriptVersion}</small>
        </div>
        ${progressHtml}
        ${urlManagementHtml}
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
    
    // Load URL count
    window.loadUrlCount();
    
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
                            <button onclick="openXPathEditor('${fieldName}', ${index})" 
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
        <div style="max-height: 300px; overflow-y: auto;">
            ${selectionsHtml}
        </div>
        <div style="text-align: center; margin-top: 15px; padding-top: 10px; border-top: 1px solid #eee;">
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

// URL Management Functions
window.loadUrlCount = function() {
    const currentDomain = window.location.hostname;
    const baseUrl = window.contentExtractorData.baseUrl;
    const apiToken = window.contentExtractorData.apiToken;
    
    if (!apiToken) {
        console.warn('⚠️ No API token available for URL management');
        document.getElementById('url-count').textContent = 'No token';
        return;
    }
    
    fetch(`${baseUrl}/content-extractor/get-test-urls/?domain=${encodeURIComponent(currentDomain)}`, {
        method: 'GET',
        headers: {
            'Authorization': `Token ${apiToken}`,
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const urlCountElement = document.getElementById('url-count');
            if (urlCountElement) {
                urlCountElement.textContent = `${data.total_urls} URLs`;
            }
            console.log(`📊 Loaded ${data.total_urls} test URLs for ${currentDomain}`);
        } else {
            console.warn('⚠️ Failed to load URL count:', data.error);
            document.getElementById('url-count').textContent = 'Error';
        }
    })
    .catch(error => {
        console.error('❌ Error loading URL count:', error);
        document.getElementById('url-count').textContent = 'Error';
    });
};

window.switchTestUrl = function(direction) {
    const currentUrl = window.location.href;
    const currentDomain = window.location.hostname;
    const baseUrl = window.contentExtractorData.baseUrl;
    const apiToken = window.contentExtractorData.apiToken;
    
    if (!apiToken) {
        alert('⚠️ No API token available for URL switching');
        return;
    }
    
    // Show loading indicator
    const urlCountElement = document.getElementById('url-count');
    const originalText = urlCountElement ? urlCountElement.textContent : '';
    if (urlCountElement) {
        urlCountElement.textContent = 'Switching...';
    }
    
    fetch(`${baseUrl}/content-extractor/switch-url/${direction}/`, {
        method: 'POST',
        headers: {
            'Authorization': `Token ${apiToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            current_url: currentUrl,
            domain: currentDomain
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log(`🔄 Switching to ${direction} URL: ${data.next_url}`);
            
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
                z-index: 10001;
                font-size: 14px;
                text-align: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            `;
            feedback.innerHTML = `
                🔄 Switching to ${direction} URL...<br>
                <small>${data.next_url}</small>
            `;
            
            document.body.appendChild(feedback);
            
            // Navigate to the new URL
            setTimeout(() => {
                window.location.href = data.next_url;
            }, 1000);
            
        } else {
            console.warn('⚠️ Failed to switch URL:', data.error);
            alert(`Failed to switch URL: ${data.error}`);
            
            // Restore original text
            if (urlCountElement) {
                urlCountElement.textContent = originalText;
            }
        }
    })
    .catch(error => {
        console.error('❌ Error switching URL:', error);
        alert(`Error switching URL: ${error.message}`);
        
        // Restore original text
        if (urlCountElement) {
            urlCountElement.textContent = originalText;
        }
    });
};

window.showAddUrlDialog = function() {
    const currentDomain = window.location.hostname;
    
    // Create modal dialog
    const modal = document.createElement('div');
    modal.className = 'content-extractor-ui';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        z-index: 10002;
        display: flex;
        justify-content: center;
        align-items: center;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    `;
    
    const dialog = document.createElement('div');
    dialog.style.cssText = `
        background: white;
        border-radius: 8px;
        padding: 20px;
        max-width: 500px;
        width: 90%;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    `;
    
    dialog.innerHTML = `
        <h3 style="margin: 0 0 15px 0; color: #17a2b8;">🌐 Add Test URL</h3>
        <p style="margin: 0 0 15px 0; color: #666; font-size: 14px;">
            Add a new URL from <strong>${currentDomain}</strong> for testing selectors across different pages.
        </p>
        <input type="url" id="new-test-url" placeholder="https://${currentDomain}/page-to-test" 
               style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 4px; 
                      font-size: 14px; margin-bottom: 15px; box-sizing: border-box;">
        <div style="display: flex; gap: 10px; justify-content: flex-end;">
            <button onclick="window.closeAddUrlDialog()" 
                    style="padding: 8px 16px; background: #6c757d; color: white; border: none; 
                           border-radius: 4px; cursor: pointer; transition: all 0.2s;"
                    onmouseover="this.style.background='#5a6268'"
                    onmouseout="this.style.background='#6c757d'">
                Cancel
            </button>
            <button onclick="window.addTestUrl()" 
                    style="padding: 8px 16px; background: #17a2b8; color: white; border: none; 
                           border-radius: 4px; cursor: pointer; transition: all 0.2s;"
                    onmouseover="this.style.background='#138496'"
                    onmouseout="this.style.background='#17a2b8'">
                ➕ Add URL
            </button>
        </div>
    `;
    
    modal.appendChild(dialog);
    document.body.appendChild(modal);
    
    // Focus the input
    setTimeout(() => {
        document.getElementById('new-test-url').focus();
    }, 100);
    
    // Close on background click
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            window.closeAddUrlDialog();
        }
    });
    
    // Close on Escape key
    const escapeHandler = function(e) {
        if (e.key === 'Escape') {
            window.closeAddUrlDialog();
            document.removeEventListener('keydown', escapeHandler);
        }
    };
    document.addEventListener('keydown', escapeHandler);
};

window.closeAddUrlDialog = function() {
    const modal = document.querySelector('.content-extractor-ui[style*="rgba(0,0,0,0.5)"]');
    if (modal) {
        modal.remove();
    }
};

window.addTestUrl = function() {
    const urlInput = document.getElementById('new-test-url');
    const newUrl = urlInput ? urlInput.value.trim() : '';
    const currentDomain = window.location.hostname;
    const baseUrl = window.contentExtractorData.baseUrl;
    const apiToken = window.contentExtractorData.apiToken;
    
    if (!newUrl) {
        alert('Please enter a URL');
        return;
    }
    
    if (!apiToken) {
        alert('⚠️ No API token available for adding URLs');
        return;
    }
    
    // Disable the button and show loading
    const addButton = event.target;
    const originalText = addButton.textContent;
    addButton.textContent = 'Adding...';
    addButton.disabled = true;
    
    fetch(`${baseUrl}/content-extractor/add-test-url/`, {
        method: 'POST',
        headers: {
            'Authorization': `Token ${apiToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            url: newUrl,
            current_domain: currentDomain
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log(`✅ Added test URL: ${newUrl}`);
            
            // Show success feedback
            const feedback = document.createElement('div');
            feedback.className = 'content-extractor-ui';
            feedback.style.cssText = `
                position: fixed;
                top: 30%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: #28a745;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                z-index: 10003;
                font-size: 14px;
                text-align: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            `;
            feedback.innerHTML = `
                ✅ URL Added Successfully!<br>
                <small>Total URLs: ${data.total_urls}</small>
            `;
            
            document.body.appendChild(feedback);
            setTimeout(() => feedback.remove(), 3000);
            
            // Close dialog and refresh URL count
            window.closeAddUrlDialog();
            window.loadUrlCount();
            
        } else {
            console.warn('⚠️ Failed to add URL:', data.error);
            alert(`Failed to add URL: ${data.error}`);
            
            // Re-enable button
            addButton.textContent = originalText;
            addButton.disabled = false;
        }
    })
    .catch(error => {
        console.error('❌ Error adding URL:', error);
        alert(`Error adding URL: ${error.message}`);
        
        // Re-enable button
        addButton.textContent = originalText;
        addButton.disabled = false;
    });
}; 