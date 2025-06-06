#!/usr/bin/env python3
import logging
import sys
import requests
import re
import time
import traceback
import os
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
import json

from apps.scrapers.selectors.base import Selector, Selected, SelectedType
from apps.scrapers.utils.image_downloader import ImageDownloader
from apps.scrapers.utils.api_client import LabEquipmentAPIClient

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import AirScience product data using the API instead of Django ORM'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default="https://www.airscience.com/product-category-page?brandname=purair-advanced-ductless-fume-hoods&brand=9",
            help='URL to scrape (default: Purair Advanced Ductless Fume Hoods)'
        )
        # API configuration
        parser.add_argument(
            '--api-base-url',
            type=str,
            help='Base URL for the API (default: from environment or localhost:8000)'
        )
        parser.add_argument(
            '--api-token',
            type=str,
            help='API token for authentication (default: from environment)'
        )
        parser.add_argument(
            '--skip-images',
            action='store_true',
            help='Skip downloading images'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a dry run without committing changes'
        )
        # New tagging arguments
        parser.add_argument(
            '--process-tags',
            action='store_true',
            help='Process tags after importing data'
        )
        parser.add_argument(
            '--categories-only',
            action='store_true',
            help='Only process product categories when processing tags'
        )
        parser.add_argument(
            '--applications-only',
            action='store_true',
            help='Only process product applications when processing tags'
        )
        parser.add_argument(
            '--tags-only',
            action='store_true',
            help='Only process tags, no import'
        )

    def handle(self, *args, **options):
        url = options['url']
        skip_images = options['skip_images']
        dry_run = options['dry_run']
        verbosity = options.get('verbosity', 1)
        process_tags = options['process_tags']
        categories_only = options['categories_only']
        applications_only = options['applications_only']
        tags_only = options['tags_only']

        # Initialize the API client
        self.api_client = LabEquipmentAPIClient(
            base_url=options['api_base_url'],
            api_token=options['api_token']
        )

        if dry_run:
            self.stdout.write("Performing dry run - no changes will be committed")

        # Load category and application tag mappings
        self.category_tags = self._load_tag_mappings("apps/scrapers/airscience-yamls/categories.yaml")
        self.application_tags = self._load_tag_mappings("apps/scrapers/airscience-yamls/applications.yaml")
            
        # Handle import if not tags-only mode
        if not tags_only:
            # Fetch the URL content
            self.stdout.write(f"Fetching content from {url}")
            response = requests.get(url)
            if response.status_code != 200:
                self.stderr.write(f"Failed to fetch URL: {response.status_code}")
                return

            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Create a Selected object with the parsed HTML
            page_selected = Selected(soup, SelectedType.SINGLE)
            
            # Load the mapping selector
            mapping_selector = Selector.fromFilePath("apps/scrapers/airscience-yamls/mapping.yaml")
            
            # Apply the mapping selector to extract data
            try:
                result = mapping_selector(page_selected)
                
                if result.selected_type == SelectedType.VALUE and isinstance(result.value, dict):
                    extracted_data = result.value
                    
                    # Process the extracted data
                    product_name = extracted_data.get('name', 'Unknown Product')
                    short_description = extracted_data.get('short_description', '')
                    full_description = extracted_data.get('full_description', '')
                    models_data = extracted_data.get('models', {})
                    images_data = extracted_data.get('imgs', [])
                    
                    self.stdout.write(f"Found product: {product_name}")
                    self.stdout.write(f"Number of models: {len(models_data)}")
                    self.stdout.write(f"Number of images: {len(images_data)}")
                    
                    # If verbosity is high, print more details
                    if verbosity > 1:
                        self._print_detailed_info(product_name, models_data, images_data)
                    
                    # Process the data and send to API
                    if not dry_run:
                        self.send_to_api(
                            product_name, 
                            short_description, 
                            full_description, 
                            models_data,
                            images_data,
                            skip_images,
                            url
                        )
                    else:
                        self.stdout.write("Dry run complete - data was not sent to API")
                else:
                    self.stderr.write(f"Unexpected result type: {result.selected_type}")
                    
            except Exception as e:
                self.stderr.write(f"Error during extraction: {e}")
                if verbosity > 1:
                    self.stderr.write(traceback.format_exc())

        # Process tags if requested
        if process_tags:
            self.process_tags(categories_only, applications_only, dry_run)

    def _print_detailed_info(self, product_name, models_data, images_data):
        """Print detailed information about models and images"""
        self.stdout.write("\nModel details:")
        for model_name, model_specs in models_data.items():
            self.stdout.write(f"\n  Model: {model_name}")
            
            # Print sections and specs
            for section in model_specs:
                if isinstance(section, dict):
                    section_title = section.get('section_title', 'Specifications')
                    self.stdout.write(f"    Section: {section_title}")
                    
                    # Print specs
                    if 'vals' in section and isinstance(section['vals'], list):
                        for spec_array in section['vals']:
                            if isinstance(spec_array, list):
                                for spec_data in spec_array:
                                    if isinstance(spec_data, dict) and 'spec_name' in spec_data and 'spec_value' in spec_data:
                                        spec_name = spec_data['spec_name']
                                        spec_value = spec_data['spec_value']
                                        
                                        # Skip specs where both name and value are None/empty or just "None"
                                        if (spec_name is None or spec_name.strip() == "" or spec_name.lower() == "none") and \
                                           (spec_value is None or spec_value.strip() == "" or spec_value.lower() == "none"):
                                            continue
                                        
                                        self.stdout.write(f"      {spec_name}: {spec_value}")
        
        # Print image URLs
        if images_data:
            self.stdout.write("\nImage URLs:")
            for i, url in enumerate(images_data):
                self.stdout.write(f"  Image {i+1}: {url}")

    def send_to_api(self, product_name, short_description, full_description, 
                   models_data, images_data, skip_images, source_url=None):
        """
        Prepare and send data to the API
        """
        try:
            # Generate a slug from the product name
            slug = self._generate_slug(product_name)
            
            # Prepare the API data
            api_data = {
                'title': product_name,
                'short_description': short_description,
                'full_description': full_description,
                'source_url': source_url,
                'slug': slug
            }
            
            # Process tags
            tags = []
            
            # Add manufacturer tag
            tags.append("Manufacturer: Air Science")
            
            # Extract product category from URL
            category = self._extract_category(source_url, product_name)
            if category:
                # Get the standardized tag from our mappings if available
                standardized_category = None
                # Check if the category is directly in the mapping
                if category in self.category_tags:
                    standardized_category = self.category_tags[category]
                else:
                    # Try to match by checking if category is in any key
                    for key, value in self.category_tags.items():
                        if category.lower() in key.lower():
                            standardized_category = value
                            break
                
                if standardized_category:
                    tags.append(f"Product Category: {standardized_category}")
                else:
                    # Use the raw category as a fallback
                    tags.append(f"Product Category: {category}")
            
            # Extract applications from product description
            applications = self._extract_applications(product_name, short_description, full_description)
            for app in applications:
                tags.append(f"Product Application: {app}")
                
            # Add tags to API data
            if tags:
                api_data['tags'] = tags
            
            # Process models data for API
            if models_data:
                api_data['models'] = []
                for model_name, specs_data in models_data.items():
                    model_info = {
                        'name': model_name,
                        'specifications': self._process_specs_for_api(specs_data)
                    }
                    api_data['models'].append(model_info)
            
            # Process images for API if not skipping
            if not skip_images and images_data:
                api_data['images'] = images_data
            
            # Send to API
            self.stdout.write(f"Sending {product_name} to API...")
            response = self.api_client.create_or_update_lab_equipment(api_data)
            
            if response.get('success', False):
                self.stdout.write(f"Successfully {response.get('message', 'processed')} with ID: {response.get('page_id')}")
            else:
                self.stderr.write(f"API error: {response.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.stderr.write(f"Error sending data to API: {str(e)}")
            raise

    def _process_specs_for_api(self, specs_data):
        """Process specification data for the API format"""
        api_specs = []
        
        for section in specs_data:
            if isinstance(section, dict) and 'section_title' in section and 'vals' in section:
                section_title = section['section_title']
                spec_group = {
                    'group_name': section_title,
                    'specs': []
                }
                
                # Process specs in this section
                if 'vals' in section and isinstance(section['vals'], list):
                    for spec_array in section['vals']:
                        if isinstance(spec_array, list):
                            for spec_data in spec_array:
                                if isinstance(spec_data, dict) and 'spec_name' in spec_data and 'spec_value' in spec_data:
                                    spec_name = spec_data['spec_name']
                                    spec_value = spec_data['spec_value']
                                    
                                    # Skip empty specs
                                    if not spec_name or not spec_value:
                                        continue
                                        
                                    # Skip specs where both name and value are None/empty or just "None"
                                    if (spec_name is None or spec_name.strip() == "" or spec_name.lower() == "none") and \
                                       (spec_value is None or spec_value.strip() == "" or spec_value.lower() == "none"):
                                        continue
                                    
                                    # Clean up spec name (remove trailing colons)
                                    if spec_name:
                                        spec_name = spec_name.rstrip(':')
                                    
                                    # Clean up spec value
                                    if spec_value and isinstance(spec_value, str):
                                        # Special handling for Monitoring Options field
                                        if spec_name == "Monitoring Options" and "/" in spec_value:
                                            # Clean up the multiple slashes with spaces
                                            spec_value = "Standard" if "Standard" in spec_value else spec_value
                                            spec_value = spec_value.replace('/ /', '')
                                            spec_value = spec_value.replace('/', '')
                                        spec_value = spec_value.strip()
                                    
                                    spec_group['specs'].append({
                                        'name': spec_name,
                                        'value': spec_value
                                    })
                
                # Only add groups with specs
                if spec_group['specs']:
                    api_specs.append(spec_group)
                    
        return api_specs

    def _generate_slug(self, title):
        """Generate a slug from a title"""
        # Convert to lowercase, replace spaces with hyphens
        slug = title.lower().replace(' ', '-')
        # Remove special characters
        slug = re.sub(r'[^a-z0-9-]', '', slug)
        # Remove duplicate hyphens
        slug = re.sub(r'-+', '-', slug)
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        return slug

    def _extract_category(self, url, product_name):
        """Extract product category from URL or product name"""
        # Try to extract from URL query parameters like brandname=purair-advanced-ductless-fume-hoods
        if url:
            match = re.search(r'brandname=([^&]+)', url)
            if match:
                category = match.group(1).replace('-', ' ').title()
                return category
                
            # Try to extract from URL path
            match = re.search(r'/([^/?&]+)$', url)
            if match:
                category = match.group(1).replace('-', ' ').title()
                return category
        
        # Fallback to product name
        if product_name:
            # Extract the first part before any specific model numbers
            parts = re.split(r'[\d-]', product_name, 1)
            if parts:
                category = parts[0].strip()
                if len(category) > 3:  # Avoid very short category names
                    return category
                    
        return None

    def _extract_applications(self, product_name, short_description, full_description):
        """Extract applications from product descriptions"""
        applications = []
        
        # Combine all text for analysis
        combined_text = f"{product_name} {short_description} {full_description}".lower()
        
        # Check for applications in our mapping
        for key, value in self.application_tags.items():
            # Convert application key to a searchable term
            search_term = key.replace('-', ' ').replace('products-for-', '').lower()
            
            # Check if the search term is in our combined text
            if search_term in combined_text:
                applications.append(value)
        
        # We could add more specific keyword detection here if needed
        application_keywords = {
            'animal': 'Animal Research',
            'cannabis': 'Cannabis & Botanicals',
            'botanical': 'Cannabis & Botanicals',
            'brew': 'Craft Beverages',
            'farm': 'Farming & Agriculture',
            'agriculture': 'Farming & Agriculture',
            'forensic': 'Forensic',
            'crime': 'Forensic',
            'science': 'Life Science',
            'biology': 'Life Science',
            'pharmaceutical': 'Pharmaceutical',
            'pharma': 'Pharmaceutical',
            'medicine': 'Pharmaceutical',
            'lab': 'Laboratory Research'
        }
        
        for keyword, application in application_keywords.items():
            if keyword in combined_text:
                applications.append(application)
        
        # Remove duplicates
        return list(set(applications))

    def process_tags(self, categories_only, applications_only, dry_run):
        """Process tags from YAML files"""
        self.stdout.write("Processing tags...")
        
        if not categories_only and not applications_only:
            self.process_tag_file("apps/scrapers/airscience-yamls/categories.yaml", dry_run)
            self.process_tag_file("apps/scrapers/airscience-yamls/applications.yaml", dry_run)
        elif categories_only:
            self.process_tag_file("apps/scrapers/airscience-yamls/categories.yaml", dry_run)
        elif applications_only:
            self.process_tag_file("apps/scrapers/airscience-yamls/applications.yaml", dry_run)
            
        self.stdout.write("Tag processing complete")

    def process_tag_file(self, yaml_file, dry_run):
        """Process tags from a single YAML file"""
        try:
            selector = Selector.fromFilePath(yaml_file)
            tag_data = selector(Selected(None, SelectedType.SINGLE)).value
            
            self.stdout.write(f"Processing tags from {yaml_file}: {len(tag_data)} tags found")
            
            # In a real implementation, you would send these tags to the API
            # For now, just log them
            if not dry_run:
                self.stdout.write("Would create/update the following tags:")
                for tag in tag_data:
                    self.stdout.write(f"  - {tag}")
            
        except Exception as e:
            self.stderr.write(f"Error processing tag file {yaml_file}: {str(e)}")

    def _load_tag_mappings(self, yaml_file):
        """Load tag mappings from a YAML file"""
        try:
            selector = Selector.fromFilePath(yaml_file)
            tag_data = selector(Selected(None, SelectedType.SINGLE)).value
            
            self.stdout.write(f"Loaded {len(tag_data)} tags from {yaml_file}")
            
            return tag_data
        except Exception as e:
            self.stderr.write(f"Error loading tag mappings from {yaml_file}: {str(e)}")
            return {} 