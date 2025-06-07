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
    console.log('❌ closeInstanceMenu called');
    const menu = document.getElementById('content-extractor-instance-menu');
    if (menu) {
        menu.remove();
    }
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
        min-width: 200px;
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
                    <div style="font-weight: bold; color: ${fieldColor}; margin-bottom: 4px;">
                        Selection ${index + 1}
                        <button onclick="removeSelection('${fieldName}', ${index})" 
                                style="float: right; background: #dc3545; color: white; border: none; 
                                       border-radius: 3px; padding: 2px 6px; font-size: 11px; cursor: pointer;"
                                title="Remove this selection">
                            ✖
                        </button>
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