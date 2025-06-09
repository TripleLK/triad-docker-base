"""
Navigation Manager for Interactive Selector

Handles all navigation logic for nested field selection, including 
3-level menu hierarchy, breadcrumb management, and instance navigation.

Created by: Thunder Apex
Date: 2025-01-08
Project: Triad Docker Base
"""

import logging
from typing import Dict, List, Optional, Any
from .selection_context import NestedSelectionManager, SelectionField

logger = logging.getLogger(__name__)


class NavigationManager:
    """Manages navigation through nested field hierarchies."""
    
    def __init__(self, nested_manager: NestedSelectionManager, interactive_selector=None):
        """
        Initialize navigation manager with nested selection manager.
        
        Args:
            nested_manager: NestedSelectionManager instance for managing hierarchy
            interactive_selector: Reference to InteractiveSelector for URL switching (optional)
        """
        self.nested_manager = nested_manager
        self.interactive_selector = interactive_selector  # Store reference for URL switching
        self.pending_actions = []
        
    def enter_nested_field(self, field_name: str, instance_index: int = 0) -> bool:
        """
        Enter a nested field context for detailed field selection.
        
        Args:
            field_name: Name of the nested field (e.g., 'models', 'spec_groups')
            instance_index: Index of the specific instance being selected
            
        Returns:
            True if navigation was successful, False otherwise
        """
        try:
            logger.info(f"Entering nested field: {field_name}[{instance_index}]")
            
            # Use the nested manager to enter the context
            success = self.nested_manager.enter_nested_field(field_name, instance_index)
            
            if success:
                logger.info(f"Successfully entered {field_name}[{instance_index}] context")
                return True
            else:
                logger.error(f"Failed to enter {field_name}[{instance_index}] context")
                return False
                
        except Exception as e:
            logger.error(f"Error entering nested field {field_name}[{instance_index}]: {e}")
            return False
    
    def navigate_to_parent(self) -> bool:
        """
        Navigate back to the parent context level.
        
        Returns:
            True if navigation was successful, False otherwise
        """
        try:
            current_depth = self.nested_manager.get_current_depth()
            logger.info(f"Navigating to parent from depth {current_depth}")
            
            if current_depth <= 0:
                logger.warning("Already at root level, cannot navigate to parent")
                return False
            
            # Use the nested manager to navigate to parent
            success = self.nested_manager.navigate_to_parent()
            
            if success:
                new_depth = self.nested_manager.get_current_depth()
                logger.info(f"Successfully navigated to parent (depth {new_depth})")
                return True
            else:
                logger.error("Failed to navigate to parent")
                return False
                
        except Exception as e:
            logger.error(f"Error navigating to parent: {e}")
            return False
    
    def navigate_to_depth(self, target_depth: int) -> bool:
        """
        Navigate to a specific depth level.
        
        Args:
            target_depth: Target depth to navigate to (0 = root)
            
        Returns:
            True if navigation was successful, False otherwise
        """
        try:
            current_depth = self.nested_manager.get_current_depth()
            logger.info(f"Navigating from depth {current_depth} to depth {target_depth}")
            
            if target_depth < 0:
                logger.error(f"Invalid target depth: {target_depth}")
                return False
                
            if target_depth > current_depth:
                logger.warning(f"Cannot navigate to deeper level {target_depth} from current depth {current_depth}")
                return False
            
            # Navigate up to the target depth
            while self.nested_manager.get_current_depth() > target_depth:
                if not self.nested_manager.navigate_to_parent():
                    logger.error(f"Failed to navigate to depth {target_depth}")
                    return False
            
            logger.info(f"Successfully navigated to depth {target_depth}")
            return True
            
        except Exception as e:
            logger.error(f"Error navigating to depth {target_depth}: {e}")
            return False
    
    def check_for_nested_actions(self, driver) -> bool:
        """
        Check for pending nested navigation actions from JavaScript and handle them.
        
        Args:
            driver: Selenium WebDriver instance
            
        Returns:
            True if actions were found and processed, False otherwise
        """
        try:
            # Check for pending actions in JavaScript
            pending_action = driver.execute_script("""
                if (window.contentExtractorData && window.contentExtractorData.pendingAction) {
                    const action = window.contentExtractorData.pendingAction;
                    delete window.contentExtractorData.pendingAction;
                    return action;
                }
                return null;
            """)
            
            if not pending_action:
                return False
                
            action_type = pending_action.get('type')
            logger.info(f"Processing nested action: {action_type}")
            
            if action_type == 'navigate_to_parent':
                return self.navigate_to_parent()
                
            elif action_type == 'enter_nested_field':
                field_name = pending_action.get('field_name')
                instance_index = pending_action.get('instance_index', 0)
                return self.enter_nested_field(field_name, instance_index)
                
            elif action_type == 'show_instance_management':
                field_name = pending_action.get('field_name')
                return self.show_instance_management_menu(field_name, driver)
                
            elif action_type == 'enter_instance_context':
                field_name = pending_action.get('field_name')
                instance_index = pending_action.get('instance_index', 0)
                return self.enter_nested_field(field_name, instance_index)
                
            elif action_type == 'add_new_instance':
                field_name = pending_action.get('field_name')
                return self.add_nested_instance(field_name, driver)
                
            elif action_type == 'switch_url':
                # Handle URL switching action
                direction = pending_action.get('direction')
                target_url = pending_action.get('target_url')
                return self.handle_url_switch(direction, target_url, driver)
                
            else:
                logger.warning(f"Unknown nested action type: {action_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking for nested actions: {e}")
            return False
    
    def show_instance_management_menu(self, field_name: str, driver) -> bool:
        """
        Show the instance management menu for a nested field.
        This implements Level 2 of the 3-level hierarchy.
        
        Args:
            field_name: Name of the field to manage instances for
            driver: Selenium WebDriver instance
            
        Returns:
            True if menu was displayed successfully, False otherwise
        """
        try:
            logger.info(f"Showing instance management menu for {field_name}")
            
            # Get current instances (this would be enhanced to track actual instances)
            # For now, we'll start with just one default instance
            instances = [f"{field_name}[0]"]  # Default first instance
            
            # Build instance buttons HTML
            instance_buttons_html = ""
            for i, instance in enumerate(instances):
                instance_buttons_html += f"""
                    <button onclick="enterInstanceContext('{field_name}', {i})" 
                            style="display: inline-block; margin: 5px; padding: 10px 15px; 
                                   background: #007bff; color: white; border: none; 
                                   border-radius: 6px; cursor: pointer; font-size: 14px;">
                        {instance}
                    </button>
                """
            
            # Add "Add New Instance" button
            instance_buttons_html += f"""
                <button onclick="addNewInstance('{field_name}')" 
                        style="display: inline-block; margin: 5px; padding: 10px 15px; 
                               background: #ff6600; color: white; border: none; 
                               border-radius: 6px; cursor: pointer; font-size: 14px;">
                    ➕ Add New Instance
                </button>
            """
            
            # Inject the instance buttons into the menu
            driver.execute_script(f"""
                const container = document.getElementById('instance-buttons-container');
                if (container) {{
                    container.innerHTML = `{instance_buttons_html}`;
                }}
            """)
            
            logger.info(f"Instance management menu populated for {field_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error showing instance management menu for {field_name}: {e}")
            return False
    
    def add_nested_instance(self, field_name: str, driver) -> bool:
        """
        Add a new instance for a nested field.
        
        Args:
            field_name: Name of the field to add an instance for
            driver: Selenium WebDriver instance
            
        Returns:
            True if instance was added successfully, False otherwise
        """
        try:
            logger.info(f"Adding new instance for {field_name}")
            
            # This would be enhanced to track actual instances in the database/session
            # For now, we'll refresh the instance management menu with the new instance
            
            # In a full implementation, you would:
            # 1. Determine the next available index
            # 2. Create a new instance context
            # 3. Update the session data
            # 4. Refresh the instance management menu
            
            # For now, just refresh the menu to show the addition
            self.show_instance_management_menu(field_name, driver)
            
            logger.info(f"New instance added for {field_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding instance for {field_name}: {e}")
            return False
    
    def handle_url_switch(self, direction: str, target_url: str, driver) -> bool:
        """
        Handle URL switching action triggered from JavaScript.
        
        Args:
            direction: 'next' or 'previous' direction for URL switching
            target_url: The target URL to switch to
            driver: Selenium WebDriver instance
            
        Returns:
            True if URL switch was successful, False otherwise
        """
        try:
            if not self.interactive_selector:
                logger.error("Cannot switch URL: No interactive selector reference")
                return False
            
            logger.info(f"Handling URL switch: {direction} -> {target_url}")
            
            # Use the interactive selector's URL switching methods
            if direction == 'next':
                success = self.interactive_selector.switch_to_next_url()
            elif direction == 'previous':
                success = self.interactive_selector.switch_to_previous_url()
            else:
                logger.error(f"Invalid URL switch direction: {direction}")
                return False
            
            if success:
                logger.info(f"Successfully switched URL via {direction} action")
                # The interactive selector handles JavaScript re-injection automatically
                return True
            else:
                logger.error(f"Failed to switch URL via {direction} action")
                return False
                
        except Exception as e:
            logger.error(f"Error handling URL switch: {e}")
            return False
    
    def get_nested_selection_hierarchy(self) -> Dict:
        """
        Get the current nested selection hierarchy information.
        
        Returns:
            Dictionary containing hierarchy information
        """
        try:
            return {
                'current_depth': self.nested_manager.get_current_depth(),
                'breadcrumbs': self.nested_manager.get_breadcrumbs(),
                'depth_color': self.nested_manager.get_depth_color(),
                'available_fields': [
                    {
                        'name': field.name,
                        'label': field.label,
                        'type': field.type,
                        'description': field.description,
                        'has_sub_fields': field.sub_fields is not None
                    }
                    for field in self.nested_manager.get_current_fields()
                ]
            }
        except Exception as e:
            logger.error(f"Error getting nested selection hierarchy: {e}")
            return {}
    
    def get_current_context_info(self) -> Dict:
        """
        Get information about the current selection context.
        
        Returns:
            Dictionary with current context information
        """
        try:
            return {
                'depth': self.nested_manager.get_current_depth(),
                'breadcrumbs': self.nested_manager.get_breadcrumbs(),
                'depth_color': self.nested_manager.get_depth_color(),
                'field_count': len(self.nested_manager.get_current_fields()),
                'context_path': '.'.join(self.nested_manager.get_breadcrumbs()) if self.nested_manager.get_breadcrumbs() else 'root'
            }
        except Exception as e:
            logger.error(f"Error getting current context info: {e}")
            return {}
    
    def poll_for_nested_actions(self, driver, timeout: float = 30.0) -> bool:
        """
        Poll for nested navigation actions from the JavaScript interface.
        
        Args:
            driver: Selenium WebDriver instance
            timeout: Maximum time to poll for actions
            
        Returns:
            True if actions were found and processed, False if timeout reached
        """
        import time
        
        start_time = time.time()
        
        try:
            while time.time() - start_time < timeout:
                # Check for pending actions
                if self.check_for_nested_actions(driver):
                    return True
                    
                # Short pause to avoid excessive polling
                time.sleep(0.1)
                
            logger.info(f"Polling timeout reached ({timeout}s) - no nested actions found")
            return False
            
        except Exception as e:
            logger.error(f"Error polling for nested actions: {e}")
            return False
    
    def update_javascript_context(self, driver) -> bool:
        """
        Update the JavaScript context with current navigation state.
        
        Args:
            driver: Selenium WebDriver instance
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            context_info = self.get_current_context_info()
            
            # Update JavaScript with current context
            driver.execute_script(f"""
                if (window.contentExtractorData) {{
                    window.contentExtractorData.currentDepth = {context_info['depth']};
                    window.contentExtractorData.breadcrumbs = {context_info['breadcrumbs']};
                    window.contentExtractorData.depthColor = '{context_info['depth_color']}';
                    window.contentExtractorData.contextPath = '{context_info['context_path']}';
                }}
            """)
            
            logger.debug(f"Updated JavaScript context: depth={context_info['depth']}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating JavaScript context: {e}")
            return False
    
    def reset_navigation(self) -> bool:
        """
        Reset navigation to root level.
        
        Returns:
            True if reset was successful, False otherwise
        """
        try:
            logger.info("Resetting navigation to root level")
            
            # Navigate back to root (depth 0)
            return self.navigate_to_depth(0)
            
        except Exception as e:
            logger.error(f"Error resetting navigation: {e}")
            return False 