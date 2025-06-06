import os
import boto3
import logging
import json
import re
import sys
import subprocess
from bs4 import BeautifulSoup, Comment
import requests
from botocore.exceptions import ClientError, NoCredentialsError
from django.conf import settings
from apps.categorized_tags.models import CategorizedTag
from urllib.parse import urlparse
from django.utils import timezone
from pathlib import Path

logger = logging.getLogger(__name__)

def preprocess_html(html_content, css_selectors=None):
    """Preprocess HTML to reduce payload size for AWS Bedrock.
    
    This function:
    1. If CSS selectors are provided, extracts only matching elements
    2. Otherwise extracts only the body content
    3. Removes script, style tags, and comments
    4. Strips excess whitespace while preserving BR tags
    5. Removes other unnecessary elements
    
    Args:
        html_content (str): The raw HTML content
        css_selectors (str, optional): Comma-separated CSS selectors to filter content
        
    Returns:
        str: Preprocessed HTML content
    """
    # Apply CSS selectors first if provided - this should ALWAYS happen regardless of debug mode
    if css_selectors and css_selectors.strip():
        try:
            logger.info(f"Applying CSS selectors: {css_selectors}")
            html_content = extract_elements_by_css_selectors(html_content, css_selectors)
            logger.info(f"After CSS selector extraction: {len(html_content)} bytes")
        except Exception as e:
            logger.error(f"Error applying CSS selectors: {str(e)}")
            # Continue with full HTML if selector extraction fails
    
    try:
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract only the body content
        body = soup.body
        if not body:
            logger.warning("No body tag found in HTML, using full content")
            body = soup
            
        # Remove unnecessary elements
        for element in body.select('script, style, iframe, noscript, [style*="display:none"], [style*="display: none"]'):
            element.decompose()
            
        # Remove comments
        for comment in body.find_all(text=lambda text: isinstance(text, Comment)):
            comment.extract()
            
        # Get the HTML as string
        processed_html = str(body)
        
        # First, protect <br> and <br/> tags by replacing them with a unique placeholder
        processed_html = re.sub(r'<br\s*/?>', '{{BR_TAG}}', processed_html, flags=re.IGNORECASE)
        
        # Remove excess whitespace
        processed_html = re.sub(r'\s+', ' ', processed_html)
        processed_html = re.sub(r'>\s+<', '><', processed_html)
        
        # Restore the <br> tags
        processed_html = processed_html.replace('{{BR_TAG}}', '<br>')
        
        logger.info(f"HTML preprocessing reduced size from {len(html_content)} to {len(processed_html)} bytes")
        return processed_html
        
    except Exception as e:
        logger.warning(f"Error preprocessing HTML: {str(e)}")
        return html_content  # Return original content if preprocessing fails

def extract_elements_by_css_selectors(html_content, css_selectors):
    """Extract HTML elements matching the provided CSS selectors.
    
    Args:
        html_content (str): The raw HTML content
        css_selectors (str): Comma-separated CSS selectors
        
    Returns:
        str: HTML content containing only the matched elements
    """
    try:
        # Parse original HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Create a new soup with just html and body tags
        new_soup = BeautifulSoup('<html><head><meta charset="utf-8"></head><body></body></html>', 'html.parser')
        
        # Split and clean selectors - trim whitespace and remove empty ones
        selectors = [s.strip() for s in css_selectors.split(',') if s.strip()]
        
        if not selectors:
            logger.warning("No valid CSS selectors provided, returning full HTML")
            return html_content
            
        logger.info(f"Extracting elements with {len(selectors)} CSS selectors: {selectors}")
        
        # First collect all matching elements to avoid modifying the DOM structure
        # which can break complex selectors like nth-child
        all_matching_elements = []
        
        # Extract and collect each matching element
        elements_found = False
        for selector in selectors:
            try:
                # Log the selector for debugging
                logger.info(f"Applying selector: '{selector}'")
                
                # Try to select elements with this selector
                matches = soup.select(selector)
                
                if matches:
                    elements_found = True
                    logger.info(f"Found {len(matches)} elements matching selector '{selector}'")
                    
                    # Log a sample of each matched element
                    for i, element in enumerate(matches):
                        # Store a deep copy of the element to avoid modifying the original
                        # Deep copy ensures we get the entire subtree
                        element_copy = str(element)  # Convert to string to ensure we get a complete copy
                        all_matching_elements.append((selector, element_copy, i))
                        
                        # Log a preview
                        element_preview = element_copy[:100] + "..." if len(element_copy) > 100 else element_copy
                        logger.info(f"Match {i+1} for '{selector}': {element_preview}")
                else:
                    logger.warning(f"No elements found matching selector '{selector}'")
                    # Try to find elements that might be similar for debugging
                    if '>' in selector:
                        parts = selector.split('>')
                        parent_selector = parts[0].strip()
                        logger.info(f"Checking parent selector: '{parent_selector}'")
                        parent_matches = soup.select(parent_selector)
                        if parent_matches:
                            logger.info(f"Found {len(parent_matches)} potential parent elements matching '{parent_selector}'")
                            
                            # Check if any nth-child selectors
                            if any('nth-child' in part for part in parts):
                                logger.info("Selector contains nth-child - showing parent's children:")
                                for pm_idx, pm in enumerate(parent_matches[:2]):  # Show for first two parents only
                                    children = pm.findChildren(recursive=False)
                                    logger.info(f"Parent {pm_idx+1} has {len(children)} direct children")
                        else:
                            logger.info(f"No parent elements found for '{parent_selector}'")
            except Exception as e:
                logger.error(f"Error applying selector '{selector}': {str(e)}")
                logger.exception("Selector error traceback:")
        
        # If no elements were found with any selector, return the original HTML
        if not elements_found:
            logger.warning("No elements matched any of the provided selectors, returning full HTML")
            return html_content
            
        # Now add all collected elements to the new soup
        logger.info(f"Adding {len(all_matching_elements)} matched elements to new document")
        for selector, element_str, idx in all_matching_elements:
            # Parse the string back to a soup element
            element_soup = BeautifulSoup(element_str, 'html.parser')
            # Get the root element
            element = next(element_soup.children)
            # Add to the new body
            new_soup.body.append(element)
            
        # Get the final HTML with extracted elements
        extracted_html = str(new_soup)
        logger.info(f"CSS selector extraction reduced HTML from {len(html_content)} to {len(extracted_html)} bytes")
        
        # Log a small preview of the extracted content
        preview = extracted_html[:200] + "..." if len(extracted_html) > 200 else extracted_html
        logger.info(f"Extracted content preview: {preview}")
        
        return extracted_html
        
    except Exception as e:
        logger.error(f"Error extracting elements with CSS selectors: {str(e)}")
        logger.exception("Full traceback:")
        return html_content  # Return original content if extraction fails

