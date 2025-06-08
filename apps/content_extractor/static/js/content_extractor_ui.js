/**
 * Content Extractor UI Components
 * 
 * This file contains UI component creation functions including
 * field menus, instance management, and draggable interfaces.
 * 
 * Created by: Electric Sentinel
 * Date: 2025-01-08
 * Project: Triad Docker Base
 */

// Create field selection menu using unified system
function createFieldMenu() {
    // Use unified menu system if available
    if (window.ContentExtractorUnifiedMenu) {
        const config = {
            id: 'content-extractor-field-menu',
            title: '🎯 Select Field to Extract',
            subtitle: 'Choose the field you want to configure',
            type: 'field',
            color: window.contentExtractorData.depthColor,
            content: buildFieldMenuContent(),
            buttons: [
                { label: '✖️ Close Menu', type: 'danger', onClick: 'window.closeFieldMenu()' }
            ],
            breadcrumbs: window.contentExtractorData.breadcrumbs
        };
        
        return window.ContentExtractorUnifiedMenu.createMenu(config);
    } else {
        // Legacy field menu creation (fallback)
        return createLegacyFieldMenu();
    }
}

// Build field menu content HTML
function buildFieldMenuContent() {
    // Build field options with selection indicators
    let fieldsHtml = '';
    window.contentExtractorData.fieldOptions.forEach(field => {
        const icon = field.has_sub_fields ? '🏗️' : (field.type === 'multi-value' ? '📋' : '📝');
        
        // Check if field has selections
        const fieldSelections = window.contentExtractorData.fieldSelections[field.name] || [];
        const hasSelections = fieldSelections.length > 0;
        const selectionCount = fieldSelections.length;
        
        // Selection indicator
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
        
        // Button styling based on selection status
        const buttonStyle = hasSelections 
            ? `background: ${field.color}40; border: 2px solid #28a745; box-shadow: 0 2px 4px rgba(40, 167, 69, 0.2);`
            : `background: ${field.color}20; border: 2px solid ${field.color};`;
        
        fieldsHtml += `
            <button onclick="selectField('${field.name}')" 
                    style="display: block; width: 100%; margin: 8px 0; padding: 12px; 
                           ${buttonStyle}
                           border-radius: 8px; cursor: pointer; text-align: left;
                           font-size: 14px; transition: all 0.2s; position: relative;"
                    onmouseover="this.style.transform='scale(1.02)'; this.style.boxShadow='0 4px 8px rgba(0,0,0,0.1)'"
                    onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='${hasSelections ? '0 2px 4px rgba(40, 167, 69, 0.2)' : 'none'}'">
                ${selectionIndicator}
                ${icon} <strong>${field.label}</strong><br>
                <small style="color: #666;">${field.description}</small>
                ${hasSelections ? `<br><small style="color: #28a745; font-weight: bold;">Last: "${fieldSelections[fieldSelections.length - 1].selected_text.substring(0, 30)}${fieldSelections[fieldSelections.length - 1].selected_text.length > 30 ? '...' : ''}"</small>` : ''}
            </button>
        `;
    });
    
    // Navigation buttons
    let navigationHtml = '';
    if (window.contentExtractorData.currentDepth > 0) {
        navigationHtml = `
            <div style="margin-top: 15px; text-align: center;">
                <button onclick="navigateToParent()" 
                        style="padding: 8px 16px; margin: 0 5px; background: #6c757d; 
                               color: white; border: none; border-radius: 6px; cursor: pointer;
                               transition: all 0.2s;"
                        onmouseover="this.style.background='#5a6268'"
                        onmouseout="this.style.background='#6c757d'">
                    ⬆️ Parent Level
                </button>
            </div>
        `;
    }
    
    // Selection summary
    const totalSelections = Object.values(window.contentExtractorData.fieldSelections).reduce((sum, selections) => sum + selections.length, 0);
    const completedFields = Object.keys(window.contentExtractorData.fieldSelections).filter(key => window.contentExtractorData.fieldSelections[key].length > 0).length;
    
    const summaryHtml = totalSelections > 0 ? `
        <div style="margin: 15px 0; padding: 10px; background: #e8f5e8; border-radius: 6px; text-align: center;">
            <strong style="color: #28a745;">📊 Progress: ${completedFields}/${window.contentExtractorData.fieldOptions.length} fields completed</strong><br>
            <small style="color: #666;">Total selections: ${totalSelections}</small>
        </div>
    ` : '';
    
    return summaryHtml + fieldsHtml + navigationHtml;
}

