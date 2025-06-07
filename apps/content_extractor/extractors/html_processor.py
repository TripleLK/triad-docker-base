"""
HTML Processor for Content Extraction

Converts HTML pages to simplified JSON DOM representation
for human-in-the-loop content selection.

Created by: Phoenix Velocity
Date: 2025-01-08
Project: Triad Docker Base
"""

import requests
import hashlib
import json
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)


class HTMLProcessor:
    """Process HTML pages into simplified JSON DOM structure"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def fetch_html(self, url: str) -> Optional[str]:
        """
        Fetch HTML content from URL with proper headers and error handling.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content as string, or None if fetch failed
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def process_html(self, html_content: str, base_url: str = None) -> BeautifulSoup:
        """
        Process HTML content to remove unnecessary elements and prepare for analysis.
        
        Args:
            html_content: Raw HTML content
            base_url: Base URL for resolving relative links
            
        Returns:
            Processed BeautifulSoup object
        """
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'noscript']):
            element.decompose()
        
        # Remove comments
        from bs4 import Comment
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Remove common non-content elements
        unwanted_selectors = [
            'header', 'footer', 'nav', '.navigation', '.nav',
            '.sidebar', '.footer', '.header', '.advertisement', '.ad'
        ]
        
        for selector in unwanted_selectors:
            for element in soup.select(selector):
                element.decompose()
        
        return soup
    
    def to_json_dom(self, soup: BeautifulSoup, max_depth: int = 10) -> Dict[str, Any]:
        """
        Convert BeautifulSoup to simplified JSON DOM structure.
        
        Args:
            soup: BeautifulSoup object
            max_depth: Maximum depth to traverse
            
        Returns:
            JSON DOM representation
        """
        def process_element(element, depth=0):
            if depth > max_depth:
                return None
            
            # Skip text nodes that are just whitespace
            if hasattr(element, 'name') and element.name is None:
                text = str(element).strip()
                if text:
                    return {"type": "text", "content": text}
                return None
            
            if not hasattr(element, 'name') or element.name is None:
                return None
            
            result = {
                "tag": element.name,
                "attributes": dict(element.attrs) if element.attrs else {},
                "children": []
            }
            
            # Add text content if it exists
            direct_text = element.get_text(strip=True) if element.get_text(strip=True) else ""
            if direct_text:
                # Only add text if it's not just from child elements
                child_text = ""
                for child in element.children:
                    if hasattr(child, 'get_text'):
                        child_text += child.get_text(strip=True)
                
                if len(direct_text) > len(child_text):
                    result["text"] = direct_text[:500]  # Limit text length
            
            # Process children
            for child in element.children:
                child_result = process_element(child, depth + 1)
                if child_result:
                    result["children"].append(child_result)
            
            return result
        
        # Start with body if it exists, otherwise the whole document
        body = soup.find('body')
        if body:
            return process_element(body)
        else:
            return process_element(soup)
    
    def generate_content_hash(self, json_dom: Dict[str, Any]) -> str:
        """
        Generate a hash of the processed content for change detection.
        
        Args:
            json_dom: JSON DOM structure
            
        Returns:
            SHA-256 hash of the content
        """
        content_str = json.dumps(json_dom, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def extract_title(self, soup: BeautifulSoup) -> str:
        """
        Extract page title from HTML.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Page title or empty string
        """
        title_element = soup.find('title')
        if title_element:
            return title_element.get_text(strip=True)
        
        # Try h1 as fallback
        h1_element = soup.find('h1')
        if h1_element:
            return h1_element.get_text(strip=True)
        
        return ""
    
    def process_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Complete processing pipeline for a single URL.
        
        Args:
            url: URL to process
            
        Returns:
            Dictionary with processed data or None if failed
        """
        # Fetch HTML
        html_content = self.fetch_html(url)
        if not html_content:
            return None
        
        # Process HTML
        soup = self.process_html(html_content, url)
        
        # Extract data
        json_dom = self.to_json_dom(soup)
        title = self.extract_title(soup)
        content_hash = self.generate_content_hash(json_dom)
        
        return {
            'url': url,
            'title': title,
            'original_html': html_content,
            'processed_dom': json_dom,
            'content_hash': content_hash
        }


def process_single_url(url: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to process a single URL.
    
    Args:
        url: URL to process
        
    Returns:
        Processed data dictionary or None if failed
    """
    processor = HTMLProcessor()
    return processor.process_url(url) 