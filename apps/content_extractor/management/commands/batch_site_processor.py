"""
Batch Site Processor - Automated Website Processing with Selector-Based Filtering

This command implements comprehensive website crawling and batch JSON generation
using existing XPath selectors as relevance filters. Only pages that pass the
selector success rate threshold are processed for AI JSON generation.

Created by: Quantum Ridge
Date: 2025-01-22
Project: Triad Docker Base - Batch Site Processing System
"""

import os
import sys
import time
import json
import logging
import hashlib
import math
import re
from datetime import datetime
from urllib.parse import urlparse, urljoin, urlunparse
from typing import List, Dict, Tuple, Optional

import requests
from bs4 import BeautifulSoup
from lxml import html, etree
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone

# Import existing models and utilities
from apps.content_extractor.models import SiteConfiguration, FieldConfiguration, SiteURL, AIJSONRecord
from apps.content_extractor.management.commands.generate_ai_json import Command as AIJSONCommand

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process websites with selector-based relevance filtering and batch AI JSON generation'

    def add_arguments(self, parser):
        parser.add_argument(
            'domain',
            type=str,
            help='Domain to process (e.g., airscience.com)'
        )
        parser.add_argument(
            '--threshold',
            type=float,
            default=0.9,
            help='Minimum selector success rate threshold (0.0-1.0, default: 0.9)'
        )
        parser.add_argument(
            '--max-pages',
            type=int,
            default=50,
            help='Maximum number of pages to crawl (default: 50)'
        )
        parser.add_argument(
            '--max-depth',
            type=int,
            default=3,
            help='Maximum crawl depth (default: 3)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only test selectors, do not generate AI JSON files'
        )
        parser.add_argument(
            '--test-selectors-only',
            action='store_true',
            help='Only test selectors on known URLs, skip crawling'
        )
        parser.add_argument(
            '--upload-to-s3',
            action='store_true',
            help='Upload generated files to S3'
        )
        parser.add_argument(
            '--s3-bucket',
            type=str,
            help='S3 bucket name (auto-generated if not provided)'
        )
        parser.add_argument(
            '--s3-prefix',
            type=str,
            default='batch-processing',
            help='S3 key prefix for organizing files (default: batch-processing)'
        )
        parser.add_argument(
            '--bedrock-format',
            action='store_true',
            help='Convert JSON files to Bedrock JSONL format'
        )
        parser.add_argument(
            '--delete-local',
            action='store_true',
            help='Delete local files after successful S3 upload'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='batch_processing_output',
            help='Output directory for generated files (default: batch_processing_output)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
        parser.add_argument(
            '--start-url',
            type=str,
            help='Custom starting URL for crawling (instead of domain root)'
        )
        parser.add_argument(
            '--product-page-pattern',
            type=str,
            default='product-category-page',
            help='Pattern to identify product pages (default: product-category-page)'
        )
        parser.add_argument(
            '--bedrock-prompt-arn',
            type=str,
            help='Bedrock prompt ARN for batch inference (uses default if not provided)'
        )

    def handle(self, *args, **options):
        """Main command handler"""
        self.domain = options['domain']
        self.threshold = options['threshold']
        self.max_pages = options['max_pages']
        self.max_depth = options['max_depth']
        self.dry_run = options['dry_run']
        self.test_selectors_only = options['test_selectors_only']
        self.upload_to_s3 = options['upload_to_s3']
        self.s3_bucket = options['s3_bucket']
        self.s3_prefix = options['s3_prefix']
        self.bedrock_format = options['bedrock_format']
        self.delete_local = options['delete_local']
        self.output_dir = options['output_dir']
        self.verbose = options['verbose']
        self.start_url = options['start_url']
        self.product_page_pattern = options['product_page_pattern']
        self.bedrock_prompt_arn = options['bedrock_prompt_arn']
        
        # Derived settings
        self.max_product_pages = self.max_pages  # Use user's max_pages setting directly
        
        # Initialize AI JSON command for reuse
        self.ai_json_command = AIJSONCommand()
        
        self.stdout.write(f"🚀 Starting batch site processing for: {self.domain}")
        self.stdout.write(f"📊 Threshold: {self.threshold:.1%}, Max pages: {self.max_pages}, Max depth: {self.max_depth}")
        
        if self.dry_run:
            self.stdout.write("🧪 DRY RUN MODE - No files will be generated")
        
        if self.test_selectors_only:
            self.stdout.write("🔍 SELECTOR TEST MODE - Only testing selectors on known URLs")
        
        if self.upload_to_s3:
            self.stdout.write("☁️  S3 UPLOAD MODE - Files will be uploaded to S3")
            if self.bedrock_format:
                self.stdout.write("🔄 BEDROCK FORMAT - JSON files will be converted to JSONL")
            if self.delete_local:
                self.stdout.write("🗑️  DELETE LOCAL - Local files will be deleted after upload")
        
        try:
            # Step 1: Load site configuration
            site_config, field_configs = self.load_site_configuration()
            
            if self.test_selectors_only:
                # Test selectors on known URLs only
                self.test_selectors_on_known_urls(site_config, field_configs)
                return
            
            # Step 2: Crawl website to discover URLs
            discovered_urls = self.crawl_site()
            
            if not discovered_urls:
                self.stdout.write("❌ No URLs discovered during crawling")
                return
            
            # Step 3: Filter to product pages if pattern specified
            if self.product_page_pattern:
                product_urls = self.filter_to_product_pages(discovered_urls)
                if not product_urls:
                    self.stdout.write(f"❌ No product pages found matching pattern: {self.product_page_pattern}")
                    return
                urls_to_process = product_urls
            else:
                urls_to_process = discovered_urls
            
            # Step 4: Filter URLs by selector success rate
            qualifying_urls = self.filter_urls_by_selector_success(urls_to_process, field_configs)
            
            if not qualifying_urls:
                self.stdout.write(f"❌ No URLs meet the {self.threshold:.1%} selector success threshold")
                return
            
            if self.dry_run:
                self.stdout.write(f"🧪 DRY RUN: Would process {len(qualifying_urls)} qualifying URLs")
                return
            
            # Step 5: Generate AI JSON for qualifying URLs
            generated_files = self.generate_ai_json_batch(qualifying_urls, site_config)
            
            if not generated_files:
                self.stdout.write("❌ No AI JSON files were generated")
                return
            
            # Step 6: Create batch manifest
            manifest_path = self.create_batch_manifest(generated_files)
            
            # Step 7: Upload to S3 if requested
            if self.upload_to_s3:
                self.upload_batch_to_s3(generated_files + [manifest_path])
            
            self.stdout.write(f"✅ Batch processing complete! Generated {len(generated_files)} files")
            
        except Exception as e:
            logger.error(f"Batch processing failed: {str(e)}")
            self.stdout.write(f"❌ Batch processing failed: {str(e)}")
            raise

    def load_site_configuration(self) -> Tuple[SiteConfiguration, List[FieldConfiguration]]:
        """Load site configuration and field configurations from database"""
        try:
            site_config = SiteConfiguration.objects.get(
                site_domain=self.domain,
                is_active=True
            )
            
            field_configs = list(site_config.field_configs.filter(is_active=True))
            
            self.stdout.write(f"📋 Loaded configuration for {site_config.site_name}")
            self.stdout.write(f"🔧 Found {len(field_configs)} active field configurations:")
            
            for config in field_configs:
                xpath_count = len(config.xpath_selectors) if config.xpath_selectors else 0
                self.stdout.write(f"  - {config.lab_equipment_field}: {xpath_count} XPath selectors")
            
            return site_config, field_configs
            
        except SiteConfiguration.DoesNotExist:
            raise Exception(f"No active site configuration found for domain: {self.domain}")

    def crawl_site(self) -> List[str]:
        """Crawl the website to discover URLs using breadth-first search"""
        if self.start_url:
            start_url = self.start_url
            self.stdout.write(f"🌐 Starting crawl from custom URL: {start_url}")
        else:
            start_url = f"https://{self.domain}"
            self.stdout.write(f"🌐 Starting crawl from domain root: {start_url}")
        
        visited = set()
        discovered_urls = set()  # Track ALL discovered URLs
        to_visit = [(start_url, 0)]  # (url, depth)
        
        while to_visit and len(visited) < self.max_pages:
            current_url, depth = to_visit.pop(0)
            
            if current_url in visited or depth > self.max_depth:
                continue
            
            try:
                self.stdout.write(f"🔍 Crawling [{len(visited)+1}/{self.max_pages}] depth {depth}: {current_url}")
                
                # Extract links from current page
                found_links = self.extract_links_from_page(current_url, self.domain)
                
                # Add current URL to visited and discovered
                visited.add(current_url)
                discovered_urls.add(current_url)
                
                # Add found links to discovered URLs and to_visit queue
                for link in found_links:
                    discovered_urls.add(link)  # Track all discovered links
                    if link not in visited and depth < self.max_depth:
                        to_visit.append((link, depth + 1))
                
                if self.verbose:
                    self.stdout.write(f"  📄 Found {len(found_links)} links on this page")
                
            except Exception as e:
                logger.warning(f"Failed to crawl {current_url}: {str(e)}")
                continue
        
        discovered_list = list(discovered_urls)
        self.stdout.write(f"🎯 Crawling complete: Visited {len(visited)} pages, discovered {len(discovered_list)} total URLs")
        
        return discovered_list

    def normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments but preserving query parameters"""
        parsed = urlparse(url)
        # Remove fragment but keep query parameters (essential for product pages)
        normalized = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, ''))
        return normalized

    def extract_links_from_page(self, url: str, domain_for_filtering: str) -> List[str]:
        """Extract all links from a page, filtered by domain"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Triad Content Extractor)'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            tree = html.fromstring(response.content)
            links = tree.xpath('//a/@href')
            
            valid_links = []
            for link in links:
                try:
                    # Convert relative URLs to absolute
                    absolute_url = urljoin(url, link)
                    
                    # Filter by domain
                    parsed = urlparse(absolute_url)
                    if parsed.netloc.endswith(domain_for_filtering):
                        normalized_url = self.normalize_url(absolute_url)
                        if normalized_url not in valid_links:
                            valid_links.append(normalized_url)
                            
                except Exception:
                    continue
            
            return valid_links
            
        except Exception as e:
            logger.warning(f"Failed to extract links from {url}: {str(e)}")
            return []

    def filter_urls_by_selector_success(
        self, 
        urls: List[str], 
        field_configs: List[FieldConfiguration]
    ) -> List[str]:
        """Filter URLs by selector success rate threshold"""
        self.stdout.write(f"🎯 Testing selectors on {len(urls)} URLs (threshold: {self.threshold:.1%})...")
        
        qualifying_urls = []
        
        for i, url in enumerate(urls, 1):
            try:
                self.stdout.write(f"  [{i}/{len(urls)}] Testing: {url}")
                
                success_rate = self.calculate_selector_success_rate(url, field_configs)
                
                if success_rate >= self.threshold:
                    qualifying_urls.append(url)
                    status = "✅ QUALIFIES"
                else:
                    status = "❌ BELOW THRESHOLD"
                
                self.stdout.write(f"    {status} Success rate: {success_rate:.1%}")
                
            except Exception as e:
                logger.warning(f"Failed to test selectors on {url}: {str(e)}")
                self.stdout.write(f"    ❌ ERROR: {str(e)}")
                continue
        
        self.stdout.write(f"📊 Selector filtering complete: {len(qualifying_urls)}/{len(urls)} URLs qualify")
        
        if self.verbose and qualifying_urls:
            self.stdout.write("✅ Qualifying URLs:")
            for url in qualifying_urls:
                self.stdout.write(f"  - {url}")
        
        return qualifying_urls

    def calculate_selector_success_rate(
        self, 
        url: str, 
        field_configs: List[FieldConfiguration]
    ) -> float:
        """Calculate the success rate of selectors on a given URL"""
        try:
            # Fetch and parse the page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Triad Content Extractor)'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            tree = html.fromstring(response.content)
            
            total_selectors = 0
            successful_selectors = 0
            
            # Test each field configuration
            for field_config in field_configs:
                if not field_config.xpath_selectors:
                    continue
                
                # Test each XPath selector for this field
                for xpath_selector in field_config.xpath_selectors:
                    total_selectors += 1
                    
                    try:
                        elements = tree.xpath(xpath_selector)
                        if elements:
                            # Check if any element has meaningful content
                            has_content = False
                            for element in elements:
                                text_content = element.text_content().strip() if hasattr(element, 'text_content') else str(element).strip()
                                if text_content and len(text_content) > 3:  # Basic content validation
                                    has_content = True
                                    break
                            
                            if has_content:
                                successful_selectors += 1
                    except Exception:
                        # XPath execution failed
                        continue
            
            if total_selectors == 0:
                return 0.0
            
            return successful_selectors / total_selectors
            
        except Exception as e:
            logger.warning(f"Failed to calculate selector success rate for {url}: {str(e)}")
            return 0.0

    def test_selectors_on_known_urls(
        self, 
        site_config: SiteConfiguration, 
        field_configs: List[FieldConfiguration]
    ):
        """Test selectors on known URLs from the database"""
        known_urls = list(site_config.urls.filter(status='active').values_list('url', flat=True))
        
        if not known_urls:
            self.stdout.write(f"❌ No known URLs found for {site_config.site_name}")
            return
        
        self.stdout.write(f"🔍 Testing selectors on {len(known_urls)} known URLs...")
        
        for i, url in enumerate(known_urls, 1):
            try:
                self.stdout.write(f"\n[{i}/{len(known_urls)}] Testing: {url}")
                
                # Check if this looks like a product page
                is_product_page = self.product_page_pattern in url
                has_query_params = '?' in url
                
                page_type = "🎯 PRODUCT PAGE" if is_product_page else "📄 General page"
                if has_query_params:
                    page_type += " (with query params)"
                self.stdout.write(f"  {page_type}")
                
                success_rate = self.calculate_selector_success_rate(url, field_configs)
                
                if success_rate >= self.threshold:
                    status = "✅ WOULD PROCESS"
                else:
                    status = "❌ WOULD SKIP"
                
                self.stdout.write(f"  {status} Success rate: {success_rate:.1%}")
                
            except Exception as e:
                self.stdout.write(f"  ❌ ERROR: {str(e)}")

    def sanitize_page_title_for_directory(self, page_title: str) -> str:
        """Convert page title to a safe directory name"""
        if not page_title:
            return "untitled_page"
        
        # Remove HTML entities and clean up
        import html as html_module
        clean_title = html_module.unescape(page_title)
        
        # Replace problematic characters with underscores
        safe_title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', clean_title)
        
        # Replace multiple spaces/underscores with single underscore
        safe_title = re.sub(r'[\s_]+', '_', safe_title)
        
        # Remove leading/trailing underscores and limit length
        safe_title = safe_title.strip('_')[:100]
        
        # Ensure it's not empty
        if not safe_title:
            return "untitled_page"
        
        return safe_title

    def create_or_get_site_url(self, url: str, site_config: SiteConfiguration, page_title: str = "") -> SiteURL:
        """Create or get SiteURL record for the given URL"""
        try:
            site_url, created = SiteURL.objects.get_or_create(
                site_config=site_config,
                url=url,
                defaults={
                    'page_title': page_title,
                    'status': 'active',
                    'processing_status': 'pending'
                }
            )
            
            # Update page title if it was empty before
            if not site_url.page_title and page_title:
                site_url.page_title = page_title
                site_url.save(update_fields=['page_title'])
            
            return site_url
            
        except Exception as e:
            logger.error(f"Failed to create/get SiteURL for {url}: {str(e)}")
            raise

    def save_ai_json_to_database(self, site_url: SiteURL, ai_json: Dict) -> AIJSONRecord:
        """Save AI JSON data to database as AIJSONRecord"""
        try:
            # Calculate content hash for change detection
            content_hash = hashlib.sha256(
                json.dumps(ai_json['field_configurations'], sort_keys=True).encode()
            ).hexdigest()
            
            # Mark previous records as outdated
            site_url.ai_json_records.filter(is_current=True).update(is_current=False)
            
            # Create new record
            ai_json_record = AIJSONRecord.objects.create(
                site_url=site_url,
                json_data=ai_json,
                content_hash=content_hash,
                is_current=True
            )
            
            # Update site_url processing status
            site_url.mark_completed()
            
            return ai_json_record
            
        except Exception as e:
            logger.error(f"Failed to save AI JSON to database for {site_url.url}: {str(e)}")
            site_url.mark_failed(f"Database save failed: {str(e)}")
            raise

    def generate_ai_json_batch(
        self, 
        urls: List[str], 
        site_config: SiteConfiguration
    ) -> List[str]:
        """Generate AI JSON for all qualifying URLs using two-mode processing"""
        self.stdout.write(f"📄 Generating AI JSON for {len(urls)} qualifying pages...")
        
        generated_files = []
        
        for i, url in enumerate(urls, 1):
            try:
                self.stdout.write(f"  [{i}/{len(urls)}] Processing: {url}")
                
                # Generate AI JSON files for this URL (overall + model batches)
                output_files = self.generate_two_mode_ai_json(url, site_config)
                
                if output_files:
                    generated_files.extend(output_files)
                    self.stdout.write(f"    ✅ Generated {len(output_files)} files:")
                    for file_path in output_files:
                        self.stdout.write(f"      - {os.path.basename(file_path)}")
                else:
                    self.stdout.write(f"    ❌ Failed to generate JSON")
                
            except Exception as e:
                logger.warning(f"Failed to generate AI JSON for {url}: {str(e)}")
                continue
        
        self.stdout.write(f"📊 Generated {len(generated_files)} AI JSON files total")
        return generated_files

    def generate_two_mode_ai_json(self, url: str, site_config: SiteConfiguration) -> List[str]:
        """Generate AI JSON for a single URL using two-mode processing"""
        try:
            # Generate base AI JSON data
            base_ai_json = self.generate_ai_json_for_raw_url(url, site_config)
            if not base_ai_json:
                return []
            
            # Extract page title from scraped content
            scraped_content = self.ai_json_command.scrape_url_content(url)
            page_title = scraped_content.get('page_title', '')
            
            # Create or get SiteURL record and save to database
            site_url = self.create_or_get_site_url(url, site_config, page_title)
            ai_json_record = self.save_ai_json_to_database(site_url, base_ai_json)
            
            # Create page-title-based directory
            safe_title = self.sanitize_page_title_for_directory(page_title)
            page_output_dir = os.path.join(self.output_dir, safe_title)
            os.makedirs(page_output_dir, exist_ok=True)
            
            # Extract model names and specification groups
            model_names = self.extract_model_names_from_json(base_ai_json)
            spec_group_names = self.extract_specification_group_names_from_json(base_ai_json)
            
            # Create output file paths with page title directory
            parsed_url = urlparse(url)
            safe_path = parsed_url.path.replace('/', '_').strip('_') or 'index'
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            generated_files = []
            
            # 1. Generate Overall Details file
            overall_details_data = base_ai_json.copy()
            overall_details_data['_processing_mode'] = 'OVERALL_DETAILS'
            overall_details_data['_page_info'] = {
                'page_title': page_title,
                'safe_directory_name': safe_title,
                'ai_json_record_id': ai_json_record.id
            }
            
            # Remove model-specific field configurations
            if 'field_configurations' in overall_details_data:
                field_configs = overall_details_data['field_configurations']
                overall_details_data['field_configurations'] = {
                    key: value for key, value in field_configs.items()
                    if not self.is_model_specific_field(key)
                }
            
            # Add specification groups
            if spec_group_names:
                overall_details_data['extracted_specification_groups'] = spec_group_names
                overall_details_data['_specification_instructions'] = {
                    "use_exact_group_names": True,
                    "no_underscores_in_names": True,
                    "extract_all_available_data": True,
                    "available_groups": spec_group_names
                }
            
            overall_details_filename = f"{safe_path}_overall_details_{timestamp}.json"
            overall_details_path = os.path.join(page_output_dir, overall_details_filename)
            
            with open(overall_details_path, 'w', encoding='utf-8') as f:
                json.dump(overall_details_data, f, indent=2, ensure_ascii=False)
            
            generated_files.append(overall_details_path)
            
            # 2. Generate Model Batch files (if models found)
            if model_names:
                models_per_batch = 4  # Default batch size
                total_batches = math.ceil(len(model_names) / models_per_batch)
                
                for batch_num in range(total_batches):
                    start_idx = batch_num * models_per_batch
                    end_idx = min(start_idx + models_per_batch, len(model_names))
                    batch_model_names = model_names[start_idx:end_idx]
                    
                    # Create model subset data
                    model_subset_data = base_ai_json.copy()
                    model_subset_data['_processing_mode'] = 'MODEL_SUBSET'
                    model_subset_data['_page_info'] = {
                        'page_title': page_title,
                        'safe_directory_name': safe_title,
                        'ai_json_record_id': ai_json_record.id
                    }
                    model_subset_data['_batch_info'] = {
                        'batch_number': batch_num + 1,
                        'total_batches': total_batches,
                        'models_in_batch': batch_model_names,
                        'total_models': len(model_names)
                    }
                    
                    # Filter to only model-specific field configurations
                    if 'field_configurations' in model_subset_data:
                        field_configs = model_subset_data['field_configurations']
                        model_subset_data['field_configurations'] = {
                            key: value for key, value in field_configs.items()
                            if self.is_model_specific_field(key) or key == 'models'
                        }
                    
                    # Add target model names and specification groups
                    model_subset_data['target_model_names'] = batch_model_names
                    
                    if spec_group_names:
                        model_subset_data['extracted_specification_groups'] = spec_group_names
                        model_subset_data['_specification_instructions'] = {
                            "use_exact_group_names": True,
                            "no_underscores_in_names": True,
                            "extract_all_available_data": True,
                            "available_groups": spec_group_names
                        }
                    
                    # Create filename
                    if total_batches > 1:
                        batch_filename = f"{safe_path}_models_batch_{batch_num + 1}_of_{total_batches}_{timestamp}.json"
                    else:
                        batch_filename = f"{safe_path}_models_{timestamp}.json"
                    
                    batch_filepath = os.path.join(page_output_dir, batch_filename)
                    
                    with open(batch_filepath, 'w', encoding='utf-8') as f:
                        json.dump(model_subset_data, f, indent=2, ensure_ascii=False)
                    
                    generated_files.append(batch_filepath)
            
            self.stdout.write(f"    📁 Files saved to directory: {safe_title}/")
            self.stdout.write(f"    💾 Database record ID: {ai_json_record.id}")
            
            return generated_files
            
        except Exception as e:
            logger.error(f"Failed to generate two-mode AI JSON for {url}: {str(e)}")
            return []

    def extract_model_names_from_json(self, ai_json: Dict) -> List[str]:
        """Extract model names from AI JSON data"""
        model_names = []
        
        try:
            # Look for models in field_configurations
            field_configs = ai_json.get('field_configurations', {})
            models_config = field_configs.get('models', {})
            
            if 'extracted_content' in models_config:
                for extraction in models_config['extracted_content']:
                    if 'extracted_data' in extraction:
                        for data in extraction['extracted_data']:
                            if 'text' in data:
                                # Split on common delimiters and clean up
                                text = data['text']
                                # Split by common model separators
                                potential_models = re.split(r'[,\n\r]+', text)
                                for model in potential_models:
                                    model = model.strip()
                                    if model and len(model) > 3:  # Basic validation
                                        model_names.append(model)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_models = []
            for model in model_names:
                if model not in seen:
                    seen.add(model)
                    unique_models.append(model)
            
            return unique_models
            
        except Exception as e:
            logger.warning(f"Failed to extract model names: {str(e)}")
            return []

    def extract_specification_group_names_from_json(self, ai_json: Dict) -> List[str]:
        """Extract specification group names from AI JSON data"""
        spec_groups = set()
        
        try:
            # Look for specification_group_names in field_configurations
            field_configs = ai_json.get('field_configurations', {})
            spec_config = field_configs.get('specification_group_names', {})
            
            if 'extracted_content' in spec_config:
                for extraction in spec_config['extracted_content']:
                    if 'extracted_data' in extraction:
                        for data in extraction['extracted_data']:
                            if 'text' in data:
                                text = data['text']
                                # Split by common separators and clean up
                                potential_groups = re.split(r'[,\n\r]+', text)
                                for group in potential_groups:
                                    group = group.strip()
                                    if group:
                                        # Clean up and title case
                                        clean_group = group.replace('_', ' ').replace('-', ' ')
                                        title_case_group = ' '.join(word.capitalize() for word in clean_group.split())
                                        spec_groups.add(title_case_group)
            
            # Convert to sorted list
            return sorted(list(spec_groups))
            
        except Exception as e:
            logger.warning(f"Failed to extract specification group names: {str(e)}")
            return []

    def is_model_specific_field(self, field_name: str) -> bool:
        """Determine if a field is model-specific"""
        model_specific_fields = {
            'models', 'model_name', 'model_names', 'specifications', 
            'spec', 'specification_group_names'
        }
        return field_name.lower() in model_specific_fields

    def generate_ai_json_for_raw_url(self, url: str, site_config: SiteConfiguration) -> Optional[Dict]:
        """Generate AI JSON for a raw URL (not a SiteURL object)"""
        try:
            # Scrape content using the existing method
            scraped_content = self.ai_json_command.scrape_url_content(url)
            
            # Get field configurations for this site
            field_configs = site_config.field_configs.filter(is_active=True)
            
            # Organize field configurations with content extraction
            field_configurations = self.ai_json_command.organize_field_configurations(
                field_configs, scraped_content['html']
            )
            
            # Assemble AI JSON structure
            ai_json = {
                'url': url,
                'site_domain': site_config.site_domain,
                'site_name': site_config.site_name,
                'field_configurations': field_configurations,
                'batch_processing_info': {
                    'processed_at': timezone.now().isoformat(),
                    'processor': 'batch_site_processor',
                    'threshold_used': self.threshold
                }
            }
            
            return ai_json
            
        except Exception as e:
            logger.error(f"Failed to generate AI JSON for raw URL {url}: {str(e)}")
            return None

    def upload_batch_to_s3(self, file_paths: List[str]):
        """Upload generated JSON files to S3 with Bedrock format support"""
        from apps.content_extractor.aws_utils import (
            get_s3_client, create_bucket_if_not_exists, upload_files_batch,
            convert_batch_to_bedrock_jsonl, generate_s3_bucket_name, delete_local_files
        )
        from datetime import datetime
        
        try:
            self.stdout.write(f"☁️  Starting S3 upload for {len(file_paths)} files...")
            
            # Generate bucket name if not provided
            if not self.s3_bucket:
                self.s3_bucket = generate_s3_bucket_name(self.domain)
                self.stdout.write(f"📦 Generated bucket name: {self.s3_bucket}")
            
            # Create bucket if it doesn't exist
            self.stdout.write(f"🔍 Checking/creating S3 bucket: {self.s3_bucket}")
            if not create_bucket_if_not_exists(self.s3_bucket, 'us-east-1'):
                raise Exception(f"Failed to create or access S3 bucket: {self.s3_bucket}")
            
            files_to_upload = file_paths.copy()
            upload_results = {}
            
            # Convert to Bedrock JSONL format if requested
            if self.bedrock_format:
                self.stdout.write("🔄 Converting JSON files to Bedrock JSONL format...")
                
                # Display prompt ARN being used
                if self.bedrock_prompt_arn:
                    self.stdout.write(f"🎯 Using custom Bedrock prompt ARN: {self.bedrock_prompt_arn}")
                else:
                    self.stdout.write("🎯 Using default Bedrock prompt ARN")
                
                # Create bedrock-jsonl subdirectory
                bedrock_dir = os.path.join(self.output_dir, 'bedrock-jsonl')
                
                # Convert JSON files to JSONL
                json_files = [f for f in file_paths if f.endswith('.json') and 'manifest' not in f]
                jsonl_files = convert_batch_to_bedrock_jsonl(json_files, bedrock_dir, self.bedrock_prompt_arn)
                
                self.stdout.write(f"✅ Converted {len(jsonl_files)} files to JSONL format")
                
                # Add JSONL files to upload list
                files_to_upload.extend(jsonl_files)
            
            # Generate S3 prefix with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            s3_prefix = f"{self.s3_prefix}/{self.domain}/{timestamp}"
            
            self.stdout.write(f"📁 S3 prefix: {s3_prefix}")
            
            # Upload files in batch
            self.stdout.write("⬆️  Uploading files to S3...")
            upload_results = upload_files_batch(files_to_upload, self.s3_bucket, s3_prefix)
            
            # Count successful uploads
            successful_uploads = {k: v for k, v in upload_results.items() if v is not None}
            failed_uploads = {k: v for k, v in upload_results.items() if v is None}
            
            self.stdout.write(f"✅ Successfully uploaded: {len(successful_uploads)} files")
            if failed_uploads:
                self.stdout.write(f"❌ Failed uploads: {len(failed_uploads)} files")
                for failed_file in failed_uploads.keys():
                    self.stdout.write(f"   - {failed_file}")
            
            # Update manifest with S3 information
            self.update_manifest_with_s3_info(upload_results, s3_prefix)
            
            # Delete local files if requested and uploads were successful
            if self.delete_local and successful_uploads:
                self.stdout.write("🗑️  Deleting local files after successful upload...")
                deleted_count, failed_count = delete_local_files(files_to_upload, successful_uploads)
                self.stdout.write(f"🗑️  Deleted {deleted_count} files, {failed_count} failed deletions")
            
            # Display S3 URLs for successful uploads
            if self.verbose and successful_uploads:
                self.stdout.write("📋 S3 URLs:")
                for local_path, s3_url in successful_uploads.items():
                    self.stdout.write(f"   {os.path.basename(local_path)} → {s3_url}")
            
            self.stdout.write(f"☁️  S3 upload complete! Bucket: {self.s3_bucket}")
            
        except Exception as e:
            logger.error(f"S3 upload failed: {str(e)}")
            self.stdout.write(f"❌ S3 upload failed: {str(e)}")
            raise

    def update_manifest_with_s3_info(self, upload_results: Dict[str, Optional[str]], s3_prefix: str):
        """Update the batch manifest with S3 upload information"""
        from datetime import datetime
        
        try:
            manifest_path = os.path.join(self.output_dir, 'batch_manifest.json')
            
            if not os.path.exists(manifest_path):
                logger.warning("Manifest file not found, skipping S3 info update")
                return
            
            # Read existing manifest
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # Add S3 information
            manifest['s3_upload_info'] = {
                'bucket': self.s3_bucket,
                'prefix': s3_prefix,
                'upload_timestamp': datetime.now().isoformat(),
                'bedrock_format_enabled': self.bedrock_format,
                'bedrock_prompt_arn': self.bedrock_prompt_arn,
                'local_files_deleted': self.delete_local,
                'upload_results': upload_results
            }
            
            # Update file entries with S3 URLs
            for file_entry in manifest.get('files', []):
                full_path = file_entry.get('full_path')
                if full_path in upload_results and upload_results[full_path]:
                    file_entry['s3_url'] = upload_results[full_path]
                    file_entry['upload_status'] = 'success'
                elif full_path in upload_results:
                    file_entry['upload_status'] = 'failed'
                else:
                    file_entry['upload_status'] = 'not_attempted'
            
            # Write updated manifest
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            self.stdout.write(f"📋 Updated manifest with S3 information: {manifest_path}")
            
        except Exception as e:
            logger.error(f"Failed to update manifest with S3 info: {str(e)}")
            self.stdout.write(f"⚠️  Failed to update manifest: {str(e)}")

    def create_batch_manifest(self, file_paths: List[str]) -> str:
        """Create a manifest file for the batch processing results"""
        manifest = {
            'batch_info': {
                'domain': self.domain,
                'timestamp': datetime.now().isoformat(),
                'threshold': self.threshold,
                'total_files': len(file_paths),
                'output_directory': self.output_dir,
                'processor_version': 'quantum-ridge-v1.0'
            },
            'files': [
                {
                    'filename': os.path.basename(path),
                    'full_path': path,
                    'size_bytes': os.path.getsize(path) if os.path.exists(path) else 0
                }
                for path in file_paths
            ]
        }
        
        manifest_path = os.path.join(self.output_dir, 'batch_manifest.json')
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        self.stdout.write(f"📋 Created manifest: {manifest_path}")
        return manifest_path

    def filter_to_product_pages(self, discovered_urls: List[str]) -> List[str]:
        """Filter discovered URLs to only product pages matching the pattern"""
        product_urls = []
        
        for url in discovered_urls:
            if self.product_page_pattern in url:
                product_urls.append(url)
                
                # Limit to max product pages
                if len(product_urls) >= self.max_product_pages:
                    break
        
        self.stdout.write(
            f"🎯 Found {len(product_urls)} product pages matching pattern '{self.product_page_pattern}' "
            f"from {len(discovered_urls)} total discovered pages"
        )
        
        if self.verbose and product_urls:
            self.stdout.write("📄 Product pages found:")
            for url in product_urls:
                self.stdout.write(f"  - {url}")
        
        return product_urls 