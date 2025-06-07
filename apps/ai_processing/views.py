import os
import json
import logging
import threading
import datetime
from threading import Thread
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from django.utils.html import format_html
import time

from .models import URLProcessingRequest, BatchURLProcessingRequest, SelectorConfiguration
from .forms import URLProcessingForm, BatchURLProcessingForm
from .utils import (
    process_url_content, 
    get_bedrock_client, 
    extract_structured_data,
    validate_url,
    get_categorized_tags,
    transform_bedrock_data_to_api_format,
    simplify_html_content
)
from apps.categorized_tags.models import CategorizedTag
from apps.base_site.api import create_or_update_lab_equipment, process_tags
from apps.base_site.models import LabEquipmentPage

logger = logging.getLogger(__name__)

@permission_required('ai_processing.add_urlprocessingrequest')
def process_url_view(request):
    """
    View for processing a URL through AWS Bedrock.
    """
    if request.method == 'POST':
        form = URLProcessingForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            
            # Get the selector choice and related data
            selector_choice = form.cleaned_data['selector_choice']
            selector_configuration = form.cleaned_data.get('selector_configuration')
            css_selectors = form.cleaned_data.get('css_selectors', '')
            
            # Validate URL first
            is_valid, error_message = validate_url(url)
            if not is_valid:
                messages.error(request, error_message)
                return render(request, 'wagtailadmin/ai_processing/form.html', {'form': form})
            
            # Create a new URLProcessingRequest
            url_request = URLProcessingRequest.objects.create(
                url=url,
                css_selectors=css_selectors if selector_choice == URLProcessingForm.SELECTOR_CHOICE_MANUAL else '',
                selector_configuration=selector_configuration if selector_choice == URLProcessingForm.SELECTOR_CHOICE_CONFIG else None
            )
            
            # Log information about the processing mode
            if selector_choice == URLProcessingForm.SELECTOR_CHOICE_CONFIG and selector_configuration:
                logger.info(f"Using selector configuration: {selector_configuration.name} (ID: {selector_configuration.id})")
            elif css_selectors:
                logger.info(f"Using manual CSS selectors: {css_selectors}")
            
            # Start processing the URL in the background
            return redirect(reverse('ai_processing:processing_status', args=[url_request.id]))
    else:
        form = URLProcessingForm()
    
    return render(request, 'wagtailadmin/ai_processing/form.html', {'form': form})

@permission_required('ai_processing.view_urlprocessingrequest')
def processing_status_view(request, request_id):
    """
    View for checking the status of a URL processing request.
    """
    url_request = get_object_or_404(URLProcessingRequest, id=request_id)
    
    # Check if the request is completed and has a created page - redirect to dashboard
    if url_request.status == 'completed':
        messages.success(request, f"Processing of URL {url_request.url} completed successfully!")
        # If a page was created, add a message with a link to edit it
        if url_request.created_page_id:
            edit_url = reverse('wagtailadmin_pages:edit', args=[url_request.created_page_id])
            messages.success(
                request, 
                format_html('Lab equipment page was created successfully. <a href="{}">Edit page</a>', edit_url)
            )
        return redirect(reverse('ai_processing:dashboard'))
    
    # Check if a request has been stuck in "processing" state for too long (>5 minutes)
    if url_request.status == 'processing':
        # Calculate time elapsed since creation (or last update)
        time_elapsed = timezone.now() - url_request.created_at
        
        # If processing for more than 5 minutes, mark as failed
        if time_elapsed > datetime.timedelta(minutes=5):
            logger.warning(f"Request {request_id} has been stuck in processing state for {time_elapsed}")
            url_request.mark_as_failed("Processing timed out after 5 minutes")
            messages.warning(request, "Processing timed out. Please try again or check your URL.")
    
    # Initiate processing if the request is still pending
    if url_request.status == 'pending':
        try:
            logger.info(f"Starting to process request {request_id} for URL: {url_request.url}")
            
            # Mark as processing
            url_request.mark_as_processing()
            
            # Start processing in the background - in a real production app, use Celery or similar
            # For now, we'll process it directly in the request (may cause timeout for larger pages)
            thread = Thread(target=process_url_request, args=(request_id,))
            thread.daemon = True
            thread.start()
            
            logger.info(f"Processing thread started for request {request_id}")
            
            # Add a success message
            messages.info(request, "URL processing started in the background. Refresh this page to check progress.")
        except Exception as e:
            logger.exception(f"Error initiating processing for request {request_id}")
            url_request.mark_as_failed(str(e))
            messages.error(request, f"Error starting processing: {str(e)}")
    
    context = {
        'url_request': url_request,
        'can_create_equipment': request.user.has_perm('base_site.add_labequipmentpage'),
    }
    
    return render(request, 'wagtailadmin/ai_processing/processing_status.html', context)

