"""
Management command to export generated AI JSON data.

Always uses two-mode processing for model subset and overall details.
Requires model names to be extracted via content extractor.

Created by: Cosmic Forge
Updated by: Quantum Flux
Date: 2025-01-22
Project: Triad Docker Base - AI JSON Export System
"""

import json
import csv
import os
import math
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.content_extractor.models import SiteConfiguration, AIJSONRecord
import re


class Command(BaseCommand):
    help = 'Export generated AI JSON data with two-mode processing (Overall Details + Model Subsets)'

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
            choices=['two-mode', 'legacy-individual', 'batch', 'csv'],
            default='two-mode',
            help='Export format (default: two-mode for model subset processing)'
        )
        parser.add_argument(
            '--include-all-versions',
            action='store_true',
            help='Include all versions (default: only export most recent version per page)'
        )
        parser.add_argument(
            '--include-metadata',
            action='store_true',
            help='Include ALL processing metadata in exports'
        )
        parser.add_argument(
            '--models-per-batch',
            type=int,
            default=4,
            help='Number of models per batch when using two-mode processing (default: 4)'
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
        if options['format'] == 'two-mode':
            self.export_two_mode_processing(records, output_dir, options)
        elif options['format'] == 'legacy-individual':
            self.export_individual_files(records, output_dir, options)
        elif options['format'] == 'batch':
            self.export_batch_file(records, output_dir, options)
        elif options['format'] == 'csv':
            self.export_csv_metadata(records, output_dir, options)

        self.stdout.write(self.style.SUCCESS(f"Export completed: {total_records} records"))

    def export_two_mode_processing(self, records, output_dir, options):
        """Export JSON files for two-mode processing (Overall Details + Model Subsets)."""
        two_mode_dir = os.path.join(output_dir, 'two_mode')
        os.makedirs(two_mode_dir, exist_ok=True)
        
        self.stdout.write("Exporting two-mode processing files...")
        
        for record in records:
            base_data = record.json_data.copy()
            model_names = self.extract_model_names_from_record(record)
            spec_group_names = self.extract_specification_group_names_from_record(record)
            
            if not model_names:
                self.stdout.write(self.style.ERROR(f"No model names found for record {record.id} - content extractor must include model names. Skipping."))
                continue
            
            # Generate file base name
            page_title = record.site_url.page_title or "Unknown_Page"
            safe_title = self.make_safe_filename(page_title)
            domain = record.site_url.site_config.site_domain
            timestamp = record.generation_timestamp.strftime('%Y%m%d_%H%M%S')
            
            # Add metadata if requested (all or nothing)
            metadata = None
            if options['include_metadata']:
                metadata = self.create_complete_export_metadata(record)
            
            # 1. Generate Overall Details file (everything except models)
            overall_details_data = base_data.copy()
            overall_details_data['_processing_mode'] = 'OVERALL_DETAILS'
            
            # Remove models from the overall details data
            if 'field_configurations' in overall_details_data:
                field_configs = overall_details_data['field_configurations']
                # Remove model-specific field configurations
                overall_details_data['field_configurations'] = {
                    key: value for key, value in field_configs.items()
                    if not self.is_model_specific_field(key)
                }
            
            if metadata:
                overall_details_data['export_metadata'] = metadata.copy()
                overall_details_data['export_metadata']['export_type'] = 'overall_details'
            
            overall_filename = f"{safe_title}_overall_details_{domain}_{timestamp}.json"
            overall_filepath = os.path.join(two_mode_dir, overall_filename)
            
            with open(overall_filepath, 'w', encoding='utf-8') as f:
                json.dump(overall_details_data, f, indent=2, ensure_ascii=False)
            
            self.stdout.write(f"  ✓ Overall Details: {overall_filename}")
            
            # 2. Generate Model Subset files
            models_per_batch = options['models_per_batch']
            total_batches = math.ceil(len(model_names) / models_per_batch)
            
            for batch_num in range(total_batches):
                start_idx = batch_num * models_per_batch
                end_idx = min(start_idx + models_per_batch, len(model_names))
                batch_model_names = model_names[start_idx:end_idx]
                
                # Create model subset data
                model_subset_data = base_data.copy()
                model_subset_data['_processing_mode'] = 'MODEL_SUBSET'
                model_subset_data['_batch_info'] = {
                    'batch_number': batch_num + 1,
                    'total_batches': total_batches,
                    'models_in_batch': batch_model_names,
                    'total_models': len(model_names)
                }
                
                # Filter to only model-specific field configurations
                if 'field_configurations' in model_subset_data:
                    field_configs = model_subset_data['field_configurations']
                    model_subset_data['field_configurations'] = {
                        key: value for key, value in field_configs.items()
                        if self.is_model_specific_field(key) or key == 'name'  # Include model names
                    }
                
                # Add the specific model names to process
                model_subset_data['target_model_names'] = batch_model_names
                
                # Add extracted specification group names for consistency
                if spec_group_names:
                    model_subset_data['extracted_specification_groups'] = spec_group_names
                    model_subset_data['_specification_instructions'] = {
                        "use_exact_group_names": True,
                        "no_underscores_in_names": True,
                        "extract_all_available_data": True,
                        "available_groups": spec_group_names
                    }
                
                if metadata:
                    model_subset_data['export_metadata'] = metadata.copy()
                    model_subset_data['export_metadata']['export_type'] = f'model_subset_batch_{batch_num + 1}'
                    model_subset_data['export_metadata']['batch_info'] = {
                        'batch_number': batch_num + 1,
                        'total_batches': total_batches,
                        'models_in_batch': batch_model_names
                    }
                
                if total_batches > 1:
                    batch_filename = f"{safe_title}_models_batch_{batch_num + 1}_of_{total_batches}_{domain}_{timestamp}.json"
                else:
                    batch_filename = f"{safe_title}_models_{domain}_{timestamp}.json"
                
                batch_filepath = os.path.join(two_mode_dir, batch_filename)
                
                with open(batch_filepath, 'w', encoding='utf-8') as f:
                    json.dump(model_subset_data, f, indent=2, ensure_ascii=False)
                
                self.stdout.write(f"  ✓ Model Subset Batch {batch_num + 1}/{total_batches}: {batch_filename}")

    def extract_model_names_from_record(self, record):
        """Extract model names from AI JSON record (content extractor only)."""
        model_names = []
        
        # Extract from field configurations only - no inference
        field_configs = record.json_data.get('field_configurations', {})
        
        # Look for model name extractions
        if 'name' in field_configs:
            name_config = field_configs['name']
            extracted_content = name_config.get('extracted_content', [])
            
            for extraction in extracted_content:
                extracted_data = extraction.get('extracted_data', [])
                for data_item in extracted_data:
                    text = data_item.get('text', '').strip()
                    if text:
                        model_names.append(text)
        
        # Also check for direct model_name field
        if 'model_name' in field_configs:
            model_name_config = field_configs['model_name']
            extracted_content = model_name_config.get('extracted_content', [])
            
            for extraction in extracted_content:
                extracted_data = extraction.get('extracted_data', [])
                for data_item in extracted_data:
                    text = data_item.get('text', '').strip()
                    if text:
                        model_names.append(text)
        
        # Remove duplicates while preserving order
        unique_model_names = []
        for name in model_names:
            if name not in unique_model_names:
                unique_model_names.append(name)
        
        return unique_model_names

    def extract_specification_group_names_from_record(self, record):
        """Extract specification group names from AI JSON record (content extractor only)."""
        group_names = []
        
        # Extract from field configurations only
        field_configs = record.json_data.get('field_configurations', {})
        
        # Look for specification group name extractions
        if 'specification_group_names' in field_configs:
            group_config = field_configs['specification_group_names']
            extracted_content = group_config.get('extracted_content', [])
            
            for extraction in extracted_content:
                extracted_data = extraction.get('extracted_data', [])
                for data_item in extracted_data:
                    text = data_item.get('text', '').strip()
                    if text:
                        # Clean up the group name - remove special characters but keep spaces
                        clean_name = text.replace('_', ' ').replace('-', ' ')
                        # Capitalize properly (Title Case)
                        clean_name = ' '.join(word.capitalize() for word in clean_name.split())
                        group_names.append(clean_name)
        
        # Remove duplicates while preserving order
        unique_group_names = []
        for name in group_names:
            if name not in unique_group_names:
                unique_group_names.append(name)
        
        return unique_group_names

    def is_model_specific_field(self, field_name):
        """Determine if a field is model-specific or universal."""
        model_specific_fields = [
            'name', 'model_name', 'model_number', 'dimensions', 'weight', 
            'capacity', 'performance', 'model_features', 'model_specifications',
            'model_images', 'model_accessories'
        ]
        
        # Check if field name contains model-related keywords
        model_keywords = ['model', 'dimension', 'weight', 'capacity', 'performance']
        field_lower = field_name.lower()
        
        return (field_name in model_specific_fields or 
                any(keyword in field_lower for keyword in model_keywords))

    def create_complete_export_metadata(self, record):
        """Create complete export metadata for a record (all or nothing approach)."""
        return {
            'record_id': record.id,
            'generation_timestamp': record.generation_timestamp.isoformat(),
            'content_hash': record.content_hash,
            'is_current': record.is_current,
            'processing_duration': str(record.processing_duration) if record.processing_duration else None,
            'json_size_kb': record.json_size_kb,
            'site_domain': record.site_url.site_config.site_domain,
            'site_name': record.site_url.site_config.site_name,
            'source_url': record.site_url.url,
            'page_title': record.site_url.page_title,
            'exported_at': timezone.now().isoformat()
        }

    def get_records_to_export(self, options):
        """Get AI JSON records based on filter options."""
        queryset = AIJSONRecord.objects.all()
        
        # Filter by domain if specified
        if options['domain']:
            queryset = queryset.filter(
                site_url__site_config__site_domain=options['domain']
            )
        
        # Filter to current only unless all versions requested
        if not options['include_all_versions']:
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
            # Use page title as primary filename component
            page_title = record.site_url.page_title or "Unknown_Page"
            safe_title = self.make_safe_filename(page_title)
            
            # Add domain prefix and timestamp for uniqueness
            domain = record.site_url.site_config.site_domain
            timestamp = record.generation_timestamp.strftime('%Y%m%d_%H%M%S')
            
            filename = f"{safe_title}_{domain}_{timestamp}.json"
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

    def make_safe_filename(self, text):
        """Convert text to safe filename with better handling for titles."""
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