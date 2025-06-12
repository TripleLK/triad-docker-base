# AI JSON to LabEquipmentPage API Conversion Prompt

## Task
Convert enhanced JSON output from an extraction pipeline into SEO-optimized JSON format required for LabEquipmentPageCreateUpdateSerializer API. Your goal is to maximize SEO performance by intelligently using ALL available data from ANY field in the input to create the most comprehensive, search-engine-friendly output possible.

## Cross-Field Intelligence
**IMPORTANT**: You have access to ALL extracted data and should intelligently cross-reference information between fields to:
- Enhance SEO metadata with relevant technical specifications
- Create comprehensive descriptions using features, models, and specifications data
- Generate rich keyword lists from all available content
- Build complete structured data using any relevant information
- Maximize search visibility by leveraging every data point available

## PROCESSING MODES

The prompt operates in two distinct modes based on the `_processing_mode` field:

### MODE 1: Overall Details
**When `_processing_mode` is "OVERALL_DETAILS":**
- Generate ALL fields EXCEPT `models_data`
- Include ONLY universal specifications that apply to ALL models in `specifications`
- Extract SEO content, descriptions, keywords, etc. from all available data
- Build comprehensive equipment overview without model-specific details
- **PROCESS IMAGES**: Extract and format image data from `gallery_images` field

### MODE 2: Model Subset  
**When `_processing_mode` is "MODEL_SUBSET":**
- Generate ONLY the `models_data` array
- Include ALL models provided in the input `models` field
- EXCLUDE any specifications that are universal across ALL models (these belong in Overall Details mode)
- Include only model-specific specifications and features
- Output format: `{"models_data": [...]}`

**IMPORTANT**: This prompt is designed for two-mode processing only. Equipment data should always be split between Overall Details and Model Subset modes for optimal token utilization and comprehensive data coverage.

## INPUT DATA STRUCTURE AND IMAGE PROCESSING

### Gallery Images Field Structure
Input may contain a `gallery_images` field with this structure:
```json
{
  "gallery_images": {
    "extracted_content": [
      {
        "extracted_data": [
          {
            "html": "<div class=\"image-wrapper\"><img src=\"/wp-content/uploads/2021/12/PDT_CA30S_Right.png\" alt=\"\"><img src=\"/wp-content/uploads/2021/12/PDT_CA30T_Front_Open.png\" alt=\"\">...</div>"
          }
        ]
      }
    ]
  }
}
```

### Image Processing Requirements
**CRITICAL**: When processing images in Overall Details mode:

1. **Extract Image URLs**: Parse the HTML in `gallery_images.extracted_content[].extracted_data[].html` to find all `<img src="...">` tags
2. **Convert to Full URLs**: 
   - If `src` starts with `/`, prepend the domain from `site_domain` field (e.g., `"https://www.airscience.com"`)
   - If `src` is already a full URL, use as-is
3. **Create Image References**: Generate both fields:
   - `image_urls`: Array of full URLs for download system
   - `alt_text_suggestions`: Descriptive alt text for each image

### Image Output Format
```json
{
  "image_urls": [
    "https://www.airscience.com/wp-content/uploads/2021/12/PDT_CA30S_Right.png",
    "https://www.airscience.com/wp-content/uploads/2021/12/PDT_CA30T_Front_Open.png"
  ],
  "alt_text_suggestions": [
    "SafeFUME CA30S cyanoacrylate fuming chamber right view",
    "SafeFUME CA30T front view with door open for fingerprint processing"
  ]
}
```

## Input Data Structure
You will receive: `{{INPUT_JSON_DATA}}`

