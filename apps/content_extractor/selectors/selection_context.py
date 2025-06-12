"""
Modular Selection Context for Nested Object Selection

Implements a recursive selection interface that can handle hierarchical data structures
like models with spec_groups, where each level can contain sub-selections.

Created by: Quantum Horizon
Date: 2025-01-08
Project: Triad Docker Base
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import json


@dataclass
class SelectionField:
    """Represents a field that can be selected in a context."""
    name: str
    label: str
    type: str  # 'single', 'multi-value', 'nested'
    description: str
    sub_fields: Optional[List['SelectionField']] = None
    color: str = '#007bff'


@dataclass
class SelectionResult:
    """Result of a selection operation."""
    field_name: str
    context_path: str  # e.g., "models.0.spec_groups.1" 
    xpath: str
    css_selector: str
    selected_text: str
    depth: int


class SelectionContext:
    """
    Modular selection context that can be used recursively for nested object selection.
    
    Each context represents a level in the hierarchy (e.g., page level, model level, spec_group level)
    and can contain sub-contexts for nested fields.
    """
    
    # Define the nested field structures for LabEquipmentPage
    FIELD_DEFINITIONS = {
        'models': SelectionField(
            name='models',
            label='Equipment Models',
            type='nested',
            description='Product model variations with detailed specifications',
            color='#bb8fce',
            sub_fields=[
                SelectionField('name', 'Model Name', 'single', 'Name of the model', color='#d7bde2'),
                SelectionField('model_number', 'Model Number', 'single', 'Identification number', color='#d7bde2'),
                SelectionField('spec_groups', 'Specification Groups', 'nested', 'Technical specification groups', 
                              color='#c39bd3',
                              sub_fields=[
                                  SelectionField('name', 'Group Name', 'single', 'Name of the specification group', color='#e8daef'),
                                  SelectionField('specs', 'Specifications', 'multi-value', 'Individual key-value specifications', color='#e8daef')
                              ])
            ]
        ),
        'spec_groups': SelectionField(
            name='spec_groups',
            label='Specification Groups',
            type='nested',
            description='Technical specifications with nested specs',
            color='#aed6f1',
            sub_fields=[
                SelectionField('name', 'Group Name', 'single', 'Name of the specification group', color='#d5e8f7'),
                SelectionField('specs', 'Specifications', 'multi-value', 'Individual key-value specifications', color='#d5e8f7')
            ]
        ),
        'features': SelectionField(
            name='features',
            label='Features',
            type='multi-value',
            description='Equipment features list',
            color='#85c1e9'
        ),
        'accessories': SelectionField(
            name='accessories',
            label='Accessories',
            type='multi-value', 
            description='Related accessories/parts',
            color='#f8c471'
        ),
        'categorized_tags': SelectionField(
            name='categorized_tags',
            label='Categorized Tags',
            type='multi-value',
            description='Category and tag assignments',
            color='#82e0aa'
        ),
        'gallery_images': SelectionField(
            name='gallery_images',
            label='Gallery Images',
            type='multi-value',
            description='Product image gallery',
            color='#f1948a'
        )
    }
    
    def __init__(self, context_path: str = "", depth: int = 0, parent_context: Optional['SelectionContext'] = None):
        """
        Initialize selection context.
        
        Args:
            context_path: Dot-separated path showing position in hierarchy (e.g., "models.0.spec_groups")
            depth: Current nesting depth (0 = root level)
            parent_context: Reference to parent context for navigation
        """
        self.context_path = context_path
        self.depth = depth
        self.parent_context = parent_context
        self.sub_contexts: Dict[str, 'SelectionContext'] = {}
        self.selections: List[SelectionResult] = []
        self.active_field: Optional[str] = None
        
    def get_available_fields(self) -> List[SelectionField]:
        """Get fields available for selection at this context level."""
        if self.depth == 0:
            # Root level - return top-level LabEquipmentPage fields
            return [
                # Single value fields
                SelectionField('title', 'Title', 'single', 'Equipment main title', color='#ff6b6b'),
                SelectionField('short_description', 'Short Description', 'single', 'Brief equipment summary', color='#4ecdc4'),
                SelectionField('full_description', 'Full Description', 'single', 'Detailed equipment description', color='#45b7d1'),
                SelectionField('model_name', 'Model Name', 'multi-value', 'Individual model names for extraction (select all models)', color='#ffa07a'),
                SelectionField('specification_group_names', 'Specification Group Names', 'multi-value', 'Extract specification group names (DIMENSIONS, ELECTRICAL, etc.)', color='#98fb98'),
                SelectionField('source_url', 'Source URL', 'single', 'Original product page URL', color='#87ceeb'),
                SelectionField('source_type', 'Source Type', 'single', 'New/Used/Refurbished indicator', color='#98d8c8'),
                # Nested/Multi-value fields
                self.FIELD_DEFINITIONS['models'],
                self.FIELD_DEFINITIONS['spec_groups'],
                self.FIELD_DEFINITIONS['features'],
                self.FIELD_DEFINITIONS['accessories'],
                self.FIELD_DEFINITIONS['categorized_tags'],
                self.FIELD_DEFINITIONS['gallery_images']
            ]
        else:
            # Sub-context level - get fields based on context path
            return self._get_context_fields()
    
    def _get_context_fields(self) -> List[SelectionField]:
        """Get fields for current sub-context based on context path."""
        path_parts = self.context_path.split('.')
        
        if 'models' in path_parts:
            if path_parts[-1] == 'spec_groups' or 'spec_groups' in path_parts:
                # Inside a spec group context
                return self.FIELD_DEFINITIONS['spec_groups'].sub_fields
            else:
                # Inside a model context
                return self.FIELD_DEFINITIONS['models'].sub_fields
                
        elif 'spec_groups' in path_parts:
            # Inside a spec group context
            return self.FIELD_DEFINITIONS['spec_groups'].sub_fields
            
        return []
    
    def enter_nested_context(self, field_name: str, instance_index: int = 0) -> 'SelectionContext':
        """
        Enter a nested selection context for a field.
        
        Args:
            field_name: Name of the nested field (e.g., 'models', 'spec_groups')
            instance_index: Index of the specific instance being selected (for multi-value fields)
            
        Returns:
            New SelectionContext for the nested field
        """
        new_path = f"{self.context_path}.{field_name}.{instance_index}" if self.context_path else f"{field_name}.{instance_index}"
        new_depth = self.depth + 1
        
        sub_context = SelectionContext(
            context_path=new_path,
            depth=new_depth,
            parent_context=self
        )
        
        self.sub_contexts[f"{field_name}.{instance_index}"] = sub_context
        return sub_context
    
    def get_depth_color(self) -> str:
        """Get border color based on selection depth."""
        depth_colors = [
            '#3498db',  # Blue - root level
            '#e74c3c',  # Red - first nesting  
            '#f39c12',  # Orange - second nesting
            '#27ae60',  # Green - third nesting
            '#9b59b6',  # Purple - fourth nesting
            '#34495e'   # Dark gray - deeper nesting
        ]
        return depth_colors[min(self.depth, len(depth_colors) - 1)]
    
    def get_breadcrumb_path(self) -> List[str]:
        """Get breadcrumb navigation path to current context."""
        if not self.context_path:
            return ['Root']
            
        parts = self.context_path.split('.')
        breadcrumbs = ['Root']
        
        for i in range(0, len(parts), 2):
            field_name = parts[i]
            instance_index = parts[i + 1] if i + 1 < len(parts) else '0'
            breadcrumbs.append(f"{field_name}[{instance_index}]")
            
        return breadcrumbs
    
    def add_selection(self, field_name: str, xpath: str, css_selector: str, selected_text: str) -> SelectionResult:
        """Add a selection result to this context."""
        result = SelectionResult(
            field_name=field_name,
            context_path=self.context_path,
            xpath=xpath,
            css_selector=css_selector,
            selected_text=selected_text,
            depth=self.depth
        )
        self.selections.append(result)
        return result
    
    def get_all_selections(self) -> List[SelectionResult]:
        """Get all selections from this context and all sub-contexts."""
        all_selections = self.selections.copy()
        
        for sub_context in self.sub_contexts.values():
            all_selections.extend(sub_context.get_all_selections())
            
        return all_selections
    
    def navigate_to_parent(self) -> Optional['SelectionContext']:
        """Navigate back to parent context."""
        return self.parent_context
    
    def export_hierarchy(self) -> Dict[str, Any]:
        """Export the complete selection hierarchy as a dictionary."""
        return {
            'context_path': self.context_path,
            'depth': self.depth,
            'selections': [
                {
                    'field_name': sel.field_name,
                    'xpath': sel.xpath,
                    'css_selector': sel.css_selector,
                    'selected_text': sel.selected_text
                }
                for sel in self.selections
            ],
            'sub_contexts': {
                key: context.export_hierarchy()
                for key, context in self.sub_contexts.items()
            }
        }
    
    def get_context_title(self) -> str:
        """Get a human-readable title for this context."""
        if not self.context_path:
            return "LabEquipmentPage Fields"
            
        breadcrumbs = self.get_breadcrumb_path()
        return " → ".join(breadcrumbs[1:])  # Skip 'Root'


class NestedSelectionManager:
    """
    Manages the overall nested selection process with context switching and navigation.
    """
    
    def __init__(self):
        """Initialize the nested selection manager."""
        self.root_context = SelectionContext()
        self.current_context = self.root_context
        self.context_history: List[SelectionContext] = [self.root_context]
    
    def get_current_fields(self) -> List[SelectionField]:
        """Get fields available in current context."""
        return self.current_context.get_available_fields()
    
    def enter_nested_field(self, field_name: str, instance_index: int = 0) -> bool:
        """
        Enter a nested field context.
        
        Args:
            field_name: Name of the field to enter
            instance_index: Index for multi-value fields
            
        Returns:
            True if successfully entered nested context
        """
        # Check if field supports nesting
        available_fields = self.current_context.get_available_fields()
        target_field = next((f for f in available_fields if f.name == field_name), None)
        
        if not target_field or target_field.type != 'nested':
            return False
            
        # Enter the nested context
        self.current_context = self.current_context.enter_nested_context(field_name, instance_index)
        self.context_history.append(self.current_context)
        return True
    
    def navigate_to_parent(self) -> bool:
        """Navigate back to parent context."""
        if len(self.context_history) <= 1:
            return False  # Already at root
            
        self.context_history.pop()
        self.current_context = self.context_history[-1]
        return True
    
    def add_selection(self, field_name: str, xpath: str, css_selector: str, selected_text: str) -> SelectionResult:
        """Add selection to current context."""
        return self.current_context.add_selection(field_name, xpath, css_selector, selected_text)
    
    def get_current_depth(self) -> int:
        """Get current selection depth."""
        return self.current_context.depth
    
    def get_depth_color(self) -> str:
        """Get color for current depth."""
        return self.current_context.get_depth_color()
    
    def get_breadcrumbs(self) -> List[str]:
        """Get breadcrumb navigation."""
        return self.current_context.get_breadcrumb_path()
    
    def export_all_selections(self) -> Dict[str, Any]:
        """Export complete selection hierarchy."""
        return self.root_context.export_hierarchy() 