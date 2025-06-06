# Enhanced Triad Scientific Import Command Documentation

## Overview

The `import_triadscientific` management command has been enhanced to support URL discovery and product categorization through tagging. The command now provides a complete workflow for discovering, extracting, importing, and categorizing Triad Scientific products.

## Features

1. **URL Discovery**:
   - Start with automatic URL discovery from the Triad Scientific website
   - Filter discovery by specific categories
   - Save discovered URLs to a file for later use
   - Control rate limiting during discovery

2. **Data Import**:
   - Import product information from URLs
   - Create or update LabEquipmentPage models
   - Process product images and specifications
   - Handle both single URL and batch imports from a file

3. **Product Categorization**:
   - Automatically extract category information from URLs
   - Apply appropriate product category tags
   - Optional manufacturer tagging
   - Process tags for existing imported products

4. **Advanced Controls**:
   - Progress reporting with estimated time remaining
   - Detailed error logging and reporting
   - Rate limiting and retry mechanisms
   - Dry run mode for testing

## Usage

### Basic Import

```bash
python manage.py import_triadscientific --url "http://www.triadscientific.com/en/products/ftir-systems/1091/mattson-ati-genesis-series-ftir-with-software/249015" --parent-page 3
```

### URL Discovery and Import

```bash
# Discover all URLs and save them
python manage.py import_triadscientific --discover-urls --output-file discovered_urls.txt

# Discover URLs for a specific category
python manage.py import_triadscientific --discover-urls --category "ftir-systems" --output-file ftir_urls.txt

# Discover URLs and import them immediately
python manage.py import_triadscientific --discover-urls --parent-page 3
```

### Batch Import with Tagging

```bash
python manage.py import_triadscientific --url-file discovered_urls.txt --parent-page 3 --process-tags
```

### Tag Processing Only

```bash
# Apply tags to all previously imported products
python manage.py import_triadscientific --tags-only --process-tags
```

## Command Options

### URL Arguments

| Option | Description |
|--------|-------------|
| `--url URL` | Single URL to scrape |
| `--url-file FILE` | File containing URLs to scrape, one per line |

### URL Discovery Arguments

| Option | Description |
|--------|-------------|
| `--discover-urls` | Discover product URLs from the Triad Scientific website |
| `--category CATEGORY` | Specific category to discover URLs for (e.g., "ftir-systems") |
| `--output-file FILE` | File to save discovered URLs to (default: discovered_product_urls.txt) |
| `--request-delay SECONDS` | Delay between requests during URL discovery in seconds (default: 1.0) |

### Import Arguments

| Option | Description |
|--------|-------------|
| `--parent-page ID` | ID of parent page to add equipment pages under (required for new pages) |
| `--update-existing` | Update existing pages instead of creating new ones |
| `--skip-images` | Skip downloading images |
| `--dry-run` | Perform a dry run without committing changes |
| `--limit N` | Limit the number of URLs to process |
| `--retry N` | Number of retry attempts for failed requests (default: 3) |
| `--retry-delay SECONDS` | Delay in seconds between retry attempts (default: 5) |

### Tagging Arguments

| Option | Description |
|--------|-------------|
| `--process-tags` | Process tags after importing data |
| `--tags-only` | Only process tags, no import |
| `--add-manufacturer-tag` | Add manufacturer tag (Triad Scientific) to products - optional |

## Workflow Examples

### Complete Workflow: Discovery to Import with Tagging

This workflow discovers all product URLs, imports them, and applies tags:

```bash
python manage.py import_triadscientific --discover-urls --parent-page 3 --process-tags
```

### Limited Category Import

This workflow imports products from a specific category with tagging:

```bash
python manage.py import_triadscientific --discover-urls --category "ftir-systems" --parent-page 3 --process-tags --limit 10
```

### Discovery Only

This workflow only discovers URLs and saves them for later:

```bash
python manage.py import_triadscientific --discover-urls --request-delay 2.0 --output-file all_products.txt
```

### Tagging Existing Products

This workflow applies tags to already imported products:

```bash
python manage.py import_triadscientific --tags-only --process-tags
```

## Tagging System

The command implements a simplified tagging approach based on URL categories:

1. **Product Category**: Extracted from the URL path (e.g., "FTIR Systems")
2. **Manufacturer**: "Triad Scientific" (only if --add-manufacturer-tag is used)

Tags are automatically created in the appropriate categories if they don't exist.

## Error Handling

- Network errors are retried according to --retry and --retry-delay settings
- Validation errors are logged and reported
- Detailed error information is written to `triad_import_errors.log`
- Import statistics are displayed after completion

## Notes

- The URL discovery process follows rate limiting to avoid overloading the website
- For large imports, consider using the --limit option for initial testing
- The --dry-run option allows for testing without making database changes
- URLs discovered with --discover-urls are saved to the specified output file for future use 