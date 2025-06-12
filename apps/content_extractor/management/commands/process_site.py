"""
Management command to process all URLs for a single site and export to site-specific directory.

Combines generation and export into a single command with site-specific organization.

Created by: Arctic Storm
Date: 2025-01-22
Project: Triad Docker Base - Site Processing System
"""

import json
import os
import time
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.content_extractor.models import SiteConfiguration, SiteURL, AIJSONRecord
from .generate_ai_json import Command as GenerateCommand
from .export_ai_json import Command as ExportCommand


class Command(BaseCommand):
    help = 'Process all URLs for a single site: generate AI JSON and export to site-specific directory'

    def add_arguments(self, parser):
        parser.add_argument(
            'domain',
            type=str,
            help='Domain to process (e.g., www.airscience.com)'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='./site_extractions',
            help='Base output directory (default: ./site_extractions)'
        )
        parser.add_argument(
            '--force-refresh',
            action='store_true',
            help='Regenerate JSON even if already exists'
        )
        parser.add_argument(
            '--format',
            choices=['individual', 'batch', 'both'],
            default='both',
            help='Export format (default: both individual and batch)'
        )
        parser.add_argument(
            '--include-metadata',
            action='store_true',
            help='Include processing metadata in exports'
        )

    def handle(self, *args, **options):
        domain = options['domain']
        start_time = time.time()
        
        self.stdout.write(f"🚀 ARCTIC STORM: Processing site {domain}")
        
        # Validate domain exists
        try:
            site_config = SiteConfiguration.objects.get(site_domain=domain)
            self.stdout.write(f"✓ Found site configuration: {site_config.site_name}")
        except SiteConfiguration.DoesNotExist:
            raise CommandError(f"Site configuration for domain '{domain}' not found")
        
        # Get URLs for this domain
        urls_to_process = site_config.urls.filter(status='active')
        if not urls_to_process.exists():
            self.stdout.write(self.style.WARNING(f"No active URLs found for domain {domain}"))
            return
        
        total_urls = urls_to_process.count()
        self.stdout.write(f"📋 Found {total_urls} active URLs to process")
        
        # Step 1: Generate AI JSON for all URLs
        self.stdout.write("\n🔄 STEP 1: Generating AI JSON for all URLs...")
        
        generate_cmd = GenerateCommand()
        success_count = 0
        error_count = 0
        
        for site_url in urls_to_process:
            try:
                # Check if we should skip (already processed and not forcing refresh)
                if not options['force_refresh'] and self.is_already_processed(site_url):
                    self.stdout.write(f"   ⏭️  Skipping {site_url.url} (already processed)")
                    success_count += 1
                    continue

                self.stdout.write(f"   🔄 Processing: {site_url.url}")
                
                # Mark as processing
                site_url.mark_processing()
                
                # Generate AI JSON using the existing command logic
                ai_json = generate_cmd.generate_ai_json_for_url(site_url)
                
                # Save the record using the existing command logic
                generate_cmd.save_ai_json_record(site_url, ai_json)
                
                # Mark as completed
                site_url.mark_completed()
                
                success_count += 1
                self.stdout.write(f"   ✅ Completed: {site_url.url}")
                
            except Exception as e:
                error_count += 1
                error_message = str(e)
                site_url.mark_failed(error_message)
                self.stdout.write(f"   ❌ Failed: {site_url.url} - {error_message}")

        self.stdout.write(f"\n📊 Generation Summary: {success_count} successful, {error_count} failed")
        
        if success_count == 0:
            self.stdout.write(self.style.ERROR("No URLs were successfully processed. Skipping export."))
            return
        
        # Step 2: Export to site-specific directory
        self.stdout.write(f"\n📤 STEP 2: Exporting to site-specific directory...")
        
        # Create site-specific directory
        safe_domain = self.make_safe_filename(domain)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        site_dir = os.path.join(options['output_dir'], safe_domain, timestamp)
        os.makedirs(site_dir, exist_ok=True)
        
        self.stdout.write(f"   📁 Export directory: {site_dir}")
        
        # Export the generated records
        records = AIJSONRecord.objects.filter(
            site_url__site_config=site_config,
            is_current=True
        ).select_related('site_url__site_config')
        
        if options['format'] in ['individual', 'both']:
            self.export_individual_files(records, site_dir, options)
        
        if options['format'] in ['batch', 'both']:
            self.export_batch_file(records, site_dir, options, site_config)
        
        # Create site summary
        self.create_site_summary(site_config, records, site_dir, success_count, error_count)
        
        # Final summary
        total_time = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(
            f"\n🎉 ARCTIC STORM: Site processing completed in {total_time:.2f} seconds"
        ))
        self.stdout.write(f"   🔢 Processed: {success_count}/{total_urls} URLs")
        self.stdout.write(f"   📁 Exported to: {site_dir}")
        self.stdout.write(f"   📊 Records: {records.count()} JSON files generated")

    def is_already_processed(self, site_url):
        """Check if URL already has current AI JSON record."""
        return site_url.ai_json_records.filter(is_current=True).exists()

    def export_individual_files(self, records, site_dir, options):
        """Export each AI JSON record as individual file."""
        individual_dir = os.path.join(site_dir, 'individual')
        os.makedirs(individual_dir, exist_ok=True)
        
        self.stdout.write(f"   📄 Exporting {records.count()} individual JSON files...")
        
        for record in records:
            # Use page title as primary filename component
            page_title = record.site_url.page_title or "Unknown_Page"
            safe_title = self.make_safe_filename(page_title)
            
            # Add domain prefix and timestamp for uniqueness
            domain = record.site_url.site_config.site_domain
            timestamp = record.generation_timestamp.strftime('%Y%m%d_%H%M%S')
            
            filename = f"{safe_title}_{timestamp}.json"
            filepath = os.path.join(individual_dir, filename)
            
            # Prepare export data
            export_data = record.json_data.copy()
            
            if options['include_metadata']:
                export_data['export_metadata'] = {
                    'record_id': record.id,
                    'generation_timestamp': record.generation_timestamp.isoformat(),
                    'content_hash': record.content_hash,
                    'is_current': record.is_current,
                    'exported_at': timezone.now().isoformat(),
                    'processing_duration': str(record.processing_duration) if record.processing_duration else None
                }
            
            # Write file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.stdout.write(f"     ✓ {filename}")

    def export_batch_file(self, records, site_dir, options, site_config):
        """Export all records as single batch JSON file."""
        self.stdout.write(f"   📦 Exporting batch JSON file...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_domain = self.make_safe_filename(site_config.site_domain)
        filename = f"{safe_domain}_batch_{timestamp}.json"
        filepath = os.path.join(site_dir, filename)
        
        batch_data = {
            'site_info': {
                'domain': site_config.site_domain,
                'site_name': site_config.site_name,
                'total_urls': records.count(),
                'exported_at': timezone.now().isoformat(),
                'export_format': 'site_batch'
            },
            'records': []
        }
        
        for record in records:
            record_data = {
                'url': record.site_url.url,
                'page_title': record.site_url.page_title,
                'generation_timestamp': record.generation_timestamp.isoformat(),
                'json_data': record.json_data
            }
            
            if options['include_metadata']:
                record_data['metadata'] = {
                    'record_id': record.id,
                    'content_hash': record.content_hash,
                    'processing_duration': str(record.processing_duration) if record.processing_duration else None,
                    'json_size_kb': record.json_size_kb
                }
            
            batch_data['records'].append(record_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, indent=2, ensure_ascii=False)
        
        self.stdout.write(f"     ✓ {filename}")

    def create_site_summary(self, site_config, records, site_dir, success_count, error_count):
        """Create a summary file for the site processing."""
        summary_file = os.path.join(site_dir, 'SITE_SUMMARY.md')
        
        # Calculate statistics
        total_urls = success_count + error_count
        success_rate = (success_count / total_urls * 100) if total_urls > 0 else 0
        
        # Field configuration stats
        field_configs = site_config.field_configs.filter(is_active=True)
        configured_fields = field_configs.count()
        
        summary_content = f"""# Site Processing Summary

**Domain:** {site_config.site_domain}
**Site Name:** {site_config.site_name}
**Processed:** {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
**Generated by:** Arctic Storm

## Processing Results

- **Total URLs:** {total_urls}
- **Successful:** {success_count}
- **Failed:** {error_count}
- **Success Rate:** {success_rate:.1f}%
- **JSON Records Generated:** {records.count()}

## Field Configuration

- **Active Fields:** {configured_fields}
- **Configured Fields:** {', '.join([fc.lab_equipment_field for fc in field_configs])}

## Export Structure

```
{site_dir}/
├── individual/           # Individual JSON files per URL
├── {site_config.site_domain}_batch_*.json  # Combined batch file
└── SITE_SUMMARY.md      # This summary file
```

## Usage

The exported JSON files can be used for:
- AI training data
- Content analysis
- API development
- Data migration

Generated by Arctic Storm site processing system.
"""
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        self.stdout.write(f"   📋 Created summary: SITE_SUMMARY.md")

    def make_safe_filename(self, text):
        """Convert text to safe filename."""
        import re
        if not text:
            return "Unknown"
            
        # Clean up the text
        safe = str(text).strip()
        
        # Replace problematic characters with underscores
        safe = re.sub(r'[<>:"/\\|?*]', '_', safe)
        safe = re.sub(r'[^\w\s\-_.]', '_', safe)
        
        # Replace spaces and multiple underscores with single underscores
        safe = re.sub(r'[\s_]+', '_', safe)
        
        # Remove leading/trailing underscores and dots
        safe = safe.strip('_.')
        
        # Limit length to 50 characters
        if len(safe) > 50:
            safe = safe[:50].rstrip('_')
        
        # Ensure we have something meaningful
        if not safe or safe == '_':
            safe = "Unknown"
            
        return safe 