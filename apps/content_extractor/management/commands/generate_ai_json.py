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

    def organize_field_configurations(self, field_configs):
        """Organize field configurations by equipment/product groupings."""
        organized_configs = {}
        
        for field_config in field_configs:
            field_name = field_config.lab_equipment_field
            
            # Determine equipment category from field name
            equipment_type = self.get_equipment_type_from_field(field_name)
            
            if equipment_type not in organized_configs:
                organized_configs[equipment_type] = {
                    'equipment_type': equipment_type,
                    'extraction_fields': {}
                }
            
            organized_configs[equipment_type]['extraction_fields'][field_name] = {
                'xpath_selectors': field_config.xpath_selectors,
                'comment': field_config.comment,
                'field_type': self.determine_field_type(field_name),
                'is_active': field_config.is_active
            }
        
        return organized_configs

    def get_equipment_type_from_field(self, field_name):
        """Determine equipment type category from field name."""
        # Map field names to equipment categories
        field_to_equipment = {
            'product_name': 'general_info',
            'product_description': 'general_info',
            'model_number': 'general_info',
            'part_number': 'general_info',
            'price': 'general_info',
            'features': 'features_specs',
            'specifications': 'features_specs',
            'dimensions': 'features_specs',
            'weight': 'features_specs',
            'accessories': 'accessories_options',
            'options': 'accessories_options',
            'gallery_images': 'media_content',
            'brochure_link': 'media_content',
            'video_link': 'media_content',
            'applications': 'applications_uses',
            'industry_applications': 'applications_uses',
            'models': 'model_variations',
            'spec_groups': 'detailed_specifications'
        }
        
        return field_to_equipment.get(field_name, 'other_fields')

    def generate_ai_json_for_url(self, site_url):
        """Generate complete AI-ready JSON for a single URL."""
        # Scrape content
        scraped_content = self.scrape_url_content(site_url.url)
        
        # Get XPath configurations for this site
        field_configs = site_url.site_config.field_configs.filter(is_active=True)
        
        # Organize field configurations by equipment type
        organized_extraction_config = self.organize_field_configurations(field_configs)
        
        # Assemble complete JSON
        ai_json = {
            'url': site_url.url,
            'site_domain': site_url.site_config.site_domain,
            'site_name': site_url.site_config.site_name,
            'scraped_content': scraped_content,
            'field_configurations': organized_extraction_config,
            'processing_metadata': {
                'timestamp': timezone.now().isoformat(),
                'status': 'ready_for_ai',
                'equipment_categories': len(organized_extraction_config),
                'total_field_count': sum(len(config['extraction_fields']) for config in organized_extraction_config.values()),
                'content_length': len(scraped_content.get('html', '')) if scraped_content else 0
            }
        }
        
        return ai_json

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
            json.dumps(ai_json['scraped_content'], sort_keys=True).encode()
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
        
        # Update page title if scraped
        if ai_json['scraped_content'].get('page_title'):
            site_url.page_title = ai_json['scraped_content']['page_title']
            site_url.save(update_fields=['page_title']) 