def get_categorized_tags():
    """Get existing tags from the database.
    
    Returns:
        list: List of existing tag names
    """
    try:
        existing_tags = list(CategorizedTag.objects.all().values_list('name', flat=True))
        return existing_tags
    except Exception as e:
        logger.error(f"Error fetching categorized tags: {str(e)}")
        return []

def get_tag_categories():
    """Get existing tag categories from the database.
    
    Returns:
        list: List of unique tag categories
    """
    try:
        tag_categories = list(set(CategorizedTag.objects.values_list('category', flat=True)))
        return tag_categories
    except Exception as e:
        logger.error(f"Error fetching tag categories: {str(e)}")
        return []

def validate_url(url):
    """Validate that a URL is accessible and returns valid HTML.
    
    Args:
        url (str): The URL to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        response = requests.head(url, timeout=10)
        response.raise_for_status()
        
        # Check if content is HTML (based on Content-Type header)
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' not in content_type.lower():
            return False, f"URL doesn't contain HTML content (Content-Type: {content_type})"
            
        return True, None
    except requests.exceptions.RequestException as e:
        return False, f"URL validation error: {str(e)}"

def get_bedrock_client():
    """
    Get an AWS Bedrock client using credentials from environment variables.
    """
    try:
        # First try to get credentials from environment variables
        aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        aws_region = os.environ.get('AWS_REGION', 'us-east-1')
        
        # If not found in environment, try to get from Django settings as fallback
        if not aws_access_key_id:
            aws_access_key_id = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
        if not aws_secret_access_key:
            aws_secret_access_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
        if not aws_region:
            aws_region = getattr(settings, 'AWS_REGION', 'us-east-1')

        # Check if credentials are available
        if not aws_access_key_id or not aws_secret_access_key:
            raise NoCredentialsError("AWS credentials not found in environment variables or Django settings")

        # Log the status of credentials (without revealing the actual values)
        logger.info(f"AWS credentials loaded successfully. Using region: {aws_region}")
        logger.info(f"AWS_ACCESS_KEY_ID present: {bool(aws_access_key_id)}")
        logger.info(f"AWS_SECRET_ACCESS_KEY present: {bool(aws_secret_access_key)}")

        # Create a Bedrock client
        client = boto3.client(
            service_name='bedrock-runtime',
            region_name=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

        return client
    except (NoCredentialsError, ClientError) as e:
        logger.error(f"Error creating Bedrock client: {str(e)}")
        raise

def process_element_with_spacing(element, keep_newlines=True):
    """
    Process an element with extra spacing between its direct children
    
    Args:
        element: BeautifulSoup element to process
        keep_newlines (bool): Whether to preserve newlines
        
    Returns:
        str: Processed text with extra spacing
    """
    # Get all direct children
    direct_children = []
    
    # Get the direct children that are element nodes (not text nodes)
    for child in element.children:
        if child.name:  # Only consider element nodes
            if keep_newlines:
                text = child.get_text(separator='\n', strip=True)
            else:
                text = child.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text)  # Clean up whitespace
            
            if text.strip():  # Only add non-empty text
                direct_children.append(text)
    
    # If we found meaningful direct children, join them with extra spacing
    if direct_children:
        # Add triple newlines between direct children for clear separation
        return "\n\n\n".join(direct_children)
    
    # Fallback: if no direct children found or they don't have text,
    # just return the original element's text with normal formatting
    if keep_newlines:
        return element.get_text(separator='\n', strip=True)
    else:
        text = element.get_text(separator=' ', strip=True)
        return re.sub(r'\s+', ' ', text)

def extract_content_with_selectors(url, selectors_config, keep_newlines=True, add_extra_spacing=True):
    """
    Extract text content from a webpage using CSS selectors with names and notes
    
    Args:
        url (str): URL of the webpage
        selectors_config (list): List of dictionaries with selector info (selector, name, note, preserve_html)
            - selector: CSS selector to target elements
            - name: Name of the section
            - note: Additional notes about the section
            - preserve_html: If True, preserves the full HTML of the element instead of just the text
        keep_newlines (bool): Whether to preserve newlines in the extracted text
        add_extra_spacing (bool): Add extra spacing between top-level elements
        
    Returns:
        str: Extracted text content
    """
    try:
        # Send a GET request to the URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        logger.info(f"Fetching {url}...")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse the HTML content
        logger.info("Parsing HTML...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract text from each CSS selector
        all_sections = []
        
        for config in selectors_config:
            selector = config.get('selector', '').strip()
            name = config.get('name', 'Unnamed Section')
            note = config.get('note', '')
            preserve_html = config.get('preserve_html', False)
            
            if not selector:
                continue
                
            logger.info(f"Processing selector: {selector} (Name: {name}, Preserve HTML: {preserve_html})")
            elements = soup.select(selector)
            
            if not elements:
                logger.info(f"No elements found for selector: {selector}")
                continue
                
            # Create a section header with the name and note
            section_text = [f"### {name} ###"]
            if note:
                section_text.append(f"Note: {note}")
            section_text.append("")  # Add an empty line after header
            
            for i, element in enumerate(elements):
                if preserve_html:
                    # Preserve full HTML content
                    html_content = str(element)
                    logger.info(f"Preserving HTML for {selector}, length: {len(html_content)}")
                    if html_content:
                        # Add element index if there are multiple elements
                        if len(elements) > 1:
                            section_text.append(f"--- Element {i+1} ---")
                        section_text.append(html_content)
                elif add_extra_spacing:
                    # Process content with extra spacing between top-level children
                    processed_text = process_element_with_spacing(element, keep_newlines)
                    if processed_text:
                        # Add element index if there are multiple elements
                        if len(elements) > 1:
                            section_text.append(f"--- Element {i+1} ---")
                        section_text.append(processed_text)
                else:
                    # Standard processing without extra spacing
                    # Get all text from this element, preserving newlines if requested
                    if keep_newlines:
                        # Replace multiple newlines with single newline for cleaner output
                        text = element.get_text(separator='\n', strip=True)
                        # But ensure paragraphs stay separated
                        text = re.sub(r'\n{3,}', '\n\n', text)
                    else:
                        text = element.get_text(separator=' ', strip=True)
                        text = re.sub(r'\s+', ' ', text)
                    
                    if text:
                        # Add element index if there are multiple elements
                        if len(elements) > 1:
                            section_text.append(f"--- Element {i+1} ---")
                        section_text.append(text)
                
                # Add spacing between elements
                if i < len(elements) - 1:
                    section_text.append("")
            
            # Add this section to the overall output
            if len(section_text) > 1:  # Only add if there's content beyond the header
                all_sections.append("\n".join(section_text))
        
        # Join all sections with clear separation
        if all_sections:
            result = "\n\n" + "\n\n".join(all_sections)
            return result
        else:
            return "No content found for the provided selectors."
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL: {str(e)}")
        return f"Error fetching URL: {str(e)}"
    except Exception as e:
        logger.error(f"Error extracting content: {str(e)}")
        return f"Error extracting content: {str(e)}"

def simplify_html_content(url, selectors_config=None):
    """
    Use the HTML simplifier functionality to extract content from a webpage using CSS selectors
    
    Args:
        url (str): URL of the webpage
        selectors_config (list, optional): List of selector configuration dictionaries
            If None, default AirScience selectors will be used
            
    Returns:
        str: Simplified HTML content
    """
    try:
        # Default selectors for AirScience pages
        if selectors_config is None:
            selectors_config = [
                {
                    "selector": "body > section:nth-child(4) .icon-image + .introprodtext",
                    "name": "Full Description",
                    "note": "This is the full description of the product, shown on the product page. You may have to re-add bullet points and other formatting."
                },
                {
                    "selector": "body > section:nth-child(5) > div > div > div.rightblock2 > div.descriptioncontainer",
                    "name": "Short Description",
                    "note": "This is the short description of the product, shown on the product page."
                },
                {
                    "selector": "select[name='form_fields[field_2400c42]'] > option[value^='Div']",
                    "name": "Model Names",
                    "note": "Each of these model names is associated with a complete set of specifications, shown in the Model Specifications section below."
                },
                {
                    "selector": "div[id^='Div']:not(div[id$='Top'])",
                    "name": "Model Specifications",
                    "note": "Each complete set of model specifications is associated with a model name in the Model Names section above."
                },
                {
                    "selector": "body > section:nth-child(9) .tab-content",
                    "name": "Technical Info Tables",
                    "note": "These are technical information tables about dimensions, filters, and applications."
                },
                {
                    "selector": "#image-wrapper",
                    "name": "Product Images",
                    "note": "Product images with full HTML preserved to maintain image URLs.",
                    "preserve_html": True
                }
            ]
        
        logger.info(f"Using HTML simplifier with URL: {url} and {len(selectors_config)} selectors")
        
        # Extract content using the selectors
        simplified_html = extract_content_with_selectors(
            url, 
            selectors_config,
            keep_newlines=True,
            add_extra_spacing=True
        )
        
        logger.info(f"Simplified HTML content size: {len(simplified_html)} bytes")
        
        # TEMPORARY: Save the simplified HTML to a file for inspection
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        domain = urlparse(url).netloc.replace(".", "_")
        debug_filename = f"simplified_html_{domain}_{timestamp}.txt"
        debug_filepath = os.path.join(settings.MEDIA_ROOT, "temp", debug_filename)
        
        # Make sure the directory exists
        os.makedirs(os.path.dirname(debug_filepath), exist_ok=True)
        
        # Save the simplified HTML
        with open(debug_filepath, 'w', encoding='utf-8') as f:
            f.write(simplified_html)
            
        logger.info(f"SAVED SIMPLIFIED HTML FOR INSPECTION AT: {debug_filepath}")
        logger.info(f"Content sample: {simplified_html[:200]}...")
        
        return simplified_html
            
    except Exception as e:
        logger.error(f"Error simplifying HTML content: {str(e)}")
        raise

def process_url_content(url, css_selectors=None):
    """
    Fetch and process HTML content from a URL to reduce payload size.
    
    Args:
        url (str): The URL to fetch content from
        css_selectors (str, optional): Comma-separated CSS selectors to filter content
        
    Returns:
        str: Processed HTML content
    """
    try:
        logger.info(f"Processing URL content: {url}")
        
        # Try to use the integrated HTML simplifier
        try:
            logger.info("Using integrated HTML simplifier to extract content")
            simplified_html = simplify_html_content(url)
            logger.info(f"HTML simplifier successfully extracted content: {len(simplified_html)} bytes")
            return simplified_html
        except Exception as e:
            logger.warning(f"HTML simplifier failed, falling back to standard method: {str(e)}")
        
        # Fallback to standard method
        # Set a user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Fetch content
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        # Check if content is HTML
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' not in content_type:
            raise ValueError(f"URL does not contain HTML content. Content-Type: {content_type}")
        
        # Get HTML content
        html_content = response.text
        
        # Log the original content for debugging (first 200 chars)
        logger.info(f"Original HTML content snippet: {html_content[:200]}...")
        logger.info(f"Original HTML content size: {len(html_content)} bytes")
        
        # Log CSS selectors if provided
        if css_selectors:
            logger.info(f"CSS selectors to apply: {css_selectors}")
        
        # Apply HTML preprocessing to reduce size while preserving important formatting
        processed_html = preprocess_html(html_content, css_selectors)
        
        logger.info(f"HTML processing: Original size: {len(html_content)} bytes, Processed size: {len(processed_html)} bytes")
        
        return processed_html
    except requests.RequestException as e:
        logger.error(f"Error fetching URL {url}: {str(e)}")
        raise

def extract_structured_data(bedrock_response):
    """Extract structured JSON data from an AWS Bedrock response.
    
    Args:
        bedrock_response (dict): The response from AWS Bedrock
        
    Returns:
        dict: Extracted structured data, or None if extraction fails
    """
    try:
        logger.info("Attempting to extract structured data from Bedrock response")
        extracted_data = None
        
        if not isinstance(bedrock_response, dict):
            logger.error(f"Expected dict, got {type(bedrock_response)}: {bedrock_response}")
            return None
            
        # Log the shape of the response to help with debugging
        logger.debug(f"Bedrock response keys: {list(bedrock_response.keys())}")
        
        # Handle Claude Bedrock response format
        if 'message' in bedrock_response and 'content' in bedrock_response['message']:
            logger.debug("Found 'message.content' structure in response")
            for i, content_item in enumerate(bedrock_response['message']['content']):
                logger.debug(f"Processing content item {i}: {list(content_item.keys())}")
                if 'text' in content_item:
                    text = content_item['text']
                    logger.debug(f"Found text in content item {i} (first 100 chars): {text[:100]}...")
                    
                    # Check for <br> tags and newlines in the raw text
                    br_count = text.lower().count('<br')
                    newline_count = text.count('\n')
                    tab_count = text.count('\t')
                    logger.info(f"Raw response text contains {br_count} <br> tags, {newline_count} newlines, and {tab_count} tabs")
                    
                    # Try to extract JSON from ```json blocks (Claude's typical output format)
                    if '```json' in text:
                        logger.debug("Found JSON code block in text")
                        # Attempt to extract text between ```json and ``` markers
                        try:
                            json_text = text.split('```json\n')[1].split('\n```')[0]
                            logger.debug(f"Extracted JSON text (first 100 chars): {json_text[:100]}...")
                            
                            # Check for <br> tags and newlines in the extracted JSON text
                            json_br_count = json_text.lower().count('<br')
                            json_newline_count = json_text.count('\n')
                            json_tab_count = json_text.count('\t')
                            logger.info(f"Extracted JSON text contains {json_br_count} <br> tags, {json_newline_count} newlines, and {json_tab_count} tabs")
                            
                            try:
                                # Preserve newlines and tabs by not using ensure_ascii
                                extracted_data = json.loads(json_text)
                                
                                # Check the full_description field in the extracted data
                                if extracted_data and 'full_description' in extracted_data:
                                    fd = extracted_data['full_description']
                                    fd_br_count = fd.lower().count('<br')
                                    fd_newline_count = fd.count('\n')
                                    fd_tab_count = fd.count('\t')
                                    logger.info(f"Extracted full_description contains {fd_br_count} <br> tags, {fd_newline_count} newlines, and {fd_tab_count} tabs")
                                    
                                logger.info("Successfully extracted structured data from JSON block")
                                return extracted_data
                            except json.JSONDecodeError as je:
                                logger.warning(f"Failed to parse JSON from code block: {str(je)}")
                                logger.debug(f"Problematic JSON text: {json_text}")
                        except (IndexError, ValueError) as e:
                            logger.warning(f"Error extracting JSON text from code block: {str(e)}")
                    
                    # If no code blocks, try the whole text
                    else:
                        logger.debug("No JSON code block found, trying to parse entire text as JSON")
                        try:
                            extracted_data = json.loads(text)
                            
                            # Check the full_description field in the extracted data
                            if extracted_data and 'full_description' in extracted_data:
                                fd = extracted_data['full_description']
                                fd_br_count = fd.lower().count('<br')
                                fd_newline_count = fd.count('\n')
                                fd_tab_count = fd.count('\t')
                                logger.info(f"Extracted full_description contains {fd_br_count} <br> tags, {fd_newline_count} newlines, and {fd_tab_count} tabs")
                            
                            logger.info("Successfully extracted structured data from text")
                            return extracted_data
                        except json.JSONDecodeError as je:
                            logger.warning(f"Text is not valid JSON: {str(je)}")
                            # Try to find anything that looks like JSON in the text
                            if '{' in text and '}' in text:
                                logger.debug("Found JSON-like brackets in text, attempting to extract")
                                try:
                                    start_idx = text.find('{')
                                    end_idx = text.rfind('}') + 1
                                    if start_idx < end_idx:
                                        json_candidate = text[start_idx:end_idx]
                                        logger.debug(f"Trying JSON candidate: {json_candidate[:100]}...")
                                        extracted_data = json.loads(json_candidate)
                                        
                                        # Check the full_description field in the extracted data
                                        if extracted_data and 'full_description' in extracted_data:
                                            fd = extracted_data['full_description']
                                            fd_br_count = fd.lower().count('<br')
                                            fd_newline_count = fd.count('\n')
                                            fd_tab_count = fd.count('\t')
                                            logger.info(f"Extracted full_description contains {fd_br_count} <br> tags, {fd_newline_count} newlines, and {fd_tab_count} tabs")
                                        
                                        logger.info("Successfully extracted JSON from text segment")
                                        return extracted_data
                                except (json.JSONDecodeError, ValueError) as e2:
                                    logger.warning(f"Failed to extract JSON from text segment: {str(e2)}")
        else:
            # Check if the response itself is directly structured data
            logger.debug("Response does not have 'message.content' structure, trying other approaches")
            for key, value in bedrock_response.items():
                if isinstance(value, dict):
                    logger.debug(f"Found dict value in key '{key}', examining")
                    # Try common response formats
                    if key in ('output', 'content', 'result', 'response', 'data'):
                        logger.debug(f"Attempting to parse value from key '{key}'")
                        
                        # Try to directly return the dict if it looks like our data
                        if any(k in value for k in ('title', 'specifications', 'tags')):
                            logger.info(f"Found what appears to be structured data in '{key}'")
                            
                            # Check the full_description field in the extracted data
                            if 'full_description' in value:
                                fd = value['full_description']
                                fd_br_count = fd.lower().count('<br')
                                fd_newline_count = fd.count('\n')
                                fd_tab_count = fd.count('\t')
                                logger.info(f"Extracted full_description contains {fd_br_count} <br> tags, {fd_newline_count} newlines, and {fd_tab_count} tabs")
                            
                            return value
        
        logger.warning("Could not extract structured data from response")
        logger.debug(f"Full response for debugging: {json.dumps(bedrock_response)}")
        return None
    except Exception as e:
        logger.exception(f"Error extracting structured data: {str(e)}")
        return None 

def extract_universal_specifications(data):
    """
    Identify specifications that are common across all models and move them to the universal level.
    
    This function:
    1. Scans all model specifications
    2. Identifies specs that appear in all models with identical values
    3. Moves these specs to the top-level "specifications" array
    4. Removes the duplicate specs from each model's specifications
    
    Args:
        data (dict): The JSON data structure containing models and specifications
        
    Returns:
        dict: The modified data structure with universal specifications properly placed
    """
    try:
        logger.info("Extracting universal specifications from models")
        
        # If there are no models or models have no specifications, return data unchanged
        if not data.get('models') or len(data['models']) == 0:
            logger.info("No models found, skipping universal specification extraction")
            return data
            
        # Initialize an empty list for universal specifications if it doesn't exist
        if 'specifications' not in data:
            data['specifications'] = []
            
        # Track all specs across all models to identify common ones
        model_count = len(data['models'])
        model_names = [model.get('name', f'[Model {i}]') for i, model in enumerate(data['models'])]
        logger.debug(f"Processing {model_count} models for universal specifications: {model_names}")
        
        # Dictionary to store all specifications from all models
        # Format: {section_name: {spec_key: {value: {count: int, models: list}}}}
        all_specs = {}
        
        # First pass: collect all specs from all models
        for model_idx, model in enumerate(data['models']):
            model_name = model.get('name', f'[Model {model_idx}]')
            if not model.get('specifications'):
                logger.warning(f"Model {model_name} has no specifications")
                # If any model lacks specifications, we can't reliably determine universal specs
                return data
                
            logger.debug(f"Processing model {model_name}")
            
            # Process each specification section in the model
            for section in model['specifications']:
                section_name = section.get('name')
                if not section_name or not section.get('specs'):
                    logger.warning(f"Skipping unnamed section or section without specs in model {model_name}")
                    continue
                    
                # Initialize section in all_specs if needed
                if section_name not in all_specs:
                    all_specs[section_name] = {}
                    
                # Process each spec in the section
                for spec in section['specs']:
                    key = spec.get('key')
                    value = spec.get('value')
                    
                    if not key or value is None:
                        logger.warning(f"Skipping invalid spec in section {section_name} for model {model_name}")
                        continue
                        
                    # Initialize spec in section if needed
                    if key not in all_specs[section_name]:
                        all_specs[section_name][key] = {}
                        
                    # Create value entry if needed
                    value_str = str(value)  # Ensure consistent comparison
                    if value_str not in all_specs[section_name][key]:
                        all_specs[section_name][key][value_str] = {
                            'count': 0,
                            'models': []
                        }
                        
                    # Update count and track which models have this spec
                    all_specs[section_name][key][value_str]['count'] += 1
                    all_specs[section_name][key][value_str]['models'].append(model_idx)
        
        # Log the collected specifications for debugging
        logger.debug(f"Collected specifications summary: {len(all_specs)} sections")
        
        # Second pass: identify universal specs (those present in all models with same value)
        universal_specs = {}  # Format: {section_name: [(key, value)]}
        
        for section_name, section_specs in all_specs.items():
            universal_specs[section_name] = []
            
            for key, values in section_specs.items():
                # Find values that appear in all models
                for value_str, value_data in values.items():
                    if value_data['count'] == model_count:
                        # This spec appears in all models with the same value
                        universal_specs[section_name].append((key, value_str))
                        logger.debug(f"Found universal spec: {section_name} - {key}: {value_str}")
        
        # Log the identified universal specs
        universal_spec_count = sum(len(specs) for specs in universal_specs.values())
        logger.info(f"Identified {universal_spec_count} universal specs across {len(universal_specs)} sections")
        
        # Third pass: Add universal specs to top level and remove from models
        for section_name, specs in universal_specs.items():
            if not specs:
                logger.debug(f"No universal specs found in section {section_name}")
                continue
                
            # Find or create this section at the universal level
            universal_section = None
            for section in data['specifications']:
                if section.get('name') == section_name:
                    universal_section = section
                    logger.debug(f"Found existing universal section: {section_name}")
                    break
                    
            if not universal_section:
                logger.debug(f"Creating new universal section: {section_name}")
                universal_section = {
                    'name': section_name,
                    'specs': []
                }
                data['specifications'].append(universal_section)
                
            # Add specs to universal section (if not already present)
            if 'specs' not in universal_section:
                universal_section['specs'] = []
                
            existing_keys = {spec.get('key') for spec in universal_section['specs']}
            for key, value in specs:
                if key not in existing_keys:
                    logger.debug(f"Adding universal spec {key}: {value} to section {section_name}")
                    universal_section['specs'].append({
                        'key': key,
                        'value': value
                    })
                    existing_keys.add(key)
            
            # Remove these specs from each model
            modified_models = set()
            for model_idx, model in enumerate(data['models']):
                model_name = model.get('name', f'[Model {model_idx}]')
                if not model.get('specifications'):
                    continue
                
                # Find the corresponding section in this model
                for model_section_idx, model_section in enumerate(model['specifications']):
                    if model_section.get('name') == section_name:
                        # Original spec count
                        original_spec_count = len(model_section.get('specs', []))
                        
                        # Filter out specs that are now at the universal level
                        new_specs = [
                            spec for spec in model_section['specs'] 
                            if (spec.get('key'), str(spec.get('value'))) not in specs
                        ]
                        
                        # If specs were removed
                        if len(new_specs) < original_spec_count:
                            modified_models.add(model_idx)
                            logger.debug(f"Removed {original_spec_count - len(new_specs)} specs from model {model_name}, section {section_name}")
                        
                        if new_specs:
                            # Update with filtered specs
                            model_section['specs'] = new_specs
                        else:
                            # If section is now empty, mark for removal
                            model_section['specs'] = []
                            logger.debug(f"Section {section_name} is now empty for model {model_name}")
                
                # Count specs before removing empty sections
                original_section_count = len(model.get('specifications', []))
                
                # Remove empty spec sections
                model['specifications'] = [
                    section for section in model['specifications'] 
                    if section.get('specs') and len(section['specs']) > 0
                ]
                
                # If sections were removed
                if len(model.get('specifications', [])) < original_section_count:
                    logger.debug(f"Removed {original_section_count - len(model.get('specifications', []))} empty sections from model {model_name}")
            
            logger.info(f"Modified {len(modified_models)} models by moving specs to universal level")
        
        # Log the results
        universal_spec_count = sum(len(section.get('specs', [])) for section in data['specifications'])
        logger.info(f"Extracted {universal_spec_count} universal specifications across {len(data['specifications'])} sections")
        
        return data
    except Exception as e:
        logger.error(f"Error extracting universal specifications: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Return the original data unchanged if there was an error
        return data

def fix_rich_text_html(content):
    """
    Fix malformed HTML in rich text content to prevent Wagtail parsing errors.
    Specifically addresses issues with unmatched <br> and </p> tags by converting
    all content with <br> tags into proper paragraph structure.
    
    Args:
        content (str): The HTML content to fix
        
    Returns:
        str: The fixed HTML content
    """
    import re
    
    # Don't process empty content
    if not content:
        return content
    
    logger.info(f"Fixing rich text HTML, original content length: {len(content)}")
    
    # Log the initial numbers of tags
    p_count = content.count('<p>')
    p_close_count = content.count('</p>')
    br_count = content.lower().count('<br')
    
    logger.info(f"Original content has {p_count} <p> tags, {p_close_count} </p> tags, and {br_count} <br> tags")
    
    # If we have <br> tags, split by them and create separate paragraphs instead
    if br_count > 0:
        # First remove any existing paragraph tags
        content = re.sub(r'</?p>', '', content)
        
        # Split by any form of <br> tag
        parts = re.split(r'<br\s*/?>|<br>', content)
        
        # Create proper paragraphs
        fixed_content = ''
        for part in parts:
            part = part.strip()
            if part:
                fixed_content += f'<p>{part}</p>'
        
        content = fixed_content
        logger.info("Replaced <br> tags with separate paragraphs")
    
    # Case 1: Content with unbalanced <p> tags
    elif p_count != p_close_count:
        logger.info(f"Detected unbalanced <p> tags: {p_count} opening vs {p_close_count} closing")
        
        # Remove all </p> tags
        content = content.replace('</p>', '')
        
        # Split by <p> tags
        parts = re.split(r'<p>', content)
        
        # Create proper paragraphs
        fixed_content = ''
        for part in parts:
            part = part.strip()
            if part:
                fixed_content += f'<p>{part}</p>'
        
        content = fixed_content
        logger.info("Fixed unbalanced <p> tags by restructuring content")
    
    # Case 2: Make sure content starts with <p> if it has any content
    elif content and not content.startswith('<p>'):
        # No <p> tags at all - wrap the whole content
        if p_count == 0 and p_close_count == 0:
            content = f'<p>{content}</p>'
            logger.info("Wrapped content in <p> tags")
        else:
            # Has some <p> tags but doesn't start with one
            # Split by paragraph tags and re-wrap each part
            parts = []
            current = ''
            in_p = False
            
            # Simple parser to extract content inside and outside <p> tags
            for char in content:
                if content[current:current+3] == '<p>':
                    if current:
                        parts.append(('text', current))
                    current = ''
                    in_p = True
                elif content[current:current+4] == '</p>':
                    if current:
                        parts.append(('p', current))
                    current = ''
                    in_p = False
                else:
                    current += char
            
            if current:
                parts.append(('text' if not in_p else 'p', current))
            
            # Rebuild with proper structure
            fixed_content = ''
            for part_type, part in parts:
                if part_type == 'text' and part.strip():
                    fixed_content += f'<p>{part.strip()}</p>'
                elif part_type == 'p':
                    fixed_content += f'<p>{part}</p>'
            
            content = fixed_content
            logger.info("Restructured mixed content to proper paragraphs")
    
    # Log the fixed numbers of tags
    p_count_after = content.count('<p>')
    p_close_count_after = content.count('</p>')
    br_count_after = content.lower().count('<br')
    
    logger.info(f"Fixed content has {p_count_after} <p> tags, {p_close_count_after} </p> tags, and {br_count_after} <br> tags")
    
    return content

def transform_bedrock_data_to_api_format(response_data, url):
    """
    Transform the data extracted by AWS Bedrock into the format required by the base_site API.
    
    Args:
        response_data (dict): The JSON data returned by AWS Bedrock
        url (str): The source URL
        
    Returns:
        dict: Data in the format expected by create_or_update_lab_equipment API
    """
    try:
        # Process the full_description to ensure it's properly formatted for RichTextField
        full_description = response_data.get('full_description', '')
        
        # Log details about the full_description before processing
        br_count = full_description.lower().count('<br')
        newline_count = full_description.count('\n')
        tab_count = full_description.count('\t')
        logger.info(f"Full description before transform contains {br_count} <br> tags, {newline_count} newlines, and {tab_count} tabs")
        
        # Replace tabs with spaces to preserve formatting
        if tab_count > 0:
            full_description = full_description.replace('\t', '    ')
        
        # Replace literal \n sequences with actual newlines if they exist
        if '\\n' in full_description:
            full_description = full_description.replace('\\n', '\n')
            logger.info(f"Replaced literal \\n sequences with actual newlines")
        
        # Convert newlines to <br> tags if they exist and there are no <br> tags already
        if newline_count > 0 and br_count == 0:
            full_description = full_description.replace('\n', '<br>')
            logger.info(f"Converted {newline_count} newlines to <br> tags")
        
        # If full_description doesn't already have <p> tags, wrap it
        if full_description and not full_description.startswith('<p>'):
            # Check if it contains <br> tags and wrap it properly for RichTextField
            if '<br>' in full_description or '<br/>' in full_description or '<br />' in full_description:
                # Make sure it's properly wrapped in <p> tags for RichTextField
                if not full_description.startswith('<p>'):
                    full_description = f'<p>{full_description}</p>'
                    logger.info("Wrapped full description with <p> tags")
            else:
                # If no <br> tags, wrap each line in <p> tags
                paragraphs = full_description.split('\n')
                full_description = ''.join([f'<p>{p}</p>' for p in paragraphs if p.strip()])
                logger.info(f"Split full description into {len(paragraphs)} paragraphs with <p> tags")
        
        # Fix any malformed HTML in the rich text content
        full_description = fix_rich_text_html(full_description)
        
        # Log the final processed full_description
        final_br_count = full_description.lower().count('<br')
        logger.info(f"Full description after transform contains {final_br_count} <br> tags")
        logger.info(f"Full description sample after transform: {full_description[:200]}")
        
        # Initialize the API data structure
        api_data = {
            'title': response_data.get('title', ''),
            'short_description': response_data.get('short_description', ''),
            'full_description': full_description,
            'source_url': url,
            'needs_review': True,  # Default to True for AI-extracted data
            'tags': [],
            'specifications': [],
            'models': [],
            'images': []
        }

        # Process tags
        if 'tags' in response_data and response_data['tags']:
            for tag in response_data['tags']:
                if isinstance(tag, dict) and 'category' in tag and 'name' in tag:
                    api_data['tags'].append(tag)
                elif isinstance(tag, str) and ':' in tag:
                    # Process string format tags (e.g., "Category: Value")
                    category, name = [part.strip() for part in tag.split(':', 1)]
                    api_data['tags'].append({'category': category, 'name': name})

        # Process specifications
        if 'specifications' in response_data and response_data['specifications']:
            # Check if specifications is a dictionary or a list
            if isinstance(response_data['specifications'], dict):
                # Handle specifications as a dictionary (original format)
                for group_name, specs in response_data['specifications'].items():
                    spec_group = {
                        'name': group_name,
                        'specs': []
                    }
                    
                    for key, value in specs.items():
                        spec_group['specs'].append({
                            'key': key,
                            'value': str(value)
                        })
                    
                    api_data['specifications'].append(spec_group)
            elif isinstance(response_data['specifications'], list):
                # Handle specifications as a list of spec groups (format found in response)
                for spec_group in response_data['specifications']:
                    if isinstance(spec_group, dict) and 'name' in spec_group and 'specs' in spec_group:
                        # If spec_group already has the correct structure, add it directly
                        api_data['specifications'].append(spec_group)
                    else:
                        logger.warning(f"Unexpected specification group format: {spec_group}")

        # Process models
        if 'models' in response_data and response_data['models']:
            logger.info(f"Processing {len(response_data['models'])} models from Bedrock response")
            
            # Log the model names for debugging
            model_names = [model.get('name', '[No name]') for model in response_data['models']]
            logger.info(f"Model names in Bedrock response: {model_names}")
            
            for i, model in enumerate(response_data['models']):
                model_name = model.get('name', '[No name]')
                logger.info(f"Processing model {i+1}: {model_name}")
                
                if 'name' not in model:
                    logger.warning(f"Skipping model {i+1} because it has no name")
                    continue
                
                model_data = {
                    'name': model.get('name', ''),
                    'model_number': ''  # Empty string for backward compatibility
                }
                
                # Process model specifications if present
                if 'specifications' in model and model['specifications']:
                    model_data['specifications'] = []
                    
                    # Check if model specifications is a dictionary or a list
                    if isinstance(model['specifications'], dict):
                        # Handle model specifications as a dictionary
                        for group_name, specs in model['specifications'].items():
                            spec_group = {
                                'name': group_name,
                                'specs': []
                            }
                            
                            for key, value in specs.items():
                                spec_group['specs'].append({
                                    'key': key,
                                    'value': str(value)
                                })
                            
                            model_data['specifications'].append(spec_group)
                    elif isinstance(model['specifications'], list):
                        # Handle model specifications as a list
                        for spec_group in model['specifications']:
                            if isinstance(spec_group, dict) and 'name' in spec_group and 'specs' in spec_group:
                                model_data['specifications'].append(spec_group)
                            else:
                                logger.warning(f"Unexpected model specification group format: {spec_group}")
                
                api_data['models'].append(model_data)
                logger.info(f"Added model {model_data['name']} to API data")
            
            logger.info(f"Processed {len(api_data['models'])} models for API data")

        # Process images
        if 'images' in response_data and response_data['images']:
            for image_url in response_data['images']:
                if image_url and isinstance(image_url, str):
                    # Handle both absolute and relative URLs
                    if not image_url.startswith(('http://', 'https://')):
                        # Parse the source URL to get the base
                        parsed_url = urlparse(url)
                        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                        
                        # Handle different relative URL formats
                        if image_url.startswith('/'):
                            image_url = f"{base_url}{image_url}"
                        else:
                            # Remove last part of path
                            path_parts = parsed_url.path.split('/')
                            base_path = '/'.join(path_parts[:-1])
                            image_url = f"{base_url}{base_path}/{image_url}"
                    
                    api_data['images'].append(image_url)
        
        # Extract universal specifications from models
        logger.info(f"Before extracting universal specifications: {len(api_data['models'])} models")
        api_data = extract_universal_specifications(api_data)
        logger.info(f"After extracting universal specifications: {len(api_data['models'])} models")
        
        # Log final model list
        final_model_names = [model.get('name', '[No name]') for model in api_data['models']]
        logger.info(f"Final model names: {final_model_names}")

        return api_data
    except Exception as e:
        logger.error(f"Error transforming Bedrock data to API format: {str(e)}")
        raise 