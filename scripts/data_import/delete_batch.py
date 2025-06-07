#!/usr/bin/env python
"""
Delete a batch URL processing request and all its associated URL requests.
"""
import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from django.utils import timezone
from apps.ai_processing.models import BatchURLProcessingRequest, URLProcessingRequest

def delete_batch(batch_id):
    """Delete a batch and all its associated URL requests."""
    try:
        # Get the batch
        batch = BatchURLProcessingRequest.objects.get(id=batch_id)
        
        # Get all URL requests associated with this batch
        url_requests = URLProcessingRequest.objects.filter(batch=batch)
        
        # Get URLs to save for later
        urls = [req.url for req in url_requests]
        
        # Count URL requests
        url_count = url_requests.count()
        
        # Delete all URL requests
        url_requests.delete()
        
        # Delete the batch
        batch_name = batch.name
        batch.delete()
        
        print(f"Deleted batch {batch_id} ({batch_name}) and {url_count} URL requests")
        
        # Save URLs to a file for reuse
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        filename = f"urls_from_deleted_batch_{batch_id}_{timestamp}.txt"
        with open(filename, 'w') as f:
            for url in urls:
                f.write(f"{url}\n")
        
        print(f"Saved URLs to {filename}")
        return filename
    
    except BatchURLProcessingRequest.DoesNotExist:
        print(f"Batch with ID {batch_id} does not exist")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python delete_batch.py <batch_id>")
        sys.exit(1)
    
    try:
        batch_id = int(sys.argv[1])
    except ValueError:
        print("Batch ID must be an integer")
        sys.exit(1)
    
    delete_batch(batch_id) 