This contains extracted website data with field configurations including:
- `title` - Product title
- `short_description` - Brief product description  
- `full_description` - Detailed product information
- `features` - Product features and capabilities
- `models` - Model specifications and details
- `gallery_images` - Product images (see Image Processing section above)
- `site_domain` - Website domain for constructing full image URLs
- Various technical specifications and compliance data
- `_processing_mode` - Optional: "OVERALL_DETAILS" or "MODEL_SUBSET"
- `_batch_info` - Optional: Batch coordination metadata
- `extracted_specification_groups` - Optional: Exact group names to use from content extractor
- `_specification_instructions` - Optional: Specification handling requirements

## Required Output Format

### STRICT REQUIREMENTS (Always the same when included)
```json
{
  "source_type": "new",
  "needs_review": true,
  "data_completeness": 0.8-1.0,
  "specification_confidence": "high|medium|low"
}
```

### Overall Details Mode Output
```json
{
  "source_type": "new",
  "needs_review": true,
  "data_completeness": 0.8-1.0,
  "specification_confidence": "high|medium|low",
  "title": "SEO-optimized product title",
  "slug": "url-friendly-slug",
  "meta_title": "60-char optimized title",
  "meta_description": "155-char compelling description",
  "meta_keywords": "comma-separated primary keywords",
  "short_description": "<p>HTML formatted brief description</p>",
  "full_description": "<div>HTML with structured content</div>",
  "seo_content": "<div>Additional SEO-focused content</div>",
  "source_url": "original URL",
  "target_keywords": ["primary", "keywords", "array"],
  "related_keywords": ["related", "terms", "array"],
  "technical_keywords": ["technical", "specifications", "terms"],
  "categorized_tags": [
    {"category": "Equipment Type", "tag": "specific equipment"},
    {"category": "Application", "tag": "primary use"},
    {"category": "Industry", "tag": "target industry"},
    {"category": "Technology", "tag": "key technology"},
    {"category": "Compliance", "tag": "standards met"}
  ],
  "specifications": {
    "Universal_Group_Name": {
      "spec_key": "value that applies to ALL models",
      "another_universal_spec": "universal value"
    }
  },
  "features_data": ["comprehensive", "feature", "list"],
  "applications": ["detailed", "application", "list"],
  "structured_data": {
    "@type": "Product",
    "@context": "https://schema.org/",
    "name": "product name",
    "description": "structured data description",
    "manufacturer": "manufacturer name",
    "category": "product category"
  },
  "image_urls": ["https://full-url-to-image1.png", "https://full-url-to-image2.png"],
  "alt_text_suggestions": ["descriptive alt text for image1", "descriptive alt text for image2"],
  "page_content_sections": {
    "overview": "section content",
    "specifications": "section content", 
    "applications": "section content",
    "models": "section content"
  }
}
```

### Model Subset Mode Output
```json
{
  "models_data": [
    {
      "model_name": "exact model identifier",
      "specifications": {
        "Model_Specific_Group": {
          "spec_key": "value unique to this model",
          "dimension": "specific to this model only"
        }
      },
      "features": ["model-specific", "features", "only"],
      "seo_description": "SEO-optimized model description"
    }
  ]
}
```

## SPECIFICATIONS HANDLING - CRITICAL

### Universal vs Model-Specific Specification Rules

**OVERALL DETAILS MODE:**
- Include ONLY specifications that are identical across ALL models in the entire product line
- Examples: Construction material, electrical voltage, compliance standards, filter types
- Group by logical categories: "Construction", "Electrical", "Compliance", "Filtration"
- These specifications will NOT be repeated in any model's individual specifications

**MODEL SUBSET MODE:**
- Include ONLY specifications that vary between models OR are unique to specific models
- Examples: Dimensions, weights, capacities, model-specific features
- EXCLUDE any specification that appears identically across all models
- Group by logical categories: "Dimensions", "Weight", "Performance", "Model Features"

### Cross-Mode Consistency Rules
1. **No Duplication**: A specification appears in either universal specs OR model specs, never both
2. **Complete Coverage**: Every specification from source data must appear somewhere
3. **Logical Grouping**: Use consistent group names across modes where applicable

