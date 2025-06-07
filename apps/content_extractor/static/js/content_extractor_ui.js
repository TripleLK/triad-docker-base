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

// Create field selection menu
function createFieldMenu() {
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
        max-width: 500px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    `;
    
    // Header
    let headerHtml = `
        <div style="text-align: center; margin-bottom: 20px;">
            <h3 style="margin: 0; color: ${window.contentExtractorData.depthColor};">
                🏗️ Manage ${fieldName} Instances
            </h3>
        </div>
    `;
    
    // Breadcrumb for instance management
    let breadcrumbHtml = `
        <div style="margin-bottom: 15px; padding: 8px 12px; background: #f8f9fa; border-radius: 6px; font-size: 14px; color: #6c757d;">
            📍 Root → ${fieldName}
        </div>
    `;
    
    // Instance buttons (placeholder - will be populated by Python backend)
    let instancesHtml = `
        <div id="instance-buttons-container" style="margin: 15px 0;">
            <!-- Instance buttons will be populated here -->
        </div>
    `;
    
    // Navigation buttons
    let navigationHtml = `
        <div style="text-align: center; margin-top: 20px;">
            <button onclick="navigateToParent()" 
                    style="padding: 8px 16px; margin: 0 5px; background: #6c757d; 
                           color: white; border: none; border-radius: 6px; cursor: pointer;">
                ⬆️ Parent Level
            </button>
            <button onclick="closeInstanceMenu()" 
                    style="padding: 8px 16px; margin: 0 5px; background: #dc3545; 
                           color: white; border: none; border-radius: 6px; cursor: pointer;">
                ✖️ Close Menu
            </button>
        </div>
    `;
    
    menu.innerHTML = headerHtml + breadcrumbHtml + instancesHtml + navigationHtml;
    document.body.appendChild(menu);
    
    // Signal to Python backend to populate instances
    window.contentExtractorData.pendingAction = {
        type: 'show_instance_management',
        field_name: fieldName
    };
    
    return menu;
} 