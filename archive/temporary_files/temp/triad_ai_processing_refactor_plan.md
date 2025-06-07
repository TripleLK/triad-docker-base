# Triad AI Processing Refactor Implementation Plan

## Overview

This document outlines a detailed implementation plan for enhancing the AI processing functionality in the Triad system. The goals are to:

1. Create a model to store selector configurations
2. Enhance URL processing with selector configuration selection 
3. Streamline the workflow by eliminating the confirmation page
4. Replace batch processing with sequential processing
5. Fix tag appearance in multi-page layouts

Each task is broken down into smaller steps to allow different developers/models to work independently with minimal context requirements.

## Implementation Progress

### Completed Tasks

**Developer 1 Completed Tasks:**
- ✅ Created the `SelectorConfiguration` model in `apps/ai_processing/models.py`
- ✅ Implemented fields for name, description, created/updated timestamps, and JSON field for selector configuration
- ✅ Added FK relationship to user
- ✅ Created and tested model migrations
- ✅ Implemented JSON schema validation for the selector configuration field
- ✅ Created admin interface for managing selector configurations

### Remaining Tasks

**Developer 2 Tasks (Next Steps):**
- Update the URL processing form to include selector configuration selection
- Update the backend view to handle both configuration selection and manual selectors
- Refactor the HTML simplification logic
- Add UI improvements

**Developer 3-5 Tasks:**
- Tasks for removing confirmation page
- Tasks for replacing batch processing with sequential processing
- Tasks for fixing tag appearance

## Implementation Steps

### Step 1: Create Selector Configuration Model

**Developer 1 Tasks:**

1. Design the database model for storing selector configurations
   - Create a new model called `SelectorConfiguration` in `apps/ai_processing/models.py`
   - Include fields for name, description, created/updated timestamps, and JSON field for selector configuration
   - Add FK relationship to user if appropriate

2. Implement migration
   - Generate and apply migrations for the new model
   - Test migration rollback to ensure it's reversible

3. Create admin interface
   - Register model in the admin site
   - Customize admin view with appropriate list display and filtering options

4. Add validation
   - Implement JSON schema validation for selector configurations
   - Add appropriate error handling and user feedback

### Step 2: Modify URL Processing Form and View

**Developer 2 Tasks:**

1. Update the URL processing form to include selector configuration selection
   - Add a dropdown for selecting from existing configurations
   - Maintain current selector input field for manual entry
   - Create conditional logic to show/hide fields based on selection
   - **IMPORTANT**: Make it clear to users that there are two distinct processing paths:
     1. Selecting a pre-configured selector model (uses the HTML simplification process)
     2. Manually specifying selectors (directly sends the selected HTML elements to the prompt)

2. Update the backend view
   - Modify the view to handle both configuration selection and manual selectors
   - Extract the selected configuration when provided
   - Fall back to manual selectors when configuration not selected
   - Implement two distinct processing paths:
     1. When a selector configuration is chosen: Use the `simplify_html_content` function with the selected configuration
     2. When manual selectors are provided: Use the current process that extracts the specified HTML elements and sends them directly to the model

3. Refactor the HTML simplification logic
   - Update the `simplify_html_content` function to accept a configuration object
   - Ensure backward compatibility with existing code
   - Add clear logging to differentiate between the two processing paths

4. Add UI improvements
   - Include tooltip help text explaining the two different approaches and when to use each
   - Add visual indicators showing which path is currently selected
   - Add "Create New Configuration" button if appropriate
   - Provide help text explaining the differences between the two approaches

### Step 3: Eliminate Confirmation Page

**Developer 3 Tasks:**

1. Identify all views and templates using the confirmation page
   - Review URL routing and view functions
   - Map out the current page flow

2. Remove confirmation page logic
   - Update view to skip confirmation step
   - Adjust redirects to send users back to the AI processing base page

3. Update success messages
   - Ensure appropriate feedback is provided without the confirmation page
   - Add appropriate notification when processing completes

4. Clean up old code
   - Remove unused templates
   - Remove unused view functions
   - Update URL patterns

### Step 4: Replace Batch Processing with Sequential Processing

**Developer 4 Tasks:**

1. Modify processing status page
   - Add button to process new URL with current configuration
   - Implement form to pre-populate with current configuration

2. Implement sequential processing
   - Add queue management for Bedrock requests
   - Ensure new requests wait for previous ones to complete
   - Add appropriate status indicators

3. Add state persistence
   - Store last used configuration in user session
   - Implement retrieval of previous configuration

4. Clean up batch processing code
   - Identify all batch processing components
   - Comment out or remove batch processing functionality
   - Update documentation to reflect changes

### Step 5: Fix Tag Appearance in Multi-Page Layouts

**Developer 5 Tasks:**

1. Identify tag display issues
   - Document current appearance with screenshots
   - Note specific CSS classes and HTML structure causing issues
   - Create mockup of desired appearance

2. Update CSS for tags
   - Modify tag styling in relevant CSS files
   - Test across different page layouts
   - Ensure responsive design

3. Update tag templates
   - Modify tag rendering templates if needed
   - Ensure consistent markup across different views

4. Add documentation
   - Add note for final implementation review
   - Include before/after screenshots when available

## Testing Plan

For each step:

1. Write unit tests for new/modified functionality
2. Perform manual testing with different test cases
3. Document edge cases and how they're handled
4. Create test fixtures where appropriate

## Wrap-Up Instructions for Each Developer

When instructed to wrap up, each developer must:

1. Remove any test scripts or temporary utility scripts created during development (except those needed by the next developer)
2. Update this plan document with:
   - A section labeling what has been completed
   - Another section stating what still needs to be done
3. Prepare a detailed briefing for the next developer, including:
   - Current project structure
   - State of the codebase
   - Any challenges encountered and how they were addressed
   - Specific context needed for the next steps
4. **NEVER continue working on the next developer's tasks** - even if they seem simple or you have extra capacity

## Notes for All Developers

- Context windows may fill up before a step is complete. If so, a new developer may need to continue work on the current step
- Each step should be completable in 1-2 turns with a model
- Maintain detailed documentation throughout
- Focus on backward compatibility where possible
- Follow Django best practices for all changes
- **STRICTLY follow the task boundaries** - do not work on tasks assigned to other developers
- **Test your work frequently throughout development** - don't wait until the end to verify functionality
- **Ask the user to manually test** features through the dashboard when it would be more efficient than writing test code
- If you reach a point where you can't proceed without knowing the outcome of a test, ask the user to test it rather than making assumptions 