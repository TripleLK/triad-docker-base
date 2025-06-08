"""
Core Content Extraction Application

Standalone app that uses selenium to extract content from web pages
using pre-configured selectors and exports data for Django admin integration.

Created by: Quantum Bear
Date: 2025-01-22
Project: Triad Docker Base
"""

import os
import json
import time
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

logger = logging.getLogger(__name__)


class ContentExtractorApp:
    """
    Main application class for standalone content extraction.
    Manages selenium driver, field mapping, and data export.
    """
    
    def __init__(self, headless: bool = True, config_file: str = None):
        """
        Initialize the content extractor application.
        
        Args:
            headless: Whether to run browser in headless mode
            config_file: Path to JSON configuration file with field mappings
        """
        self.headless = headless
        self.driver = None
        self.session_id = str(uuid.uuid4())
        self.config = {}
        self.extracted_data = {}
        self.current_url = ""
        self.current_domain = ""
        
        # Load configuration if provided
        if config_file and os.path.exists(config_file):
            self.load_config(config_file)
        
        # Set up logging
        self.setup_logging()
    
    def setup_logging(self):
        """Configure logging for the application."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'content_extractor_{self.session_id[:8]}.log'),
                logging.StreamHandler()
            ]
        )
        logger.info(f"Content Extractor App initialized with session ID: {self.session_id}")
    
    def load_config(self, config_file: str) -> bool:
        """
        Load field mapping configuration from JSON file.
        
        Args:
            config_file: Path to JSON configuration file
            
        Returns:
            True if config loaded successfully, False otherwise
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            logger.info(f"Loaded configuration from {config_file}")
            logger.info(f"Configuration contains {len(self.config.get('fields', []))} field mappings")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return False
    
    def setup_driver(self) -> bool:
        """
        Set up Chrome WebDriver with appropriate options.
        
        Returns:
            True if driver setup successful, False otherwise
        """
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Standard options for reliability
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            # Exclude automation flags
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Try webdriver manager first
            if WEBDRIVER_MANAGER_AVAILABLE:
                try:
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                except Exception:
                    self.driver = webdriver.Chrome(options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("WebDriver setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup WebDriver: {e}")
            return False
    
    def load_page(self, url: str, wait_time: int = 10) -> bool:
        """
        Load a web page and wait for it to be ready.
        
        Args:
            url: URL to load
            wait_time: Maximum time to wait for page load
            
        Returns:
            True if page loaded successfully, False otherwise
        """
        if not self.driver:
            if not self.setup_driver():
                return False
        
        try:
            logger.info(f"Loading page: {url}")
            self.driver.get(url)
            
            # Wait for page to be ready
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Update current URL and domain
            self.current_url = url
            self.current_domain = self.get_domain_from_url(url)
            
            logger.info(f"Successfully loaded page: {url} (domain: {self.current_domain})")
            return True
            
        except TimeoutException:
            logger.error(f"Timeout loading page: {url}")
            return False
        except WebDriverException as e:
            logger.error(f"WebDriver error loading page {url}: {e}")
            return False
    
    def extract_content(self, url: str, field_mappings: Dict = None) -> Dict:
        """
        Extract content from a web page using configured field mappings.
        
        Args:
            url: URL to extract content from
            field_mappings: Optional field mappings to use (overrides config)
            
        Returns:
            Dictionary of extracted content keyed by field name
        """
        if not self.load_page(url):
            return {}
        
        # Use provided mappings or load from config
        mappings = field_mappings or self.config.get('fields', {})
        if not mappings:
            logger.error("No field mappings provided for extraction")
            return {}
        
        extracted = {}
        
        for field_name, field_config in mappings.items():
            try:
                content = self.extract_field(field_name, field_config)
                if content:
                    extracted[field_name] = content
                    logger.info(f"Successfully extracted {field_name}: {content[:100]}...")
                else:
                    logger.warning(f"No content extracted for field: {field_name}")
                    
            except Exception as e:
                logger.error(f"Error extracting field {field_name}: {e}")
                extracted[field_name] = {
                    'error': str(e),
                    'xpath': field_config.get('xpath', ''),
                    'css_selector': field_config.get('css_selector', '')
                }
        
        # Store extracted data
        self.extracted_data[url] = extracted
        
        return extracted
    
    def extract_field(self, field_name: str, field_config: Dict) -> Dict:
        """
        Extract content for a specific field using its configuration.
        
        Args:
            field_name: Name of the field to extract
            field_config: Configuration dict with xpath, css_selector, etc.
            
        Returns:
            Dictionary with extracted content and metadata
        """
        xpath = field_config.get('xpath', '')
        css_selector = field_config.get('css_selector', '')
        
        if not xpath and not css_selector:
            logger.error(f"No selector provided for field: {field_name}")
            return {}
        
        try:
            # Try XPath first
            if xpath:
                elements = self.driver.find_elements(By.XPATH, xpath)
                if elements:
                    content = self.extract_element_content(elements[0])
                    return {
                        'content': content,
                        'xpath': xpath,
                        'css_selector': css_selector,
                        'extraction_method': 'xpath',
                        'confidence': 'high' if content else 'low',
                        'content_type': self.detect_content_type(content)
                    }
            
            # Try CSS selector if XPath failed
            if css_selector:
                elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)
                if elements:
                    content = self.extract_element_content(elements[0])
                    return {
                        'content': content,
                        'xpath': xpath,
                        'css_selector': css_selector,
                        'extraction_method': 'css_selector',
                        'confidence': 'medium' if content else 'low',
                        'content_type': self.detect_content_type(content)
                    }
            
            # No content found
            return {
                'content': '',
                'xpath': xpath,
                'css_selector': css_selector,
                'extraction_method': 'none',
                'confidence': 'low',
                'content_type': 'text',
                'error': 'No elements found'
            }
            
        except Exception as e:
            logger.error(f"Error extracting field {field_name}: {e}")
            return {
                'content': '',
                'xpath': xpath,
                'css_selector': css_selector,
                'extraction_method': 'error',
                'confidence': 'low',
                'content_type': 'text',
                'error': str(e)
            }
    
    def extract_element_content(self, element) -> str:
        """
        Extract content from a web element.
        
        Args:
            element: Selenium WebElement
            
        Returns:
            Extracted text content
        """
        try:
            # Try text first
            text = element.text.strip()
            if text:
                return text
            
            # Try innerHTML if no text
            html = element.get_attribute('innerHTML')
            if html:
                return html.strip()
            
            # Try value attribute for inputs
            value = element.get_attribute('value')
            if value:
                return value.strip()
            
            return ''
            
        except Exception as e:
            logger.error(f"Error extracting element content: {e}")
            return ''
    
    def detect_content_type(self, content: str) -> str:
        """
        Detect the type of extracted content.
        
        Args:
            content: Extracted content string
            
        Returns:
            Content type classification
        """
        if not content:
            return 'text'
        
        # Check for HTML tags
        if '<' in content and '>' in content:
            return 'html'
        
        # Check for URLs
        if content.startswith(('http://', 'https://', 'www.')):
            return 'url'
        
        # Check for numeric content
        if content.replace('.', '').replace(',', '').replace('-', '').isdigit():
            return 'number'
        
        # Check for list-like content
        if '\n' in content or '•' in content or content.count(',') > 2:
            return 'list'
        
        return 'text'
    
    def export_to_ai_format(self, session_id: str = None) -> Dict:
        """
        Export extracted data in AIPreparationRecord format.
        
        Args:
            session_id: Optional session ID to use
            
        Returns:
            Dictionary formatted for Django admin import
        """
        export_session_id = session_id or self.session_id
        export_data = {
            'session_id': export_session_id,
            'extraction_timestamp': datetime.now().isoformat(),
            'selections': {}
        }
        
        for url, page_data in self.extracted_data.items():
            export_data['source_url'] = url
            
            for field_name, field_data in page_data.items():
                export_data['selections'][field_name] = {
                    'content': field_data.get('content', ''),
                    'xpath': field_data.get('xpath', ''),
                    'css_selector': field_data.get('css_selector', ''),
                    'confidence': field_data.get('confidence', 'medium'),
                    'content_type': field_data.get('content_type', 'text'),
                    'extraction_method': field_data.get('extraction_method', 'page_selection'),
                    'instance_index': 0
                }
        
        return export_data
    
    def save_export_file(self, output_file: str, session_id: str = None) -> bool:
        """
        Save extracted data to JSON file for Django admin import.
        
        Args:
            output_file: Path to output JSON file
            session_id: Optional session ID to use
            
        Returns:
            True if file saved successfully, False otherwise
        """
        try:
            export_data = self.export_to_ai_format(session_id)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported data saved to: {output_file}")
            logger.info(f"Session ID: {export_data['session_id']}")
            logger.info(f"Fields extracted: {list(export_data['selections'].keys())}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save export file: {e}")
            return False
    
    def get_domain_from_url(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.replace('www.', '')
        except Exception:
            return url
    
    def close(self):
        """Clean up and close the browser."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Sample configuration for testing
SAMPLE_CONFIG = {
    "name": "Lab Equipment Extractor",
    "description": "Extract lab equipment details from product pages",
    "fields": {
        "title": {
            "xpath": "//h1[contains(@class, 'product-title') or contains(@class, 'entry-title')]",
            "css_selector": "h1.product-title, h1.entry-title, .product-name h1",
            "description": "Product title"
        },
        "short_description": {
            "xpath": "//div[contains(@class, 'product-summary') or contains(@class, 'short-description')]//p[1]",
            "css_selector": ".product-summary p, .short-description p",
            "description": "Brief product description"
        },
        "full_description": {
            "xpath": "//div[contains(@class, 'product-description') or contains(@class, 'product-details')]",
            "css_selector": ".product-description, .product-details, .product-content",
            "description": "Full product description"
        },
        "features": {
            "xpath": "//div[contains(@class, 'features') or contains(@class, 'highlights')]//ul",
            "css_selector": ".features ul, .highlights ul, .product-features ul",
            "description": "Product features list"
        },
        "specifications": {
            "xpath": "//div[contains(@class, 'specifications') or contains(@class, 'specs')]//table",
            "css_selector": ".specifications table, .specs table, .product-specs table",
            "description": "Technical specifications"
        }
    }
} 