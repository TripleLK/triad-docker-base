#!/usr/bin/env python3
import logging
import sys
import requests
import re
import time
import traceback
import os
import importlib.util
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import concurrent.futures
import threading
import queue
import datetime
import json
from tqdm import tqdm
import signal

from apps.scrapers.Scrapers import Scraper
from apps.scrapers.utils.image_downloader import ImageDownloader
from apps.scrapers.utils.api_client import LabEquipmentAPIClient
from apps.categorized_tags.models import CategorizedTag, TagCategory

# Import the URL discoverer using dynamic import to handle the hyphenated directory name
discoverer_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                              'triadscientific-yamls', 'url_discovery.py')
spec = importlib.util.spec_from_file_location("url_discovery", discoverer_path)
url_discovery = importlib.util.module_from_spec(spec)
sys.modules["url_discovery"] = url_discovery
spec.loader.exec_module(url_discovery)
TriadUrlDiscoverer = url_discovery.TriadUrlDiscoverer

# Setup module-level logger
logger = logging.getLogger(__name__)

# Global variables for process management
stop_processing = False
stats_lock = threading.Lock()

# Define a signal handler for graceful shutdown
def signal_handler(sig, frame):
    global stop_processing
    print("\nGracefully shutting down... (This may take a moment)")
    stop_processing = True