@require_POST
@permission_required('ai_processing.change_urlprocessingrequest')
def create_lab_equipment_view(request, request_id):
    """
    View for creating a lab equipment page from the extracted data.
    """
    url_request = get_object_or_404(URLProcessingRequest, id=request_id)
    
    # Check if the request has been completed and has data
    if url_request.status != 'completed' or not url_request.response_data:
        messages.error(request, 'Cannot create lab equipment: URL processing not completed or no data available.')
        return redirect(reverse('ai_processing:processing_status', args=[url_request.id]))
    
    try:
        # Transform the Bedrock data to API format
        api_data = transform_bedrock_data_to_api_format(url_request.response_data, url_request.url)
        
        # Process tags
        if 'tags' in api_data and api_data['tags']:
            processed_tags = process_tags(api_data['tags'])
            api_data['processed_tag_ids'] = [tag.id for tag in processed_tags]
        
        # Ensure the page is created as a draft (not published)
        api_data['is_published'] = False
        
        # Create the lab equipment page
        result = create_or_update_lab_equipment_internal(api_data)
        
        if result['success']:
            messages.success(request, f'Lab equipment page created successfully as a draft with ID: {result["page_id"]}')
            
            # Redirect to the edit page for the new lab equipment
            edit_url = reverse('wagtailadmin_pages:edit', args=[result['page_id']])
            return redirect(edit_url)
        else:
            messages.error(request, f'Error creating lab equipment page: {result["error"]}')
    
    except Exception as e:
        logger.exception("Error creating lab equipment page")
        messages.error(request, f'Error creating lab equipment page: {str(e)}')
    
    return redirect(reverse('ai_processing:processing_status', args=[url_request.id]))

@require_POST
@permission_required('ai_processing.view_urlprocessingrequest')
def preview_extraction_view(request, request_id):
    """
    View for previewing the extracted data in a user-friendly format.
    """
    url_request = get_object_or_404(URLProcessingRequest, id=request_id)
    
    # Check if the request has been completed and has data
    if url_request.status != 'completed' or not url_request.response_data:
        return JsonResponse({
            'success': False,
            'error': 'URL processing not completed or no data available.'
        })
    
    try:
        # Transform the data for preview (similar to transform_bedrock_data_to_api_format 
        # but with a more user-friendly format)
        preview_data = {
            'title': url_request.response_data.get('title', ''),
            'short_description': url_request.response_data.get('short_description', ''),
            'full_description': url_request.response_data.get('full_description', ''),
            'tags': url_request.response_data.get('tags', []),
            'specifications': url_request.response_data.get('specifications', {}),
            'models': url_request.response_data.get('models', []),
            'images': url_request.response_data.get('images', []),
        }
        
        # Ensure models are in the correct format
        if 'models' in preview_data and preview_data['models']:
            for model in preview_data['models']:
                # If a model still has model_number field from old data, combine it with name
                if 'model_number' in model and model['model_number']:
                    model['name'] = f"{model['name']} ({model['model_number']})"
                    # Remove the model_number field from preview
                    model.pop('model_number', None)
        
        return JsonResponse({
            'success': True,
            'preview_data': preview_data
        })
        
    except Exception as e:
        logger.exception("Error generating preview")
        return JsonResponse({
            'success': False,
            'error': f'Error generating preview: {str(e)}'
        })

