#!/usr/bin/env python3
"""
Simplified HTML to JSON extraction tool.
Fetches raw HTML and parses all elements regardless of visibility.
No Selenium interactions - just clean HTML parsing.
"""

import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import argparse
import sys
from pathlib import Path


class SimpleHtmlExtractor:
    """Simplified HTML extractor that processes all elements regardless of visibility"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def fetch_html(self, url):
        """Fetch HTML content using requests"""
        try:
            print(f"Fetching {url}...")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def generate_css_selector(self, element, soup):
        """Generate a CSS selector for the given element"""
        def get_element_path(elem):
            path = []
            while elem and elem.name and elem != soup:
                # Get tag name
                tag = elem.name
                
                # Add ID if present
                if elem.get('id'):
                    path.append(f"{tag}#{elem['id']}")
                    break  # ID is unique, we can stop here
                
                # Add class if present
                classes = elem.get('class', [])
                if classes:
                    class_str = '.'.join(classes)
                    tag_with_class = f"{tag}.{class_str}"
                else:
                    tag_with_class = tag
                
                # Find position among siblings with same tag
                siblings = [s for s in elem.parent.children if hasattr(s, 'name') and s.name == elem.name]
                if len(siblings) > 1:
                    position = siblings.index(elem) + 1
                    tag_with_class += f":nth-of-type({position})"
                
                path.append(tag_with_class)
                elem = elem.parent
            
            return ' > '.join(reversed(path))
        
        return get_element_path(element)
    
    def extract_element_data(self, element, soup, base_url):
        """Extract data from a single element"""
        # Generate CSS selector
        css_selector = self.generate_css_selector(element, soup)
        
        # Get text content (all text, visible or not)
        text_content = element.get_text(strip=True, separator=' ')
        
        # Get HTML content
        html_content = str(element)
        
        # Get attributes
        attributes = dict(element.attrs) if element.attrs else {}
        
        # Handle relative URLs in href and src attributes
        for attr in ['href', 'src']:
            if attr in attributes:
                attributes[attr] = urljoin(base_url, attributes[attr])
        
        return {
            'css_selector': css_selector,
            'tag_name': element.name,
            'text_content': text_content,
            'html_content': html_content,
            'attributes': attributes,
            'has_children': bool(element.find_all())
        }
    
    def extract_page_data(self, url):
        """Extract all data from a page"""
        html_content = self.fetch_html(url)
        if not html_content:
            return None
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all elements that have content (text or children)
        all_elements = soup.find_all(lambda tag: (
            tag.get_text(strip=True) or  # Has text content
            tag.find_all() or           # Has child elements
            tag.attrs                   # Has attributes
        ))
        
        print(f"Found {len(all_elements)} elements with content")
        
        # Extract data from each element
        elements_data = []
        for element in all_elements:
            try:
                element_data = self.extract_element_data(element, soup, url)
                elements_data.append(element_data)
            except Exception as e:
                print(f"Error processing element {element.name}: {e}")
                continue
        
        return {
            'url': url,
            'total_elements': len(elements_data),
            'elements': elements_data
        }
    
    def save_to_json(self, data, output_file):
        """Save extracted data to JSON file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Data saved to {output_file}")
        except Exception as e:
            print(f"Error saving to {output_file}: {e}")


def main():
    parser = argparse.ArgumentParser(description='Simple HTML to JSON extraction tool')
    parser.add_argument('url', help='URL to extract HTML from')
    parser.add_argument('--output', '-o', help='Output JSON file', required=True)
    
    args = parser.parse_args()
    
    extractor = SimpleHtmlExtractor()
    data = extractor.extract_page_data(args.url)
    
    if data:
        extractor.save_to_json(data, args.output)
        print(f"Successfully extracted {data['total_elements']} elements from {args.url}")
    else:
        print("Failed to extract data")
        sys.exit(1)


if __name__ == "__main__":
    main() 