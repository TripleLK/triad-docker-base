#!/usr/bin/env python3
"""
Test script to verify form element extraction
"""

from html_to_json import DOMToJSONConverter
from bs4 import BeautifulSoup
import json

def test_form_extraction():
    # Test HTML with comprehensive form elements
    test_html = '''
    <html>
    <body>
    <form method="post" action="/submit" name="test-form">
        <fieldset>
            <legend>Personal Information</legend>
            <label for="name">Full Name:</label>
            <input type="text" id="name" name="name" placeholder="Enter your name" value="John Doe">
            
            <label for="email">Email:</label>
            <input type="email" id="email" name="email" required>
            
            <label for="country">Country:</label>
            <select id="country" name="country">
                <optgroup label="North America">
                    <option value="us">United States</option>
                    <option value="ca" selected>Canada</option>
                </optgroup>
                <optgroup label="Europe">
                    <option value="uk">United Kingdom</option>
                    <option value="fr">France</option>
                </optgroup>
            </select>
            
            <fieldset>
                <legend>Preferences</legend>
                <label>
                    <input type="checkbox" name="newsletter" value="yes"> Subscribe to newsletter
                </label>
            </fieldset>
            
            <button type="submit">Submit Form</button>
            <button type="reset">Reset</button>
        </fieldset>
    </form>
    </body>
    </html>
    '''
    
    # Create converter and parse
    converter = DOMToJSONConverter('test', use_selenium=False)
    soup = BeautifulSoup(test_html, 'html.parser')
    body = soup.find('body')
    result = converter.element_to_dict(body, soup)
    
    # Recursively find all form elements
    def find_form_elements(node, elements=[]):
        if isinstance(node, dict):
            tag = node.get('tag', '')
            if tag in ['form', 'fieldset', 'legend', 'label', 'input', 'select', 'optgroup', 'option', 'button']:
                elements.append({
                    'tag': tag,
                    'attributes': node.get('attributes', {}),
                    'text_content': node.get('text_content', '')
                })
            for child in node.get('children', []):
                find_form_elements(child, elements)
        return elements
    
    form_elements = find_form_elements(result, [])
    
    print("=== FORM ELEMENTS EXTRACTED ===")
    for i, elem in enumerate(form_elements, 1):
        print(f"{i}. {elem['tag'].upper()}")
        if elem['attributes']:
            print(f"   Attributes: {elem['attributes']}")
        if elem['text_content']:
            print(f"   Text: {elem['text_content']}")
        print()
    
    print(f"Total form elements found: {len(form_elements)}")
    
    # Check for specific elements
    tags_found = [elem['tag'] for elem in form_elements]
    expected_tags = ['form', 'fieldset', 'legend', 'label', 'input', 'select', 'optgroup', 'option', 'button']
    
    print("=== ELEMENT TYPE SUMMARY ===")
    for tag in expected_tags:
        count = tags_found.count(tag)
        print(f"{tag}: {count} found")
    
    # Verify we have all expected form elements
    missing_tags = [tag for tag in expected_tags if tag not in tags_found]
    if missing_tags:
        print(f"\n⚠️  Missing form element types: {missing_tags}")
        return False
    else:
        print(f"\n✅ All form element types successfully extracted!")
        return True

if __name__ == '__main__':
    test_form_extraction() 