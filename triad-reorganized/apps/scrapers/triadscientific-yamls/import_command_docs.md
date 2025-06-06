# Triad Scientific Import Command Documentation

This document explains how to use the Django management command for importing Triad Scientific product data into the Wagtail CMS.

## Overview

The `import_triadscientific` command extracts product information from the Triad Scientific website using the YAML-based scraper configuration and creates or updates Django/Wagtail pages to represent these products.

## Features

- Extracts product data using modular YAML selectors
- Creates LabEquipmentPage instances with proper relationships
- Handles product images, specifications, and models
- Supports batch import from a file of URLs
- Includes comprehensive error handling and reporting
- Creates a log file for monitoring and debugging

## Prerequisites

Before running the command, ensure:

1. You have the Django/Wagtail project set up correctly
2. The database migrations have been applied (including the `source_url` field)
3. You have identified the parent page ID where new equipment pages should be added
4. You have a list of URLs to import or a specific URL to test

## Usage

### Basic Usage

```bash
python manage.py import_triadscientific --url <URL> --parent-page <PAGE_ID>
```

### Batch Import from File

```bash
python manage.py import_triadscientific --url-file <PATH_TO_FILE> --parent-page <PAGE_ID>
```

The URL file should contain one URL per line. It can optionally include product names after a pipe character:
```
http://example.com/product1 | Product Name 1
http://example.com/product2 | Product Name 2
```

### Command Options

- `--url`: Single URL to scrape
- `--url-file`: File containing URLs to scrape (one per line)
- `--parent-page`: ID of parent page to add equipment pages under (required for new pages)
- `--update-existing`: Update existing pages instead of creating new ones
- `--skip-images`: Skip downloading and processing images
- `--dry-run`: Perform a dry run without committing changes to the database
- `--limit`: Limit the number of URLs to process
- `--retry`: Number of retry attempts for failed requests (default: 3)
- `--retry-delay`: Delay in seconds between retry attempts (default: 5)
- `--verbosity`: Control the verbosity level (0-3)

## Examples

### Import a Single Product

```bash
python manage.py import_triadscientific --url "http://www.triadscientific.com/en/products/atomic-absorption/942/agilent-240fs-aa-spectrometer-no-ultraa-used-mint/260487" --parent-page 5
```

### Import Multiple Products with a Limit

```bash
python manage.py import_triadscientific --url-file apps/scrapers/triadscientific-yamls/sample_product_urls.txt --parent-page 5 --limit 10
```

### Dry Run to Test Without Changes

```bash
python manage.py import_triadscientific --url-file apps/scrapers/triadscientific-yamls/sample_product_urls.txt --parent-page 5 --dry-run --verbosity 2
```

### Update Existing Products

```bash
python manage.py import_triadscientific --url-file apps/scrapers/triadscientific-yamls/sample_product_urls.txt --parent-page 5 --update-existing
```

## Monitoring and Logging

The command creates a log file (`triad_import.log`) that contains detailed information about the import process, including:

- Successfully imported products
- Errors and failures
- Skipped products
- Validation issues

Use this log file for troubleshooting issues or monitoring the import process.

## Error Handling

The command includes comprehensive error handling:

1. **Network Errors**: Automatic retry for transient network issues
2. **Data Validation**: Checks for missing or malformed data
3. **Database Errors**: Proper transaction handling to prevent partial imports
4. **Error Reporting**: Detailed error messages and traceback in logs

## Data Structure

For each product, the command extracts:

1. **Product Name**: Title of the product
2. **Short Description**: Brief summary (with fallback mechanism)
3. **Full Description**: Detailed HTML description
4. **Images**: Product image URLs
5. **Models**: Product model information (typically one model per product)
6. **Specifications**: Technical specifications organized in groups

## Best Practices

1. **Start with a Dry Run**: Always use `--dry-run` first to verify extraction
2. **Use Verbosity**: Set `--verbosity 2` for detailed output during testing
3. **Limit Initial Imports**: Use `--limit` when first importing to catch issues early
4. **Check the Logs**: Review `triad_import.log` for detailed information
5. **Regular Updates**: Run with `--update-existing` periodically to refresh data

## Troubleshooting

### Common Issues

1. **Missing Parent Page**: Ensure the `--parent-page` ID exists
2. **URL Formatting**: Make sure URLs are correctly formatted
3. **Database Errors**: Check that all migrations have been applied
4. **Extraction Problems**: Verify selectors in the YAML files still match website structure

## Advanced Usage

### Customizing the Import Process

The import process can be customized by modifying the YAML selectors in the `apps/scrapers/triadscientific-yamls/` directory:

- `mapping.yaml`: Main configuration that references other YAML files
- `name.yaml`: Extracts product names
- `short_description.yaml`: Extracts product summaries
- `full_description.yaml`: Extracts detailed descriptions
- `imgs.yaml`: Extracts product images
- `models.yaml`: Extracts product model information
- `specs_groups.yaml`: Extracts technical specifications

If the website structure changes, update these YAML files to adjust the selectors. 