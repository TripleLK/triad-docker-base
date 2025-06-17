/**
 * Content Extractor Core Functions
 * 
 * This file contains core utility functions and color definitions
 * for the interactive content extractor system.
 * 
 * Created by: Electric Sentinel
 * Date: 2025-01-08
 * Project: Triad Docker Base
 */

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
function getDepthColor(depth) {
    return DEPTH_COLORS[Math.min(depth, DEPTH_COLORS.length - 1)];
}

// Field-specific highlight colors (legacy support)
const FIELD_COLORS = {
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
};

// Get field color with depth override
function getFieldColor(fieldName) {
    if (window.contentExtractorData.currentDepth > 0) {
        // Use depth color for nested contexts
        return getDepthColor(window.contentExtractorData.currentDepth);
    }
    return FIELD_COLORS[fieldName] || '#007bff';
}

// Generate unique ID for elements
function generateElementId() {
    return 'content-extractor-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
}

// Get XPath for element
function getElementXPath(element) {
    if (element.id) {
        return '//*[@id="' + element.id + '"]';
    }
    
    if (element === document.body) {
        return '/html/body';
    }
    
    let path = '';
    let current = element;
    
    while (current && current !== document.body) {
        let selector = current.tagName.toLowerCase();
        let siblings = Array.from(current.parentNode.children).filter(e => e.tagName === current.tagName);
        
        if (siblings.length > 1) {
            let index = siblings.indexOf(current) + 1;
            selector += '[' + index + ']';
        }
        
        path = '/' + selector + path;
        current = current.parentNode;
    }
    
    return '/html/body' + path;
}

// Get CSS selector for element
function getElementCSSSelector(element) {
    if (element.id) {
        return '#' + element.id;
    }
    
    let path = [];
    let current = element;
    
    while (current && current !== document.body) {
        let selector = current.tagName.toLowerCase();
        
        if (current.className) {
            let classes = current.className.split(' ').filter(c => c.trim());
            if (classes.length > 0) {
                selector += '.' + classes.join('.');
            }
        }
        
        let siblings = Array.from(current.parentNode.children).filter(e => 
            e.tagName === current.tagName && e.className === current.className
        );
        
        if (siblings.length > 1) {
            let index = siblings.indexOf(current) + 1;
            selector += ':nth-of-type(' + index + ')';
        }
        
        path.unshift(selector);
        current = current.parentNode;
    }
    
    return path.join(' > ');
}

// Highlight element
function highlightElement(element, color) {
    if (!element) return;
    
    element.style.outline = '3px solid ' + color;
    element.style.outlineOffset = '2px';
    element.style.backgroundColor = color + '20';
    element.style.cursor = 'pointer';
}

// Remove highlight from element
function removeHighlight(element) {
    if (!element) return;
    
    element.style.outline = '';
    element.style.outlineOffset = '';
    element.style.backgroundColor = '';
    element.style.cursor = '';
}

/**
 * Safe XPath element loader function
 * Can be called from browser console/terminal
 * 
 * @param {string} xpath - The XPath expression to evaluate
 * @param {Document|Element} contextNode - Context node for evaluation (defaults to document)
 * @returns {Element|null} - The first matching element or null
 */
function getElementByXpath(xpath, contextNode = document) {
    try {
        // Validate inputs
        if (!xpath || typeof xpath !== 'string') {
            console.error('getElementByXpath: Invalid XPath provided:', xpath);
            return null;
        }
        
        if (!contextNode || typeof contextNode.evaluate === 'undefined') {
            console.error('getElementByXpath: Invalid context node provided');
            return null;
        }
        
        // Evaluate XPath
        const result = contextNode.evaluate(
            xpath, 
            contextNode, 
            null, 
            XPathResult.FIRST_ORDERED_NODE_TYPE, 
            null
        );
        
        const element = result.singleNodeValue;
        
        if (element) {
            console.log('✅ Found element:', element);
            console.log('📍 Element location:', getElementXPath(element));
            
            // Briefly highlight the found element for visual confirmation
            const originalOutline = element.style.outline;
            const originalBackground = element.style.backgroundColor;
            
            highlightElement(element, '#00ff00'); // Green highlight
            
            // Remove highlight after 2 seconds
            setTimeout(() => {
                element.style.outline = originalOutline;
                element.style.backgroundColor = originalBackground;
            }, 2000);
            
            return element;
        } else {
            console.warn('⚠️ No element found for XPath:', xpath);
            return null;
        }
        
    } catch (error) {
        console.error('❌ Error evaluating XPath:', xpath, error);
        return null;
    }
}

/**
 * Get multiple elements by XPath
 * 
 * @param {string} xpath - The XPath expression to evaluate
 * @param {Document|Element} contextNode - Context node for evaluation (defaults to document)
 * @returns {Array<Element>} - Array of matching elements
 */
function getElementsByXpath(xpath, contextNode = document) {
    try {
        // Validate inputs
        if (!xpath || typeof xpath !== 'string') {
            console.error('getElementsByXpath: Invalid XPath provided:', xpath);
            return [];
        }
        
        if (!contextNode || typeof contextNode.evaluate === 'undefined') {
            console.error('getElementsByXpath: Invalid context node provided');
            return [];
        }
        
        // Evaluate XPath for multiple results
        const result = contextNode.evaluate(
            xpath, 
            contextNode, 
            null, 
            XPathResult.ORDERED_NODE_ITERATOR_TYPE, 
            null
        );
        
        const elements = [];
        let element = result.iterateNext();
        
        while (element) {
            elements.push(element);
            element = result.iterateNext();
        }
        
        console.log(`✅ Found ${elements.length} elements for XPath:`, xpath);
        
        // Briefly highlight all found elements
        elements.forEach((el, index) => {
            const originalOutline = el.style.outline;
            const originalBackground = el.style.backgroundColor;
            
            highlightElement(el, '#00ff00'); // Green highlight
            
            // Remove highlight after 2 seconds
            setTimeout(() => {
                el.style.outline = originalOutline;
                el.style.backgroundColor = originalBackground;
            }, 2000);
        });
        
        return elements;
        
    } catch (error) {
        console.error('❌ Error evaluating XPath:', xpath, error);
        return [];
    }
}

// Make functions globally accessible for terminal use
window.getElementByXpath = getElementByXpath;
window.getElementsByXpath = getElementsByXpath;

// Add to console for easy discovery
console.log('🔧 XPath utilities loaded:');
console.log('  • getElementByXpath(xpath) - Find single element');
console.log('  • getElementsByXpath(xpath) - Find multiple elements');
console.log('  • Example: getElementByXpath("//h1[@class=\\"title\\"]")'); 