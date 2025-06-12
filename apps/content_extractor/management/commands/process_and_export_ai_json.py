"""
Combined Management command to generate and export AI JSON in one step.

Combines generate_ai_json and export_ai_json functionality to generate AI-ready JSON 
and immediately export it using two-mode processing (Overall Details + Model Subsets).
Only exports the most recent version, not historical data.

Created by: Dynamic Flux
Date: 2025-01-22
Project: Triad Docker Base - Combined AI JSON Processing
"""

import json
import os
import math
import time
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.content_extractor.models import SiteConfiguration, SiteURL, AIJSONRecord
from .generate_ai_json import Command as GenerateCommand
from .export_ai_json import Command as ExportCommand


class Command(BaseCommand):
    help = 'Generate and export AI JSON in one step (most recent version only, two-mode processing)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            type=str,
            help='Process and export URLs for specific domain only'
        )
        parser.add_argument(
            '--url-id',
            type=int,
            help='Process and export specific URL by ID'
        )
        parser.add_argument(
            '--all-sites',
            action='store_true',
            help='Process and export all active sites'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='./ai_json_exports',
            help='Output directory for exported files (default: ./ai_json_exports)'
        )
        parser.add_argument(
            '--models-per-batch',
            type=int,
            default=4,
            help='Number of models per batch for model subset processing (default: 4)'
        )
        parser.add_argument(
            '--force-refresh',
            action='store_true',
            help='Regenerate JSON even if already exists'
        )
        parser.add_argument(
            '--include-metadata',
            action='store_true',
            help='Include processing metadata in exports'
        )

    def handle(self, *args, **options):
        start_time = time.time()
        
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting combined AI JSON generation and export')
        )
        
        # Step 1: Generate AI JSON
        self.stdout.write('\n📝 Step 1: Generating AI JSON...')
        generate_success = self._run_generate_step(options)
        
        if not generate_success:
            raise CommandError("AI JSON generation failed")
        
        # Step 2: Export the generated JSON using two-mode processing
        self.stdout.write('\n📤 Step 2: Exporting generated AI JSON...')
        export_success = self._run_export_step(options)
        
        if not export_success:
            raise CommandError("AI JSON export failed")
        
        # Summary
        total_time = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Combined processing completed in {total_time:.2f} seconds'
        ))

    def _run_generate_step(self, options):
        """Run the AI JSON generation step."""
        try:
            # Initialize generate command
            generate_cmd = GenerateCommand()
            generate_cmd.stdout = self.stdout
            generate_cmd.style = self.style
            
            # Build arguments for generate command
            generate_args = []
            generate_options = {
                'force_refresh': options['force_refresh'],
                'domain': options.get('domain'),
                'url_id': options.get('url_id'),
                'all_sites': options.get('all_sites', False)
            }
            
            # Run generation
            generate_cmd.handle(*generate_args, **generate_options)
            self.stdout.write(self.style.SUCCESS('✅ AI JSON generation completed'))
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ AI JSON generation failed: {e}'))
            return False

    def _run_export_step(self, options):
        """Run the AI JSON export step with two-mode processing."""
        try:
            # Get records to export (most recent only)
            records = self._get_records_to_export(options)
            
            if not records.exists():
                self.stdout.write(self.style.WARNING("No AI JSON records found to export"))
                return True  # Not an error, just nothing to export
            
            total_records = records.count()
            self.stdout.write(f"Exporting {total_records} AI JSON records...")
            
            # Create output directory
            output_dir = options['output_dir']
            os.makedirs(output_dir, exist_ok=True)
            
            # Run two-mode export
            self._export_two_mode_processing(records, output_dir, options)
            
            self.stdout.write(self.style.SUCCESS(f'✅ Export completed: {total_records} records'))
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ AI JSON export failed: {e}'))
            return False

    def _get_records_to_export(self, options):
        """Get AI JSON records based on filter options (most recent only)."""
        queryset = AIJSONRecord.objects.filter(is_current=True)  # Only most recent
        
        # Filter by domain if specified
        if options['domain']:
            queryset = queryset.filter(
                site_url__site_config__site_domain=options['domain']
            )
        
        # Filter by specific URL if specified
        if options.get('url_id'):
            queryset = queryset.filter(site_url__id=options['url_id'])
        
        return queryset.select_related(
            'site_url__site_config'
        ).order_by('-generation_timestamp')

    def _export_two_mode_processing(self, records, output_dir, options):
        """Export JSON files for two-mode processing with enhanced spec group support."""
        two_mode_dir = os.path.join(output_dir, 'two_mode')
        os.makedirs(two_mode_dir, exist_ok=True)
        
        self.stdout.write("Exporting two-mode processing files...")
        
        # Initialize export command for helper methods
        export_cmd = ExportCommand()
        
        for record in records:
            base_data = record.json_data.copy()
            model_names = export_cmd.extract_model_names_from_record(record)
            spec_group_names = export_cmd.extract_specification_group_names_from_record(record)
            
            if not model_names:
                self.stdout.write(self.style.ERROR(
                    f"No model names found for record {record.id} - content extractor must include model names. Skipping."
                ))
                continue
            
            # Generate file base name
            page_title = record.site_url.page_title or "Unknown_Page"
            safe_title = export_cmd.make_safe_filename(page_title)
            domain = record.site_url.site_config.site_domain
            timestamp = record.generation_timestamp.strftime('%Y%m%d_%H%M%S')
            
            # Add metadata if requested
            metadata = None
            if options['include_metadata']:
                metadata = export_cmd.create_complete_export_metadata(record)
            
            # 1. Generate Overall Details file (everything except models)
            overall_details_data = base_data.copy()
            overall_details_data['_processing_mode'] = 'OVERALL_DETAILS'
            
            # Remove models from the overall details data
            if 'field_configurations' in overall_details_data:
                field_configs = overall_details_data['field_configurations']
                overall_details_data['field_configurations'] = {
                    key: value for key, value in field_configs.items()
                    if not export_cmd.is_model_specific_field(key)
                }
            
            # Add extracted specification group names to overall details (unique names only)
            if spec_group_names:
                overall_details_data['extracted_specification_groups'] = spec_group_names
                overall_details_data['_specification_instructions'] = {
                    "use_exact_group_names": True,
                    "no_underscores_in_names": True,
                    "extract_all_available_data": True,
                    "available_groups": spec_group_names
                }
                self.stdout.write(f"  📋 Including {len(spec_group_names)} specification groups: {', '.join(spec_group_names)}")
            
            if metadata:
                overall_details_data['export_metadata'] = metadata.copy()
                overall_details_data['export_metadata']['export_type'] = 'overall_details'
            
            overall_filename = f"{safe_title}_overall_details_{domain}_{timestamp}.json"
            overall_filepath = os.path.join(two_mode_dir, overall_filename)
            
            with open(overall_filepath, 'w', encoding='utf-8') as f:
                json.dump(overall_details_data, f, indent=2, ensure_ascii=False)
            
            self.stdout.write(f"  ✓ Overall Details: {overall_filename}")
            
            # 2. Generate Model Subset files with enhanced spec group support
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
                        if export_cmd.is_model_specific_field(key) or key == 'name'
                    }
                
                # Add the specific model names to process
                model_subset_data['target_model_names'] = batch_model_names
                
                # ENSURE spec_group_names are included in model subset data
                if spec_group_names:
                    model_subset_data['extracted_specification_groups'] = spec_group_names
                    model_subset_data['_specification_instructions'] = {
                        "use_exact_group_names": True,
                        "no_underscores_in_names": True,
                        "extract_all_available_data": True,
                        "available_groups": spec_group_names
                    }
                    self.stdout.write(f"  📋 Including {len(spec_group_names)} specification groups: {', '.join(spec_group_names)}")
                
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