// Legacy field menu creation (kept for backward compatibility)
function createLegacyFieldMenu() {
    const menuId = 'content-extractor-field-menu';
    let existingMenu = document.getElementById(menuId);
    if (existingMenu) {
        existingMenu.remove();
    }
    
    const menu = document.createElement('div');
    menu.id = menuId;
    menu.className = 'content-extractor-ui'; // Mark as our UI
    menu.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        border: 3px solid ${window.contentExtractorData.depthColor};
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        z-index: 10000;
        max-width: 600px;
        max-height: 80vh;
        overflow-y: auto;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        cursor: move;
    `;
    
    // Add draggable functionality
    let isDragging = false;
    let dragOffset = { x: 0, y: 0 };
    
    menu.addEventListener('mousedown', function(e) {
        // Only allow dragging from the header area
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
    
    // Build breadcrumb navigation
    let breadcrumbHtml = '';
    if (window.contentExtractorData.breadcrumbs.length > 0) {
        breadcrumbHtml = `
            <div style="margin-bottom: 15px; padding: 8px 12px; background: #f8f9fa; border-radius: 6px; font-size: 14px; color: #6c757d;">
                📍 ${window.contentExtractorData.breadcrumbs.join(' → ')}
            </div>
        `;
    }
    
    // Build field options with selection indicators
    let fieldsHtml = '';
    window.contentExtractorData.fieldOptions.forEach(field => {
        const icon = field.has_sub_fields ? '🏗️' : (field.type === 'multi-value' ? '📋' : '📝');
        
        // Check if field has selections
        const fieldSelections = window.contentExtractorData.fieldSelections[field.name] || [];
        const hasSelections = fieldSelections.length > 0;
        const selectionCount = fieldSelections.length;
        
        // Selection indicator
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
        
        // Button styling based on selection status
        const buttonStyle = hasSelections 
            ? `background: ${field.color}40; border: 2px solid #28a745; box-shadow: 0 2px 4px rgba(40, 167, 69, 0.2);`
            : `background: ${field.color}20; border: 2px solid ${field.color};`;
        
        fieldsHtml += `
            <button onclick="selectField('${field.name}')" 
                    style="display: block; width: 100%; margin: 8px 0; padding: 12px; 
                           ${buttonStyle}
                           border-radius: 8px; cursor: pointer; text-align: left;
                           font-size: 14px; transition: all 0.2s; position: relative;"
                    onmouseover="this.style.transform='scale(1.02)'; this.style.boxShadow='0 4px 8px rgba(0,0,0,0.1)'"
                    onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='${hasSelections ? '0 2px 4px rgba(40, 167, 69, 0.2)' : 'none'}'">
                ${selectionIndicator}
                ${icon} <strong>${field.label}</strong><br>
                <small style="color: #666;">${field.description}</small>
                ${hasSelections ? `<br><small style="color: #28a745; font-weight: bold;">Last: "${fieldSelections[fieldSelections.length - 1].selected_text.substring(0, 30)}${fieldSelections[fieldSelections.length - 1].selected_text.length > 30 ? '...' : ''}"</small>` : ''}
            </button>
        `;
    });
    
    // Navigation buttons
    let navigationHtml = '';
    if (window.contentExtractorData.currentDepth > 0) {
        navigationHtml = `
            <div style="margin-top: 15px; text-align: center;">
                <button onclick="navigateToParent()" 
                        style="padding: 8px 16px; margin: 0 5px; background: #6c757d; 
                               color: white; border: none; border-radius: 6px; cursor: pointer;
                               transition: all 0.2s;"
                        onmouseover="this.style.background='#5a6268'"
                        onmouseout="this.style.background='#6c757d'">
                    ⬆️ Parent Level
                </button>
            </div>
        `;
    }
    
    // Selection summary
    const totalSelections = Object.values(window.contentExtractorData.fieldSelections).reduce((sum, selections) => sum + selections.length, 0);
    const completedFields = Object.keys(window.contentExtractorData.fieldSelections).filter(key => window.contentExtractorData.fieldSelections[key].length > 0).length;
    
    const summaryHtml = totalSelections > 0 ? `
        <div style="margin: 15px 0; padding: 10px; background: #e8f5e8; border-radius: 6px; text-align: center;">
            <strong style="color: #28a745;">📊 Progress: ${completedFields}/${window.contentExtractorData.fieldOptions.length} fields completed</strong><br>
            <small style="color: #666;">Total selections: ${totalSelections}</small>
        </div>
    ` : '';
    
    menu.innerHTML = `
        <div class="menu-header" style="text-align: center; margin-bottom: 20px; cursor: grab; padding: 5px; border-radius: 6px;"
             onmousedown="this.style.cursor='grabbing'" onmouseup="this.style.cursor='grab'">
            <h3 style="margin: 0; color: ${window.contentExtractorData.depthColor};">
                🎯 Select Field to Extract
            </h3>
            <small style="color: #666;">Drag here to move</small>
        </div>
        ${breadcrumbHtml}
        ${summaryHtml}
        ${fieldsHtml}
        ${navigationHtml}
        <div style="text-align: center; margin-top: 20px;">
            <button onclick="window.closeFieldMenu()" 
                    style="padding: 8px 16px; background: #dc3545; color: white; 
                           border: none; border-radius: 6px; cursor: pointer; transition: all 0.2s;"
                    onmouseover="this.style.background='#c82333'"
                    onmouseout="this.style.background='#dc3545'">
                ✖️ Close Menu
            </button>
        </div>
    `;
    
    document.body.appendChild(menu);
    return menu;
}

