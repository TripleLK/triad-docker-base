"""
Management command to bulk import URLs for site configurations.

Supports CSV and text file formats for adding multiple URLs to existing site configurations.

Created by: Cosmic Forge
Date: 2025-01-22
Project: Triad Docker Base - URL Management System
"""

import csv
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from apps.content_extractor.models import SiteConfiguration, SiteURL


class Command(BaseCommand):
    help = 'Bulk import URLs for site configurations from CSV or text files'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Path to CSV or text file containing URLs'
        )
        parser.add_argument(
            '--domain',
            type=str,
            required=True,
            help='Domain of the site configuration to add URLs to'
        )
        parser.add_argument(
            '--format',
            choices=['csv', 'txt'],
            default='txt',
            help='File format (csv or txt, default: txt)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing'
        )
        parser.add_argument(
            '--skip-duplicates',
            action='store_true',
            help='Skip URLs that already exist for this site'
        )

    def handle(self, *args, **options):
        # Get site configuration
        try:
            site_config = SiteConfiguration.objects.get(site_domain=options['domain'])
        except SiteConfiguration.DoesNotExist:
            raise CommandError(f"Site configuration for domain '{options['domain']}' not found")

        # Read URLs from file
        urls_to_import = self.read_urls_from_file(options['file_path'], options['format'])
        
        if not urls_to_import:
            self.stdout.write(self.style.WARNING("No valid URLs found in file"))
            return

        self.stdout.write(f"Found {len(urls_to_import)} URLs to import for {site_config.site_name}")

        # Validate URLs
        valid_urls = []
        validator = URLValidator()
        
        for url in urls_to_import:
            try:
                validator(url)
                valid_urls.append(url)
            except ValidationError:
                self.stdout.write(self.style.WARNING(f"Invalid URL format: {url}"))

        if not valid_urls:
            self.stdout.write(self.style.ERROR("No valid URLs to import"))
            return

        self.stdout.write(f"Validated {len(valid_urls)} URLs")

        # Check for duplicates if requested
        if options['skip_duplicates']:
            existing_urls = set(
                site_config.urls.values_list('url', flat=True)
            )
            new_urls = [url for url in valid_urls if url not in existing_urls]
            duplicate_count = len(valid_urls) - len(new_urls)
            
            if duplicate_count > 0:
                self.stdout.write(f"Skipping {duplicate_count} duplicate URLs")
            
            valid_urls = new_urls

        if not valid_urls:
            self.stdout.write(self.style.WARNING("No new URLs to import (all were duplicates)"))
            return

        # Show preview
        self.stdout.write(f"\nURLs to import ({len(valid_urls)}):")
        for i, url in enumerate(valid_urls[:10], 1):  # Show first 10
            self.stdout.write(f"  {i}. {url}")
        
        if len(valid_urls) > 10:
            self.stdout.write(f"  ... and {len(valid_urls) - 10} more")

        # Dry run check
        if options['dry_run']:
            self.stdout.write(self.style.SUCCESS("\nDry run complete - no URLs were imported"))
            return

        # Import URLs
        self.stdout.write(f"\nImporting {len(valid_urls)} URLs...")
        
        created_count = 0
        error_count = 0

        for url in valid_urls:
            try:
                site_url, created = SiteURL.objects.get_or_create(
                    site_config=site_config,
                    url=url,
                    defaults={
                        'status': 'active',
                        'processing_status': 'pending'
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f"✓ Added: {url}")
                else:
                    self.stdout.write(f"- Exists: {url}")
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f"✗ Error adding {url}: {str(e)}"))

        # Summary
        self.stdout.write(self.style.SUCCESS(
            f"\nImport complete: {created_count} URLs created, {error_count} errors"
        ))

    def read_urls_from_file(self, file_path, file_format):
        """Read URLs from file based on format."""
        urls = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                if file_format == 'csv':
                    urls = self.read_csv_urls(file)
                else:  # txt format
                    urls = self.read_txt_urls(file)
                    
        except FileNotFoundError:
            raise CommandError(f"File not found: {file_path}")
        except Exception as e:
            raise CommandError(f"Error reading file: {str(e)}")
        
        return urls

    def read_csv_urls(self, file):
        """Read URLs from CSV file (expects 'url' column)."""
        urls = []
        reader = csv.DictReader(file)
        
        if 'url' not in reader.fieldnames:
            raise CommandError("CSV file must have 'url' column")
        
        for row in reader:
            url = row['url'].strip()
            if url:
                urls.append(url)
        
        return urls

    def read_txt_urls(self, file):
        """Read URLs from text file (one URL per line)."""
        urls = []
        
        for line in file:
            url = line.strip()
            if url and not url.startswith('#'):  # Skip empty lines and comments
                urls.append(url)
        
        return urls 