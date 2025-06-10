# AI JSON to LabEquipmentPage API Conversion Prompt

## Task
Convert enhanced AI JSON output from Iron Catalyst pipeline into the JSON format required for LabEquipmentPageCreateUpdateSerializer API.

## Input Format
```json
{
  "url": "{{SOURCE_URL}}",
  "site_domain": "{{SITE_DOMAIN}}",
  "field_configurations": {
    "title": {"extracted_content": [{"extracted_data": [{"text": "..."}]}]},
    "short_description": {"extracted_content": [{"extracted_data": [{"text": "..."}]}]},
    "full_description": {"extracted_content": [{"extracted_data": [{"text": "..."}]}]},
    "features": {"extracted_content": [{"extracted_data": [{"text": "..."}]}]},
    "models": {"extracted_content": [{"extracted_data": [{"text": "..."}]}]},
    "accessories": {"extracted_content": [{"extracted_data": [{"text": "...", "attributes": {"src": "..."}}]}]},
    "categorized_tags": {"extracted_content": [{"extracted_data": [{"text": "..."}]}]}
  }
}
```

## Required Output
```json
{
  "title": "{{EQUIPMENT_TITLE}}",
  "slug": "{{AUTO_GENERATED_SLUG}}",
  "short_description": "{{SHORT_DESCRIPTION_HTML}}",
  "full_description": "{{FULL_DESCRIPTION_HTML}}",
  "source_url": "{{SOURCE_URL}}",
  "source_type": "{{SOURCE_TYPE}}",
  "data_completeness": {{DATA_COMPLETENESS_SCORE}},
  "specification_confidence": "{{CONFIDENCE_LEVEL}}",
  "needs_review": true,
  "categorized_tags": [{{CATEGORIZED_TAGS_ARRAY}}],
  "specifications": {{SPECIFICATIONS_JSON}},
  "models_data": {{MODELS_DATA_JSON}},
  "features_data": [{{FEATURES_LIST}}]
}
```

## Transformation Rules

### Core Fields
- **title**: Extract from `field_configurations.title.extracted_content[0].extracted_data[0].text`
- **slug**: Generate from title (lowercase, hyphens, no special chars)
- **short_description**: Extract from `short_description` field, clean HTML format
- **full_description**: Extract from `full_description` field, rich HTML format
- **source_url**: Use input JSON `url` field
- **source_type**: Set to "{{SOURCE_TYPE}}" (default: "new")

### Quality Metrics
- **data_completeness**: Calculate 0.0-1.0 based on field completion
  - Title: +0.3, Descriptions: +0.2, Features: +0.2, Models: +0.2, URL: +0.1
- **specification_confidence**: "high"/"medium"/"low" based on content quality
- **needs_review**: Always `true` for AI-generated content

### Structured Data
- **categorized_tags**: Extract from `categorized_tags` field, return array of tag name strings
- **features_data**: Extract from `features` field, split into array of feature strings
- **models_data**: Parse `models` field into structured model objects
- **specifications**: Extract specs from `models` field, organize into spec groups

### Content Processing
1. Clean excessive whitespace, normalize formatting
2. Convert to appropriate HTML for rich text fields
3. Split multi-value content appropriately
4. Handle missing fields with fallbacks
5. Preserve image URLs from attributes where relevant

## Template Variables
- `{{EQUIPMENT_TITLE}}`: Cleaned title text
- `{{AUTO_GENERATED_SLUG}}`: URL-safe slug
- `{{SHORT_DESCRIPTION_HTML}}`: Formatted short description
- `{{FULL_DESCRIPTION_HTML}}`: Rich HTML full description  
- `{{SOURCE_URL}}`: Original extraction URL
- `{{SOURCE_TYPE}}`: Equipment type ("new", "used", "refurbished")
- `{{DATA_COMPLETENESS_SCORE}}`: Completeness score 0.0-1.0
- `{{CONFIDENCE_LEVEL}}`: Confidence level string
- `{{CATEGORIZED_TAGS_ARRAY}}`: Tag names as string array
- `{{SPECIFICATIONS_JSON}}`: Nested specifications structure
- `{{MODELS_DATA_JSON}}`: Array of model objects
- `{{FEATURES_LIST}}`: Array of feature strings

## Output Requirements
Generate valid JSON for LabEquipmentPageCreateUpdateSerializer with:
- Proper JSON syntax and formatting
- All required fields present
- Appropriate data types (strings, arrays, objects, numbers, booleans)
- Clean HTML in rich text fields
- Structured arrays and objects for complex fields

Transform the provided AI JSON into this API-ready format. 