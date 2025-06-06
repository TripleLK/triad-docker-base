#!/usr/bin/env python3
# apps/scrapers/selectors/categorized_tag_page_selector.py

import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from .base import Selector, Selected, SelectedType
from apps.categorized_tags.models import CategorizedTag, TagCategory
from apps.base_site.models import LabEquipmentPage

log = logging.getLogger(__name__)

class CategorizedTagPageSelector(Selector):
    """
    Extracts product links from a category/application page and generates tags.
    
    This selector is used to find all products on a category or application page
    and return a mapping of product URLs to tag information.
    """
    
    def __init__(self, category_name, url_pattern, tag_mapping, product_links_selector, 
                 log_level="INFO", required=False):
        """
        Initialize the selector
        
        Args:
            category_name: The tag category name (e.g. "Product Category", "Product Application")
            url_pattern: Pattern for the category URL with a placeholder for the category value
            tag_mapping: Dict mapping URL parameter values to friendly tag names
            product_links_selector: CSS selector for extracting product links
            log_level: Level of logging (DEBUG, INFO, WARNING, ERROR)
            required: Whether the selector must find at least one result
        """
        self.category_name = category_name
        self.url_pattern = url_pattern
        self.tag_mapping = tag_mapping
        self.product_links_selector = product_links_selector
        self.log_level = log_level.upper()
        self.required = required
        
        # Categories and Applications typically are on listing pages, so expect SINGLE type input
        self.expected_selected = SelectedType.SINGLE
    
    def select(self, selected: Selected) -> Selected:
        """
        Process the input and extract tag information
        
        Args:
            selected: Input Selected object (typically the BeautifulSoup of a page)
            
        Returns:
            Selected object with VALUE type containing a dictionary mapping:
            {
                "category_name": str,
                "tags": [
                    {
                        "tag_name": str,
                        "product_urls": [str, ...]
                    },
                    ...
                ]
            }
        """
        self.validate_selected_type(selected)
        
        # Result structure
        result = {
            "category_name": self.category_name,
            "tags": []
        }
        
        # Process each tag in the mapping
        for category_value, tag_name in self.tag_mapping.items():
            log.info(f"Processing {self.category_name} tag: {tag_name}")
            
            # Generate the URL for this category value
            url = self.url_pattern.format(category_value=category_value)
            
            try:
                # Fetch the category/application page
                response = requests.get(url)
                if response.status_code != 200:
                    log.warning(f"Failed to fetch URL: {url} (Status: {response.status_code})")
                    continue
                
                # Parse the page
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find product links
                product_links = soup.select(self.product_links_selector)
                product_urls = []
                
                for link in product_links:
                    href = link.get('href')
                    if href:
                        # Make sure URL is absolute
                        if not href.startswith('http'):
                            if href.startswith('/'):
                                base_url = url.split('//', 1)[1].split('/', 1)[0]
                                href = f"https://{base_url}{href}"
                            else:
                                # Relative URL - construct based on current URL
                                href = f"{url.rstrip('/')}/{href}"
                        
                        product_urls.append(href)
                
                # Add tag information to the result
                tag_info = {
                    "tag_name": tag_name,
                    "product_urls": product_urls
                }
                
                result["tags"].append(tag_info)
                log.info(f"Found {len(product_urls)} products for tag '{tag_name}'")
                
            except Exception as e:
                log.error(f"Error processing tag '{tag_name}' at URL {url}: {str(e)}")
        
        # Check if we need to have at least one result
        if self.required and not result["tags"]:
            raise ValueError(f"No tags found for category '{self.category_name}'")
        
        return Selected(result, SelectedType.VALUE)
    
    @classmethod
    def fromYamlDict(cls, yaml_dict):
        """Create a CategorizedTagPageSelector from a YAML dictionary."""
        if isinstance(yaml_dict, dict):
            category_name = yaml_dict.get('category_name')
            url_pattern = yaml_dict.get('url_pattern')
            tag_mapping = yaml_dict.get('tag_mapping', {})
            product_links_selector = yaml_dict.get('product_links_selector')
            log_level = yaml_dict.get('log_level', 'INFO')
            required = yaml_dict.get('required', False)
            
            if not category_name:
                raise ValueError("category_name is required for CategorizedTagPageSelector")
            if not url_pattern:
                raise ValueError("url_pattern is required for CategorizedTagPageSelector")
            if not product_links_selector:
                raise ValueError("product_links_selector is required for CategorizedTagPageSelector")
            
            return cls(
                category_name=category_name,
                url_pattern=url_pattern,
                tag_mapping=tag_mapping,
                product_links_selector=product_links_selector,
                log_level=log_level,
                required=required
            )
        else:
            raise ValueError("Expected dictionary for CategorizedTagPageSelector configuration")
    
    def toYamlDict(self):
        """Convert the selector to a YAML-compatible dictionary."""
        return {
            "categorized_tag_page_selector": {
                "category_name": self.category_name,
                "url_pattern": self.url_pattern,
                "tag_mapping": self.tag_mapping,
                "product_links_selector": self.product_links_selector,
                "log_level": self.log_level,
                "required": self.required
            }
        }
    
    def apply_tags_to_pages(self) -> Dict[str, int]:
        """
        Apply the tags to LabEquipmentPage instances based on the URL.
        
        This is an action method rather than a selector method. It runs the selector,
        creates the tags if needed, and applies them to pages based on URL matching.
        
        Returns:
            Dictionary with stats about how many tags were applied
        """
        # Make sure we have the tag category
        tag_category, created = TagCategory.objects.get_or_create(
            name=self.category_name
        )
        
        log.info(f"Using tag category: {self.category_name} (ID: {tag_category.id})")
        
        # Run the selector on a dummy input (empty soup)
        dummy_soup = BeautifulSoup("", 'html.parser')
        dummy_selected = Selected(dummy_soup, SelectedType.SINGLE)
        result = self.select(dummy_selected)
        
        if result.selected_type != SelectedType.VALUE or not isinstance(result.value, dict):
            raise ValueError("Unexpected result from tag selector")
        
        # Stats to return
        stats = {
            "total_urls": 0,
            "matched_pages": 0,
            "tags_applied": 0,
            "tags_created": 0,
            "url_matching_failures": 0,
            "debug_first_urls": []
        }
        
        # Process each tag
        for tag_info in result.value.get("tags", []):
            tag_name = tag_info.get("tag_name")
            product_urls = tag_info.get("product_urls", [])
            
            if not tag_name or not product_urls:
                continue
                
            # Create or get the tag
            tag, created = CategorizedTag.objects.get_or_create(
                category=self.category_name,
                name=tag_name
            )
            
            log.info(f"Processing tag '{tag.category}: {tag.name}' (ID: {tag.id}, Created: {created})")
            
            if created:
                stats["tags_created"] += 1
            
            # Find matching pages and apply the tag
            stats["total_urls"] += len(product_urls)
            
            # Store up to 3 URLs for debugging
            if len(stats["debug_first_urls"]) < 3 and product_urls:
                stats["debug_first_urls"].extend(product_urls[:3-len(stats["debug_first_urls"])])
            
            # Track unmatched URLs for this tag
            unmatched_urls = []
            
            for url in product_urls:
                # Try to find the page using flexible URL matching
                page = self._find_page_by_flexible_url_match(url)
                
                if page:
                    log.info(f"Found page for URL: {url} (ID: {page.page_ptr_id})")
                    stats["matched_pages"] += 1
                    
                    # Add tag if not already present - using proper Django ORM methods
                    # First check if the tag is already there
                    if tag not in page.categorized_tags.all():
                        log.info(f"Adding tag '{tag.category}: {tag.name}' to page '{page.title}'")
                        try:
                            # The correct way to add a tag to the M2M relationship
                            page.categorized_tags.add(tag)
                            
                            # Explicitly save the page to ensure changes are persisted
                            # This ensures the revision system captures the change
                            page.save()
                            
                            # Now check if it worked
                            if tag in page.categorized_tags.all():
                                log.info(f"Successfully verified tag was added")
                                stats["tags_applied"] += 1
                            else:
                                log.error(f"Tag appears not to have been added even after save")
                        except Exception as e:
                            log.error(f"Error adding tag: {str(e)}")
                else:
                    log.warning(f"No page found for URL: {url}")
                    unmatched_urls.append(url)
                    stats["url_matching_failures"] += 1
            
            # Log info about unmatched URLs
            if unmatched_urls:
                log.info(f"Unmatched URLs for tag '{tag_name}': {len(unmatched_urls)} out of {len(product_urls)}")
                if len(unmatched_urls) <= 5:
                    for url in unmatched_urls:
                        log.info(f"  Unmatched: {url}")
                else:
                    for url in unmatched_urls[:5]:
                        log.info(f"  Unmatched (first 5): {url}")
        
        log.info(f"Finished applying tags. Stats: {stats}")
        return stats
        
    def _find_page_by_flexible_url_match(self, url: str) -> Optional[LabEquipmentPage]:
        """
        Find a page using flexible URL matching strategies.
        
        This method tries multiple approaches to match a URL to a page:
        1. Direct match on the exact URL
        2. Match on the brandname parameter
        3. Match on URL path patterns
        
        Args:
            url: The URL to find a match for
            
        Returns:
            LabEquipmentPage instance if found, None otherwise
        """
        from urllib.parse import urlparse, parse_qs
        
        # Try direct match first
        page = LabEquipmentPage.objects.filter(airscience_url=url).first()
        if page:
            log.debug(f"Direct URL match found for: {url}")
            return page
        
        # Parse the URL
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        
        # Try matching by brandname parameter
        if 'brandname' in query:
            brandname = query['brandname'][0]
            pages = LabEquipmentPage.objects.filter(airscience_url__contains=f'brandname={brandname}')
            if pages.exists():
                page = pages.first()
                log.info(f"Matched by brandname parameter: {brandname}")
                return page
        
        # Try matching by similar URL path pattern
        path = parsed.path
        if path:
            pages = LabEquipmentPage.objects.filter(airscience_url__contains=path)
            if pages.exists():
                # If multiple matches, try to get the closest one
                if pages.count() > 1:
                    # If we have brandname, try to further refine
                    if 'brandname' in query:
                        brandname = query['brandname'][0]
                        # Look for partial matches in title
                        for word in brandname.replace('-', ' ').split():
                            word_match = pages.filter(title__icontains=word)
                            if word_match.exists():
                                log.info(f"Matched by path + title word '{word}': {url}")
                                return word_match.first()
                
                page = pages.first()
                log.info(f"Matched by path pattern: {path}")
                return page
                
        # No match found
        return None 