#!/usr/bin/env python3
"""
Page Comparison Tool with DFS-based CSS Selector Optimization

This script implements an intelligent CSS selector optimization algorithm:
1. Identifies unique content at the leaf level
2. Uses DFS to propagate up the tree when >70% of children are unique  
3. Outputs optimized CSS selectors with their complete HTML content

The algorithm performs DFS traversal, coloring nodes as it goes up the tree
to find the most efficient selectors for non-duplicate content.

Can also accept URLs directly and will convert them to JSON first.
"""

import json
import argparse
import sys
from pathlib import Path
from collections import defaultdict, deque
import copy
import tempfile
import os
import re
import logging
from datetime import datetime

# Import the converter from html_to_json
from html_to_json import DOMToJSONConverter


class OptimizedPageComparator:
    def __init__(self, threshold=0.7, log_file=None):
        self.pages = []
        self.threshold = threshold  # 70% threshold for parent optimization
        self.all_selectors = set()
        self.selector_to_content = defaultdict(dict)  # selector -> {page_id: content}
        self.selector_to_element = defaultdict(dict)  # selector -> {page_id: full_element}
        self.temp_files = []
        self.original_html = {}
        
        # For DFS algorithm
        self.unique_leaves = set()  # Leaf selectors with unique content across pages
        self.single_page_elements = set()  # Elements only on some pages (count for optimization but not final output)
        self.colored_nodes = {}  # selector -> color status
        self.optimized_selectors = set()  # Final optimized selector set
        
        # For generalization tracking
        self.generalized_to_original = {}  # generalized_selector -> representative_original_selector
        
        # Setup logging
        self.setup_logging(log_file)
        
    def setup_logging(self, log_file=None):
        """Setup comprehensive logging"""
        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"optimization_trace_{timestamp}.log"
            
        # Configure logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"=== Starting CSS Selector Optimization Trace ===")
        self.logger.info(f"Log file: {log_file}")
        self.logger.info(f"Optimization threshold: {self.threshold}")
        
    def check_existing_json_files(self, urls):
        """Check if JSON files already exist for the given URLs and return their paths"""
        json_files = []
        missing_urls = []
        
        for i, url in enumerate(urls):
            # Create a safe filename from the URL
            import hashlib
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            json_filename = f"page_{i}_{url_hash}.json"
            
            if Path(json_filename).exists():
                self.logger.info(f"Found existing JSON file for URL {i}: {json_filename}")
                json_files.append(json_filename)
            else:
                self.logger.info(f"No existing JSON file found for URL {i}, will need to convert: {url}")
                missing_urls.append((i, url))
                json_files.append(None)  # Placeholder
        
        return json_files, missing_urls
        
    def convert_urls_to_json(self, urls, reuse_existing=True):
        """Convert URLs to JSON files and return their paths, optionally reusing existing files"""
        if reuse_existing:
            json_files, missing_urls = self.check_existing_json_files(urls)
            
            if not missing_urls:
                self.logger.info("All JSON files already exist, reusing them")
                return [f for f in json_files if f is not None]
            else:
                self.logger.info(f"Need to convert {len(missing_urls)} URLs, reusing {len([f for f in json_files if f])}")
        else:
            json_files = [None] * len(urls)
            missing_urls = [(i, url) for i, url in enumerate(urls)]
        
        # Convert only the missing URLs
        for i, url in missing_urls:
            self.logger.info(f"Converting URL {i+1}/{len(urls)}: {url}")
            
            converter = DOMToJSONConverter(url)
            
            # Get the original HTML first
            html_content = converter.fetch_html(url)
            if html_content:
                self.original_html[i] = html_content
                self.logger.debug(f"Fetched HTML for page {i}, length: {len(html_content)} chars")
                
                # Check if our target content is in the raw HTML
                if "1727.25" in html_content:
                    self.logger.warning(f"FOUND '1727.25' in raw HTML for page {i}")
                else:
                    self.logger.info(f"'1727.25' NOT found in raw HTML for page {i}")
            
            result = converter.convert_url_to_json(url)
            
            if not result:
                self.logger.error(f"Failed to convert URL: {url}")
                continue
            
            # Check if target content is in the JSON
            json_str = json.dumps(result)
            if "1727.25" in json_str:
                self.logger.warning(f"FOUND '1727.25' in JSON result for page {i}")
            else:
                self.logger.info(f"'1727.25' NOT found in JSON result for page {i}")
            
            # Create persistent file with predictable name
            import hashlib
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            json_filename = f"page_{i}_{url_hash}.json"
            
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            json_files[i] = json_filename
            self.logger.info(f"Converted to file: {json_filename}")
        
        return [f for f in json_files if f is not None]
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                os.unlink(temp_file)
                self.logger.info(f"Cleaned up temporary file: {temp_file}")
            except OSError:
                pass
    
    def load_json_files(self, file_paths):
        """Load multiple JSON files from different pages"""
        for i, file_path in enumerate(file_paths):
            try:
                self.logger.info(f"Loading JSON file {i}: {file_path}")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                page_info = {
                    'id': i,
                    'file_path': file_path,
                    'url': data.get('url', 'unknown'),
                    'title': data.get('title', 'unknown'),
                    'dom_tree': data.get('dom_tree', {})
                }
                self.pages.append(page_info)
                self.logger.info(f"Loaded page {i}: {page_info['url']}")
                
                # Check if target content is in the DOM tree
                dom_str = json.dumps(page_info['dom_tree'])
                if "1727.25" in dom_str:
                    self.logger.warning(f"FOUND '1727.25' in DOM tree for page {i}")
                else:
                    self.logger.info(f"'1727.25' NOT found in DOM tree for page {i}")
                
            except Exception as e:
                self.logger.error(f"Error loading {file_path}: {e}")
                continue
                
        if len(self.pages) < 2:
            self.logger.error("Need at least 2 pages to compare")
            return False
            
        return True
    
    def _get_content_signature(self, element):
        """
        Create a content signature that captures both structure and actual content values.
        This ensures that elements with different content values are treated as unique.
        """
        try:
            # Get text content
            text_content = self._get_element_text_content(element)
            
            # Special debug logging for our target measurement
            if "1727.25" in str(text_content):
                self.logger.warning(f"FOUND '1727.25' in text_content of element: {element.get('css_selector', 'unknown')}")
                self.logger.warning(f"Full text content: {text_content}")
            
            # Get tag and basic attributes for structure
            tag = element.get('tag', 'unknown')
            element_id = element.get('id', '')
            classes = ' '.join(element.get('classes', []))
            
            # Create a content-focused signature that includes:
            # 1. The actual text content (most important for uniqueness)
            # 2. Basic structural info
            # 3. Parent context for disambiguation
            
            # Primary signature: focus on actual content
            if text_content and text_content.strip():
                # For elements with meaningful text content, use the content as primary identifier
                content_sig = f"text:{text_content.strip()}"
            else:
                # For structural elements, use tag and attributes
                content_sig = f"tag:{tag}"
                if element_id:
                    content_sig += f"#id:{element_id}"
                if classes:
                    content_sig += f".class:{classes}"
                    
            # Add parent context to distinguish similar elements in different contexts
            parent_context = self._get_parent_context_signature(element)
            if parent_context:
                content_sig = f"parent:{parent_context}[{content_sig}]"
                
            # Special debug logging for our target
            if "1727.25" in str(content_sig):
                self.logger.warning(f"Content signature: {content_sig}")
                
            return content_sig
            
        except Exception as e:
            self.logger.error(f"Error creating content signature: {e}")
            return f"tag:{element.get('tag', 'unknown')}"
    
    def _get_element_text_content(self, element):
        """
        Extract meaningful text content from an element, handling various text fields.
        """
        try:
            # Try various text content fields that might exist in the element
            text_sources = [
                element.get('text_content', ''),
                element.get('text', ''),
                element.get('inner_text', ''),
                element.get('textContent', ''),
                element.get('innerText', '')
            ]
            
            # Find the most comprehensive text content
            best_text = ""
            for text in text_sources:
                if text and isinstance(text, str) and len(text.strip()) > len(best_text.strip()):
                    best_text = text.strip()
            
            # If no direct text, try to extract from children or HTML content
            if not best_text:
                html_content = element.get('html_content', '')
                if html_content:
                    # Simple text extraction from HTML (remove tags)
                    import re
                    text_from_html = re.sub(r'<[^>]+>', ' ', html_content)
                    text_from_html = re.sub(r'\s+', ' ', text_from_html).strip()
                    if text_from_html:
                        best_text = text_from_html
            
            return best_text
            
        except Exception as e:
            self.logger.debug(f"Error extracting text content: {e}")
            return ""
    
    def _get_parent_context_signature(self, element):
        """
        Get a simplified parent context signature for disambiguation.
        This helps distinguish similar elements in different page sections.
        """
        try:
            # Get a few levels of parent context
            parent_path = []
            current = element
            levels = 0
            max_levels = 3  # Limit context depth to avoid over-specification
            
            while current and levels < max_levels:
                parent = current.get('parent')
                if not parent:
                    break
                    
                # Add parent tag and key identifying attributes
                parent_tag = parent.get('tag', 'unknown')
                parent_id = parent.get('id', '')
                parent_classes = parent.get('classes', [])
                
                parent_sig = parent_tag
                if parent_id:
                    parent_sig += f"#{parent_id}"
                elif parent_classes:
                    # Use first meaningful class
                    meaningful_classes = [c for c in parent_classes if c not in ['container', 'row', 'col']]
                    if meaningful_classes:
                        parent_sig += f".{meaningful_classes[0]}"
                        
                parent_path.insert(0, parent_sig)
                current = parent
                levels += 1
                
            return " > ".join(parent_path) if parent_path else ""
            
        except Exception as e:
            return ""
    
    def index_elements(self):
        """Index all elements by their CSS selectors across all pages"""
        self.logger.info("=== Starting element indexing ===")
        
        target_found_count = 0
        
        for page in self.pages:
            page_id = page['id']
            self.logger.info(f"Indexing elements for page {page_id}")
            
            def index_recursive(element, parent_selector=None, depth=0):
                nonlocal target_found_count
                
                if not isinstance(element, dict):
                    return
                    
                selector = element.get('css_selector')
                if selector:
                    self.all_selectors.add(selector)
                    
                    # Store content signature
                    content_sig = self._get_content_signature(element)
                    self.selector_to_content[selector][page_id] = content_sig
                    
                    # Store full element
                    self.selector_to_element[selector][page_id] = element
                    
                    # Log detailed info if this contains our target
                    if content_sig and "1727.25" in str(content_sig):
                        target_found_count += 1
                        self.logger.warning(f"TARGET FOUND #{target_found_count} - Page {page_id}, Selector: {selector}")
                        self.logger.warning(f"Content signature: {content_sig}")
                        self.logger.warning(f"Element tag: {element.get('tag')}")
                        self.logger.warning(f"Element text: {element.get('text_content', '')[:200]}...")
                
                # Process children
                for child in element.get('children', []):
                    index_recursive(child, selector, depth + 1)
            
            index_recursive(page['dom_tree'])
            self.logger.info(f"Finished indexing page {page_id}")
        
        self.logger.info(f"=== Element indexing complete ===")
        self.logger.info(f"Total selectors: {len(self.all_selectors)}")
        self.logger.info(f"Target '1727.25' found in {target_found_count} elements")
        
        # Log all selectors that contain our target
        self.logger.info("=== Checking all indexed content for target ===")
        for selector in self.all_selectors:
            for page_id, content_sig in self.selector_to_content[selector].items():
                if content_sig and "1727.25" in str(content_sig):
                    self.logger.warning(f"INDEXED TARGET: Page {page_id}, Selector: {selector}")
                    self.logger.warning(f"Content: {content_sig}")
    
    def identify_unique_leaves(self):
        """
        Identify leaf elements that contain unique content across pages.
        Now includes single-page elements in final output as they represent real differences.
        """
        self.logger.info("Identifying unique leaf elements...")
        unique_leaves = set()  # Elements with different content across all pages
        single_page_elements = set()  # Elements only present on some pages
        target_in_unique = 0
        target_in_single_page = 0
        
        for selector, page_contents in self.selector_to_content.items():
            # Check if present on all pages
            if len(page_contents) != len(self.pages):
                # Element only exists on some pages - single page element
                if self._is_meaningful_content(selector, page_contents):
                    single_page_elements.add(selector)
                    if "1727.25" in str(page_contents):
                        target_in_single_page += 1
                        self.logger.warning(f"Target '1727.25' found in single-page element: {selector}")
            else:
                # Element exists on all pages - check if content differs
                signatures = []
                for page_id, content in page_contents.items():
                    if isinstance(content, dict):
                        signatures.append(content.get('content_signature', ''))
                    else:
                        signatures.append(str(content))
                        
                if len(set(signatures)) > 1:  # Different content across pages
                    if self._is_meaningful_content(selector, page_contents):
                        unique_leaves.add(selector)
                        if "1727.25" in str(page_contents):
                            target_in_unique += 1
                            self.logger.warning(f"Target '1727.25' found in unique element: {selector}")
        
        self.logger.info(f"Found {len(unique_leaves)} unique leaves")
        self.logger.info(f"Found {len(single_page_elements)} single-page elements")
        self.logger.info(f"Target '1727.25' found in {target_in_unique} unique leaves")
        self.logger.info(f"Target '1727.25' found in {target_in_single_page} single-page elements")
        
        self.single_page_elements = single_page_elements
        return unique_leaves

    def _is_meaningful_content(self, selector, page_contents):
        """
        Determine if this selector represents meaningful product specification content
        vs navigation/noise elements
        """
        # Get sample content to analyze
        sample_content = None
        for content in page_contents.values():
            if content:
                sample_content = content
                break
        
        if not sample_content:
            return False
            
        # Handle both string and dict content formats
        if isinstance(sample_content, dict):
            text_content = sample_content.get('text_content', '').lower()
        else:
            text_content = str(sample_content).lower()
            
        selector_lower = selector.lower()
        
        # EXCLUDE: Script tags and style elements (never meaningful product content)
        if any(tag in selector_lower for tag in ['script', 'style', 'noscript']):
            return False
            
        # EXCLUDE: Script-related attributes and IDs
        if any(pattern in selector_lower for pattern in [
            'js-', 'script', 'javascript', 'jquery', 'elementor-frontend',
            'wp-block-library', 'css-', 'stylesheet'
        ]):
            return False
        
        # INCLUDE: Product specification indicators
        meaningful_indicators = [
            'dimension', 'weight', 'specification', 'technical', 'model',
            'capacity', 'height', 'width', 'depth', 'size', 'measurement',
            'mm', 'kg', 'lbs', 'volt', 'amp', 'watt', 'cfm', 'temperature',
            'pressure', 'flow', 'filter', 'hepa', 'ulpa', 'efficiency',
            'application', 'feature', 'option', 'accessory', 'div1', 'div2',
            'tab1', 'tab2', 'tab3', 'tab4', 'spec', 'external', 'internal',
            'shipping', 'net weight', 'gross weight', 'electrical', 'mechanical'
        ]
        
        # EXCLUDE: Navigation and noise indicators  
        noise_indicators = [
            'menu', 'nav', 'header', 'footer', 'sidebar', 'breadcrumb',
            'search', 'login', 'cart', 'checkout', 'social', 'facebook',
            'twitter', 'linkedin', 'youtube', 'instagram', 'cookie',
            'privacy', 'terms', 'legal', 'copyright', 'trademark',
            'elementor', 'wordpress', 'plugin', 'widget', 'popup',
            'modal', 'overlay', 'banner', 'advertisement', 'ad-',
            'tracking', 'analytics', 'gtm', 'google', 'facebook',
            'pixel', 'beacon', 'script', 'style', 'css', 'js',
            'sm-174905', 'random-id', 'auto-generated', 'timestamp'
        ]
        
        # Check for meaningful content indicators
        has_meaningful = any(indicator in text_content or indicator in selector_lower 
                           for indicator in meaningful_indicators)
        
        # Check for noise indicators
        has_noise = any(indicator in text_content or indicator in selector_lower 
                       for indicator in noise_indicators)
        
        # Additional checks for specific patterns
        
        # INCLUDE: Elements with product measurements
        has_measurements = any(pattern in text_content for pattern in [
            'mm', 'cm', 'inch', '"', 'kg', 'lbs', 'volt', 'amp', 'watt',
            'cfm', 'psi', 'bar', 'temp', '°f', '°c', 'hz', 'db'
        ])
        
        # INCLUDE: Product model/specification related selectors
        is_product_selector = any(pattern in selector_lower for pattern in [
            'div1', 'div2', 'tab1', 'tab2', 'tab3', 'tab4', 'spec',
            'model', 'product', 'dimension', 'weight', 'technical'
        ])
        
        # EXCLUDE: Random IDs that look auto-generated
        has_random_id = any(pattern in selector_lower for pattern in [
            'sm-17490', 'elementor-element', 'wp-', 'widget-', 'menu-item-',
            'post-', 'page-id-', 'attachment-'
        ])
        
        # EXCLUDE: Pure navigation elements
        is_navigation = any(word in text_content for word in [
            'about', 'products', 'services', 'contact', 'home', 'filters',
            'sales', 'safety', 'library', 'support'
        ]) and len(text_content.split()) < 5  # Short navigation text
        
        # Decision logic
        if has_random_id or is_navigation:
            return False
            
        if has_meaningful or has_measurements or is_product_selector:
            return True
            
        if has_noise:
            return False
            
        # Default: include if content seems substantial
        return len(text_content) > 20 and not has_noise
    
    def build_tree_structure(self):
        """Build parent-child relationships from CSS selectors"""
        self.logger.info("=== Building tree structure ===")
        
        children_map = defaultdict(set)  # parent -> set of children
        parent_map = {}  # child -> parent
        
        # Sort selectors by specificity (longer = more specific)
        sorted_selectors = sorted(self.all_selectors, key=lambda x: x.count(' > '))
        
        for selector in sorted_selectors:
            parts = selector.split(' > ')
            if len(parts) > 1:
                # Find parent selector
                parent_parts = parts[:-1]
                potential_parent = ' > '.join(parent_parts)
                
                # Look for exact parent match
                if potential_parent in self.all_selectors:
                    children_map[potential_parent].add(selector)
                    parent_map[selector] = potential_parent
        
        self.logger.info(f"Built tree structure: {len(children_map)} parents, {len(parent_map)} children")
        return children_map, parent_map
    
    def dfs_optimize_selectors(self, unique_leaves, threshold=0.7):
        """
        Implement the clarified optimization algorithm:
        1. Find unique leaves (including single-page elements as they represent differences)
        2. For each unique leaf, find its highest ancestor that only contains unique children
        3. For parents of those highest ancestors, if they have 70%+ unique children, use parent instead
        """
        self.logger.info(f"Starting clarified optimization algorithm with {threshold} threshold...")
        
        # Step 1: All meaningful differences include both unique leaves and single-page elements
        all_unique_elements = unique_leaves.union(self.single_page_elements)
        target_in_optimized = 0
        
        self.logger.info(f"Starting with {len(unique_leaves)} unique leaves + {len(self.single_page_elements)} single-page elements")
        self.logger.info(f"Total meaningful differences: {len(all_unique_elements)}")
        
        # Step 2: Build parent-child relationships
        parent_to_children = {}
        child_to_parent = {}
        
        # Build comprehensive parent-child relationships
        for selector in self.all_selectors:
            parts = selector.split(' > ')
            for i in range(1, len(parts)):
                parent_selector = ' > '.join(parts[:i])
                child_selector = ' > '.join(parts[:i+1])
                
                if parent_selector in self.all_selectors and child_selector in self.all_selectors:
                    if parent_selector not in parent_to_children:
                        parent_to_children[parent_selector] = set()
                    parent_to_children[parent_selector].add(child_selector)
                    child_to_parent[child_selector] = parent_selector
        
        self.logger.debug(f"Built parent-child relationships for {len(parent_to_children)} parents")
        
        # Step 3: For each unique element, find its highest ancestor that only contains unique children
        highest_unique_ancestors = set()
        
        for unique_element in all_unique_elements:
            current = unique_element
            highest_ancestor = current
            
            # Walk up the tree
            while current in child_to_parent:
                parent = child_to_parent[current]
                parent_children = parent_to_children.get(parent, set())
                
                # Check if ALL children of this parent are unique
                all_children_unique = all(child in all_unique_elements for child in parent_children)
                
                if all_children_unique and len(parent_children) > 0:
                    # This parent only has unique children - it can represent all of them
                    highest_ancestor = parent
                    current = parent
                else:
                    # This parent has some non-unique children - stop here
                    break
            
            highest_unique_ancestors.add(highest_ancestor)
            self.logger.debug(f"Unique element {unique_element} -> highest ancestor {highest_ancestor}")
        
        self.logger.info(f"Found {len(highest_unique_ancestors)} highest ancestors with only unique children")
        
        # Step 4: Apply 70% threshold to parents of highest ancestors
        optimized_selectors = set(highest_unique_ancestors)
        
        for ancestor in highest_unique_ancestors:
            if ancestor in child_to_parent:
                parent = child_to_parent[ancestor]
                parent_children = parent_to_children.get(parent, set())
                
                if len(parent_children) > 0:
                    # Count how many children are highest ancestors (unique)
                    unique_children_count = len([child for child in parent_children if child in highest_unique_ancestors])
                    unique_ratio = unique_children_count / len(parent_children)
                    
                    self.logger.debug(f"Parent {parent}: {unique_children_count}/{len(parent_children)} unique children = {unique_ratio:.2%}")
                    
                    if unique_ratio >= threshold:
                        # Use parent instead of individual children
                        self.logger.info(f"Optimizing: {parent} replaces {unique_children_count} unique children (>{threshold:.0%} threshold)")
                        
                        # Remove all children that are highest ancestors
                        children_to_remove = [child for child in parent_children if child in highest_unique_ancestors]
                        for child in children_to_remove:
                            optimized_selectors.discard(child)
                            self.logger.debug(f"  Removed child: {child}")
                        
                        # Add the parent
                        optimized_selectors.add(parent)
                        
                        # Check if target content is in this optimized selector
                        page_contents = self.selector_to_content.get(parent, {})
                        for content in page_contents.values():
                            if content and "1727.25" in str(content):
                                target_in_optimized += 1
                                self.logger.warning(f"TARGET IN OPTIMIZED: {parent}")
                                self.logger.warning(f"Content: {content}")
                                break
        
        # Also check for target in remaining non-optimized selectors
        for selector in optimized_selectors:
            if selector in highest_unique_ancestors:  # Only check non-parent selectors
                page_contents = self.selector_to_content.get(selector, {})
                for content in page_contents.values():
                    if content and "1727.25" in str(content):
                        target_in_optimized += 1
                        self.logger.warning(f"TARGET IN FINAL SELECTOR: {selector}")
                        self.logger.warning(f"Content: {content}")
                        break
        
        self.logger.info(f"Target '1727.25' found in {target_in_optimized} optimized selectors")
        self.logger.info(f"Optimization completed: {len(all_unique_elements)} differences -> {len(optimized_selectors)} final selectors")
        self.logger.debug(f"Final optimized selectors: {sorted(optimized_selectors)}")
        
        return optimized_selectors
    
    def extract_html_content(self, selector, page_id):
        """Extract complete HTML content for a selector from a specific page"""
        element = self.selector_to_element[selector].get(page_id)
        
        if not element:
            return None
            
        def element_to_html(elem):
            """Convert element back to HTML"""
            if not isinstance(elem, dict):
                return str(elem)
                
            tag = elem.get('tag', 'div')
            attributes = elem.get('attributes', {})
            text_content = elem.get('text_content', '')
            children = elem.get('children', [])
            
            # Build attribute string
            attr_str = ''
            if isinstance(attributes, dict):
                for key, value in attributes.items():
                    if value:
                        attr_str += f' {key}="{value}"'
                    else:
                        attr_str += f' {key}'
            
            # Handle self-closing tags
            if tag in ['img', 'br', 'hr', 'input', 'meta', 'link']:
                return f'<{tag}{attr_str} />'
            
            # Build children HTML
            children_html = ''
            if children:
                for child in children:
                    children_html += element_to_html(child)
            elif text_content:
                children_html = text_content
            
            return f'<{tag}{attr_str}>{children_html}</{tag}>'
        
        html_content = element_to_html(element)
        
        # Log if this HTML contains our target
        if html_content and "1727.25" in html_content:
            self.logger.warning(f"TARGET IN EXTRACTED HTML: Page {page_id}, Selector: {selector}")
            self.logger.warning(f"HTML snippet: {html_content[:200]}...")
        
        return html_content
    
    def optimize_comparison(self, threshold=0.7):
        """
        Run the complete DFS-based optimization algorithm.
        
        This algorithm:
        1. Extracts content from all pages and builds DOM trees
        2. Identifies elements with unique content (different values across pages)
        3. Uses DFS to optimize selectors by replacing children when >threshold are unique
        4. Generates final output with optimized CSS selectors and their HTML content
        """
        self.logger.info("=== Starting DFS-based optimization ===")
        
        # Step 1: Index all elements and their content
        self.index_elements()
        
        # Step 2: Identify elements with unique content
        self.unique_leaves = self.identify_unique_leaves()
        
        # Step 3: DFS optimization to find optimal parent selectors
        self.optimized_selectors = self.dfs_optimize_selectors(self.unique_leaves, threshold)
        
        # Step 4: Generate final output with HTML content
        return self.generate_optimized_output()
    
    def generate_optimized_output(self):
        """Generate the final output with optimized selectors and HTML content"""
        self.logger.info("=== Generating optimized output ===")
        
        # Post-processing: Remove child selectors when parent is already included
        self.logger.info("Post-processing: Removing redundant child selectors...")
        original_count = len(self.optimized_selectors)
        
        # Sort selectors by length (shorter = more general/parent)
        sorted_selectors = sorted(self.optimized_selectors, key=len)
        filtered_selectors = set()
        
        for selector in sorted_selectors:
            # Check if this selector is a child of any already included selector
            is_child = False
            for existing_selector in filtered_selectors:
                if selector.startswith(existing_selector + " > ") or selector.startswith(existing_selector + " "):
                    # This selector is a child of an existing one
                    is_child = True
                    self.logger.info(f"Removing redundant child selector: {selector}")
                    self.logger.info(f"  Parent already included: {existing_selector}")
                    break
            
            if not is_child:
                filtered_selectors.add(selector)
        
        removed_count = original_count - len(filtered_selectors)
        self.logger.info(f"Removed {removed_count} redundant child selectors")
        self.logger.info(f"Selector count after redundancy removal: {len(filtered_selectors)}")
        
        # Apply generalization to the filtered selectors
        self.logger.info("Applying selector generalization...")
        generalized_selectors = self.generalize_selectors(filtered_selectors)
        self.optimized_selectors = generalized_selectors
        
        generalization_change = len(filtered_selectors) - len(generalized_selectors)
        self.logger.info(f"Generalization change: {len(filtered_selectors)} -> {len(generalized_selectors)} selectors ({generalization_change:+d})")
        self.logger.info(f"Final selector count: {len(generalized_selectors)}")
        
        result = {
            'summary': {
                'total_pages': len(self.pages),
                'total_selectors_analyzed': len(self.all_selectors),
                'unique_leaf_selectors': len(self.unique_leaves),
                'single_page_elements': len(self.single_page_elements),
                'selectors_after_optimization': original_count,
                'selectors_after_redundancy_removal': len(filtered_selectors),
                'final_generalized_selectors': len(self.optimized_selectors),
                'optimization_threshold': self.threshold
            },
            'pages': [
                {
                    'id': page['id'],
                    'url': page['url'],
                    'title': page['title']
                }
                for page in self.pages
            ],
            'optimized_selectors': []
        }
        
        target_in_final_output = 0
        
        for selector in sorted(self.optimized_selectors):
            selector_data = {
                'css_selector': selector,
                'reason': self.colored_nodes.get(selector, 'unique_content'),
                'content_by_page': {}
            }
            
            # Extract content for each page
            for page in self.pages:
                page_id = page['id']
                
                # For generalized selectors, use representative original selector for content extraction
                content_selector = self.generalized_to_original.get(selector, selector)
                
                html_content = self.extract_html_content(content_selector, page_id)
                content_signature = self.selector_to_content[content_selector].get(page_id)
                
                selector_data['content_by_page'][page_id] = {
                    'page_url': page['url'],
                    'html_content': html_content,
                    'content_signature': content_signature
                }
                
                # Check if target is in final output
                if (html_content and "1727.25" in html_content) or (content_signature and "1727.25" in str(content_signature)):
                    target_in_final_output += 1
                    self.logger.warning(f"TARGET IN FINAL OUTPUT: Page {page_id}, Selector: {selector} (using content from {content_selector})")
            
            result['optimized_selectors'].append(selector_data)
        
        self.logger.info(f"=== Output generation complete ===")
        self.logger.info(f"Target '1727.25' appears in {target_in_final_output} final output entries")
        
        # Final check - search the entire result JSON for our target
        result_json = json.dumps(result)
        if "1727.25" in result_json:
            self.logger.warning(f"FINAL CHECK: '1727.25' IS present in final JSON output")
        else:
            self.logger.error(f"FINAL CHECK: '1727.25' is NOT present in final JSON output")
        
        return result

    def create_output_folder(self, base_name="optimized_comparison_output"):
        """Create output folder with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"{base_name}_{timestamp}"
        output_dir = Path(folder_name)
        output_dir.mkdir(exist_ok=True)
        return output_dir
    
    def save_results_to_folder(self, report, output_dir):
        """Save optimized comparison results to organized files in output folder"""
        print(f"\nSaving results to folder: {output_dir}")
        
        # 1. Save optimized selectors list
        selectors_file = output_dir / "optimized_selectors.txt"
        with open(selectors_file, 'w', encoding='utf-8') as f:
            f.write("Optimized CSS Selectors\n")
            f.write("=" * 40 + "\n\n")
            
            for i, elem in enumerate(report['optimized_selectors'], 1):
                f.write(f"{i}. {elem['css_selector']} ({elem['reason']})\n")
            
            f.write(f"\nTotal: {len(report['optimized_selectors'])} selectors\n")
            f.write(f"Optimization threshold: {report['summary']['optimization_threshold']:.1%}\n")
        
        print(f"Saved selectors to: {selectors_file}")
        
        # 2. Save detailed selector info with HTML content
        selectors_detail_file = output_dir / "selectors_with_html.json"
        with open(selectors_detail_file, 'w', encoding='utf-8') as f:
            json.dump(report['optimized_selectors'], f, indent=2, ensure_ascii=False)
        
        print(f"Saved detailed selector info to: {selectors_detail_file}")
        
        # 3. Save full comparison report
        report_file = output_dir / "full_optimization_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"Saved full report to: {report_file}")
        
        # 4. Save summary
        summary_file = output_dir / "optimization_summary.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("CSS Selector Optimization Summary\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Pages compared: {report['summary']['total_pages']}\n")
            f.write(f"Total selectors analyzed: {report['summary']['total_selectors_analyzed']}\n")
            f.write(f"Unique leaf selectors: {report['summary']['unique_leaf_selectors']}\n")
            f.write(f"Single-page elements: {report['summary']['single_page_elements']}\n")
            f.write(f"Optimized selectors: {report['summary']['final_generalized_selectors']}\n")
            f.write(f"Optimization threshold: {report['summary']['optimization_threshold']:.1%}\n\n")
            
            f.write("Pages:\n")
            for i, page in enumerate(report['pages']):
                f.write(f"  {i}. {page['url']}\n")
                f.write(f"     Title: {page['title']}\n\n")
            
            f.write("Optimized CSS Selectors:\n")
            for i, elem in enumerate(report['optimized_selectors'], 1):
                f.write(f"  {i}. {elem['css_selector']} ({elem['reason']})\n")
        
        print(f"Saved summary to: {summary_file}")
        
        # 5. Save simple JSON list of selectors only
        selectors_list_file = output_dir / "selectors_list.json"
        selectors_list = [elem['css_selector'] for elem in report['optimized_selectors']]
        with open(selectors_list_file, 'w', encoding='utf-8') as f:
            json.dump(selectors_list, f, indent=2, ensure_ascii=False)
        
        print(f"Saved simple selectors list to: {selectors_list_file}")
        
        return output_dir

    def generalize_selectors(self, selectors):
        """
        Generalize selectors by identifying patterns where selectors differ only by numbers/words.
        Also handles nth-child patterns by using parent selectors when appropriate.
        
        Args:
            selectors: Set of CSS selectors to generalize
            
        Returns:
            Set of generalized selectors, updates self.generalized_to_original mapping
        """
        self.logger.info("=== Starting selector generalization ===")
        self.logger.info(f"Input selectors count: {len(selectors)}")
        
        # Track all selectors to ensure none are lost
        input_selectors = set(selectors)
        processed_selectors = set()
        
        # Group selectors by their base pattern (everything except varying parts)
        nth_child_groups = defaultdict(list)  # parent -> [nth-child selectors]
        
        # First pass: identify nth-child patterns
        for selector in selectors:
            if ':nth-of-type(' in selector or ':nth-child(' in selector:
                # Extract parent part (everything before the nth selector)
                if ':nth-of-type(' in selector:
                    parent_part = selector.split(':nth-of-type(')[0]
                    nth_child_groups[parent_part].append(selector)
                elif ':nth-child(' in selector:
                    parent_part = selector.split(':nth-child(')[0]
                    nth_child_groups[parent_part].append(selector)
            
        # Handle nth-child generalization: use parent if 2+ nth children
        generalized_selectors = set()
        
        for parent, nth_selectors in nth_child_groups.items():
            if len(nth_selectors) >= 2:
                self.logger.info(f"Nth-child generalization: {parent} replaces {len(nth_selectors)} selectors")
                self.logger.debug(f"  Original nth selectors: {nth_selectors}")
                generalized_selectors.add(parent)
                processed_selectors.update(nth_selectors)
                # Map generalized parent to first original selector for content extraction
                self.generalized_to_original[parent] = nth_selectors[0]
            else:
                # Keep single nth-child selectors as-is
                self.logger.debug(f"Keeping single nth-child selector: {nth_selectors[0]}")
                generalized_selectors.update(nth_selectors)
                processed_selectors.update(nth_selectors)
        
        self.logger.info(f"Nth-child phase: processed {len(processed_selectors)} selectors, generated {len([p for p, g in nth_child_groups.items() if len(g) >= 2])} generalizations")
        
        # Second pass: identify ID/class/attribute patterns for remaining selectors
        remaining_selectors = selectors - processed_selectors
        self.logger.info(f"Remaining selectors for pattern matching: {len(remaining_selectors)}")
        
        # Group selectors by their structure and varying parts
        pattern_groups = defaultdict(list)
        no_pattern_selectors = set()
        
        for selector in remaining_selectors:
            # Parse the selector to identify varying parts
            pattern_key = self._extract_pattern_key(selector)
            if pattern_key:
                pattern_groups[pattern_key].append(selector)
                self.logger.debug(f"Pattern found for {selector}: {pattern_key}")
            else:
                # Keep selectors that don't match any pattern
                no_pattern_selectors.add(selector)
                self.logger.debug(f"No pattern found for selector: {selector}")
        
        self.logger.info(f"Pattern analysis: {len(pattern_groups)} pattern groups, {len(no_pattern_selectors)} selectors with no patterns")
        
        # Add selectors with no patterns directly to output
        generalized_selectors.update(no_pattern_selectors)
        processed_selectors.update(no_pattern_selectors)
        
        # Generalize pattern groups
        generalizations_created = 0
        for pattern_key, group_selectors in pattern_groups.items():
            if len(group_selectors) >= 2:
                generalized_selector = self._create_generalized_selector(pattern_key, group_selectors)
                if generalized_selector:
                    self.logger.info(f"Pattern generalization: {generalized_selector} replaces {len(group_selectors)} selectors")
                    self.logger.debug(f"  Original selectors: {group_selectors}")
                    generalized_selectors.add(generalized_selector)
                    processed_selectors.update(group_selectors)
                    # Map generalized selector to first original selector for content extraction
                    self.generalized_to_original[generalized_selector] = group_selectors[0]  
                    generalizations_created += 1
                else:
                    # Fallback: keep original selectors
                    self.logger.warning(f"Failed to create generalized selector for pattern {pattern_key}, keeping originals: {group_selectors}")
                    generalized_selectors.update(group_selectors)
                    processed_selectors.update(group_selectors)
            else:
                # Keep single selectors as-is
                self.logger.debug(f"Single selector in pattern group, keeping as-is: {group_selectors[0]}")
                generalized_selectors.update(group_selectors)
                processed_selectors.update(group_selectors)
        
        # CRITICAL VERIFICATION: Ensure no selectors were lost
        unprocessed_selectors = input_selectors - processed_selectors
        if unprocessed_selectors:
            self.logger.error(f"ERROR: {len(unprocessed_selectors)} selectors were not processed!")
            self.logger.error(f"Unprocessed selectors: {list(unprocessed_selectors)}")
            # Add them to the output to prevent loss
            generalized_selectors.update(unprocessed_selectors)
        else:
            self.logger.info("✓ VERIFICATION PASSED: All input selectors were processed")
        
        self.logger.info(f"Pattern phase: created {generalizations_created} generalizations")
        self.logger.info(f"Final generalization complete: {len(selectors)} -> {len(generalized_selectors)} selectors")
        self.logger.info(f"Total generalizations created: {len(self.generalized_to_original)}")
        
        # Log detailed breakdown
        self.logger.debug("=== Generalization Summary ===")
        self.logger.debug(f"Input selectors: {len(input_selectors)}")
        self.logger.debug(f"Nth-child generalizations: {len([p for p, g in nth_child_groups.items() if len(g) >= 2])}")
        self.logger.debug(f"Pattern generalizations: {generalizations_created}")
        self.logger.debug(f"Selectors with no pattern: {len(no_pattern_selectors)}")
        self.logger.debug(f"Single nth-child selectors: {len([s for group in nth_child_groups.values() if len(group) == 1 for s in group])}")
        self.logger.debug(f"Single pattern selectors: {len([s for group in pattern_groups.values() if len(group) == 1 for s in group])}")
        self.logger.debug(f"Final output count: {len(generalized_selectors)}")
        
        return generalized_selectors
    
    def _extract_pattern_key(self, selector):
        """
        Extract a pattern key from a selector by identifying the varying parts.
        Returns a tuple that can be used to group similar selectors.
        """
        import re
        
        # Enhanced pattern for ID attributes with varying parts and optional suffixes
        # This handles cases like: #Div1, #Div2, #Div1Top, #Div2Top, #content-1, #content-2, etc.
        # Fixed to handle prefixes ending with dashes/underscores: content-, item-, etc.
        better_id_pattern = r'#([a-zA-Z][a-zA-Z_-]*)(\d+)([a-zA-Z_-]*)'
        
        # Pattern for class attributes with varying suffixes
        class_pattern = r'\.([a-zA-Z_-]+)[\d\-_]*(\d+[\w\-_]*)?'
        # Pattern for attribute values with varying parts: [value="something123"]
        attr_pattern = r'\[([^=]+)="([a-zA-Z_-]+)[\d\-_]*(\d+[\w\-_]*)?"?\]'
        
        # Try to find the primary varying pattern
        for pattern_type, pattern in [('id', better_id_pattern), ('class', class_pattern), ('attr', attr_pattern)]:
            matches = re.findall(pattern, selector)
            if matches:
                # Use the first match to create a pattern key
                match = matches[0]
                if pattern_type == 'id':
                    prefix, varying_part, suffix = match[0], match[1], match[2]
                    # Create pattern key: (selector_structure, pattern_type, prefix, suffix)
                    selector_structure = re.sub(better_id_pattern, f'#{prefix}VARYING{suffix}', selector)
                    return (selector_structure, pattern_type, prefix, suffix)
                elif pattern_type == 'class':
                    prefix = match[0]
                    selector_structure = re.sub(class_pattern, f'.{prefix}VARYING', selector)
                    return (selector_structure, pattern_type, prefix, '')
                elif pattern_type == 'attr':
                    attr_name, prefix = match[0], match[1]
                    selector_structure = re.sub(attr_pattern, f'[{attr_name}="{prefix}VARYING"]', selector)
                    return (selector_structure, pattern_type, f'{attr_name}={prefix}', '')
        
        return None
    
    def _create_generalized_selector(self, pattern_key, group_selectors):
        """
        Create a generalized CSS selector from a pattern key and group of similar selectors.
        """
        if len(pattern_key) == 4:
            selector_structure, pattern_type, prefix_info, suffix = pattern_key
        else:
            # Handle legacy 3-tuple format
            selector_structure, pattern_type, prefix_info = pattern_key
            suffix = ''
        
        if pattern_type == 'id':
            if suffix:
                # Handle cases like #Div1Top, #Div2Top -> div[id^="Div"][id$="Top"]
                generalized = selector_structure.replace(
                    f'#{prefix_info}VARYING{suffix}', 
                    f'[id^="{prefix_info}"][id$="{suffix}"]'
                )
            else:
                # Handle cases like #Div1, #Div2 -> div[id^="Div"]
                generalized = selector_structure.replace(f'#{prefix_info}VARYING', f'[id^="{prefix_info}"]')
            return generalized
        elif pattern_type == 'class':
            # Replace .prefixVARYING with .prefix attribute selector
            generalized = selector_structure.replace(f'.{prefix_info}VARYING', f'[class*="{prefix_info}"]')
            return generalized
        elif pattern_type == 'attr':
            # Handle attribute patterns
            attr_name, prefix = prefix_info.split('=', 1)
            generalized = selector_structure.replace(f'[{attr_name}="{prefix}VARYING"]', f'[{attr_name}^="{prefix}"]')
            return generalized
        
        return None


def main():
    parser = argparse.ArgumentParser(description='Compare JSON DOM representations with DFS-based CSS selector optimization')
    
    # Create mutually exclusive group for input type
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--json-files', nargs='+', help='JSON files to compare (minimum 2)')
    input_group.add_argument('--urls', nargs='+', help='URLs to convert and compare (minimum 2)')
    
    parser.add_argument('-o', '--output', help='Output JSON report file path')
    parser.add_argument('--pretty', action='store_true', help='Pretty print JSON output')
    parser.add_argument('--show-selectors', action='store_true', 
                       help='Show only the CSS selectors of optimized elements')
    parser.add_argument('--force-reprocess', action='store_true',
                       help='Force re-conversion of URLs even if JSON files already exist')
    parser.add_argument('--output-folder', action='store_true',
                       help='Create output folder with selectors and content files')
    parser.add_argument('--folder-name', default='optimized_comparison_output',
                       help='Base name for output folder (default: optimized_comparison_output)')
    parser.add_argument('--threshold', type=float, default=0.7,
                       help='Optimization threshold (0.0-1.0, default: 0.7)')
    parser.add_argument('--log-file', help='Log file path (default: auto-generated with timestamp)')
    
    args = parser.parse_args()
    
    # Validate threshold
    if not 0.0 <= args.threshold <= 1.0:
        print("Error: Threshold must be between 0.0 and 1.0")
        sys.exit(1)
    
    # Create log file name if not provided
    log_file = args.log_file
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"optimization_trace_{timestamp}.log"
    
    comparator = OptimizedPageComparator(threshold=args.threshold, log_file=log_file)
    
    try:
        if args.urls:
            # Convert URLs to JSON files first
            if len(args.urls) < 2:
                comparator.logger.error("Need at least 2 URLs to compare")
                sys.exit(1)
            
            comparator.logger.info(f"Converting {len(args.urls)} URLs to JSON...")
            # Use force_reprocess flag to control whether to reuse existing files
            json_files = comparator.convert_urls_to_json(args.urls, reuse_existing=not args.force_reprocess)
            
            if len(json_files) < 2:
                comparator.logger.error("Could not convert enough URLs to JSON files")
                sys.exit(1)
                
        else:
            # Use provided JSON files
            json_files = args.json_files
            if len(json_files) < 2:
                comparator.logger.error("Need at least 2 JSON files to compare")
                sys.exit(1)
            
            # Check if all files exist
            for file_path in json_files:
                if not Path(file_path).exists():
                    comparator.logger.error(f"File not found: {file_path}")
                    sys.exit(1)
        
        if not comparator.load_json_files(json_files):
            sys.exit(1)
        
        report = comparator.optimize_comparison()
        
        # Handle output folder creation
        if args.output_folder:
            output_dir = comparator.create_output_folder(args.folder_name)
            comparator.save_results_to_folder(report, output_dir)
        
        if args.show_selectors:
            # Just show the CSS selectors
            selectors = [elem['css_selector'] for elem in report['optimized_selectors']]
            for selector in selectors:
                print(selector)
        else:
            # Full report
            json_str = json.dumps(report, indent=2 if args.pretty else None, ensure_ascii=False)
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(json_str)
                comparator.logger.info(f"Report saved to: {args.output}")
            else:
                print(json_str)
        
        # Print summary
        comparator.logger.info(f"\n=== FINAL SUMMARY ===")
        comparator.logger.info(f"- Compared {report['summary']['total_pages']} pages")
        comparator.logger.info(f"- Analyzed {report['summary']['total_selectors_analyzed']} total selectors")
        comparator.logger.info(f"- Found {report['summary']['unique_leaf_selectors']} unique leaf selectors")
        comparator.logger.info(f"- Found {report['summary']['single_page_elements']} single-page elements")
        comparator.logger.info(f"- Generated {report['summary']['final_generalized_selectors']} optimized selectors")
        comparator.logger.info(f"- Optimization threshold: {report['summary']['optimization_threshold']:.1%}")
        comparator.logger.info(f"- Log file: {log_file}")
        
        if report['summary']['final_generalized_selectors'] > 0:
            comparator.logger.info(f"\nTop optimized selectors:")
            for elem in report['optimized_selectors'][:5]:  # Show first 5
                comparator.logger.info(f"  - {elem['css_selector']} ({elem['reason']})")
    
    finally:
        # No cleanup needed since we're using persistent files now
        pass


if __name__ == '__main__':
    main() 