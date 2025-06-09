"""
Interactive Selector for Content Extraction - Refactored

Uses Selenium to display web pages and capture user selections
for generating robust content selectors with field-specific assignment.
Modular design with separate managers for different concerns.

Created by: Thunder Apex
Date: 2025-01-08
Project: Triad Docker Base
"""

import time
import json
import logging
from typing import Dict, List, Optional, Tuple

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# Import modular components
from .selection_context import NestedSelectionManager, SelectionField
from .js_injection import JavaScriptInjectionManager
from .database_operations import DatabaseOperationsManager
from .navigation_manager import NavigationManager

logger = logging.getLogger(__name__)


class InteractiveSelector:
    """
    Streamlined interactive selector using modular components.
    
    This class orchestrates the different managers to provide a clean interface
    for interactive content selection with nested field support.
    """
    
    def __init__(self, headless: bool = False, session_name: str = None, base_url: str = 'http://localhost:8000', api_token: str = None):
        """
        Initialize interactive content selector with hierarchical field management.
        
        Args:
            headless: Run browser in headless mode
            session_name: Name for this selection session
            base_url: Base URL for API calls (default: http://localhost:8000)
            api_token: API token for authentication (optional)
        """
        self.headless = headless
        self.driver = None
        self.session_name = session_name or f"session_{int(time.time())}"
        self.base_url = base_url
        self.api_token = api_token
        self.current_url = None
        self.current_domain = None
        
        # Initialize modular managers
        self.nested_manager = NestedSelectionManager()
        self.js_manager = JavaScriptInjectionManager()
        self.db_manager = DatabaseOperationsManager(self.session_name)
        self.nav_manager = NavigationManager(self.nested_manager)
        
        # Legacy support for backward compatibility
        self.selected_elements = []
        self.selection_session_data = {
            'active_field': None,
            'field_selections': {},
            'multi_value_examples': {}
        }
    
    def setup_driver(self) -> bool:
        """Set up Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        
        # Explicitly set Chrome binary path for macOS
        chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Additional options for macOS ARM64 compatibility
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        
        # Try multiple approaches to get ChromeDriver working
        approaches = [
            self._setup_with_webdriver_manager,
            self._setup_with_system_chromedriver,
            self._setup_with_homebrew_chromedriver
        ]
        
        for i, approach in enumerate(approaches, 1):
            try:
                logger.info(f"Attempting ChromeDriver setup method {i}/3...")
                service = approach()
                if service:
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    
                    # Execute script to remove webdriver property
                    self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                    
                    logger.info(f"WebDriver setup complete using method {i}")
                    return True
                    
            except Exception as e:
                logger.warning(f"Method {i} failed: {e}")
                continue
        
        logger.error("All ChromeDriver setup methods failed")
        return False
    
    def _setup_with_webdriver_manager(self):
        """Try to setup ChromeDriver using webdriver-manager with permission fixes."""
        import os
        import stat
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Install chromedriver
        driver_path = ChromeDriverManager().install()
        logger.info(f"ChromeDriver downloaded to: {driver_path}")
        
        # Fix permissions on macOS ARM64
        if os.path.exists(driver_path):
            # Make sure the chromedriver is executable
            current_permissions = os.stat(driver_path).st_mode
            os.chmod(driver_path, current_permissions | stat.S_IEXEC | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            logger.info(f"Fixed permissions for ChromeDriver: {driver_path}")
            
            return Service(driver_path)
        
        return None
    
    def _setup_with_system_chromedriver(self):
        """Try to use system-installed ChromeDriver."""
        import shutil
        
        # Check if chromedriver is available in PATH
        chromedriver_path = shutil.which("chromedriver")
        if chromedriver_path:
            logger.info(f"Found system ChromeDriver: {chromedriver_path}")
            return Service(chromedriver_path)
        
        return None
    
    def _setup_with_homebrew_chromedriver(self):
        """Try to use Homebrew-installed ChromeDriver."""
        import os
        
        # Common Homebrew paths for ChromeDriver
        homebrew_paths = [
            "/opt/homebrew/bin/chromedriver",  # ARM64 Homebrew
            "/usr/local/bin/chromedriver",     # Intel Homebrew
            "/opt/homebrew/Caskroom/chromedriver/latest/chromedriver"
        ]
        
        for path in homebrew_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                logger.info(f"Found Homebrew ChromeDriver: {path}")
                return Service(path)
        
        return None

    def load_page(self, url: str, wait_time: int = 10) -> bool:
        """
        Load a web page and inject the selection interface.
        
        Args:
            url: URL to load
            wait_time: Time to wait for page load
            
        Returns:
            True if page loaded successfully, False otherwise
        """
        try:
            if not self.driver:
                if not self.setup_driver():
                    return False
            
            logger.info(f"Loading page: {url}")
            self.driver.get(url)
            self.current_url = url
            self.current_domain = self.db_manager.get_domain_from_url(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located(("tag name", "body"))
            )
            
            # Inject JavaScript interface
            self._inject_selection_js()
            
            logger.info(f"Page loaded successfully: {self.current_domain}")
            return True
            
        except TimeoutException:
            logger.error(f"Timeout loading page: {url}")
            return False
        except Exception as e:
            logger.error(f"Error loading page {url}: {e}")
            return False
    
    def _inject_selection_js(self):
        """Inject the JavaScript selection interface."""
        try:
            # Get current context information
            current_fields = self.nested_manager.get_current_fields()
            current_depth = self.nested_manager.get_current_depth()
            depth_color = self.nested_manager.get_depth_color()
            breadcrumbs = self.nested_manager.get_breadcrumbs()
            
            # Generate and inject JavaScript
            js_code = self.js_manager.get_selection_javascript(
                current_fields, current_depth, depth_color, breadcrumbs, self.base_url, self.api_token
            )
            
            self.driver.execute_script(js_code)
            logger.info("JavaScript interface injected successfully")
            
        except Exception as e:
            logger.error(f"Failed to inject JavaScript: {e}")
    
    def show_field_menu(self) -> bool:
        """Show the field selection menu."""
        try:
            # First check if JavaScript functions are available and if re-injection is needed
            js_status = self.driver.execute_script("""
                return {
                    showFieldMenu: typeof window.showFieldMenu !== 'undefined',
                    createFieldMenu: typeof window.createFieldMenu !== 'undefined',
                    contentExtractorData: typeof window.contentExtractorData !== 'undefined',
                    controlPanel: document.getElementById('content-extractor-control-panel') !== null,
                    needsReinjection: window.contentExtractorData ? window.contentExtractorData.needsReinjection : false,
                    injectionTimestamp: window.contentExtractorData ? window.contentExtractorData.injectionTimestamp : null
                };
            """)
            
            logger.info(f"JavaScript status check: {js_status}")
            
            # Check if re-injection is needed
            needs_reinject = (
                not js_status.get('showFieldMenu', False) or 
                not js_status.get('createFieldMenu', False) or
                js_status.get('needsReinjection', False)
            )
            
            if needs_reinject:
                logger.info("JavaScript functions not available or re-injection requested, re-injecting...")
                self._inject_selection_js()
                
                # Wait a moment for injection to complete
                time.sleep(0.5)
                
                # Check again after re-injection
                js_status_after = self.driver.execute_script("""
                    return {
                        showFieldMenu: typeof window.showFieldMenu !== 'undefined',
                        createFieldMenu: typeof window.createFieldMenu !== 'undefined',
                        contentExtractorData: typeof window.contentExtractorData !== 'undefined',
                        controlPanel: document.getElementById('content-extractor-control-panel') !== null
                    };
                """)
                logger.info(f"After re-injection: {js_status_after}")
                
                # Clear the re-injection flag
                self.driver.execute_script("""
                    if (window.contentExtractorData) {
                        window.contentExtractorData.needsReinjection = false;
                    }
                """)
                
            # Now try to show the menu using the window-attached function
            self.driver.execute_script("window.showFieldMenu();")
            logger.info("window.showFieldMenu() called successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to show field menu: {e}")
            # Try re-injecting JavaScript as a fallback
            try:
                logger.info("Attempting to re-inject JavaScript and retry...")
                self._inject_selection_js()
                time.sleep(0.5)
                self.driver.execute_script("window.showFieldMenu();")
                return True
            except Exception as e2:
                logger.error(f"Failed even after re-injection: {e2}")
            return False
            
    def start_field_selection(self, field_name: str) -> bool:
        """Start selection mode for a specific field."""
        try:
            self.selection_session_data['active_field'] = field_name
            self.driver.execute_script(f"startSelection('{field_name}');")
            logger.info(f"Started selection for field: {field_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to start field selection for {field_name}: {e}")
            return False

    def stop_selection(self) -> List[Dict]:
        """Stop selection mode and return collected selections."""
        try:
            selections = self.driver.execute_script("""
                stopSelection();
                return window.contentExtractorData.fieldSelections;
            """)
            
            # Update internal state
            active_field = self.selection_session_data.get('active_field')
            if active_field and active_field in selections:
                self.selection_session_data['field_selections'][active_field] = selections[active_field]
            
            self.selection_session_data['active_field'] = None
            logger.info("Selection stopped, returning collected selections")
            return selections.get(active_field, []) if active_field else []
            
        except Exception as e:
            logger.error(f"Failed to stop selection: {e}")
            return []
    
    def poll_for_nested_actions(self, timeout: float = 30.0) -> bool:
        """Poll for nested navigation actions from the JavaScript interface."""
        return self.nav_manager.poll_for_nested_actions(self.driver, timeout)
    
    def check_for_nested_actions(self) -> bool:
        """Check for nested navigation actions from the JavaScript interface."""
        return self.nav_manager.check_for_nested_actions(self.driver)
    
    def navigate_to_depth(self, target_depth: int) -> bool:
        """Navigate to a specific depth level."""
        success = self.nav_manager.navigate_to_depth(target_depth)
        if success:
            # Update JavaScript context and re-inject
            self._inject_selection_js()
            self.nav_manager.update_javascript_context(self.driver)
        return success
    
    def enter_nested_field(self, field_name: str, instance_index: int = 0) -> bool:
        """Enter a nested field context."""
        success = self.nav_manager.enter_nested_field(field_name, instance_index)
        if success:
            # Update JavaScript context and re-inject
            self._inject_selection_js()
            self.nav_manager.update_javascript_context(self.driver)
        return success
    
    def navigate_to_parent(self) -> bool:
        """Navigate back to parent context."""
        success = self.nav_manager.navigate_to_parent()
        if success:
            # Update JavaScript context and re-inject
            self._inject_selection_js()
            self.nav_manager.update_javascript_context(self.driver)
        return success
    
    def get_field_selections(self, field_name: str) -> List[Dict]:
        """Get selections for a specific field."""
        return self.selection_session_data['field_selections'].get(field_name, [])
    
    def get_all_field_selections(self) -> Dict[str, List[Dict]]:
        """Get all field selections."""
        try:
            # Get latest selections from JavaScript
            js_selections = self.driver.execute_script("""
                return window.contentExtractorData ? window.contentExtractorData.fieldSelections : {};
            """)
            
            # Merge with internal state
            all_selections = self.selection_session_data['field_selections'].copy()
            all_selections.update(js_selections or {})
            
            return all_selections
            
        except Exception as e:
            logger.error(f"Failed to get all field selections: {e}")
            return self.selection_session_data['field_selections']

    def save_field_selector(self, field_name: str, xpath: str, css_selector: str = "", 
                           requires_manual_input: bool = False, manual_input_note: str = "") -> bool:
        """Save field selector using AI preparation record."""
        return self.db_manager.save_ai_preparation_record(
            field_name=field_name,
            extracted_content=manual_input_note if requires_manual_input else "",
            xpath=xpath,
            css_selector=css_selector,
            user_comment=manual_input_note,
            extraction_method="text_input" if requires_manual_input else "page_selection",
            source_url=self.current_url,
            confidence_level="medium"
        )
    
    def save_ai_selection(self, field_name: str, extracted_content: str, xpath: str, 
                         css_selector: str = "", user_comment: str = "", 
                         confidence_level: str = "medium", content_type: str = "text",
                         instance_index: int = 0, parent_record_id: int = None) -> bool:
        """
        Save AI preparation record with full context.
        
        Args:
            field_name: Name of the field being extracted
            extracted_content: The actual extracted content
            xpath: XPath selector used
            css_selector: CSS selector alternative
            user_comment: User-provided context for AI
            confidence_level: Confidence in extraction (high, medium, low)
            content_type: Type of content (text, list, nested_data, html, number, url)
            instance_index: Instance number for multi-instance fields
            parent_record_id: Parent record for nested structures
            
        Returns:
            True if saved successfully
        """
        return self.db_manager.save_ai_preparation_record(
            field_name=field_name,
            extracted_content=extracted_content,
            xpath=xpath,
            css_selector=css_selector,
            user_comment=user_comment,
            extraction_method="page_selection",
            confidence_level=confidence_level,
            content_type=content_type,
            source_url=self.current_url,
            instance_index=instance_index,
            parent_record_id=parent_record_id
        )
    
    def get_ai_session_records(self) -> List:
        """Get all AI preparation records for the current session."""
        return self.db_manager.get_session_records()
    
    def export_ai_session(self, format: str = 'structured') -> Dict:
        """Export session data formatted for AI processing."""
        return self.db_manager.export_session_for_ai(format=format)
    
    def get_session_statistics(self) -> Dict:
        """Get statistics about the current extraction session."""
        return self.db_manager.get_extraction_statistics()
    
    def test_selector_on_page(self, selector, test_url: str) -> Dict:
        """Test a saved selector on a specific page."""
        return self.db_manager.test_selector_on_page(selector, test_url, self.driver)

    def test_all_selectors_on_page(self, test_url: str) -> Dict[str, Dict]:
        """Test all saved selectors on a page."""
        return self.db_manager.test_all_selectors_on_page(test_url, self.driver, self.current_domain)
    
    def get_saved_selectors(self, domain: str = None) -> List:
        """Get saved selectors for a domain."""
        target_domain = domain or self.current_domain
        return self.db_manager.get_saved_selectors(target_domain)
    
    def get_current_context_info(self) -> Dict:
        """Get current navigation context information."""
        return self.nav_manager.get_current_context_info()
    
    def get_nested_selection_hierarchy(self) -> Dict:
        """Get nested selection hierarchy information."""
        return self.nav_manager.get_nested_selection_hierarchy()

    def handle_control_panel_actions(self) -> Dict:
        """
        Monitor and handle control panel actions from JavaScript.
        
        Returns:
            Dictionary with action results
        """
        try:
            # Check for nested navigation actions first
            if self.nav_manager.check_for_nested_actions(self.driver):
                return {'status': 'success', 'action': 'nested_navigation', 'message': 'Processed nested navigation'}
            
            # Check for other control panel actions
            action_data = self.driver.execute_script("""
                if (window.contentExtractorData && window.contentExtractorData.controlPanelAction) {
                    const action = window.contentExtractorData.controlPanelAction;
                    delete window.contentExtractorData.controlPanelAction;
                    return action;
                }
                return null;
            """)
            
            if not action_data:
                return {'status': 'no_action', 'message': 'No pending actions'}
            
            action_type = action_data.get('type')
            
            if action_type == 'save':
                return self._handle_save_action(action_data)
            elif action_type == 'test':
                return self._handle_test_action(action_data)
            elif action_type == 'navigate':
                return self._handle_navigate_action(action_data.get('url'))
            else:
                return {'status': 'error', 'message': f'Unknown action type: {action_type}'}
            
        except Exception as e:
            logger.error(f"Error handling control panel actions: {e}")
            return {'status': 'error', 'message': str(e)}

    def _handle_save_action(self, save_data: Dict) -> Dict:
        """Handle save action from control panel."""
        try:
            field_name = save_data.get('field_name')
            selections = self.get_field_selections(field_name)
            
            if not selections:
                return {'status': 'error', 'message': f'No selections found for field: {field_name}'}
            
            # Choose the best selector
            best_selection = self.db_manager.choose_best_selector(selections)
            
            # Save to database
            success = self.save_field_selector(
                field_name,
                best_selection.get('xpath', ''),
                best_selection.get('css_selector', '')
            )
            
            if success:
                return {'status': 'success', 'message': f'Saved selector for {field_name}'}
            else:
                return {'status': 'error', 'message': f'Failed to save selector for {field_name}'}
            
        except Exception as e:
            logger.error(f"Error handling save action: {e}")
            return {'status': 'error', 'message': str(e)}

    def _handle_test_action(self, test_data: Dict) -> Dict:
        """Handle test action from control panel."""
        try:
            test_url = test_data.get('url', self.current_url)
            results = self.test_all_selectors_on_page(test_url)
            
            return {
                'status': 'success',
                'message': f'Tested {len(results)} selectors',
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error handling test action: {e}")
            return {'status': 'error', 'message': str(e)}

    def _handle_navigate_action(self, navigate_url: str) -> Dict:
        """Handle navigation action from control panel."""
        try:
            if self.load_page(navigate_url):
                return {'status': 'success', 'message': f'Navigated to {navigate_url}'}
            else:
                return {'status': 'error', 'message': f'Failed to navigate to {navigate_url}'}
            
        except Exception as e:
            logger.error(f"Error handling navigate action: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_page_info(self) -> Dict:
        """Get information about the current page."""
        try:
            return {
                'url': self.current_url,
                'domain': self.current_domain,
                'title': self.driver.title if self.driver else '',
                'depth': self.nested_manager.get_current_depth(),
                'breadcrumbs': self.nested_manager.get_breadcrumbs()
            }
        except Exception as e:
            logger.error(f"Error getting page info: {e}")
            return {}
        
    def clear_selections(self):
        """Clear all selections."""
        try:
            self.driver.execute_script("""
                if (window.contentExtractorData) {
                    window.contentExtractorData.fieldSelections = {};
                    window.contentExtractorData.selectedElements = [];
                    window.contentExtractorData.selectedDOMElements.clear();
                }
            """)
            self.selection_session_data['field_selections'] = {}
            logger.info("All selections cleared")
        except Exception as e:
            logger.error(f"Error clearing selections: {e}")
    
    def close(self):
        """Close the browser and clean up resources."""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
            logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    def __del__(self):
        """Ensure browser is closed when object is destroyed."""
        self.close() 