class Command(BaseCommand):
    help = 'Import Triad Scientific product data using the API instead of Django ORM'

    def add_arguments(self, parser):
        # Original URL arguments
        parser.add_argument(
            '--url',
            type=str,
            help='URL to scrape'
        )
        parser.add_argument(
            '--url-file',
            type=str,
            help='File containing URLs to scrape, one per line'
        )
        
        # New URL discovery arguments
        parser.add_argument(
            '--discover-urls',
            action='store_true',
            help='Discover product URLs from the Triad Scientific website'
        )
        parser.add_argument(
            '--category',
            type=str,
            help='Specific category to discover URLs for (e.g., "ftir-systems")'
        )
        parser.add_argument(
            '--output-file',
            type=str,
            default='discovered_product_urls.txt',
            help='File to save discovered URLs to'
        )
        parser.add_argument(
            '--request-delay',
            type=float,
            default=1.0,
            help='Delay between requests during URL discovery (in seconds)'
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
        
        # Original import arguments
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
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of URLs to process'
        )
        parser.add_argument(
            '--retry',
            type=int,
            default=3,
            help='Number of retry attempts for failed requests (default: 3)'
        )
        parser.add_argument(
            '--retry-delay',
            type=int,
            default=5,
            help='Delay in seconds between retry attempts (default: 5)'
        )
        
        # New tagging arguments
        parser.add_argument(
            '--add-manufacturer-tag',
            action='store_true',
            help='Add manufacturer tag to imported products'
        )
        
        # Step 6: Parallel processing arguments
        parser.add_argument(
            '--workers',
            type=int,
            default=4,
            help='Number of worker threads for parallel processing (default: 4)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of items to process in a single batch (default: 10)'
        )
        parser.add_argument(
            '--checkpoint-file',
            type=str,
            default='triad_checkpoint.json',
            help='Checkpoint file to save/resume progress'
        )
        parser.add_argument(
            '--resume',
            action='store_true',
            help='Resume from the last checkpoint'
        )
        parser.add_argument(
            '--stats-interval',
            type=int,
            default=60,
            help='Interval in seconds for printing statistics during processing (default: 60)'
        )
        parser.add_argument(
            '--log-file',
            type=str,
            default='triad_import.log',
            help='Log file for detailed import information'
        )

    def handle(self, *args, **options):
        # Register signal handler for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        
        # Setup logging
        self._setup_logging(options['log_file'])
        
        # Initialize the API client
        self.api_client = LabEquipmentAPIClient(
            base_url=options['api_base_url'],
            api_token=options['api_token']
        )
        
        # Check if we're in discover mode
        if options['discover_urls']:
            self.discover_urls_parallel(
                category=options['category'],
                request_delay=options['request_delay'],
                output_file=options['output_file'],
                workers=options['workers']
            )
            return

        # Get URLs to process
        urls = self._get_urls_to_process(options)
        if not urls:
            self.stdout.write("No URLs to process.")
            return
            
        # Apply limit if specified
        limit = options['limit']
        if limit is not None and limit > 0:
            urls = urls[:limit]

        # Initialize statistics
        stats = {
            'total': len(urls),
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': datetime.datetime.now(),
        }
        
        # Create a new scraper for triad scientific
        scraper = Scraper("apps/scrapers/triadscientific-yamls/mapping.yaml")
        
        # Create a requests session with retry capability
        session = self._create_session_with_retry(options['retry'], options['retry_delay'])
        
        # Process the URLs in parallel
        self.process_urls_parallel(
            urls=urls,
            scraper=scraper,
            session=session,
            skip_images=options['skip_images'],
            dry_run=options['dry_run'],
            workers=options['workers'],
            batch_size=options['batch_size'],
            checkpoint_file=options['checkpoint_file'],
            stats=stats,
            add_manufacturer_tag=options['add_manufacturer_tag']
        )
        
        # Final statistics report
        self._print_stats_report(stats, final=True)

    def _stats_reporting_thread(self, stats, interval, stop_event):
        """Thread that periodically reports statistics during processing"""
        while not stop_event.is_set():
            time.sleep(interval)
            if not stop_event.is_set():  # Check again after sleep
                self._print_stats_report(stats, final=False)

    def _print_stats_report(self, stats, final=True):
        """Print a statistics report"""
        with stats_lock:
            current_time = datetime.datetime.now()
            elapsed = (current_time - stats['start_time']).total_seconds()
            elapsed_str = str(datetime.timedelta(seconds=int(elapsed)))
            
            processed = stats['processed']
            total = stats['total']
            successful = stats['successful']
            failed = stats['failed']
            skipped = stats['skipped']
            
            # Calculate remaining time (if not final report)
            remaining_str = "N/A"
            if not final and processed > 0 and processed < total:
                items_per_second = processed / elapsed
                remaining_seconds = (total - processed) / items_per_second if items_per_second > 0 else 0
                remaining_str = str(datetime.timedelta(seconds=int(remaining_seconds)))
            
            # Format the report
            report = f"\n--- Import Progress Report {'(FINAL)' if final else ''} ---\n"
            report += f"Processed: {processed}/{total} ({processed/total*100:.1f}%)\n"
            report += f"Successful: {successful} | Failed: {failed} | Skipped: {skipped}\n"
            report += f"Elapsed time: {elapsed_str}\n"
            
            if not final:
                report += f"Estimated time remaining: {remaining_str}\n"
                
            self.stdout.write(report)

    def _save_checkpoint(self, checkpoint_file, stats, all_urls, processed_urls=None):
        """Save a checkpoint to resume from later"""
        with stats_lock:
            checkpoint_data = {
                "last_updated": datetime.datetime.now().isoformat(),
                "stats": {k: v for k, v in stats.items() if k != 'start_time'},
                "all_urls": all_urls,
                "processed_urls": processed_urls or []
            }
            
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)

    def discover_urls_parallel(self, category=None, request_delay=1.0, output_file=None, workers=4):
        """Discover product URLs from the Triad Scientific website in parallel"""
        self.stdout.write("Starting URL discovery...")
        
        discoverer = TriadUrlDiscoverer(delay=request_delay)
        
        if category:
            self.stdout.write(f"Discovering URLs for category: {category}")
            urls = discoverer.discover_category_urls(category)
        else:
            self.stdout.write("Discovering URLs for all categories")
            urls = discoverer.discover_all_product_urls(workers=workers)
        
        if not urls:
            self.stdout.write("No URLs discovered.")
            return
        
        self.stdout.write(f"Discovered {len(urls)} product URLs")
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                for url in urls:
                    f.write(f"{url}\n")
            self.stdout.write(f"URLs saved to {output_file}")
        
        return urls

    def process_urls_parallel(self, urls, scraper, session, skip_images, 
                             dry_run, workers, batch_size, checkpoint_file, stats, add_manufacturer_tag):
        """Process URLs in parallel using a thread pool"""
        # Set up a thread for reporting statistics
        stop_event = threading.Event()
        stats_thread = threading.Thread(
            target=self._stats_reporting_thread,
            args=(stats, 60, stop_event),
            daemon=True
        )
        stats_thread.start()
        
        # Set up a work queue
        work_queue = queue.Queue()
        for url in urls:
            work_queue.put(url)
        
        # Create and start worker threads
        def worker_thread():
            while not stop_processing:
                try:
                    url = work_queue.get(block=False)
                except queue.Empty:
                    break
                
                try:
                    result = self._process_single_url(
                        url, 
                        scraper, 
                        session, 
                        skip_images, 
                        dry_run,
                        add_manufacturer_tag
                    )
                    
                    # Update statistics
                    with stats_lock:
                        stats['processed'] += 1
                        if result:
                            if result.get('success', False):
                                stats['successful'] += 1
                            elif result.get('skipped', False):
                                stats['skipped'] += 1
                            else:
                                stats['failed'] += 1
                        else:
                            stats['failed'] += 1
                            
                    # Save checkpoint after each batch
                    if stats['processed'] % batch_size == 0:
                        processed_urls = [u for u in urls if u not in [i for i in work_queue.queue]]
                        self._save_checkpoint(checkpoint_file, stats, urls, processed_urls)
                        
                except Exception as e:
                    logger.exception(f"Error processing URL {url}: {str(e)}")
                    with stats_lock:
                        stats['processed'] += 1
                        stats['failed'] += 1
                
                finally:
                    work_queue.task_done()
        
        # Start worker threads
        threads = []
        for _ in range(min(workers, len(urls))):
            thread = threading.Thread(target=worker_thread)
            thread.start()
            threads.append(thread)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Stop the stats reporting thread
        stop_event.set()
        stats_thread.join()
        
        # Save final checkpoint
        self._save_checkpoint(checkpoint_file, stats, urls, urls)

    def _process_single_url(self, url, scraper, session, skip_images, dry_run, add_manufacturer_tag):
        """Process a single URL and send the data to the API"""
        logger.info(f"Processing URL: {url}")
        
        try:
            # Extract product data using scraper
            with session.get(url) as response:
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                product_data = scraper.scrape(url)
            
            # Extract relevant fields
            product_name = product_data.get('name', '')
            short_description = product_data.get('short_description', '')
            full_description = product_data.get('full_description', '')
            models_data = product_data.get('models', {})
            images_data = product_data.get('imgs', [])
            
            # Validate required data
            if not self._validate_data(product_name, short_description, full_description, models_data, images_data):
                logger.warning(f"Skipping {url} due to missing required data")
                return {'skipped': True, 'reason': 'Missing required data'}
            
            # Extract category info for tagging
            category_info = self._extract_category_from_url(url)
            
            # Prepare data for API
            api_data = {
                'title': product_name,
                'short_description': short_description,
                'full_description': full_description,
                'source_url': url,
                # Generate slug from title
                'slug': self._generate_slug(product_name)
            }
            
            # Process tags if we have a category
            if category_info and add_manufacturer_tag:
                # Add a manufacturer tag and a product category tag
                tags = []
                
                # Add manufacturer tag (Manufacturer: Triad Scientific)
                tags.append("Manufacturer: Triad Scientific")
                
                # Add category tag (Product Category: category_info)
                if category_info:
                    tags.append(f"Product Category: {category_info}")
                
                # Extract any potential application tags from title or description
                # This is simplified - in a production system you might have a more
                # sophisticated approach to extract relevant application tags
                applications = self._extract_applications(product_name, short_description)
                for application in applications:
                    tags.append(f"Product Application: {application}")
                
                # Add tags to the API data
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
            
            # Send to API if not dry run
            if not dry_run:
                response = self.api_client.create_or_update_lab_equipment(api_data)
                logger.info(f"API response for {url}: {response}")
                
                if response.get('success', False):
                    return {'success': True, 'page_id': response.get('page_id')}
                else:
                    logger.error(f"API error for {url}: {response.get('error', 'Unknown error')}")
                    return {'success': False, 'error': response.get('error', 'Unknown error')}
            else:
                logger.info(f"Dry run - would send to API: {json.dumps(api_data, indent=2)[:500]}...")
                return {'success': True, 'dry_run': True}
                
        except Exception as e:
            error_msg = f"Error processing {url}: {str(e)}"
            logger.exception(error_msg)
            return {'success': False, 'error': error_msg}

    def _create_session_with_retry(self, retry_attempts, retry_delay):
        """Create a requests session with retry capability"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=retry_attempts,
            backoff_factor=retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        
        # Apply retry strategy to session
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session

    def _setup_logging(self, log_file):
        """Configure logging for the importer"""
        logger.setLevel(logging.INFO)
        
        # Create file handler
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            
            # Add handlers to logger
            logger.addHandler(file_handler)

    def _validate_data(self, product_name, short_description, full_description, models_data, images_data):
        """Validate that we have the required data to proceed"""
        if not product_name:
            logger.warning("Missing product name")
            return False
            
        if not short_description:
            logger.warning(f"Missing short description for {product_name}")
            
        if not full_description:
            logger.warning(f"Missing full description for {product_name}")
            
        if not models_data:
            logger.warning(f"No model data for {product_name}")
            
        if not images_data:
            logger.warning(f"No images for {product_name}")
            
        # At minimum we need a name and either description to proceed
        return bool(product_name and (short_description or full_description))

    def _extract_category_from_url(self, url):
        """Extract product category from URL"""
        # Try to extract from URL pattern like triadscientific.com/product-category/category-name/
        category_match = re.search(r'product-category/([^/]+)', url)
        if category_match:
            category = category_match.group(1)
            # Clean up category name
            category = category.replace('-', ' ').title()
            return category
            
        # Alternative method - get the first path segment after domain
        parsed_url = url.split('/')
        if len(parsed_url) >= 4:  # Has domain and at least one path segment
            # Find the index after domain
            for i, segment in enumerate(parsed_url):
                if segment.endswith('triadscientific.com'):
                    if i + 1 < len(parsed_url) and parsed_url[i+1]:
                        category = parsed_url[i+1]
                        if category not in ['product', 'products', 'product-category']:
                            return category.replace('-', ' ').title()
                        elif i + 2 < len(parsed_url) and parsed_url[i+2]:
                            return parsed_url[i+2].replace('-', ' ').title()
        
        return None

    def _extract_applications(self, product_name, description):
        """Extract potential applications from product name or description"""
        applications = []
        
        # Dictionary of keywords to application mappings
        application_keywords = {
            'chromatography': 'Chromatography',
            'hplc': 'Chromatography',
            'spectroscopy': 'Spectroscopy',
            'spectrometer': 'Spectroscopy',
            'mass spec': 'Mass Spectrometry',
            'microscope': 'Microscopy',
            'dna': 'Molecular Biology',
            'pcr': 'Molecular Biology',
            'centrifuge': 'Sample Preparation',
            'analyzer': 'Analysis',
            'diagnostic': 'Clinical Diagnostics',
            'biotech': 'Biotechnology',
            'pharmaceutical': 'Pharmaceutical',
            'chemistry': 'Chemistry',
            'biological': 'Life Science',
            'biology': 'Life Science',
            'lab': 'Laboratory Research',
            'research': 'Research',
        }
        
        # Combine name and description for searching
        text_to_search = (product_name + ' ' + description).lower()
        
        # Look for each keyword
        for keyword, application in application_keywords.items():
            if keyword.lower() in text_to_search:
                applications.append(application)
        
        # Remove duplicates and return
        return list(set(applications))

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
                                        
                                    # Clean up the spec name (remove trailing colons)
                                    spec_name = spec_name.rstrip(':')
                                    
                                    spec_group['specs'].append({
                                        'name': spec_name,
                                        'value': spec_value
                                    })
                
                # Only add groups with specs
                if spec_group['specs']:
                    api_specs.append(spec_group)
                    
        return api_specs

    def _get_urls_to_process(self, options):
        """Get the list of URLs to process based on command line options"""
        urls = []
        
        # Single URL
        if options['url']:
            urls = [options['url']]
            
        # URL file
        elif options['url_file']:
            try:
                with open(options['url_file'], 'r') as f:
                    urls = [line.strip() for line in f if line.strip()]
            except Exception as e:
                self.stderr.write(f"Error reading URL file: {str(e)}")
                return []
                
        # Resume from checkpoint
        elif options['resume'] and os.path.exists(options['checkpoint_file']):
            try:
                with open(options['checkpoint_file'], 'r') as f:
                    checkpoint_data = json.load(f)
                    all_urls = checkpoint_data.get('all_urls', [])
                    processed_urls = set(checkpoint_data.get('processed_urls', []))
                    urls = [url for url in all_urls if url not in processed_urls]
                    
                    # Update statistics from checkpoint
                    for key, value in checkpoint_data.get('stats', {}).items():
                        stats[key] = value
                        
                    self.stdout.write(f"Resuming from checkpoint with {len(urls)} remaining URLs")
                    
            except Exception as e:
                self.stderr.write(f"Error loading checkpoint: {str(e)}")
                return []
        
        return urls 