// Instance management menu creation
function createInstanceManagementMenu(fieldName) {
    const menuId = 'content-extractor-instance-menu';
    let existingMenu = document.getElementById(menuId);
    if (existingMenu) {
        existingMenu.remove();
    }
    
    const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
    if (!field) return;

    const menu = document.createElement('div');
    menu.id = menuId;
    menu.className = 'content-extractor-ui'; // Mark as our UI
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
        max-width: 500px;
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

    // Get existing instances for this field
    const instanceSelections = window.contentExtractorData.instanceSelections || {};
    const fieldInstances = instanceSelections[fieldName] || [];
    
    // Header
    const headerHtml = `
        <div class="menu-header" style="text-align: center; margin-bottom: 20px; cursor: grab; padding: 5px; border-radius: 6px;"
             onmousedown="this.style.cursor='grabbing'" onmouseup="this.style.cursor='grab'">
            <h3 style="margin: 0; color: ${field.color};">
                📋 ${field.label} Management
            </h3>
            <small style="color: #666;">Manage multiple instances of this field</small>
        </div>
    `;
    
    // Field description
    const descriptionHtml = `
        <div style="margin-bottom: 15px; padding: 8px 12px; background: #f8f9fa; border-radius: 6px; font-size: 14px;">
            <strong>${field.label}</strong><br>
            <small style="color: #666;">${field.description}</small>
        </div>
    `;
    
    // Add New Instance button (prominent when no instances exist)
    const addNewButtonHtml = `
        <button onclick="createNewInstance('${fieldName}')" 
                style="display: block; width: 100%; margin: ${fieldInstances.length === 0 ? '20px 0 30px 0' : '10px 0 15px 0'}; padding: ${fieldInstances.length === 0 ? '20px' : '12px'}; 
                       background: #28a745; color: white; border: none; border-radius: 8px; 
                       cursor: pointer; text-align: center; font-size: ${fieldInstances.length === 0 ? '16px' : '14px'}; font-weight: bold;
                       transition: all 0.2s; box-shadow: 0 2px 6px rgba(40, 167, 69, 0.3);"
                onmouseover="this.style.background='#218838'; this.style.transform='scale(1.02)'"
                onmouseout="this.style.background='#28a745'; this.style.transform='scale(1)'">
            ➕ Add New ${field.label}
        </button>
    `;
    
    // Instances list
    let instancesListHtml = '';
    if (fieldInstances.length > 0) {
        instancesListHtml = `
            <div style="margin: 15px 0;">
                <h4 style="margin: 0 0 10px 0; color: ${field.color}; font-size: 14px;">
                    Existing Instances (${fieldInstances.length}):
                </h4>
                <div style="max-height: 200px; overflow-y: auto;">
        `;
        
        fieldInstances.forEach((instance, index) => {
            const completedSubfields = Object.keys(instance.subfields || {}).filter(
                subfieldName => (instance.subfields[subfieldName] || []).length > 0
            ).length;
            const totalSubfields = field.sub_fields ? field.sub_fields.length : 0;
            const progressText = totalSubfields > 0 ? ` (${completedSubfields}/${totalSubfields})` : '';
            
            instancesListHtml += `
                <div style="margin: 8px 0; padding: 12px; background: ${field.color}10; border: 1px solid ${field.color}40; 
                           border-radius: 6px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: bold; color: ${field.color};">
                            ${field.label}[${index + 1}]${progressText}
                        </div>
                        <div style="font-size: 12px; color: #666;">
                            Click to manage subfields
                        </div>
                    </div>
                    <div>
                        <button onclick="openInstanceSubfields('${fieldName}', ${index})" 
                                style="padding: 6px 12px; margin: 0 2px; background: #007bff; color: white; 
                                       border: none; border-radius: 4px; cursor: pointer; font-size: 12px;"
                                onmouseover="this.style.background='#0056b3'"
                                onmouseout="this.style.background='#007bff'">
                            ⚙️ Edit
                        </button>
                        <button onclick="deleteInstance('${fieldName}', ${index})" 
                                style="padding: 6px 12px; margin: 0 2px; background: #dc3545; color: white; 
                                       border: none; border-radius: 4px; cursor: pointer; font-size: 12px;"
                                onmouseover="this.style.background='#c82333'"
                                onmouseout="this.style.background='#dc3545'">
                            🗑️
                        </button>
                    </div>
                </div>
            `;
        });
        
        instancesListHtml += `
                </div>
            </div>
        `;
    } else {
        instancesListHtml = `
            <div style="text-align: center; margin: 20px 0; padding: 20px; 
                       background: #f8f9fa; border: 2px dashed #dee2e6; border-radius: 8px;">
                <div style="font-size: 18px; margin-bottom: 10px;">📝</div>
                <div style="font-weight: bold; color: #6c757d; margin-bottom: 5px;">
                    No ${field.label} instances yet
                </div>
                <div style="font-size: 12px; color: #6c757d;">
                    Click "Add New ${field.label}" to get started
                </div>
            </div>
        `;
    }
    
    // Navigation buttons
    const navigationHtml = `
        <div style="text-align: center; margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee;">
            <button onclick="closeInstanceMenu()" 
                    style="padding: 8px 16px; margin: 0 5px; background: #6c757d; color: white; 
                           border: none; border-radius: 6px; cursor: pointer; transition: all 0.2s;"
                    onmouseover="this.style.background='#5a6268'"
                    onmouseout="this.style.background='#6c757d'">
                ⬅️ Back to Fields
            </button>
        </div>
    `;
    
    menu.innerHTML = headerHtml + descriptionHtml + addNewButtonHtml + instancesListHtml + navigationHtml;
    document.body.appendChild(menu);
    
    return menu;
}

