# AWS Bedrock Integration - Day 2: Admin Interface & Form Implementation

## Overview
This briefing outlines the second day of implementing a new Django app that provides an admin interface for interacting with AWS Bedrock AI models. Today's focus is on creating the admin UI components and implementing the form handling for URL submissions.

## Current Status
By now, we should have completed:
- Basic app structure for `ai_processing`
- AWS Bedrock client configuration
- Environment variable setup for AWS credentials

## Today's Objectives
1. Create the Wagtail admin menu integration
2. Implement the URL submission form
3. Create the views for handling form submission
4. Implement the initial UI for displaying results

## Detailed Tasks

### 1. Wagtail Admin Integration
- Implement the `wagtail_hooks.py` file to register the admin views
- Create custom menu items in the Wagtail admin sidebar
- Set up proper permissions for accessing the admin interface

Wagtail hooks are used to extend the Wagtail admin interface. Looking at existing examples like `apps/categorized_tags/wagtail_hooks.py` will provide guidance on how to structure this integration. The goal is to create a dedicated section in the admin for our AI processing functionality.

### 2. Form Implementation
- Create a form class in `forms.py` for URL submission
- Implement validation for URL inputs
- Add fields for any additional parameters needed for the Bedrock model

The form should be simple but robust, validating that the URL is properly formatted and reachable. Consider adding optional fields that might help with the AI processing (e.g., context about the page, specific sections to focus on).

### 3. View Implementation
- Create a view for displaying the URL submission form
- Implement the view that handles form submission and calls the Bedrock API
- Create a results view for displaying the processed data

The view architecture should follow the pattern:
1. Display form → 2. Submit URL → 3. Process with Bedrock → 4. Display results

### 4. Template Creation
- Create the necessary HTML templates for the admin interface
- Implement a form template for URL submission
- Create a results template for displaying the AI-processed data

Templates should be placed in the `templates/wagtailadmin/ai_processing/` directory and follow Wagtail's admin UI conventions for consistency.

## Bedrock Integration Details
When processing the form submission, we need to:

1. Extract the URL from the form data
2. Fetch the HTML content from the URL
3. Format the input variables for the Bedrock prompt:
   ```python
   input_variables = {
       'site_html': {'text': html_content},
       'page_url': {'text': url},
       'existing_tags': {'text': existing_tags_json}
   }
   ```
4. Call the Bedrock API using the converse method
5. Parse the JSON response from the model
6. Format and display the results

## Handling Asynchronous Processing
Consider implementing asynchronous processing for long-running requests:
- Implement a background task queue for processing URLs
- Show a loading indicator or status page
- Notify the user when processing is complete

## Error Handling
Implement robust error handling for:
- URL fetch failures
- Bedrock API errors
- Invalid or unexpected AI responses
- Timeouts and rate limits

## Expected Outcomes
By the end of Day 2, we should have:
1. A functional admin interface in the Wagtail admin
2. A working form for URL submission
3. Initial integration with the Bedrock API for processing
4. Basic results display for the AI-processed data

## Notes for Implementation
- Reference the `WorkingCall.ipynb` for the correct API call structure
- Look at existing admin interfaces in the project for UI consistency
- Remember to properly escape and sanitize HTML content from external URLs before display
- Consider adding a preview of the fetched URL content before processing
