import json
import logging
from django.core.management.base import BaseCommand, CommandError
from apps.ai_processing.models import URLProcessingRequest
from apps.ai_processing.utils import validate_url, get_bedrock_client, process_url_content, extract_structured_data
from apps.categorized_tags.models import CategorizedTag

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Process a URL with AWS Bedrock to extract structured data'

    def add_arguments(self, parser):
        parser.add_argument('--url', type=str, help='URL to process')
        parser.add_argument('--request-id', type=int, help='ID of an existing URLProcessingRequest to process')
        parser.add_argument('--process-pending', action='store_true', help='Process all pending requests')

    def handle(self, *args, **options):
        url = options.get('url')
        request_id = options.get('request_id')
        process_pending = options.get('process_pending')
        
        if not any([url, request_id, process_pending]):
            raise CommandError("You must provide either a URL, a request ID, or the --process-pending flag")
        
        if url:
            # Create a new URLProcessingRequest
            is_valid, error_message = validate_url(url)
            if not is_valid:
                raise CommandError(f"Invalid URL: {error_message}")
            
            url_request = URLProcessingRequest.objects.create(url=url)
            self.stdout.write(f"Created new URLProcessingRequest with ID: {url_request.id}")
            
            # Process the URL
            self._process_url_request(url_request)
        
        elif request_id:
            # Process an existing URLProcessingRequest
            try:
                url_request = URLProcessingRequest.objects.get(id=request_id)
            except URLProcessingRequest.DoesNotExist:
                raise CommandError(f"URLProcessingRequest with ID {request_id} does not exist")
            
            self._process_url_request(url_request)
        
        elif process_pending:
            # Process all pending requests
            pending_requests = URLProcessingRequest.objects.filter(status='pending')
            count = pending_requests.count()
            
            if count == 0:
                self.stdout.write(self.style.WARNING("No pending requests found"))
                return
            
            self.stdout.write(f"Processing {count} pending requests...")
            
            for url_request in pending_requests:
                try:
                    self._process_url_request(url_request)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing request {url_request.id}: {str(e)}"))
                    continue
            
            self.stdout.write(self.style.SUCCESS(f"Processed {count} pending requests"))

    def _process_url_request(self, url_request):
        """Process a URLProcessingRequest with AWS Bedrock"""
        try:
            self.stdout.write(f"Processing URL: {url_request.url}")
            
            # Mark as processing
            url_request.mark_as_processing()
            
            # Get a Bedrock client
            client = get_bedrock_client()
            
            # Process the URL
            html_content = process_url_content(url_request.url)
            
            # Get existing tags for context
            existing_tags = CategorizedTag.objects.all().values('category', 'name')
            existing_tags_list = [{'category': tag['category'], 'name': tag['name']} for tag in existing_tags]
            
            # Prepare input variables for Bedrock
            input_variables = {
                'site_html': {'text': html_content},
                'page_url': {'text': url_request.url},
                'existing_tags': {'text': json.dumps(existing_tags_list) if existing_tags_list else ''}
            }
            
            # Call AWS Bedrock
            self.stdout.write("Calling AWS Bedrock API...")
            
            model_id = "arn:aws:bedrock:us-east-1:891377295311:prompt/LGO4BMQJG7"  # Replace with your actual prompt ARN
            bedrock_response = client.converse(
                modelId=model_id,
                promptVariables=input_variables
            )
            
            # Extract the structured data
            result = bedrock_response.get('output', {})
            structured_data = extract_structured_data(result)
            
            if structured_data:
                # Mark as completed
                url_request.mark_as_completed(structured_data)
                self.stdout.write(self.style.SUCCESS(f"Successfully processed URL: {url_request.url}"))
            else:
                # Mark as failed
                url_request.mark_as_failed("Failed to extract structured data from Bedrock response")
                self.stdout.write(self.style.ERROR(f"Failed to extract structured data from Bedrock response"))
        
        except Exception as e:
            # Mark as failed
            error_message = str(e)
            url_request.mark_as_failed(error_message)
            self.stdout.write(self.style.ERROR(f"Error processing URL: {error_message}"))
            raise CommandError(error_message) 