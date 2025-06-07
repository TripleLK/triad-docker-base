import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.ai_processing.utils import get_bedrock_client
from apps.ai_processing.models import URLProcessingRequest
from apps.categorized_tags.models import CategorizedTag

class Command(BaseCommand):
    help = 'Test AWS Bedrock integration with example values'

    def handle(self, *args, **options):
        # Print environment variables for debugging
        self.stdout.write(self.style.SUCCESS('Testing AWS Bedrock integration'))
        self.stdout.write(f"AWS_ACCESS_KEY_ID: {os.environ.get('AWS_ACCESS_KEY_ID', 'Not set')[:5]}...")
        self.stdout.write(f"AWS_SECRET_ACCESS_KEY: {os.environ.get('AWS_SECRET_ACCESS_KEY', 'Not set')[:5]}...")
        self.stdout.write(f"AWS_REGION: {os.environ.get('AWS_REGION', 'Not set')}")
        self.stdout.write(f"AWS_BEDROCK_PROMPT_ARN: {os.environ.get('AWS_BEDROCK_PROMPT_ARN', 'Not set')}")
        
        # Get example URL
        example_url = "http://www.triadscientific.com/en/products/particle-size-analysis/953/n-a/251185"
        
        # Get existing tags from the database
        existing_tags = list(CategorizedTag.objects.all().values_list('name', flat=True))
        self.stdout.write(f"Existing tags: {', '.join(existing_tags[:10])}... (total: {len(existing_tags)})")
        
        # Get categories as well
        tag_categories = list(set(CategorizedTag.objects.values_list('category', flat=True)))
        self.stdout.write(f"Tag categories: {', '.join(tag_categories)}")
        
        # Create a test URL processing request
        url_request = URLProcessingRequest.objects.create(url=example_url)
        self.stdout.write(f"Created test URL processing request: {url_request}")
        
        try:
            # Get the Bedrock client
            client = get_bedrock_client()
            self.stdout.write("Got Bedrock client, initializing...")
            
            # Explicitly initialize the client
            client._initialize_client()
            self.stdout.write("Successfully initialized Bedrock client")
            
            # Process the URL with both the URL and pre-loaded HTML content
            self.stdout.write("Sending request to AWS Bedrock...")
            
            # Read the example HTML
            try:
                with open('tmp/example_values.md', 'r') as f:
                    content = f.read()
                    html_content = content.split('html: ')[1] if 'html: ' in content else ''
                    self.stdout.write(f"Successfully loaded example HTML ({len(html_content)} characters)")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error loading example HTML: {str(e)}"))
                html_content = "<div>Example product page</div>"
            
            # Use the process_url method that properly initializes the client
            result = client.process_url(example_url, existing_tags)
            
            # Update the request with the response
            url_request.mark_as_completed(result)
            
            # Display the response
            self.stdout.write(self.style.SUCCESS('\nSuccessfully processed URL'))
            
            # Extract the JSON from the response
            extracted_data = None
            
            if isinstance(result, dict):
                # Handle new Claude Bedrock response format
                if 'message' in result and 'content' in result['message']:
                    for content_item in result['message']['content']:
                        if 'text' in content_item:
                            text = content_item['text']
                            # Try to extract JSON from ```json blocks (Claude's typical output format)
                            if '```json' in text:
                                json_text = text.split('```json\n')[1].split('\n```')[0]
                                try:
                                    extracted_data = json.loads(json_text)
                                    self.stdout.write(self.style.SUCCESS("Successfully extracted structured data from JSON block"))
                                except json.JSONDecodeError:
                                    self.stdout.write(self.style.WARNING("Failed to parse JSON from code block"))
                            # If no code blocks, try the whole text
                            else:
                                try:
                                    extracted_data = json.loads(text)
                                    self.stdout.write(self.style.SUCCESS("Successfully extracted structured data from text"))
                                except json.JSONDecodeError:
                                    self.stdout.write(self.style.WARNING("Text is not valid JSON"))
                                    self.stdout.write(f"Raw text: {text[:500]}...")
            
            # Display extracted data
            if extracted_data:
                self.stdout.write("\nExtracted Data:")
                self.stdout.write(f"Title: {extracted_data.get('title', 'Not found')}")
                self.stdout.write(f"Short Description: {extracted_data.get('short_description', 'Not found')[:100]}...")
                
                if 'tags' in extracted_data:
                    self.stdout.write("\nExtracted Tags:")
                    for tag in extracted_data['tags']:
                        self.stdout.write(f"  - {tag.get('category', 'Unknown')}: {tag.get('name', 'Unknown')}")
                
                if 'models' in extracted_data:
                    self.stdout.write("\nExtracted Models:")
                    for model in extracted_data['models']:
                        self.stdout.write(f"  - {model.get('name', 'Unknown')}")
                        
                if 'specifications' in extracted_data:
                    self.stdout.write("\nExtracted Specifications:")
                    for spec_group in extracted_data['specifications']:
                        self.stdout.write(f"  {spec_group.get('name', 'Unknown')}:")
                        for spec in spec_group.get('specs', []):
                            self.stdout.write(f"    - {spec.get('key', 'Unknown')}: {spec.get('value', 'Unknown')}")
            else:
                self.stdout.write(self.style.WARNING("\nNo structured data could be extracted"))
                self.stdout.write("Raw response (truncated):")
                self.stdout.write(str(result)[:500] + "...")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error processing URL: {str(e)}'))
            url_request.mark_as_failed(str(e)) 