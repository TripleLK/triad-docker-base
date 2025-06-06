# Detailed Briefing for Developer 2: URL Processing Form and View Update

## What's Been Completed

Developer 1 has successfully:
- Created a `SelectorConfiguration` model to store selector configurations in the database
- Implemented proper validation for the JSON schema
- Created an admin interface for managing these configurations
- Created and tested database migrations

## Current Project Structure

### Key Files and Components

1. **SelectorConfiguration Model** - `apps/ai_processing/models.py`
   - Stores a name, description, and JSON configuration for selectors
   - Has validation to ensure proper schema for the selector configuration
   - Links to a user who created it
   - Timestamps for creation and updates

2. **Admin Interface** - `apps/ai_processing/admin.py`
   - Admin interface for managing selector configurations
   - Handles setting the created_by field automatically

3. **Existing HTML Processing Functions** - `apps/ai_processing/utils.py`
   - `simplify_html_content(url, selectors_config=None)` - Main function that needs to be updated to work with the new model
   - `extract_content_with_selectors(url, selectors_config, keep_newlines=True, add_extra_spacing=True)` - Used by simplify_html_content

4. **URL Processing Views** - `apps/ai_processing/views.py`
   - These will need to be updated to incorporate selector configuration selection

## Your Tasks

Your work will focus on:

1. **Updating the URL processing form** to include selector configuration selection:
   - You'll need to add a dropdown for selecting existing configurations
   - Keep the current selector input field for manual entry
   - Make it clear to users that there are two distinct processing paths

2. **Updating the backend view** to handle both paths:
   - When a configuration is selected: Use `simplify_html_content` with the selected configuration
   - When manual selectors are provided: Use the current process with direct HTML selection

3. **Refactoring the HTML simplification logic** to accept a configuration object:
   - Update `simplify_html_content` to work with the new model
   - Ensure backward compatibility

## Implementation Notes

### Current Selector Configuration Format

The existing `simplify_html_content` function expects a list of dictionaries with this structure:

```python
[
    {
        "selector": "css_selector_string",
        "name": "Section Name",
        "note": "Optional note about this section",
        "preserve_html": True/False  # Optional, defaults to False
    },
    # More selector configurations...
]
```

### How to Get Selector Configurations from the Model

You'll need to fetch the configurations from the database, for example:

```python
from apps.ai_processing.models import SelectorConfiguration

# For a form dropdown
selector_configs = SelectorConfiguration.objects.all()

# To get a specific configuration
config = SelectorConfiguration.objects.get(id=config_id)
selectors_config = config.selector_config  # This is the JSON field containing the list
```

### Forms Update

The form will need to be updated to include:
- A dropdown for selecting an existing configuration
- Logic to show/hide fields based on the selection
- Clear help text explaining the two paths

### View Update

The view needs to:
- Extract the selected configuration when provided
- Use the right processing path based on user selection

## Potential Challenges

1. **Form Conditional Logic**: You'll need to implement JavaScript to show/hide the appropriate form fields based on the user's selection.

2. **Backward Compatibility**: Ensure existing URLs still work and that the system falls back gracefully to manual selectors.

3. **Testing Both Paths**: Make sure both processing paths (configuration-based and manual selectors) work correctly.

## Next Steps

1. First, examine the current form implementation in `apps/ai_processing/forms.py`
2. Then check the view that processes the form in `apps/ai_processing/views.py`
3. Implement the form changes
4. Update the view to handle both processing paths
5. Test both paths thoroughly

Good luck with your implementation! If you encounter any issues, please document them for the next developer. 