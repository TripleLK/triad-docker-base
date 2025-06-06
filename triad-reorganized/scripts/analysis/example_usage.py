#!/usr/bin/env python3
"""
Example usage of the HTML to JSON converter and page comparison tools.

This script demonstrates how to:
1. Convert individual URLs to JSON
2. Compare multiple URLs directly
3. Compare existing JSON files
"""

import subprocess
import sys
import tempfile
import os

def run_command(cmd):
    """Run a command and print the output"""
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def example_single_url_conversion():
    """Example: Convert a single URL to JSON"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Converting a single URL to JSON")
    print("="*80)
    
    url = "https://httpbin.org/html"  # Simple test page
    output_file = "example_page.json"
    
    cmd = ["python", "html_to_json.py", url, "-o", output_file, "--pretty"]
    
    if run_command(cmd):
        print(f"\nSuccessfully converted {url} to {output_file}")
        
        # Show file size
        if os.path.exists(output_file):
            size = os.path.getsize(output_file)
            print(f"Generated JSON file size: {size} bytes")

def example_compare_urls():
    """Example: Compare multiple URLs directly"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Comparing multiple URLs directly")
    print("="*80)
    
    # Use different endpoints that will have different content
    urls = [
        "https://httpbin.org/html",
        "https://httpbin.org/json", 
        "https://httpbin.org/xml"
    ]
    
    cmd = ["python", "compare_pages.py", "--urls"] + urls + ["--pretty", "--keep-temp-files"]
    
    if run_command(cmd):
        print("\nSuccessfully compared URLs!")

def example_compare_with_selectors_only():
    """Example: Get only the CSS selectors of different elements"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Getting only CSS selectors of different elements")
    print("="*80)
    
    urls = [
        "https://httpbin.org/html",
        "https://httpbin.org/json"
    ]
    
    cmd = ["python", "compare_pages.py", "--urls"] + urls + ["--show-selectors"]
    
    if run_command(cmd):
        print("\nSuccessfully extracted different element selectors!")

def example_compare_json_files():
    """Example: Compare existing JSON files"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Comparing existing JSON files")
    print("="*80)
    
    # First create some JSON files
    urls = ["https://httpbin.org/html", "https://httpbin.org/json"]
    json_files = []
    
    for i, url in enumerate(urls):
        output_file = f"temp_page_{i}.json"
        cmd = ["python", "html_to_json.py", url, "-o", output_file]
        if run_command(cmd):
            json_files.append(output_file)
    
    if len(json_files) >= 2:
        # Now compare the JSON files
        cmd = ["python", "compare_pages.py", "--json-files"] + json_files + ["--pretty"]
        run_command(cmd)
    
    # Cleanup
    for file in json_files:
        try:
            os.unlink(file)
            print(f"Cleaned up: {file}")
        except OSError:
            pass

def main():
    """Run all examples"""
    print("HTML to JSON Converter & Page Comparison Tool - Examples")
    print("="*80)
    
    examples = [
        ("Single URL Conversion", example_single_url_conversion),
        ("Direct URL Comparison", example_compare_urls),
        ("Selectors Only Output", example_compare_with_selectors_only),
        ("JSON File Comparison", example_compare_json_files)
    ]
    
    for name, func in examples:
        try:
            func()
        except KeyboardInterrupt:
            print(f"\nInterrupted during: {name}")
            break
        except Exception as e:
            print(f"\nError in {name}: {e}")
            continue
    
    print("\n" + "="*80)
    print("All examples completed!")
    print("="*80)

if __name__ == "__main__":
    main() 