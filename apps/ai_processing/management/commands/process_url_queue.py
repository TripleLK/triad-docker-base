#!/usr/bin/env python
import os
import json
import logging
import time
import argparse
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.ai_processing.models import BatchURLProcessingRequest, URLProcessingRequest
from apps.ai_processing.views import process_url_request

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Process URLs from a queue one at a time, loading from a file of Triad Scientific URLs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--urls-file',
            type=str,
            help='File containing URLs to process, one per line'
        )
        parser.add_argument(
            '--batch-name',
            type=str,
            default=f"Triad Import {timezone.now().strftime('%Y-%m-%d %H:%M')}",
            help='Name for the batch of URLs'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=2.0,
            help='Delay between processing URLs (in seconds)'
        )
        parser.add_argument(
            '--css-selectors',
            type=str,
            default='',
            help='Optional CSS selectors to filter content'
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show status of existing queue and exit'
        )
        parser.add_argument(
            '--queue-file',
            type=str,
            default='triad_url_queue.json',
            help='File to save/load queue status'
        )
        parser.add_argument(
            '--process',
            action='store_true',
            help='Process the next URL in the queue'
        )
        parser.add_argument(
            '--resume',
            action='store_true',
            help='Resume processing the entire queue'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=3,
            help='Limit the number of URLs to process when resuming (default: 3)'
        )

    def handle(self, *args, **options):
        # Initialize the queue handler
        queue_handler = TriadURLQueueHandler(
            queue_file=options['queue_file'],
            batch_name=options['batch_name'],
            css_selectors=options['css_selectors'],
            delay=options['delay']
        )
        
        # Show status and exit if requested
        if options['status']:
            queue_handler.show_status()
            return
            
        # Load URLs from file if provided
        if options['urls_file']:
            queue_handler.load_urls_from_file(options['urls_file'])
            self.stdout.write(self.style.SUCCESS(f"URLs loaded from {options['urls_file']}"))
            queue_handler.show_status()
        
        # Process one URL and exit if requested
        if options['process']:
            result = queue_handler.process_next_url()
            status_msg = "Processed URL successfully" if result else "Failed to process URL or no URLs in queue"
            self.stdout.write(self.style.SUCCESS(status_msg))
            
        # Resume processing the entire queue if requested
        if options['resume']:
            limit = options['limit']
            self.stdout.write(self.style.SUCCESS(f"Resuming queue processing with limit of {limit} URLs"))
            queue_handler.process_queue(limit=limit)