// Field setting method menu creation
function createFieldSettingMethodMenu(fieldName) {
    const menuId = 'content-extractor-method-menu';
    let existingMenu = document.getElementById(menuId);
    if (existingMenu) {
        existingMenu.remove();
    }
    
    const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
    if (!field) return;
    
    const menu = document.createElement('div');
    menu.id = menuId;
    menu.className = 'content-extractor-ui'; // Mark as our UI
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
        max-width: 500px;
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
    
    // Check if field has existing selections for display
    const fieldSelections = window.contentExtractorData.fieldSelections[fieldName] || [];
    const hasSelections = fieldSelections.length > 0;
    
    // Current value display
    let currentValueHtml = '';
    if (hasSelections) {
        const lastSelection = fieldSelections[fieldSelections.length - 1];
        const valuePreview = lastSelection.selected_text.length > 60 
            ? lastSelection.selected_text.substring(0, 60) + '...'
            : lastSelection.selected_text;
        currentValueHtml = `
            <div style="margin: 15px 0; padding: 10px; background: ${field.color}10; border: 1px solid ${field.color}40; border-radius: 6px;">
                <div style="font-size: 12px; color: #666; margin-bottom: 5px;">
                    Current Value${field.type === 'multi-value' ? ` (${fieldSelections.length} items)` : ''}:
                </div>
                <div style="font-weight: bold; color: ${field.color};">
                    "${valuePreview}"
                </div>
            </div>
        `;
    }
    
    menu.innerHTML = `
        <div class="menu-header" style="text-align: center; margin-bottom: 20px; cursor: grab; padding: 5px; border-radius: 6px;"
             onmousedown="this.style.cursor='grabbing'" onmouseup="this.style.cursor='grab'">
            <h3 style="margin: 0; color: ${field.color};">
                🎯 How to set "${field.label}"?
            </h3>
            <small style="color: #666;">Choose your input method</small>
        </div>
        
        <div style="margin-bottom: 15px; padding: 8px 12px; background: #f8f9fa; border-radius: 6px; font-size: 14px;">
            <strong>${field.label}</strong> (${field.type})<br>
            <small style="color: #666;">${field.description}</small>
        </div>
        
        ${currentValueHtml}
        
        <div style="margin: 15px 0;">
            <button onclick="startPageSelection('${fieldName}')" 
                    style="display: block; width: 100%; margin: 8px 0; padding: 15px; 
                           background: #007bff; color: white; border: none; border-radius: 8px; 
                           cursor: pointer; text-align: left; font-size: 14px; transition: all 0.2s;"
                    onmouseover="this.style.background='#0056b3'; this.style.transform='scale(1.02)'"
                    onmouseout="this.style.background='#007bff'; this.style.transform='scale(1)'">
                🖱️ <strong>Select from Page Elements</strong><br>
                <small style="opacity: 0.9;">Click elements on the webpage to extract content</small>
            </button>
            
            <button onclick="startTextInput('${fieldName}')" 
                    style="display: block; width: 100%; margin: 8px 0; padding: 15px; 
                           background: #28a745; color: white; border: none; border-radius: 8px; 
                           cursor: pointer; text-align: left; font-size: 14px; transition: all 0.2s;"
                    onmouseover="this.style.background='#1e7e34'; this.style.transform='scale(1.02)'"
                    onmouseout="this.style.background='#28a745'; this.style.transform='scale(1)'">
                ✏️ <strong>Enter Text Manually</strong><br>
                <small style="opacity: 0.9;">Type or paste the value directly</small>
            </button>
            
            <button onclick="startFileImport('${fieldName}')" 
                    style="display: block; width: 100%; margin: 8px 0; padding: 15px; 
                           background: #6c757d; color: white; border: none; border-radius: 8px; 
                           cursor: pointer; text-align: left; font-size: 14px; transition: all 0.2s; opacity: 0.6;"
                    onmouseover="this.style.background='#545b62'; this.style.transform='scale(1.02)'"
                    onmouseout="this.style.background='#6c757d'; this.style.transform='scale(1)'"
                    disabled title="Coming soon">
                📁 <strong>Import from File</strong><br>
                <small style="opacity: 0.9;">Load values from CSV, JSON, or text file (Coming Soon)</small>
            </button>
            
            <button onclick="startAIExtraction('${fieldName}')" 
                    style="display: block; width: 100%; margin: 8px 0; padding: 15px; 
                           background: #6f42c1; color: white; border: none; border-radius: 8px; 
                           cursor: pointer; text-align: left; font-size: 14px; transition: all 0.2s; opacity: 0.6;"
                    onmouseover="this.style.background='#5a32a3'; this.style.transform='scale(1.02)'"
                    onmouseout="this.style.background='#6f42c1'; this.style.transform='scale(1)'"
                    disabled title="Coming soon">
                🤖 <strong>AI-Powered Extraction</strong><br>
                <small style="opacity: 0.9;">Let AI find and extract the content automatically (Coming Soon)</small>
            </button>
        </div>
        
        <div style="text-align: center; margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee;">
            <button onclick="closeFieldSettingMethodMenu()" 
                    style="padding: 8px 16px; margin: 0 5px; background: #dc3545; color: white; 
                           border: none; border-radius: 6px; cursor: pointer; transition: all 0.2s;"
                    onmouseover="this.style.background='#c82333'"
                    onmouseout="this.style.background='#dc3545'">
                ⬅️ Back to Fields
            </button>
            ${hasSelections ? `
                <button onclick="clearFieldSelections('${fieldName}')" 
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

// Text input dialog creation
function createTextInputDialog(fieldName) {
    const dialogId = 'content-extractor-text-dialog';
    let existingDialog = document.getElementById(dialogId);
    if (existingDialog) {
        existingDialog.remove();
    }
    
    const field = window.contentExtractorData.fieldOptions.find(f => f.name === fieldName);
    if (!field) return;
    
    const dialog = document.createElement('div');
    dialog.id = dialogId;
    dialog.className = 'content-extractor-ui'; // Mark as our UI
    dialog.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        border: 3px solid ${field.color};
        border-radius: 12px;
        padding: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        z-index: 10001;
        max-width: 500px;
        min-width: 400px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    `;
    
    // Get existing values for display
    const fieldSelections = window.contentExtractorData.fieldSelections[fieldName] || [];
    let existingValueText = '';
    if (fieldSelections.length > 0) {
        if (field.type === 'single') {
            existingValueText = fieldSelections[0].selected_text || '';
        } else {
            existingValueText = fieldSelections.map(s => s.selected_text).join('\n');
        }
    }
    
    dialog.innerHTML = `
        <div style="text-align: center; margin-bottom: 20px;">
            <h3 style="margin: 0; color: ${field.color};">
                ✏️ Enter "${field.label}"
            </h3>
            <small style="color: #666;">Type or paste the value${field.type === 'multi-value' ? 's (one per line)' : ''}</small>
        </div>
        
        <div style="margin-bottom: 15px; padding: 8px 12px; background: #f8f9fa; border-radius: 6px; font-size: 14px;">
            <strong>${field.label}</strong> (${field.type})<br>
            <small style="color: #666;">${field.description}</small>
        </div>
        
        <div style="margin-bottom: 15px;">
            <label style="display: block; font-weight: bold; margin-bottom: 5px; color: #333;">
                ${field.type === 'multi-value' ? 'Values (one per line):' : 'Value:'}
            </label>
            <textarea id="text-input-field" 
                      style="width: 100%; min-height: ${field.type === 'multi-value' ? '120px' : '80px'}; 
                             padding: 10px; border: 2px solid ${field.color}40; border-radius: 6px; 
                             font-family: inherit; font-size: 14px; resize: vertical; outline: none;
                             transition: border-color 0.2s;"
                      placeholder="${field.type === 'multi-value' ? 'Enter each value on a new line...' : 'Enter the value...'}"
                      onFocus="this.style.borderColor='${field.color}'"
                      onBlur="this.style.borderColor='${field.color}40'">${existingValueText}</textarea>
        </div>
        
        ${field.type === 'multi-value' ? `
            <div style="margin-bottom: 15px; font-size: 12px; color: #666; background: #f8f9fa; padding: 8px; border-radius: 4px;">
                💡 <strong>Tip:</strong> For multi-value fields, put each item on a separate line. Empty lines will be ignored.
            </div>
        ` : ''}
        
        <div style="text-align: center; margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee;">
            <button onclick="saveTextInput('${fieldName}')" 
                    style="padding: 10px 20px; margin: 0 5px; background: #28a745; color: white; 
                           border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: bold;
                           transition: all 0.2s;"
                    onmouseover="this.style.background='#1e7e34'; this.style.transform='scale(1.05)'"
                    onmouseout="this.style.background='#28a745'; this.style.transform='scale(1)'">
                ✅ Save
            </button>
            <button onclick="cancelTextInput('${fieldName}')" 
                    style="padding: 10px 20px; margin: 0 5px; background: #6c757d; color: white; 
                           border: none; border-radius: 6px; cursor: pointer; font-size: 14px;
                           transition: all 0.2s;"
                    onmouseover="this.style.background='#5a6268'"
                    onmouseout="this.style.background='#6c757d'">
                ❌ Cancel
            </button>
        </div>
    `;
    
    document.body.appendChild(dialog);
    
    // Focus on the textarea
    setTimeout(() => {
        const textarea = document.getElementById('text-input-field');
        if (textarea) {
            textarea.focus();
            textarea.select(); // Select existing text if any
        }
    }, 100);
    
    return dialog;
} 