def create_or_update_lab_equipment_internal(data):
    """
    Internal function to create or update a lab equipment page.
    This is a simplified version of the API function for use within the Wagtail admin.
    """
    try:
        # Validate required fields
        required_fields = ['title', 'short_description']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return {
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }
        
        # Check if we have an existing page with the same source URL
        existing_page = None
        if 'source_url' in data and data['source_url']:
            try:
                existing_page = LabEquipmentPage.objects.get(source_url=data['source_url'])
            except LabEquipmentPage.DoesNotExist:
                pass
        
        # Ensure the page is created as a draft
        data['is_published'] = False
        
        # Begin creation/update process
        from django.db import transaction
        with transaction.atomic():
            if existing_page:
                # Update existing page
                from apps.base_site.api import update_lab_equipment_page
                result = update_lab_equipment_page(existing_page, data)
            else:
                # Create new page
                from apps.base_site.api import create_lab_equipment_page
                result = create_lab_equipment_page(data)
            
            return result
            
    except Exception as e:
        logger.exception("Error processing lab equipment data")
        return {
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }

@permission_required('ai_processing.change_urlprocessingrequest')
@require_POST
def process_url_ajax(request, request_id):
    """Process a URL asynchronously via AJAX."""
    try:
        process_url_request(request_id)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        logger.error(f"AJAX error processing URL request {request_id}: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def process_url_request(request_id):
    """Process a URL request using the AWS Bedrock client.
    
    Args:
        request_id (int): The ID of the URLProcessingRequest to process
    """
    url_request = get_object_or_404(URLProcessingRequest, id=request_id)
    
    try:
        # Log the start of processing
        logger.info(f"Processing URL request {request_id}: {url_request.url}")
        
        # Mark the request as processing
        url_request.mark_as_processing()
        
        # Get AWS Bedrock client
        client = get_bedrock_client()
        
        # Process URL content (fetch and preprocess HTML)
        logger.info(f"Fetching and preprocessing HTML from {url_request.url}")
        
        # Determine which processing method to use
        if url_request.selector_configuration:
            # Use the simplify_html_content function with the selector configuration
            logger.info(f"Using selector configuration: {url_request.selector_configuration.name}")
            html_content = simplify_html_content(url_request.url, url_request.selector_configuration.selector_config)
        elif url_request.css_selectors:
            # Use the existing process with CSS selectors
            logger.info(f"Using CSS selectors: {url_request.css_selectors}")
            html_content = process_url_content(url_request.url, url_request.css_selectors)
        else:
            # No selectors provided at all, process the entire HTML
            logger.info("No selectors or configuration provided, processing entire HTML")
            html_content = process_url_content(url_request.url)
        
        # Prepare a comprehensive prompt for extracting information from the HTML
        # Include any existing tags for context
        existing_tags = get_categorized_tags()
        
        # Extracted content length for logging
        html_length = len(html_content)
        logger.info(f"Preprocessed HTML length: {html_length} characters")
        
        # Warn if content is too large (Bedrock has token limits)
        if html_length > 200000:  # Arbitrary limit, adjust based on Bedrock's limitations
            logger.warning(f"HTML content is very large ({html_length} chars), it may exceed Bedrock's limits")
        
        if not html_content:
            raise ValueError("Failed to extract HTML content from URL")
        
        logger.info(f"Successfully fetched HTML content (size: {len(html_content)} bytes)")
        
        # Log the number of <br> tags in the content before sending to Bedrock
        br_count = html_content.lower().count('<br')
        logger.info(f"Number of <br> tags before sending to Bedrock: {br_count}")
        
        # Check for and log newline/tab characters
        newline_count = html_content.count('\n')
        tab_count = html_content.count('\t')
        logger.info(f"Content contains {newline_count} newlines and {tab_count} tabs before sending to Bedrock")
        
        # Log a snippet of the content with <br> tags (for debugging)
        if '<br' in html_content.lower():
            # Find a section with <br> tags and show context
            br_index = html_content.lower().find('<br')
            start_index = max(0, br_index - 50)
            end_index = min(len(html_content), br_index + 100)
            br_context = html_content[start_index:end_index]
            logger.info(f"Content around <br> tag: {br_context}")
        
        # Limit the size of HTML content to avoid exceeding Bedrock API limits
        max_size = 100000  # 100KB, increased from 50KB for better coverage
        if len(html_content) > max_size:
            logger.warning(f"HTML content too large ({len(html_content)} bytes), truncating to {max_size} bytes")
            html_content = html_content[:max_size]
        
        # Get existing tags for context
        logger.info("Fetching existing tags for context")
        existing_tags = CategorizedTag.objects.all().values('category', 'name')
        existing_tags_list = [{'category': tag['category'], 'name': tag['name']} for tag in existing_tags]
        logger.info(f"Found {len(existing_tags_list)} existing tags")
        
        # Prepare input variables for Bedrock
        input_variables = {
            'site_html': {'text': html_content},
            'page_url': {'text': url_request.url},
            'existing_tags': {'text': json.dumps(existing_tags_list) if existing_tags_list else ''}
        }
        
        # Call AWS Bedrock
        logger.info("Calling AWS Bedrock API...")
        
        # Get prompt ARN from environment or settings
        prompt_arn = os.environ.get('AWS_BEDROCK_PROMPT_ARN')
        if not prompt_arn:
            prompt_arn = getattr(settings, 'AWS_BEDROCK_PROMPT_ARN', "arn:aws:bedrock:us-east-1:891377295311:prompt/LGO4BMQJG7")
        
        logger.info(f"Using prompt ARN: {prompt_arn}")
        
        bedrock_response = client.converse(
            modelId=prompt_arn,
            promptVariables=input_variables
        )
        
        logger.info("Received response from AWS Bedrock")
        
        # Extract the structured data
        logger.info("Extracting structured data from response")
        result = bedrock_response.get('output', {})
        
        # Log result keys and structure for debugging
        logger.info(f"Bedrock output keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        structured_data = extract_structured_data(result)
        
        if structured_data:
            logger.info("Successfully extracted structured data")
            
            # Log the full_description from the structured data
            full_description = structured_data.get('full_description', '')
            
            # Check for <br> tags in the full_description
            full_desc_br_count = full_description.lower().count('<br')
            logger.info(f"Number of <br> tags in the full_description from Bedrock: {full_desc_br_count}")
            
            # Check for and log newline/tab characters in the full_description
            full_desc_newline_count = full_description.count('\n')
            full_desc_tab_count = full_description.count('\t')
            logger.info(f"Full description contains {full_desc_newline_count} newlines and {full_desc_tab_count} tabs")
            
            # Log the first 200 characters of the full_description
            logger.info(f"Full description snippet: {full_description[:200]}")
            
            # Mark as completed
            url_request.mark_as_completed(structured_data)
            logger.info(f"Request {request_id} marked as completed")
            
            # Set the name field based on response title
            if 'title' in structured_data and structured_data['title']:
                url_request.name = structured_data['title']
                url_request.save(update_fields=['name'])
            
            # Automatically create a draft page from the extracted data
            try:
                # Transform the Bedrock data to API format
                api_data = transform_bedrock_data_to_api_format(structured_data, url_request.url)
                
                # Process tags
                if 'tags' in api_data and api_data['tags']:
                    processed_tags = process_tags(api_data['tags'])
                    api_data['processed_tag_ids'] = [tag.id for tag in processed_tags]
                
                # Ensure the page is created as a draft (not published)
                api_data['is_published'] = False
                
                # Ensure needs_review is set to True
                api_data['needs_review'] = True
                
                # Create the lab equipment page
                result = create_or_update_lab_equipment_internal(api_data)
                
                if result['success']:
                    logger.info(f"Automatically created draft page with ID: {result['page_id']}")
                    url_request.created_page_id = result['page_id']
                    url_request.save(update_fields=['created_page_id'])
                else:
                    logger.error(f"Failed to auto-create page: {result.get('error', 'Unknown error')}")
            except Exception as e:
                logger.exception(f"Error auto-creating page for request {request_id}")
        else:
            error_msg = "Failed to extract structured data from Bedrock response"
            logger.error(error_msg)
            logger.error(f"Raw response content: {result}")
            url_request.mark_as_failed(error_msg)
            
    except Exception as e:
        error_message = str(e)
        logger.exception(f"Error processing URL request {request_id}: {error_message}")
        
        # Mark as failed
        try:
            url_request.mark_as_failed(error_message)
            logger.info(f"Request {request_id} marked as failed")
        except Exception as e2:
            logger.exception(f"Error marking request {request_id} as failed: {str(e2)}")
        
        # Don't re-raise the exception - we've already logged it and marked the request as failed

@permission_required('ai_processing.view_urlprocessingrequest')
def dashboard_view(request):
    """
    Dashboard view for monitoring all URL processing requests.
    Includes filtering by status and pagination.
    """
    # Check if we should show batches or individual requests
    view_type = request.GET.get('view', 'individual')
    
    if view_type == 'batch':
        # Get filter parameters from request
        status_filter = request.GET.get('status', '')
        search_query = request.GET.get('search', '')
        
        # Start with all batches
        batches = BatchURLProcessingRequest.objects.all()
        
        # Apply status filter if specified
        if status_filter and status_filter in ['pending', 'processing', 'completed', 'failed', 'partial']:
            batches = batches.filter(status=status_filter)
        
        # Apply search filter if specified
        if search_query:
            batches = batches.filter(name__icontains=search_query)
        
        # Sort by created_at (newest first)
        batches = batches.order_by('-created_at')
        
        # Paginate the results
        paginator = Paginator(batches, 20)  # Show 20 batches per page
        page = request.GET.get('page')
        
        try:
            paginated_batches = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page
            paginated_batches = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver last page of results
            paginated_batches = paginator.page(paginator.num_pages)
        
        # Prepare context for template
        context = {
            'view_type': 'batch',
            'batches': paginated_batches,
            'status_filter': status_filter,
            'search_query': search_query,
            'total_count': batches.count(),
            'pending_count': BatchURLProcessingRequest.objects.filter(status='pending').count(),
            'processing_count': BatchURLProcessingRequest.objects.filter(status='processing').count(),
            'completed_count': BatchURLProcessingRequest.objects.filter(status='completed').count(),
            'failed_count': BatchURLProcessingRequest.objects.filter(status='failed').count(),
            'partial_count': BatchURLProcessingRequest.objects.filter(status='partial').count(),
        }
        
    else:  # Individual view (default)
        # Get filter parameters from request
        status_filter = request.GET.get('status', '')
        search_query = request.GET.get('search', '')
        batch_filter = request.GET.get('batch', '')
        
        # Start with all requests
        requests = URLProcessingRequest.objects.all()
        
        # Apply status filter if specified
        if status_filter and status_filter in ['pending', 'processing', 'completed', 'failed']:
            requests = requests.filter(status=status_filter)
        
        # Apply search filter if specified
        if search_query:
            requests = requests.filter(url__icontains=search_query)
            
        # Apply batch filter if specified
        if batch_filter:
            if batch_filter == 'nobatch':
                requests = requests.filter(batch__isnull=True)
            else:
                try:
                    batch_id = int(batch_filter)
                    requests = requests.filter(batch_id=batch_id)
                except ValueError:
                    pass
        
        # Sort by created_at (newest first)
        requests = requests.order_by('-created_at')
        
        # Paginate the results
        paginator = Paginator(requests, 20)  # Show 20 requests per page
        page = request.GET.get('page')
        
        try:
            paginated_requests = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page
            paginated_requests = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver last page of results
            paginated_requests = paginator.page(paginator.num_pages)
        
        # Get all batches for the batch filter dropdown
        batches = BatchURLProcessingRequest.objects.all().order_by('-created_at')
        
        # Prepare context for template
        context = {
            'view_type': 'individual',
            'requests': paginated_requests,
            'batches': batches,
            'status_filter': status_filter,
            'search_query': search_query,
            'batch_filter': batch_filter,
            'total_count': requests.count(),
            'pending_count': URLProcessingRequest.objects.filter(status='pending').count(),
            'processing_count': URLProcessingRequest.objects.filter(status='processing').count(),
            'completed_count': URLProcessingRequest.objects.filter(status='completed').count(),
            'failed_count': URLProcessingRequest.objects.filter(status='failed').count(),
        }
    
    return render(request, 'wagtailadmin/ai_processing/dashboard.html', context)

@require_POST
@permission_required('ai_processing.delete_urlprocessingrequest')
def delete_request_view(request, request_id):
    """
    View for deleting a URL processing request.
    """
    url_request = get_object_or_404(URLProcessingRequest, id=request_id)
    url_request.delete()
    messages.success(request, f'Request for {url_request.url} has been deleted.')
    return redirect(reverse('ai_processing:dashboard'))

@require_POST
@permission_required('ai_processing.change_urlprocessingrequest')
def retry_request_view(request, request_id):
    """
    View for retrying a failed or stalled URL processing request.
    """
    url_request = get_object_or_404(URLProcessingRequest, id=request_id)
    
    # Only retry failed requests or stuck processing requests
    if url_request.status not in ['failed', 'processing']:
        messages.error(request, f'Cannot retry request with status {url_request.status}')
        return redirect(reverse('ai_processing:dashboard'))
    
    # Reset the request status to pending
    url_request.status = 'pending'
    url_request.error_message = None
    url_request.save(update_fields=['status', 'error_message'])
    
    messages.success(request, f'Request for {url_request.url} has been queued for retry.')
    return redirect(reverse('ai_processing:processing_status', args=[url_request.id]))

@permission_required('ai_processing.add_batchurlprocessingrequest')
def batch_process_view(request):
    """
    View for submitting a batch of URLs for processing.
    """
    if request.method == 'POST':
        form = BatchURLProcessingForm(request.POST)
        if form.is_valid():
            # Get the validated data
            batch_name = form.cleaned_data['name']
            urls = form.cleaned_data['urls']
            
            # Get the selector choice and related data
            selector_choice = form.cleaned_data['selector_choice']
            selector_configuration = form.cleaned_data.get('selector_configuration')
            css_selectors = form.cleaned_data.get('css_selectors', '')
            
            # Create a new batch
            batch = BatchURLProcessingRequest.objects.create(
                name=batch_name,
                css_selectors=css_selectors if selector_choice == BatchURLProcessingForm.SELECTOR_CHOICE_MANUAL else '',
                selector_configuration=selector_configuration if selector_choice == BatchURLProcessingForm.SELECTOR_CHOICE_CONFIG else None,
                total_urls=len(urls)
            )
            
            # Log information about the processing mode
            if selector_choice == BatchURLProcessingForm.SELECTOR_CHOICE_CONFIG and selector_configuration:
                logger.info(f"Batch created with selector configuration: {selector_configuration.name} (ID: {selector_configuration.id})")
            elif css_selectors:
                logger.info(f"Batch created with CSS selectors: {css_selectors}")
            
            # Create URL processing requests for each URL
            for url in urls:
                # Validate URL first
                is_valid, error_message = validate_url(url)
                if is_valid:
                    URLProcessingRequest.objects.create(
                        url=url,
                        batch=batch,
                        css_selectors=css_selectors if selector_choice == BatchURLProcessingForm.SELECTOR_CHOICE_MANUAL else '',
                        selector_configuration=selector_configuration if selector_choice == BatchURLProcessingForm.SELECTOR_CHOICE_CONFIG else None
                    )
                else:
                    logger.warning(f"Skipping invalid URL in batch: {url} - {error_message}")
            
            # Update batch status
            batch.update_status()
            
            # Start processing the batch in a background thread
            thread = threading.Thread(target=process_batch_urls, args=(batch.id,))
            thread.daemon = True
            thread.start()
            
            messages.success(request, f"Batch '{batch_name}' with {len(urls)} URLs has been submitted for processing.")
            return redirect(reverse('ai_processing:batch_status', args=[batch.id]))
    else:
        form = BatchURLProcessingForm()
    
    return render(request, 'wagtailadmin/ai_processing/batch_form.html', {'form': form})

@permission_required('ai_processing.view_batchurlprocessingrequest')
def batch_status_view(request, batch_id):
    """
    View for checking the status of a batch URL processing request.
    """
    batch = get_object_or_404(BatchURLProcessingRequest, id=batch_id)
    
    # Get individual URL requests in this batch
    url_requests = batch.url_requests.all().order_by('-created_at')
    
    # Apply filters if provided
    status_filter = request.GET.get('status', '')
    if status_filter and status_filter in ['pending', 'processing', 'completed', 'failed']:
        url_requests = url_requests.filter(status=status_filter)
    
    # Paginate the URL requests
    paginator = Paginator(url_requests, 20)  # Show 20 requests per page
    page = request.GET.get('page')
    
    try:
        paginated_requests = paginator.page(page)
    except PageNotAnInteger:
        paginated_requests = paginator.page(1)
    except EmptyPage:
        paginated_requests = paginator.page(paginator.num_pages)
    
    # Prepare context for template
    context = {
        'batch': batch,
        'url_requests': paginated_requests,
        'status_filter': status_filter,
        'pending_count': batch.url_requests.filter(status='pending').count(),
        'processing_count': batch.url_requests.filter(status='processing').count(),
        'completed_count': batch.url_requests.filter(status='completed').count(),
        'failed_count': batch.url_requests.filter(status='failed').count(),
    }
    
    return render(request, 'wagtailadmin/ai_processing/batch_status.html', context)

def process_batch_urls(batch_id, rate_limit_delay=2):
    """
    Process all URLs in a batch sequentially (one at a time).
    This function is designed to be run in a background thread.
    
    Args:
        batch_id: ID of the BatchURLProcessingRequest
        rate_limit_delay: Delay between processing requests (in seconds)
    """
    logger.info(f"Starting sequential batch processing for batch ID: {batch_id}")
    
    try:
        batch = BatchURLProcessingRequest.objects.get(id=batch_id)
    except BatchURLProcessingRequest.DoesNotExist:
        logger.error(f"Batch ID {batch_id} not found")
        return
    
    # Update batch status to processing
    batch.status = 'processing'
    batch.save(update_fields=['status'])
    
    # Get all pending requests for this batch
    pending_requests = URLProcessingRequest.objects.filter(
        batch_id=batch_id,
        status='pending'
    ).order_by('created_at')  # Process in order of creation
    
    logger.info(f"Found {pending_requests.count()} pending requests in batch {batch_id}")
    
    # Process each URL one at a time
    for request in pending_requests:
        logger.info(f"Processing URL: {request.url} (Request ID: {request.id})")
        
        # Process this URL
        process_url_request(request.id)
        
        # Update batch status after each request
        batch.refresh_from_db()
        batch.update_status()
        
        # Rate limiting delay between requests
        time.sleep(rate_limit_delay)
    
    # Auto-create pages for completed requests that don't have pages yet
    completed_requests = URLProcessingRequest.objects.filter(
        batch_id=batch_id,
        status='completed',
        created_page_id__isnull=True
    )
    
    logger.info(f"Auto-creating pages for {completed_requests.count()} completed requests in batch {batch_id}")
    
    for request in completed_requests:
        try:
            # Transform the Bedrock data to API format
            api_data = transform_bedrock_data_to_api_format(request.response_data, request.url)
            
            # Process tags
            if 'tags' in api_data and api_data['tags']:
                processed_tags = process_tags(api_data['tags'])
                api_data['processed_tag_ids'] = [tag.id for tag in processed_tags]
            
            # Ensure the page is created as a draft (not published)
            api_data['is_published'] = False
            
            # Ensure needs_review is set to True
            api_data['needs_review'] = True
            
            # Create the lab equipment page
            result = create_or_update_lab_equipment_internal(api_data)
            
            if result['success']:
                logger.info(f"Automatically created draft page with ID: {result['page_id']} for URL: {request.url}")
                request.created_page_id = result['page_id']
                request.save(update_fields=['created_page_id'])
            else:
                logger.error(f"Failed to auto-create page for URL {request.url}: {result.get('error', 'Unknown error')}")
        except Exception as e:
            logger.exception(f"Error auto-creating page for request {request.id}")
    
    # Update the batch status one final time
    batch.refresh_from_db()
    batch.update_status()
    
    logger.info(f"Batch processing complete for batch ID: {batch_id}")

@require_POST
@permission_required('ai_processing.delete_batchurlprocessingrequest')
def delete_batch_view(request, batch_id):
    """
    View for deleting a batch URL processing request and all its URL requests.
    """
    batch = get_object_or_404(BatchURLProcessingRequest, id=batch_id)
    batch_name = batch.name
    
    # Delete all URL requests in this batch
    batch.url_requests.all().delete()
    
    # Delete the batch
    batch.delete()
    
    messages.success(request, f'Batch "{batch_name}" has been deleted.')
    return redirect(reverse('ai_processing:dashboard'))

@require_POST
@permission_required('ai_processing.change_batchurlprocessingrequest')
def retry_batch_view(request, batch_id):
    """
    View for retrying failed URLs in a batch.
    """
    batch = get_object_or_404(BatchURLProcessingRequest, id=batch_id)
    
    # Get all failed requests in this batch
    failed_requests = batch.url_requests.filter(status='failed')
    count = failed_requests.count()
    
    if count == 0:
        messages.info(request, f'No failed requests to retry in batch "{batch.name}".')
        return redirect(reverse('ai_processing:batch_status', args=[batch_id]))
    
    # Reset failed requests to pending
    failed_requests.update(status='pending', error_message=None)
    
    # Update batch status
    batch.status = 'processing'
    batch.save(update_fields=['status'])
    
    # Start processing in a background thread
    thread = threading.Thread(target=process_batch_urls, args=(batch.id,))
    thread.daemon = True
    thread.start()
    
    messages.success(request, f'Retrying {count} failed requests in batch "{batch.name}".')
    return redirect(reverse('ai_processing:batch_status', args=[batch_id]))

@require_POST
def api_batch_process(request):
    """
    API endpoint for submitting a batch of URLs for processing.
    Expects JSON data with:
    - name: batch name
    - urls: list of URLs to process
    - api_key: for authentication
    
    Returns JSON with:
    - success: boolean
    - batch_id: ID of the created batch
    - message: status message
    """
    try:
        # Check if JSON data
        if request.content_type != 'application/json':
            return JsonResponse({
                'success': False,
                'message': 'Request must be in JSON format'
            }, status=400)
        
        # Parse JSON data
        data = json.loads(request.body)
        
        # Check required fields
        if 'name' not in data:
            return JsonResponse({
                'success': False,
                'message': 'Batch name is required'
            }, status=400)
            
        if 'urls' not in data or not data['urls']:
            return JsonResponse({
                'success': False,
                'message': 'URLs list is required'
            }, status=400)
            
        if 'api_key' not in data:
            return JsonResponse({
                'success': False,
                'message': 'API key is required'
            }, status=401)
        
        # Validate API key
        api_key = data['api_key']
        expected_api_key = os.environ.get('AI_PROCESSING_API_KEY', '')
        
        if not expected_api_key or api_key != expected_api_key:
            return JsonResponse({
                'success': False,
                'message': 'Invalid API key'
            }, status=401)
        
        # Create the batch
        batch_name = data['name']
        urls = data['urls']
        
        if not isinstance(urls, list):
            return JsonResponse({
                'success': False,
                'message': 'URLs must be a list'
            }, status=400)
        
        # Create batch
        batch = BatchURLProcessingRequest.objects.create(
            name=batch_name,
            total_urls=len(urls)
        )
        
        # Create URL requests
        valid_count = 0
        invalid_urls = []
        
        for url in urls:
            # Validate URL
            is_valid, error_message = validate_url(url)
            
            if is_valid:
                URLProcessingRequest.objects.create(
                    url=url,
                    batch=batch
                )
                valid_count += 1
            else:
                invalid_urls.append({'url': url, 'error': error_message})
        
        # Update batch status
        batch.update_status()
        
        # No valid URLs
        if valid_count == 0:
            batch.delete()
            return JsonResponse({
                'success': False,
                'message': 'No valid URLs provided',
                'invalid_urls': invalid_urls
            }, status=400)
        
        # Start processing in background
        thread = threading.Thread(target=process_batch_urls, args=(batch.id,))
        thread.daemon = True
        thread.start()
        
        # Return success response
        return JsonResponse({
            'success': True,
            'batch_id': batch.id,
            'message': f'Batch created with {valid_count} valid URLs',
            'invalid_urls': invalid_urls if invalid_urls else None
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        logger.exception('Error in API batch process')
        return JsonResponse({
            'success': False,
            'message': f'Server error: {str(e)}'
        }, status=500) 