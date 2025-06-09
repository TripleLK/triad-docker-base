"""
Management command to generate AI-ready JSON for content extraction pipeline.

Combines scraped content from site URLs with stored XPath configurations
to create comprehensive JSON data for AI processing.

Created by: Cosmic Forge
Date: 2025-01-22
Project: Triad Docker Base - AI JSON Generation System
"""

import json
import hashlib
import re
import time
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.content_extractor.models import SiteConfiguration, SiteURL, FieldConfiguration, AIJSONRecord
import requests
from lxml import html, etree


class Command(BaseCommand):
    help = 'Generate AI-ready JSON for site URLs using stored XPath configurations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            type=str,
            help='Process URLs for specific domain only'
        )
        parser.add_argument(
            '--url-id',
            type=int,
            help='Process specific URL by ID'
        )
        parser.add_argument(
            '--all-sites',
            action='store_true',
            help='Process all active sites'
        )
        parser.add_argument(
            '--force-refresh',
            action='store_true',
            help='Regenerate JSON even if already exists'
        )

    def handle(self, *args, **options):
        start_time = time.time()
        
        if options['url_id']:
            # Process single URL
            urls_to_process = SiteURL.objects.filter(id=options['url_id'])
            if not urls_to_process.exists():
                raise CommandError(f"URL with ID {options['url_id']} not found")
                
        elif options['domain']:
            # Process URLs for specific domain
            try:
                site_config = SiteConfiguration.objects.get(site_domain=options['domain'])
                urls_to_process = site_config.urls.filter(status='active')
            except SiteConfiguration.DoesNotExist:
                raise CommandError(f"Site configuration for domain '{options['domain']}' not found")
                
        elif options['all_sites']:
            # Process all active URLs from all active sites
            urls_to_process = SiteURL.objects.filter(
                status='active',
                site_config__is_active=True
            )
        else:
            raise CommandError("Must specify --domain, --url-id, or --all-sites")

        if not urls_to_process.exists():
            self.stdout.write(self.style.WARNING("No URLs found to process"))
            return

        total_urls = urls_to_process.count()
        self.stdout.write(f"Processing {total_urls} URLs...")

        success_count = 0
        error_count = 0

        for site_url in urls_to_process:
            try:
                # Check if we should skip (already processed and not forcing refresh)
                if not options['force_refresh'] and self.is_already_processed(site_url):
                    self.stdout.write(f"Skipping {site_url.url} (already processed)")
                    continue

                self.stdout.write(f"Processing: {site_url.url}")
                
                # Mark as processing
                site_url.mark_processing()
                
                # Generate AI JSON
                ai_json = self.generate_ai_json_for_url(site_url)
                
                # Save the record
                self.save_ai_json_record(site_url, ai_json)
                
                # Mark as completed
                site_url.mark_completed()
                
                success_count += 1
                self.stdout.write(self.style.SUCCESS(f"✓ Completed: {site_url.url}"))
                
            except Exception as e:
                error_count += 1
                error_message = str(e)
                site_url.mark_failed(error_message)
                self.stdout.write(self.style.ERROR(f"✗ Failed: {site_url.url} - {error_message}"))

        # Summary
        total_time = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(
            f"\nCompleted processing {total_urls} URLs in {total_time:.2f} seconds"
        ))
        self.stdout.write(f"Success: {success_count}, Errors: {error_count}")

    def is_already_processed(self, site_url):
        """Check if URL already has current AI JSON record."""
        return site_url.ai_json_records.filter(is_current=True).exists()

    def clean_html_content(self, html_text):
        """Clean HTML content by removing JavaScript, CSS, and normalizing whitespace."""
        # Remove script tags and their content
        html_text = re.sub(r'<script[^>]*>.*?</script>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove style tags and their content
        html_text = re.sub(r'<style[^>]*>.*?</style>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove inline style attributes
        html_text = re.sub(r'style\s*=\s*["\'][^"\']*["\']', '', html_text, flags=re.IGNORECASE)
        
        # Remove JavaScript event attributes (onclick, onload, etc.)
        html_text = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', html_text, flags=re.IGNORECASE)
        
        # Normalize whitespace: replace \r\n\t with spaces and collapse multiple spaces
        html_text = re.sub(r'[\r\n\t]+', ' ', html_text)
        html_text = re.sub(r'\s+', ' ', html_text)
        
        # Trim leading/trailing whitespace
        html_text = html_text.strip()
        
        return html_text

    def organize_field_configurations(self, field_configs, scraped_html=None):
        """Organize field configurations with flat structure using actual model field names."""
        organized_configs = {}
        
        # Parse HTML for content extraction if provided
        html_tree = None
        if scraped_html:
            try:
                html_tree = html.fromstring(scraped_html)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"HTML parsing failed: {str(e)}"))
        
        for field_config in field_configs:
            field_name = field_config.lab_equipment_field
            
            # Build field configuration with content extraction (flat structure)
            field_config_data = {
                'xpath_selectors': field_config.xpath_selectors,
                'comment': field_config.comment,
                'field_type': self.determine_field_type(field_name),
                'is_active': field_config.is_active
            }
            
            # Extract content if HTML is available
            if html_tree is not None and field_config.xpath_selectors:
                content_extraction = self.extract_content_for_selectors(
                    html_tree, field_config.xpath_selectors, field_name
                )
                field_config_data.update(content_extraction)
            
            # Use actual field name directly (no artificial categories)
            organized_configs[field_name] = field_config_data
        
        return organized_configs

    def extract_content_for_selectors(self, html_tree, xpath_selectors, field_name):
        """Extract content and attributes using XPath selectors and return extraction results."""
        extraction_results = {
            'extracted_content': [],
            'extraction_summary': {
                'total_selectors': len(xpath_selectors),
                'successful_extractions': 0,
                'failed_extractions': 0,
                'extraction_errors': []
            }
        }
        
        for i, xpath_selector in enumerate(xpath_selectors):
            try:
                # Apply XPath selector to HTML
                elements = html_tree.xpath(xpath_selector)
                
                if elements:
                    # Extract text content and attributes from matched elements
                    extracted_data = []
                    for element in elements[:5]:  # Limit to first 5 matches for preview
                        try:
                            # Extract text content
                            text_content = ""
                            if hasattr(element, 'text_content'):
                                text_content = element.text_content().strip()
                            elif isinstance(element, str):
                                text_content = element.strip()
                            else:
                                text_content = str(element).strip()
                            
                            # Extract element attributes
                            attributes = {}
                            if hasattr(element, 'tag') and hasattr(element, 'get'):
                                # Image attributes
                                if element.tag == 'img':
                                    if element.get('src'):
                                        attributes['src'] = element.get('src')
                                    if element.get('alt'):
                                        attributes['alt'] = element.get('alt')
                                    if element.get('title'):
                                        attributes['title'] = element.get('title')
                                
                                # Link attributes
                                elif element.tag == 'a':
                                    if element.get('href'):
                                        attributes['href'] = element.get('href')
                                    if element.get('title'):
                                        attributes['title'] = element.get('title')
                                
                                # Input attributes
                                elif element.tag == 'input':
                                    if element.get('value'):
                                        attributes['value'] = element.get('value')
                                    if element.get('placeholder'):
                                        attributes['placeholder'] = element.get('placeholder')
                                
                                # Data attributes (for JavaScript-driven content)
                                for attr in element.attrib:
                                    if attr.startswith('data-'):
                                        attributes[attr] = element.get(attr)
                            
                            # Include data if there's text content OR attributes
                            if text_content or attributes:
                                extracted_item = {}
                                if text_content:
                                    extracted_item['text'] = text_content
                                if attributes:
                                    extracted_item['attributes'] = attributes
                                extracted_data.append(extracted_item)
                                
                        except Exception as e:
                            extraction_results['extraction_summary']['extraction_errors'].append({
                                'selector_index': i,
                                'xpath': xpath_selector,
                                'error': f"Content extraction error: {str(e)}"
                            })
                    
                    if extracted_data:
                        extraction_results['extracted_content'].append({
                            'selector_index': i,
                            'xpath': xpath_selector,
                            'match_count': len(elements),
                            'extracted_data': extracted_data,
                            'preview_note': f"Showing first {len(extracted_data)} of {len(elements)} matches" if len(elements) > len(extracted_data) else "All matches shown"
                        })
                        extraction_results['extraction_summary']['successful_extractions'] += 1
                    else:
                        extraction_results['extracted_content'].append({
                            'selector_index': i,
                            'xpath': xpath_selector,
                            'match_count': len(elements),
                            'extracted_data': [],
                            'extraction_note': "Elements found but no content or attributes extracted"
                        })
                        extraction_results['extraction_summary']['failed_extractions'] += 1
                else:
                    # No matches found
                    extraction_results['extracted_content'].append({
                        'selector_index': i,
                        'xpath': xpath_selector,
                        'match_count': 0,
                        'extracted_data': [],
                        'extraction_note': "No elements matched this XPath selector"
                    })
                    extraction_results['extraction_summary']['failed_extractions'] += 1
                    
            except Exception as e:
                # XPath execution error
                extraction_results['extraction_summary']['failed_extractions'] += 1
                extraction_results['extraction_summary']['extraction_errors'].append({
                    'selector_index': i,
                    'xpath': xpath_selector,
                    'error': f"XPath execution error: {str(e)}"
                })
                extraction_results['extracted_content'].append({
                    'selector_index': i,
                    'xpath': xpath_selector,
                    'match_count': 0,
                    'extracted_data': [],
                    'extraction_note': f"XPath error: {str(e)}"
                })
        
        return extraction_results

    def generate_ai_json_for_url(self, site_url):
        """Generate complete AI-ready JSON for a single URL with simplified structure."""
        # Scrape content
        scraped_content = self.scrape_url_content(site_url.url)
        
        # Get XPath configurations for this site
        field_configs = site_url.site_config.field_configs.filter(is_active=True)
        
        # Organize field configurations with flat structure and content extraction
        field_configurations = self.organize_field_configurations(field_configs, scraped_content['html'])
        
        # Calculate extraction statistics
        extraction_stats = self.calculate_extraction_statistics(field_configurations)
        
        # Assemble simplified JSON structure (no redundant scraped_content)
        ai_json = {
            'url': site_url.url,
            'site_domain': site_url.site_config.site_domain,
            'site_name': site_url.site_config.site_name,
            'field_configurations': field_configurations,
            'processing_metadata': {
                'timestamp': timezone.now().isoformat(),
                'status': 'ready_for_ai_with_content_mapping',
                'total_field_count': len(field_configurations),
                'content_length': len(scraped_content.get('html', '')) if scraped_content else 0,
                'extraction_statistics': extraction_stats
            }
        }
        
        return ai_json

    def calculate_extraction_statistics(self, field_configurations):
        """Calculate overall extraction statistics from flat field configurations."""
        total_fields = 0
        total_selectors = 0
        total_successful_extractions = 0
        total_failed_extractions = 0
        fields_with_content = 0
        
        for field_name, field_data in field_configurations.items():
            total_fields += 1
            
            if 'extraction_summary' in field_data:
                summary = field_data['extraction_summary']
                total_selectors += summary['total_selectors']
                total_successful_extractions += summary['successful_extractions']
                total_failed_extractions += summary['failed_extractions']
                
                if summary['successful_extractions'] > 0:
                    fields_with_content += 1
        
        success_rate = (total_successful_extractions / total_selectors * 100) if total_selectors > 0 else 0
        
        return {
            'total_fields_configured': total_fields,
            'total_xpath_selectors': total_selectors,
            'successful_extractions': total_successful_extractions,
            'failed_extractions': total_failed_extractions,
            'fields_with_extracted_content': fields_with_content,
            'extraction_success_rate_percent': round(success_rate, 1),
            'content_mapping_status': 'complete' if total_successful_extractions > 0 else 'no_content_extracted'
        }

    def scrape_url_content(self, url):
        """Scrape HTML content from the given URL."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Triad Content Extractor)'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Clean the HTML content
            cleaned_html = self.clean_html_content(response.text)
            
            # Parse and extract page title
            try:
                tree = html.fromstring(response.content)
                title_elements = tree.xpath('//title/text()')
                page_title = title_elements[0].strip() if title_elements else ""
            except:
                page_title = ""
            
            # Return cleaned HTML content
            return {
                'html': cleaned_html,
                'page_title': page_title,
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type', ''),
                'scraped_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Failed to scrape URL content: {str(e)}")

    def determine_field_type(self, field_name):
        """Determine if field should be single or multi-value based on field name."""
        multi_value_fields = ['features', 'accessories', 'models', 'gallery_images', 'spec_groups', 'options', 'applications']
        return 'multi-value' if field_name in multi_value_fields else 'single'

    def save_ai_json_record(self, site_url, ai_json):
        """Save the generated AI JSON as a record."""
        # Calculate content hash for change detection
        content_hash = hashlib.sha256(
            json.dumps(ai_json['field_configurations'], sort_keys=True).encode()
        ).hexdigest()
        
        # Mark previous records as outdated
        site_url.ai_json_records.filter(is_current=True).update(is_current=False)
        
        # Create new record
        AIJSONRecord.objects.create(
            site_url=site_url,
            json_data=ai_json,
            content_hash=content_hash,
            is_current=True
        )
        
        # Page title is handled separately in scraping, not from extracted fields 