class TriadURLQueueHandler:
    """Handler for processing a queue of Triad Scientific URLs."""
    
    def __init__(self, queue_file='triad_url_queue.json', batch_name=None, css_selectors='', delay=2.0):
        self.queue_file = queue_file
        self.batch_name = batch_name or f"Triad Import {timezone.now().strftime('%Y-%m-%d %H:%M')}"
        self.css_selectors = css_selectors
        self.delay = delay
        self.queue_data = self.load_queue()
        self.stdout = getattr(Command(), 'stdout', None)
    
    def load_queue(self):
        """Load the queue from file or create a new one."""
        if os.path.exists(self.queue_file):
            try:
                logger.info(f"Loading queue from {self.queue_file}")
                with open(self.queue_file, 'r') as f:
                    data = json.load(f)
                    if 'batch_id' in data:
                        # Verify the batch still exists in the database
                        try:
                            BatchURLProcessingRequest.objects.get(id=data['batch_id'])
                        except BatchURLProcessingRequest.DoesNotExist:
                            logger.warning(f"Batch ID {data['batch_id']} not found in database, creating new batch")
                            data['batch_id'] = None
                    return data
            except Exception as e:
                logger.error(f"Error loading queue file: {e}")
        
        # Default empty queue
        return {
            'batch_id': None,
            'pending_urls': [],
            'processed_urls': [],
            'failed_urls': [],
            'last_updated': timezone.now().isoformat()
        }
    
    def save_queue(self):
        """Save the queue to file."""
        self.queue_data['last_updated'] = timezone.now().isoformat()
        with open(self.queue_file, 'w') as f:
            json.dump(self.queue_data, f, indent=2)
        logger.info(f"Queue saved to {self.queue_file}")
    
    def load_urls_from_file(self, url_file):
        """Load URLs from a file and add them to the queue."""
        if not os.path.exists(url_file):
            logger.error(f"URL file not found: {url_file}")
            return False
        
        with open(url_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        existing_urls = set(self.queue_data['pending_urls'] + 
                          self.queue_data['processed_urls'] + 
                          self.queue_data['failed_urls'])
        
        new_urls = [url for url in urls if url not in existing_urls]
        
        if new_urls:
            self.queue_data['pending_urls'].extend(new_urls)
            logger.info(f"Added {len(new_urls)} new URLs to the queue")
            
            # If batch doesn't exist yet, create one
            if self.queue_data['batch_id'] is None:
                self.create_batch()
            else:
                # Add new URLs to existing batch
                self.add_urls_to_batch(new_urls)
                
            self.save_queue()
            return True
        else:
            logger.info("No new URLs to add to the queue")
            return False
    
    def create_batch(self):
        """Create a new batch in the database for this queue."""
        batch = BatchURLProcessingRequest.objects.create(
            name=self.batch_name,
            css_selectors=self.css_selectors,
            total_urls=len(self.queue_data['pending_urls'])
        )
        
        # Add all pending URLs to the batch
        for url in self.queue_data['pending_urls']:
            URLProcessingRequest.objects.create(
                url=url,
                batch=batch,
                css_selectors=self.css_selectors
            )
        
        # Update batch status
        batch.update_status()
        
        # Save batch ID in queue data
        self.queue_data['batch_id'] = batch.id
        logger.info(f"Created new batch with ID {batch.id}")
        
        self.save_queue()
    
    def add_urls_to_batch(self, urls):
        """Add URLs to an existing batch."""
        if not self.queue_data['batch_id']:
            logger.error("No batch ID found in queue data")
            return
        
        try:
            batch = BatchURLProcessingRequest.objects.get(id=self.queue_data['batch_id'])
            
            # Add URLs to the batch
            for url in urls:
                URLProcessingRequest.objects.create(
                    url=url,
                    batch=batch,
                    css_selectors=self.css_selectors
                )
            
            # Update the batch total
            batch.total_urls = batch.url_requests.count()
            batch.save(update_fields=['total_urls'])
            
            # Update batch status
            batch.update_status()
            
            logger.info(f"Added {len(urls)} URLs to batch {batch.id}")
        except BatchURLProcessingRequest.DoesNotExist:
            logger.error(f"Batch with ID {self.queue_data['batch_id']} does not exist")
    
    def process_next_url(self):
        """Process the next URL in the queue."""
        if not self.queue_data['pending_urls']:
            logger.info("No pending URLs in the queue")
            return False
        
        if not self.queue_data['batch_id']:
            logger.error("No batch ID found in queue data")
            return False
        
        # Get the next URL
        url = self.queue_data['pending_urls'][0]
        logger.info(f"Processing next URL in queue: {url}")
        
        try:
            # Find the corresponding URL request in the database
            batch = BatchURLProcessingRequest.objects.get(id=self.queue_data['batch_id'])
            url_request = URLProcessingRequest.objects.filter(
                batch=batch,
                url=url,
                status='pending'
            ).first()
            
            if not url_request:
                logger.warning(f"URL request for {url} not found in database, skipping")
                self.queue_data['pending_urls'].remove(url)
                self.queue_data['failed_urls'].append(url)
                self.save_queue()
                return False
            
            # Process the URL request
            logger.info(f"Processing URL request ID {url_request.id}")
            process_url_request(url_request.id)
            
            # Update queue data
            self.queue_data['pending_urls'].remove(url)
            
            # Check the request status
            url_request.refresh_from_db()
            if url_request.status == 'completed':
                logger.info(f"URL {url} processed successfully")
                self.queue_data['processed_urls'].append(url)
            else:
                logger.warning(f"URL {url} processing failed, status: {url_request.status}")
                self.queue_data['failed_urls'].append(url)
            
            # Update batch status
            batch.update_status()
            
            # Save queue data
            self.save_queue()
            
            return True
        except Exception as e:
            logger.exception(f"Error processing URL {url}: {e}")
            
            # Update queue data
            self.queue_data['pending_urls'].remove(url)
            self.queue_data['failed_urls'].append(url)
            self.save_queue()
            
            return False
    
    def process_queue(self, limit=3):
        """Process all URLs in the queue until done or limit is reached."""
        if not self.queue_data['pending_urls']:
            logger.info("No pending URLs in the queue")
            return
        
        total_urls = len(self.queue_data['pending_urls'])
        processed_count = 0
        
        logger.info(f"Processing queue with {total_urls} URLs" + 
                  (f" (limit: {limit})" if limit else ""))
        
        try:
            while self.queue_data['pending_urls'] and (limit is None or processed_count < limit):
                if self.process_next_url():
                    processed_count += 1
                    logger.info(f"Processed {processed_count}/{total_urls} URLs")
                    
                    # Add delay between requests
                    if self.queue_data['pending_urls'] and (limit is None or processed_count < limit):
                        logger.info(f"Waiting {self.delay} seconds before next URL...")
                        time.sleep(self.delay)
        except KeyboardInterrupt:
            logger.info("Processing interrupted by user")
        except Exception as e:
            logger.exception(f"Error during queue processing: {e}")
        finally:
            logger.info(f"Queue processing finished. Processed {processed_count} URLs.")
            
            # Print final stats
            self.show_status()
    
    def show_status(self):
        """Show the current status of the queue."""
        pending = len(self.queue_data['pending_urls'])
        processed = len(self.queue_data['processed_urls'])
        failed = len(self.queue_data['failed_urls'])
        total = pending + processed + failed
        
        batch_info = "No batch created yet"
        if self.queue_data['batch_id']:
            try:
                batch = BatchURLProcessingRequest.objects.get(id=self.queue_data['batch_id'])
                batch_info = f"Batch '{batch.name}' (ID: {batch.id}, Status: {batch.status})"
            except BatchURLProcessingRequest.DoesNotExist:
                batch_info = f"Batch with ID {self.queue_data['batch_id']} does not exist"
        
        status_text = f"\nTriad URL Queue Status:\n"
        status_text += f"=====================================\n"
        status_text += f"Queue file: {self.queue_file}\n"
        status_text += f"Last updated: {self.queue_data.get('last_updated', 'Never')}\n"
        status_text += f"Batch: {batch_info}\n"
        status_text += f"Pending URLs: {pending}\n"
        status_text += f"Processed URLs: {processed}\n"
        status_text += f"Failed URLs: {failed}\n"
        status_text += f"Total URLs: {total}\n"
        if pending > 0:
            status_text += f"Next URL: {self.queue_data['pending_urls'][0]}\n"
        status_text += f"=====================================\n"
        
        if self.stdout:
            self.stdout.write(status_text)
        else:
            print(status_text)