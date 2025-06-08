#!/usr/bin/env python3
"""
Debug script to test bookmarklet generation and identify blocking issues.
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.contrib.staticfiles import finders
import urllib.parse

def test_bookmarklet_generation():
    """Test the bookmarklet generation process."""
    print("=== Bookmarklet Debug Test ===")
    
    # Find the JavaScript file
    js_file_path = finders.find('js/bookmarklet/bookmarklet_core.js')
    print(f"JavaScript file path: {js_file_path}")
    
    if not js_file_path or not os.path.exists(js_file_path):
        print("ERROR: JavaScript file not found!")
        return
    
    # Load the content
    with open(js_file_path, 'r', encoding='utf-8') as f:
        js_content = f.read()
    
    print(f"Original file size: {len(js_content)} characters")
    print(f"Contains backticks: {'`' in js_content}")
    print(f"Contains template literals: {'${' in js_content}")
    
    # Test the current minification approach
    def minify_js_for_bookmarklet(js_content):
        """Same function as in wagtail_hooks.py"""
        import re
        
        # Remove single-line comments (but not // inside strings)
        # This regex matches // that are not inside quoted strings
        js_content = re.sub(r'(?<!["\'])//.*', '', js_content)
        
        # Remove multi-line comments /* ... */
        js_content = re.sub(r'/\*.*?\*/', '', js_content, flags=re.DOTALL)
        
        # Remove excessive whitespace but preserve necessary spaces
        # Replace multiple whitespace characters with single space
        js_content = re.sub(r'\s+', ' ', js_content)
        
        # Remove spaces around operators (but be careful with edge cases)
        # Be very conservative to avoid breaking syntax
        js_content = re.sub(r'\s*([{}();,])\s*', r'\1', js_content)
        
        # Trim and return
        return js_content.strip()
    
    # Test minification
    minified_js = minify_js_for_bookmarklet(js_content)
    print(f"Minified size: {len(minified_js)} characters")
    
    # Create bookmarklet URL
    encoded_js = urllib.parse.quote(minified_js, safe='')
    bookmarklet_url = f"javascript:{encoded_js}"
    
    print(f"Bookmarklet URL length: {len(bookmarklet_url)} characters")
    
    # Check if URL is too long (browsers have limits)
    if len(bookmarklet_url) > 2000:
        print("WARNING: Bookmarklet URL is very long and may be blocked by browsers!")
    
    # Test for potential problematic patterns
    problematic_patterns = [
        ('Template literals', '`'),
        ('Unescaped quotes', '"'),
        ('Unescaped single quotes', "'"),
        ('Newlines in minified', '\n'),
        ('Carriage returns', '\r'),
    ]
    
    for name, pattern in problematic_patterns:
        if pattern in minified_js:
            print(f"WARNING: Found {name} in minified JavaScript!")
    
    # Show first and last parts of the bookmarklet URL
    print("First 200 chars of bookmarklet URL:")
    print(repr(bookmarklet_url[:200]))
    print("Last 200 chars of bookmarklet URL:")
    print(repr(bookmarklet_url[-200:]))
    
    # Test if the minified JavaScript is syntactically valid
    try:
        # Try to evaluate it in a safe way
        import subprocess
        result = subprocess.run(['node', '-c'], input=minified_js, text=True, capture_output=True)
        if result.returncode == 0:
            print("✅ Minified JavaScript syntax is valid")
        else:
            print("❌ Minified JavaScript has syntax errors:")
            print(result.stderr)
    except FileNotFoundError:
        print("Node.js not available for syntax validation")
    
    return bookmarklet_url

if __name__ == '__main__':
    test_bookmarklet_generation() 