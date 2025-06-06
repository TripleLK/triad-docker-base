# AWS Bedrock Integration - Day 1: Project Setup and Integration Testing

## Overview
This briefing outlines the implementation of a new Django app that provides an admin interface for interacting with AWS Bedrock AI models. The app allows administrators to input a URL, which is processed by a Bedrock AI model to extract structured information about lab equipment.

## Current Project Context
The system is a Django-Wagtail application for a lab equipment catalog. It currently includes:
- Custom tagging system (`categorized_tags` app)
- Content management through Wagtail admin
- Management commands for various operations
- Existing apps organized in the `apps/` directory

## ✅ Completed Objectives
1. Set up the project infrastructure for AWS Bedrock integration
2. Create the new Django app structure
3. Configure AWS authentication and connection
4. Successfully test the AWS Bedrock integration with real credentials
5. Implement proper response parsing and data extraction
6. Optimize HTML processing to reduce payload size
7. Integrate with the existing categorized_tags system
8. Implement validation and security checks
9. Create an admin dashboard for monitoring processing requests
10. Implement proper error handling and logging
11. Fix HTML formatting issues in extracted content
12. Implement batch processing for multiple URLs

## Completed Tasks

### ✅ 1. Created New Django App
- Created a new app called `ai_processing` within the `apps` directory
- Set up the basic app structure:
  - Created models for URL processing requests
  - Created forms for submitting URLs
  - Created views for handling requests
  - Created templates for the Wagtail admin interface
  - Added URL routing
  - Integrated with the Wagtail admin menu
