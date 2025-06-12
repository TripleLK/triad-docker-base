#!/usr/bin/env python3
"""
HTML to JSON DOM Converter

This script fetches HTML from a URL and converts it to a JSON representation
of the DOM tree, including CSS selectors for each element. It filters out
elements that don't contain text, images, or aren't parents of such elements.

Enhanced to capture hidden content and use Selenium for JavaScript-rendered content.
"""

import requests
import json
import re
from bs4 import BeautifulSoup, NavigableString, Comment
from urllib.parse import urljoin, urlparse
import argparse
import sys
import time

# Optional Selenium imports - will fallback to requests if not available
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class DOMToJSONConverter:
    def __init__(self, base_url, use_selenium=True):
        self.base_url = base_url
        self.element_counter = 0
        self.use_selenium = use_selenium and SELENIUM_AVAILABLE
        
    def fetch_html_selenium(self, url):
        """Fetch HTML content using Selenium WebDriver - simplified approach without interactions"""
        if not SELENIUM_AVAILABLE:
            print("Selenium not available, falling back to requests")
            return self.fetch_html_requests(url)
            
        try:
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            service = Service()
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            try:
                print(f"Loading URL with Selenium: {url}")
                driver.get(url)
                
                # Simple wait for page load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Just get the full page source - no interactions needed
                print("Page loaded, extracting HTML source...")
                html_content = driver.page_source
                
                print(f"HTML content extracted: {len(html_content)} characters")
                return html_content
                
            finally:
                driver.quit()
                
        except Exception as e:
            print(f"Error with Selenium: {e}")
            print("Falling back to requests...")
            return self.fetch_html_requests(url)
    
    def fetch_html_requests(self, url):
        """Fetch HTML content using requests (fallback method)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching URL {url}: {e}")
            return None
    
    def fetch_html(self, url):
        """Fetch HTML content from URL using best available method"""
        if self.use_selenium:
            return self.fetch_html_selenium(url)
        else:
            return self.fetch_html_requests(url)
    
    def generate_css_selector(self, element, soup=None):
        """Generate a unique CSS selector for an element, making it more specific if needed"""
        if element.name is None:
            return None
            
        path = []
        current = element
        
        while current and current.name:
            # Get tag name
            tag = current.name
            
            # Add ID if available
            if current.get('id'):
                selector_candidate = f"{tag}#{current['id']}"
                # Check if this would be unique
                if soup:
                    found = soup.select(selector_candidate)
                    if len(found) == 1:
                        path.append(selector_candidate)
                        break
                    else:
                        # ID is not unique, continue with more specific path
                        path.append(selector_candidate)
                else:
                    path.append(selector_candidate)
                    break
            
            # Add classes if available
            classes = current.get('class', [])
            if classes:
                class_str = '.'.join(classes)
                tag_with_class = f"{tag}.{class_str}"
            else:
                tag_with_class = tag
            
            # Find position among siblings with same tag and classes
            if current.parent:
                siblings = [s for s in current.parent.children 
                           if hasattr(s, 'name') and s.name == current.name 
                           and s.get('class', []) == classes]
                if len(siblings) > 1:
                    index = siblings.index(current) + 1
                    tag_with_class += f":nth-of-type({index})"
                
                # If still not unique enough, add attributes to make it more specific
                if soup and len(path) == 0:  # Only check for root element
                    candidate_selector = ' > '.join(reversed(path + [tag_with_class]))
                    if not candidate_selector:
                        candidate_selector = tag_with_class
                    
                    # Test uniqueness
                    found = soup.select(candidate_selector)
                    if len(found) > 1:
                        # Add more attributes to make it unique
                        for attr_name, attr_value in current.attrs.items():
                            if attr_name not in ['class', 'id'] and isinstance(attr_value, str):
                                # Escape special characters in attribute values
                                escaped_value = attr_value.replace('"', '\\"')
                                tag_with_class += f'[{attr_name}="{escaped_value}"]'
                                
                                # Test if this makes it unique
                                test_selector = ' > '.join(reversed(path + [tag_with_class]))
                                if not test_selector:
                                    test_selector = tag_with_class
                                try:
                                    found = soup.select(test_selector)
                                    if len(found) == 1:
                                        break
                                except:
                                    # If selector is invalid, skip this attribute
                                    tag_with_class = tag_with_class.rsplit('[', 1)[0]
                                    continue
            
            path.append(tag_with_class)
            current = current.parent
            
            # Stop at body or html
            if current and current.name in ['body', 'html']:
                path.append(current.name)
                break
        
        return ' > '.join(reversed(path))
    
    def has_meaningful_content(self, element):
        """Check if element should be included - exclude only non-displayable tags"""
        if element.name is None:
            return False
            
        # EXCLUDE only non-displayable content tags
        excluded_tags = {
            'script', 'style', 'noscript', 'meta', 'link', 'head', 
            'comment', 'title'  # title handled separately in main conversion
        }
        
        if element.name.lower() in excluded_tags:
            return False
            
        # INCLUDE everything else - all visible and hidden HTML elements
        return True
    
    def extract_all_text(self, element, include_hidden=True):
        """Extract all text content including hidden elements with whitespace cleanup"""
        if element.name is None:
            return ""
            
        # Get all text, including from hidden elements
        texts = []
        
        # Direct text content
        for text_node in element.children:
            if isinstance(text_node, NavigableString) and not isinstance(text_node, Comment):
                text = str(text_node).strip()
                # Clean up excess whitespace
                text = ' '.join(text.split())
                if text:
                    texts.append(text)
        
        # Get text from child elements - include ALL content including hidden
        for child in element.children:
            if hasattr(child, 'name') and child.name:
                # Only skip truly non-displayable tags
                excluded_tags = {'script', 'style', 'noscript', 'meta', 'link', 'head', 'comment', 'title'}
                if child.name.lower() not in excluded_tags:
                    child_text = self.extract_all_text(child, include_hidden=True)
                    if child_text:
                        texts.append(child_text)
        
        # Join and clean up whitespace
        result = ' '.join(texts).strip()
        return ' '.join(result.split())  # Normalize whitespace
    
    def is_parent_of_meaningful_content(self, element):
        """Check if element is a parent of included elements"""
        if element.name is None:
            return False
            
        # Check all descendants
        for descendant in element.descendants:
            if hasattr(descendant, 'name') and self.has_meaningful_content(descendant):
                return True
        return False
    
    def should_include_element(self, element):
        """Determine if element should be included - include all except non-displayable tags"""
        return (self.has_meaningful_content(element) or 
                self.is_parent_of_meaningful_content(element))
    
    def extract_text_content(self, element):
        """Extract text content from element, including hidden content"""
        # Extract both visible and hidden text
        text = self.extract_all_text(element, include_hidden=True)
        
        # Also extract values from form elements
        if element.name in ['input', 'select', 'textarea']:
            value = element.get('value', '')
            placeholder = element.get('placeholder', '')
            if value:
                text = f"{text} {value}".strip()
            if placeholder:
                text = f"{text} {placeholder}".strip()
        
        # For select elements, also get option text
        if element.name == 'select':
            options = element.find_all('option')
            option_texts = [opt.get_text(strip=True) for opt in options if opt.get_text(strip=True)]
            if option_texts:
                text = f"{text} {' '.join(option_texts)}".strip()
        
        # For optgroup elements, get label attribute
        if element.name == 'optgroup':
            label = element.get('label', '')
            if label:
                text = f"{text} {label}".strip()
        
        # For label elements, get 'for' attribute to show association
        if element.name == 'label':
            for_attr = element.get('for', '')
            if for_attr:
                text = f"{text} [for: {for_attr}]".strip()
        
        return text if text else None
    
    def element_to_dict(self, element, soup=None):
        """Convert BeautifulSoup element to dictionary"""
        if element.name is None:
            return None
            
        # Skip if element shouldn't be included
        if not self.should_include_element(element):
            return None
        
        self.element_counter += 1
        
        result = {
            'id': self.element_counter,
            'tag': element.name,
            'css_selector': self.generate_css_selector(element, soup),
            'attributes': dict(element.attrs) if element.attrs else {},
            'text_content': self.extract_text_content(element),
            'children': []
        }
        
        # Process children
        for child in element.children:
            if hasattr(child, 'name'):  # It's a tag
                child_dict = self.element_to_dict(child, soup)
                if child_dict:  # Only add if it should be included
                    result['children'].append(child_dict)
        
        # Include all elements that passed initial filtering
        return result
    
    def validate_selectors(self, html_content, json_data):
        """Validate that all CSS selectors in JSON work on original HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        def validate_recursive(node):
            if isinstance(node, dict) and 'css_selector' in node:
                selector = node['css_selector']
                if selector:
                    try:
                        found_elements = soup.select(selector)
                        if not found_elements:
                            print(f"WARNING: Selector '{selector}' found no elements")
                        elif len(found_elements) > 1:
                            print(f"WARNING: Selector '{selector}' found {len(found_elements)} elements (should be unique)")
                    except Exception as e:
                        print(f"ERROR: Invalid selector '{selector}': {e}")
                
                # Validate children
                for child in node.get('children', []):
                    validate_recursive(child)
        
        validate_recursive(json_data)
    
    def convert_url_to_json(self, url):
        """Main method to convert URL to JSON"""
        print(f"Fetching HTML from: {url}")
        if self.use_selenium:
            print("Using Selenium WebDriver for enhanced content extraction...")
        
        html_content = self.fetch_html(url)
        
        if not html_content:
            return None
        
        print("Parsing HTML...")
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find body element, fall back to html if no body
        root_element = soup.find('body') or soup.find('html')
        if not root_element:
            print("ERROR: No body or html element found")
            return None
        
        print("Converting to JSON...")
        dom_tree = self.element_to_dict(root_element, soup)  # Pass soup for selector validation
        
        if not dom_tree:
            print("ERROR: Failed to convert DOM to JSON")
            return None
        
        # Get page title
        title_element = soup.find('title')
        title = title_element.get_text(strip=True) if title_element else "Unknown"
        
        result = {
            'url': url,
            'title': title,
            'total_elements': self.element_counter,
            'dom_tree': dom_tree
        }
        
        print(f"Validating CSS selectors...")
        self.validate_selectors(html_content, dom_tree)
        
        print(f"Conversion complete. Found {self.element_counter} elements.")
        return result


def main():
    parser = argparse.ArgumentParser(description='Convert HTML page to JSON DOM representation')
    parser.add_argument('url', help='URL to fetch and convert')
    parser.add_argument('-o', '--output', help='Output JSON file path')
    parser.add_argument('--pretty', action='store_true', help='Pretty print JSON output')
    parser.add_argument('--no-selenium', action='store_true', help='Disable Selenium WebDriver (use requests only)')
    
    args = parser.parse_args()
    
    # Create converter
    converter = DOMToJSONConverter(args.url, use_selenium=not args.no_selenium)
    
    # Convert URL to JSON
    result = converter.convert_url_to_json(args.url)
    
    if not result:
        print("ERROR: Failed to convert URL to JSON")
        sys.exit(1)
    
    # Output JSON
    json_str = json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(json_str)
        print(f"JSON saved to: {args.output}")
    else:
        print(json_str)


if __name__ == '__main__':
    main() 