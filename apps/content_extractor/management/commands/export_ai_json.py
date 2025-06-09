"""
Management command to export generated AI JSON data.

Supports multiple export formats including individual files, batch JSON, and CSV metadata.

Created by: Cosmic Forge
Date: 2025-01-22
Project: Triad Docker Base - AI JSON Export System
"""

import json
import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.content_extractor.models import SiteConfiguration, AIJSONRecord


class Command(BaseCommand):
    help = 'Export generated AI JSON data in various formats'

    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            type=str,
            help='Export data for specific domain only'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='./ai_json_exports',
            help='Output directory for exported files (default: ./ai_json_exports)'
        )
        parser.add_argument(
            '--format',
            choices=['individual', 'batch', 'csv', 'all'],
            default='individual',
            help='Export format (default: individual)'
        )
        parser.add_argument(
            '--current-only',
            action='store_true',
            help='Export only current (latest) JSON records'
        )
        parser.add_argument(
            '--include-metadata',
            action='store_true',
            help='Include processing metadata in exports'
        )

    def handle(self, *args, **options):
        # Get records to export
        records = self.get_records_to_export(options)
        
        if not records.exists():
            self.stdout.write(self.style.WARNING("No AI JSON records found to export"))
            return

        # Create output directory
        output_dir = options['output_dir']
        os.makedirs(output_dir, exist_ok=True)
        
        total_records = records.count()
        self.stdout.write(f"Exporting {total_records} AI JSON records to {output_dir}")

        # Export based on format
        if options['format'] == 'individual' or options['format'] == 'all':
            self.export_individual_files(records, output_dir, options)
            
        if options['format'] == 'batch' or options['format'] == 'all':
            self.export_batch_file(records, output_dir, options)
            
        if options['format'] == 'csv' or options['format'] == 'all':
            self.export_csv_metadata(records, output_dir, options)

        self.stdout.write(self.style.SUCCESS(f"Export completed: {total_records} records"))

    def get_records_to_export(self, options):
        """Get AI JSON records based on filter options."""
        queryset = AIJSONRecord.objects.all()
        
        # Filter by domain if specified
        if options['domain']:
            queryset = queryset.filter(
                site_url__site_config__site_domain=options['domain']
            )
        
        # Filter to current only if requested
        if options['current_only']:
            queryset = queryset.filter(is_current=True)
        
        return queryset.select_related(
            'site_url__site_config'
        ).order_by('-generation_timestamp')

    def export_individual_files(self, records, output_dir, options):
        """Export each AI JSON record as individual file."""
        individual_dir = os.path.join(output_dir, 'individual')
        os.makedirs(individual_dir, exist_ok=True)
        
        self.stdout.write("Exporting individual JSON files...")
        
        for record in records:
            # Create filename with timestamp and domain
            timestamp = record.generation_timestamp.strftime('%Y%m%d_%H%M%S')
            domain = record.site_url.site_config.site_domain
            safe_url = self.make_safe_filename(record.site_url.url)
            
            filename = f"{domain}_{timestamp}_{safe_url}.json"
            filepath = os.path.join(individual_dir, filename)
            
            # Prepare export data
            export_data = record.json_data.copy()
            
            if options['include_metadata']:
                export_data['export_metadata'] = {
                    'record_id': record.id,
                    'generation_timestamp': record.generation_timestamp.isoformat(),
                    'content_hash': record.content_hash,
                    'is_current': record.is_current,
                    'exported_at': timezone.now().isoformat()
                }
            
            # Write file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.stdout.write(f"  ✓ {filename}")

    def export_batch_file(self, records, output_dir, options):
        """Export all records as single batch JSON file."""
        self.stdout.write("Exporting batch JSON file...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ai_json_batch_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        batch_data = {
            'export_info': {
                'total_records': records.count(),
                'exported_at': timezone.now().isoformat(),
                'format': 'batch',
                'include_metadata': options['include_metadata']
            },
            'records': []
        }
        
        for record in records:
            record_data = {
                'record_id': record.id,
                'url': record.site_url.url,
                'site_domain': record.site_url.site_config.site_domain,
                'generation_timestamp': record.generation_timestamp.isoformat(),
                'is_current': record.is_current,
                'json_data': record.json_data
            }
            
            if options['include_metadata']:
                record_data['metadata'] = {
                    'content_hash': record.content_hash,
                    'processing_duration': str(record.processing_duration) if record.processing_duration else None,
                    'json_size_kb': record.json_size_kb
                }
            
            batch_data['records'].append(record_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, indent=2, ensure_ascii=False)
        
        self.stdout.write(f"  ✓ {filename}")

    def export_csv_metadata(self, records, output_dir, options):
        """Export record metadata as CSV file."""
        self.stdout.write("Exporting CSV metadata file...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ai_json_metadata_{timestamp}.csv"
        filepath = os.path.join(output_dir, filename)
        
        fieldnames = [
            'record_id', 'site_domain', 'site_name', 'url', 'page_title',
            'generation_timestamp', 'is_current', 'content_hash',
            'json_size_kb', 'processing_duration', 'field_count'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in records:
                # Extract field count from JSON data
                field_count = 0
                if record.json_data.get('extraction_config'):
                    field_count = len(record.json_data['extraction_config'])
                
                row = {
                    'record_id': record.id,
                    'site_domain': record.site_url.site_config.site_domain,
                    'site_name': record.site_url.site_config.site_name,
                    'url': record.site_url.url,
                    'page_title': record.site_url.page_title or '',
                    'generation_timestamp': record.generation_timestamp.isoformat(),
                    'is_current': record.is_current,
                    'content_hash': record.content_hash,
                    'json_size_kb': round(record.json_size_kb, 2),
                    'processing_duration': str(record.processing_duration) if record.processing_duration else '',
                    'field_count': field_count
                }
                
                writer.writerow(row)
        
        self.stdout.write(f"  ✓ {filename}")

    def make_safe_filename(self, url):
        """Convert URL to safe filename."""
        # Remove protocol and replace unsafe characters
        safe = url.replace('https://', '').replace('http://', '')
        safe = safe.replace('/', '_').replace('?', '_').replace('&', '_')
        safe = safe.replace('=', '_').replace('#', '_').replace(':', '_')
        
        # Limit length
        if len(safe) > 50:
            safe = safe[:50]
        
        return safe 