- Registered the app in Django settings (automatically handled by Django's app discovery)

The app follows the structure:
```
apps/ai_processing/
├── __init__.py
├── admin.py
├── apps.py
├── forms.py
├── management/
│   ├── __init__.py
│   └── commands/
│       ├── __init__.py
│       └── test_bedrock.py
├── migrations/
│   └── __init__.py
├── models.py
├── README.md
├── templates/
│   └── wagtailadmin/
│       └── ai_processing/
│           ├── dashboard.html
│           ├── form.html
│           └── processing_status.html
├── urls.py
├── utils.py
├── views.py
└── wagtail_hooks.py
```

### ✅ 2. AWS Authentication Setup
- Implemented secure AWS credential management using environment variables
- Added AWS credentials to environment files in `/envs` directory:
  - AWS_ACCESS_KEY_ID
  - AWS_SECRET_ACCESS_KEY
  - AWS_REGION (using us-east-1)
  - AWS_BEDROCK_PROMPT_ARN
- Created utility functions that load credentials from environment variables

### ✅ 3. Bedrock Client Configuration
- Created a utility module (utils.py) for AWS Bedrock client initialization
- Implemented connection error handling and retry logic
- Ensured the client can properly authenticate with AWS
- Added a factory function for client instantiation

### ✅ 4. Integration Testing
- Created a test command for verifying AWS Bedrock integration
- Successfully tested the integration with live AWS credentials
- Verified proper response parsing and structured data extraction
- Confirmed integration with existing tag categories system
- Validated the complete request flow: pending → processing → completed

### ✅ 5. HTML Preprocessing
- Implemented HTML preprocessing to reduce payload size
- Created utility function for HTML processing that:
  - Extracts only the body content
  - Removes script, style tags, and other unnecessary elements
  - Strips excess whitespace
  - Significantly reduces the size of HTML sent to Bedrock

### ✅ 6. Tag System Integration
- Added functions to fetch categorized tags and categories from the database
- Integrated tag loading into the main request flow
- Updated the process_url method to use existing tags
- Ensured proper integration with the existing categorized_tags system

### ✅ 7. Validation and Security Checks
- Added URL validation before processing
- Implemented HTML size limits (5MB max)
- Created comprehensive error handling and logging
- Added validation of content types to ensure HTML responses

### ✅ 8. Admin Dashboard Implementation
- Created a dashboard view for monitoring URL processing requests
- Implemented filtering by status and search functionality
- Added pagination for handling large numbers of requests
- Created action buttons for managing requests (retry, delete, view)
- Added status tracking with visual indicators

## AWS Bedrock Integration Approach
The integration uses the AWS SDK for Python (boto3) to interact with Bedrock services:

- Initialization of the Bedrock runtime client using environment variables
- Using the correct prompt ARN
- Properly formatting the input variables (site_html, page_url, existing_tags)
- Handling and processing the response

The implementation uses the `converse` method:
```python
bedrock_response = client.converse(
    modelId=self.model_id,
    promptVariables=input_variables
)
```

## Security Considerations Implemented
- AWS credentials are stored in environment variables, not in code
- Added proper error handling for failed API calls
- Added validation for user input before sending to Bedrock
- Implemented status tracking for requests
- Ensured credentials are loaded from the appropriate environment files
- Added HTML size limits to prevent excessive payload sizes
- Implemented URL validation to ensure only valid URLs are processed

## Data Processing Capabilities
The integration now successfully extracts structured data from lab equipment product pages:
- Product title and description
- Manufacturer information
- Technical specifications
- Categorized tags matching our existing taxonomy
- Product models and their details
- Image URLs

## Completed Outcomes
1. ✅ New Django app structure created and ready for use
2. ✅ AWS credential management configured securely
3. ✅ Working utility for Bedrock client initialization
4. ✅ Successfully tested AWS Bedrock connectivity with real credentials
5. ✅ Wagtail admin integration for URL processing
6. ✅ Implemented proper structured data extraction from responses
7. ✅ Successfully integrated with existing categorized_tags system
8. ✅ Optimized HTML processing to reduce payload size
9. ✅ Added validation and security checks
10. ✅ Created monitoring dashboard for URL processing
11. ✅ Implemented batch processing for multiple URLs

## Next Steps
1. ✅ ~~Move tag functionality from test command into the app itself~~
2. ✅ ~~Optimize HTML processing by:~~
   - ~~Including only the body content~~
   - ~~Removing script tags and other unnecessary elements~~
   - ~~Reducing the overall size of the HTML sent to Bedrock~~
3. ✅ ~~Integrate with lab equipment database to store extracted data~~
4. ✅ ~~Create dashboard for monitoring URL processing~~
5. ✅ ~~Implement batch processing for multiple URLs~~
6. Extract common specifications from model-specific specs to universal specs level
   - Analyze patterns in model-specific specifications
   - Create algorithms to identify common specs across models
   - Implement automatic consolidation of universal specifications
7. Implement tag normalization with AI assistance
   - Create a system for suggesting normalized tag forms
   - Add interface for approving normalized tags
   - Implement batch tag normalization
8. Enhance the UI to display structured data in a more user-friendly format

## Implementation Notes
- The project follows Django-Wagtail conventions throughout
- Integration has been tested with real AWS credentials and is functioning correctly
- The integration properly handles the current Bedrock API response format
- The system successfully integrates with the existing categorized_tags system
- HTML preprocessing significantly reduces payload size
- Dashboard provides clear status tracking for all URL processing requests

## Lab Equipment Database Integration

### Overview
The integration with the lab equipment database allows administrators to transform AI-extracted data into actual LabEquipmentPage entries in the Wagtail CMS. This completes the workflow from URL submission to database entry, all within the Wagtail admin interface.

### Integration Components
1. **Data Transformation Utilities**
   - Created utility functions to transform AI-extracted data into the format required by the base_site API
   - Implemented proper handling of tags, specifications, models, and images
   - Added validation and error handling

2. **Admin Interface**
   - Added a processing status view to track URL processing
   - Implemented preview functionality to review extracted data before saving
   - Created an interface for approving and importing data to the database
   - Added UI components for better user experience
   - Implemented a central dashboard for monitoring all processing requests

3. **Database Integration**
   - Used the existing base_site API for creating lab equipment pages
   - Ensured proper tag processing and relationship handling
   - Implemented model specifications and images import
   - Added validation checks before database insertion

4. **Background Processing**
   - Created a management command for processing URLs in the background
   - Added status tracking and error handling
   - Ensured secure credential management

### Workflow
1. Admin submits a URL through the AI Processing interface
2. URL is processed by AWS Bedrock (either immediately or in the background)
3. Admin can preview the extracted data in a user-friendly format
4. Admin can approve the data and create a lab equipment entry
5. The system transforms the data and creates a LabEquipmentPage
6. Admin is redirected to the Wagtail edit page for final review

### Security and Performance Considerations
- Proper permission checks for all admin views
- Validation of data before database insertion
- Handling of image URLs and external content
- Error tracking and reporting
- Status tracking for long-running processes

### Integration With Existing Systems
- Uses the existing LabEquipmentPage model
- Leverages the categorized_tags system
- Works with the existing Wagtail admin interface
- Follows Wagtail best practices for content management
- Reuses the existing base_site API for database operations

## Batch Processing Implementation

### Overview
The batch processing system allows administrators to submit multiple URLs at once for processing by AWS Bedrock. This greatly improves efficiency when processing many lab equipment pages.

### Implementation Components
1. **Data Models**
   - Created `BatchURLProcessingRequest` model to track batch operations
   - Added relationship between individual `URLProcessingRequest` and batches
   - Implemented status tracking and progress calculation

2. **Processing Logic**
   - Implemented threaded processing with rate limiting
   - Added concurrent request management (default 3 concurrent requests)
   - Created batch-level status tracking based on individual URL statuses
   - Implemented proper error handling to ensure individual failures don't affect the batch

3. **Admin Interface**
   - Created a batch submission form for entering multiple URLs
   - Added batch status monitoring view with progress tracking
   - Implemented batch-level actions (retry failed URLs, delete batch)
   - Enhanced the dashboard to toggle between individual and batch views

4. **API Integration**
   - Created an API endpoint for programmatic batch submission
   - Implemented security with API key authentication
   - Added validation and error handling for the API

### Workflow
1. Admin submits multiple URLs through the batch form or API
2. System creates a batch and individual URL processing requests
3. Background thread processes URLs concurrently with rate limiting
4. Admin can monitor batch progress through the dashboard
5. Admin can view individual URL statuses within the batch
6. Failed URLs can be retried without reprocessing successful ones

### Security and Performance Considerations
- Rate limiting to prevent API overload
- Configurable concurrency for different server capacities
- API key authentication for programmatic access
- Progress tracking and status updates
- Transaction handling to prevent data corruption
