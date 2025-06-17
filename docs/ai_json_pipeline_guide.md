# AI JSON Pipeline Guide

**Created by: Cosmic Forge**  
**Date: 2025-01-22**  
**System: URL Management and AI JSON Generation**

## Overview

The AI JSON Pipeline system provides comprehensive URL management and automated generation of AI-ready JSON data for content extraction. Built on top of the existing XPath highlighting system, it enables batch processing of site URLs with stored field configurations.

## System Architecture

### Models

#### SiteURL
- Manages collections of URLs for each site configuration
- Tracks processing status (pending, processing, completed, failed)
- Stores page titles and processing notes
- Unique constraint: one URL per site configuration

#### AIJSONRecord
- Stores generated AI-ready JSON data
- Includes content hashing for change detection
- Maintains version history (current vs outdated records)
- Links to source URL and processing metadata

### Management Commands

#### 1. generate_ai_json
Generates AI-ready JSON by combining scraped content with XPath configurations.

**Usage Examples:**
```bash
# Process all URLs for a specific domain
python manage.py generate_ai_json --domain example-lab-supplier.com

# Process a specific URL by ID
python manage.py generate_ai_json --url-id 123

# Process all active sites
python manage.py generate_ai_json --all-sites

# Force regeneration of existing JSON
python manage.py generate_ai_json --domain example.com --force-refresh
```

**Output JSON Structure:**
```json
{
  "url": "https://example.com/product/123",
  "site_domain": "example.com",
  "site_name": "Example Lab Supplier",
  "scraped_content": {
    "html": "<html>...</html>",
    "page_title": "Lab Equipment XYZ",
    "status_code": 200,
    "content_type": "text/html",
    "scraped_at": "2025-01-22T15:30:00Z"
  },
  "extraction_config": {
    "title": {
      "xpath_selectors": ["//h1[@class='product-title']/text()"],
      "comment": "Main product title",
      "field_type": "single"
    },
    "features": {
      "xpath_selectors": ["//ul[@class='features']//li/text()"],
      "comment": "List of product features",
      "field_type": "multi-value"
    }
  },
  "processing_metadata": {
    "timestamp": "2025-01-22T15:30:00Z",
    "status": "ready_for_ai",
    "field_count": 8,
    "content_length": 45623
  }
}
```

#### 2. import_site_urls
Bulk import URLs from CSV or text files.

**Text File Format:**
```
# Comments start with #
https://example.com/product/abc-123
https://example.com/product/xyz-456
https://example.com/product/def-789
```

**CSV File Format:**
```csv
url,notes
https://example.com/product/abc-123,High priority product
https://example.com/product/xyz-456,Complex specifications
```

**Usage Examples:**
```bash
# Import from text file
python manage.py import_site_urls urls.txt --domain example.com

# Import from CSV with duplicate checking
python manage.py import_site_urls products.csv --domain example.com --format csv --skip-duplicates

# Dry run to preview imports
python manage.py import_site_urls urls.txt --domain example.com --dry-run
```

#### 3. export_ai_json
Export generated AI JSON data in multiple formats.

**Usage Examples:**
```bash
# Export individual JSON files for a domain
python manage.py export_ai_json --domain example.com --format individual

# Export all current records as batch file
python manage.py export_ai_json --format batch --current-only

# Export metadata as CSV
python manage.py export_ai_json --format csv --output-dir ./exports

# Export everything with metadata
python manage.py export_ai_json --format all --include-metadata
```

**Export Formats:**
- **Individual**: Separate JSON file per record
- **Batch**: Single JSON file with all records
- **CSV**: Metadata spreadsheet (record IDs, timestamps, sizes, etc.)

## Admin Interface

### Wagtail Snippets
All models are available as Wagtail snippets in the admin interface:

- **Site Configurations**: Manage domains and settings
- **Field Configurations**: Configure XPath selectors per field
- **Site URLs**: Add/edit individual URLs with status tracking
- **AI JSON Records**: View generated JSON data and metadata

### URL Management Workflow
1. Create/configure Site Configuration for target domain
2. Add Field Configurations with XPath selectors
3. Import URLs using `import_site_urls` command
4. Generate AI JSON using `generate_ai_json` command
5. Export results using `export_ai_json` command

## Best Practices

### URL Management
- Use descriptive notes for complex URLs
- Organize URLs by priority (high-value products first)
- Monitor processing status regularly
- Clean up failed URLs and investigate errors

### AI JSON Generation
- Start with small batches to test configurations
- Use `--force-refresh` sparingly (only when configs change)
- Monitor content hashes to detect site changes
- Keep current records for latest data access

### Performance Considerations
- Process large batches during off-peak hours
- Monitor processing duration for optimization
- Use content hashing to avoid unnecessary regeneration
- Consider background task processing for very large sites

## Troubleshooting

### Common Issues

**Command Error: Site configuration not found**
```bash
# Check available domains
python manage.py shell -c "from apps.content_extractor.models import SiteConfiguration; print([s.site_domain for s in SiteConfiguration.objects.all()])"
```

**Processing Failures**
- Check URL accessibility (403, 404, timeout errors)
- Verify XPath selectors work with current site structure
- Review error notes in URL model for specific failure details

**Large File Exports**
- Use `--current-only` to reduce export size
- Export by domain rather than all sites
- Consider CSV format for metadata analysis

### Debugging Commands
```bash
# List all URLs and their status
python manage.py shell -c "
from apps.content_extractor.models import SiteURL
for url in SiteURL.objects.all():
    print(f'{url.site_config.site_domain}: {url.url} - {url.processing_status}')
"

# Check AI JSON record counts
python manage.py shell -c "
from apps.content_extractor.models import AIJSONRecord
print(f'Total records: {AIJSONRecord.objects.count()}')
print(f'Current records: {AIJSONRecord.objects.filter(is_current=True).count()}')
"
```

## Integration Points

### With Existing System
- Builds on SiteConfiguration/FieldConfiguration models
- Uses same XPath highlighting foundation
- Maintains Wagtail admin consistency
- Leverages existing field definitions

### For AI Processing
- JSON structure optimized for LLM consumption
- Includes extraction hints and field types
- Provides content and configuration separation
- Supports batch processing workflows

## Future Enhancements

### Planned Features
- Background task processing with Celery
- Real-time progress monitoring
- Automatic retry mechanisms for failed URLs
- Content change detection and alerts
- API endpoints for external integrations

### Extensibility
- Custom export formats
- Plugin architecture for scrapers
- AI-assisted XPath generation
- Integration with content management systems 