## OUTPUT EFFICIENCY STRATEGIES

### Condensed Formatting (when needed)
- Use abbreviated but clear keys: "w"/"width", "h"/"height", "temp"/"temperature"
- Combine related specs: "net_weight": "156 lbs | 71 kg"
- Use efficient formatting: "24\" | 610 mm"

### Strategic Content Organization
- Prioritize most important technical specifications
- Use concise but complete descriptions
- Maintain consistency across all processing modes

## Cross-Field Intelligence Examples

**Title Enhancement**: If features mention "programmable control" and specs show "humidity control", create title: "Programmable Humidity-Controlled [Equipment Name]"

**Description Building**: Combine short_description + key features + primary applications for rich full_description

**Keyword Generation**: Extract from title + features + specifications + applications for comprehensive keyword arrays

**SEO Content**: Use technical specifications to create additional content sections highlighting capabilities

**Image Processing**: Use product name and model information to create descriptive alt text that improves SEO

## VALIDATION CHECKLIST

**Overall Details Mode:**
- [ ] All universal specifications included in `specifications`
- [ ] No model-specific data included
- [ ] SEO fields leverage all available data
- [ ] Complete equipment overview provided
- [ ] Images processed and both `image_urls` and `alt_text_suggestions` included
- [ ] Image URLs are full URLs (include domain if needed)

**Model Subset Mode:**  
- [ ] All assigned models processed
- [ ] No universal specifications duplicated
- [ ] Only model-specific specifications included
- [ ] Model features and descriptions complete
- [ ] Extracted specification group names used exactly as provided (if available)
- [ ] NO underscores in group names or specification keys

**Both Modes:**
- [ ] Categorized tags use proper {category, tag} format
- [ ] Cross-field intelligence applied throughout
- [ ] Technical accuracy maintained
- [ ] Specification group names use proper capitalization and spacing
- [ ] Complete specification data extracted (not just basic dimensions)

## Critical Success Factors
1. **MODE COMPLIANCE**: Strict adherence to processing mode requirements
2. **SPECIFICATION SEPARATION**: Clear distinction between universal and model-specific specs
3. **COMPLETENESS**: All data processed according to mode rules
4. **SEO OPTIMIZATION**: Maximum search visibility within mode constraints
5. **CONSISTENCY**: Uniform structure and quality across all outputs
6. **IMAGE PROCESSING**: Complete extraction and formatting of image data in Overall Details mode

## SPECIFICATION GROUP EXTRACTION REQUIREMENTS

### Use Extracted Group Names (When Available)
If input contains `extracted_specification_groups` field:
1. **Use EXACT group names** provided - do not modify or rename them
2. **Extract specifications for these groups** from source data
3. **Maintain exact spelling and capitalization** from extracted names
4. **No group coordination needed** - just use the names as-is

### Naming Standards (All Cases)
1. **NO underscores** in group names or specification keys
2. **Use spaces** for readability: "Dimensions & Weights" not "Dimensions_Weights"  
3. **Use proper capitalization**: "Electrical Requirements" not "electrical requirements"
4. **No special characters** except spaces, ampersands (&), and standard punctuation

### Extraction Approach
1. **Use provided group names** if available in `extracted_specification_groups`
2. **Extract ALL available data** for each group name
3. **Create logical groupings** if no group names provided
4. **Focus on completeness** - don't skip specification data

### Examples of Proper Group Names
✅ **Correct**: "Dimensions & Weights", "Electrical Requirements", "Protection & Compliance"
❌ **Incorrect**: "Dimensions_Weights", "electrical_requirements", "protection-compliance"

Output ONLY JSON. Do not put it in a code block or provide any fluff before or after.

Transform the provided input data into this SEO-optimized API format, using ALL available information to create the most search-engine-friendly and comprehensive equipment listing possible while strictly adhering to the specified processing mode. Ensure complete image processing when in Overall Details mode. 