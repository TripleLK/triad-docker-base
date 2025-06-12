"""
Management command to import AI JSON files into Lab Equipment Pages.

Created by: Stellar Bridge
Date: 2025-01-22
Project: Triad Docker Base

This command processes AI JSON export files (overall_details + model batches)
and creates Lab Equipment Pages using the existing API serializer infrastructure.
"""

import os
import json
import logging
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.lab_equipment_api.serializers import LabEquipmentPageCreateUpdateSerializer
from apps.base_site.models import LabEquipmentPage

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import AI JSON files into Lab Equipment Pages'

    def add_arguments(self, parser):
        parser.add_argument(
            'directory',
            type=str,
            help='Directory containing AI JSON files to import'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a dry run without creating database entries'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite existing equipment pages with same source URL'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )

    def handle(self, *args, **options):
        directory = Path(options['directory'])
        dry_run = options['dry_run']
        force_update = options['force']
        verbose = options['verbose']

        if not directory.exists():
            raise CommandError(f"Directory does not exist: {directory}")

        if not directory.is_dir():
            raise CommandError(f"Path is not a directory: {directory}")

        self.stdout.write(f"Processing AI JSON files in: {directory}")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No database changes will be made"))

        try:
            # Discover and group JSON files
            file_groups = self.discover_json_file_groups(directory)
            
            if not file_groups:
                self.stdout.write(self.style.WARNING("No valid AI JSON file groups found"))
                return

            self.stdout.write(f"Found {len(file_groups)} equipment groups to process")

            # Process each group
            total_created = 0
            total_updated = 0
            total_errors = 0

            for group_name, files in file_groups.items():
                self.stdout.write(f"\nProcessing group: {group_name}")
                
                try:
                    result = self.process_file_group(
                        group_name, files, dry_run, force_update, verbose
                    )
                    
                    if result['action'] == 'created':
                        total_created += 1
                    elif result['action'] == 'updated':
                        total_updated += 1
                        
                    if verbose:
                        self.stdout.write(
                            self.style.SUCCESS(f"✅ {result['action']}: {result['message']}")
                        )
                    else:
                        self.stdout.write(self.style.SUCCESS(f"✅ {result['action']}"))
                        
                except Exception as e:
                    total_errors += 1
                    self.stdout.write(
                        self.style.ERROR(f"❌ Error processing {group_name}: {str(e)}")
                    )
                    if verbose:
                        logger.exception(f"Error processing {group_name}")

            # Summary
            self.stdout.write(f"\n" + "="*50)
            self.stdout.write(f"SUMMARY:")
            self.stdout.write(f"Created: {total_created}")
            self.stdout.write(f"Updated: {total_updated}")
            self.stdout.write(f"Errors: {total_errors}")
            
            if dry_run:
                self.stdout.write(self.style.WARNING("DRY RUN - No actual changes made"))

        except Exception as e:
            logger.exception("Error during AI JSON import")
            raise CommandError(f"Import failed: {str(e)}")

    def discover_json_file_groups(self, directory):
        """
        Discover and group AI JSON files by equipment name.
        
        Supports two detection methods:
        1. File naming pattern: *_overall_details_*.json + *_models_batch_*_*.json
        2. JSON content analysis: presence of 'models_data' field
        """
        json_files = list(directory.glob("*.json"))
        
        if not json_files:
            return {}

        groups = {}
        
        # Method 1: Try file naming pattern detection
        overall_files = []
        model_files = []
        
        for json_file in json_files:
            filename = json_file.name
            
            if 'overall_details' in filename:
                overall_files.append(json_file)
            elif 'models_batch' in filename or 'batch' in filename:
                model_files.append(json_file)

        # If we found files with naming pattern, group them
        if overall_files or model_files:
            # For simplified case, assume all files in directory belong to same equipment
            equipment_name = directory.name  # Use directory name as equipment name
            groups[equipment_name] = {
                'overall_details': overall_files[0] if overall_files else None,
                'model_batches': model_files
            }

        # Method 2: If no groups found via naming, try content analysis
        if not groups:
            groups = self.group_files_by_content_analysis(json_files)

        return groups

    def extract_equipment_name_from_filename(self, filename, file_type):
        """Extract equipment name from filename based on pattern."""
        try:
            if file_type == 'overall':
                # Pattern: EquipmentName_overall_details_*.json
                parts = filename.split('_overall_details_')
                return parts[0] if len(parts) >= 2 else filename.replace('.json', '')
            elif file_type == 'models':
                # Pattern: EquipmentName_models_batch_*_*.json
                parts = filename.split('_models_batch_')
                return parts[0] if len(parts) >= 2 else filename.replace('.json', '')
        except Exception:
            pass
        
        return filename.replace('.json', '')

    def group_files_by_content_analysis(self, json_files):
        """Group files by analyzing JSON content structure."""
        groups = {}
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Determine file type by content
                if 'models_data' in data:
                    file_type = 'models'
                    # Try to extract equipment name from JSON content
                    equipment_name = self.extract_equipment_name_from_content(data, json_file)
                else:
                    file_type = 'overall'
                    equipment_name = self.extract_equipment_name_from_content(data, json_file)
                
                if equipment_name not in groups:
                    groups[equipment_name] = {'overall_details': None, 'model_batches': []}
                
                if file_type == 'overall':
                    groups[equipment_name]['overall_details'] = json_file
                else:
                    groups[equipment_name]['model_batches'].append(json_file)
                    
            except Exception as e:
                logger.warning(f"Could not analyze file {json_file}: {str(e)}")
                continue
        
        return groups

    def extract_equipment_name_from_content(self, data, json_file):
        """Extract equipment name from JSON content."""
        # Try title field first
        if 'title' in data and data['title']:
            title = data['title']
            # Simplify title for grouping
            return title.split(' ')[0]  # Use first word as base name
        
        # Fallback to filename
        return json_file.stem

    def process_file_group(self, group_name, files, dry_run, force_update, verbose):
        """Process a group of files (overall_details + model_batches) into a Lab Equipment Page."""
        overall_file = files['overall_details']
        model_files = files['model_batches']
        
        if not overall_file:
            raise ValueError(f"No overall details file found for {group_name}")

        # Load overall details
        with open(overall_file, 'r', encoding='utf-8') as f:
            overall_data = json.load(f)

        # Load and combine model data
        combined_models = []
        for model_file in sorted(model_files):  # Sort for consistent processing
            with open(model_file, 'r', encoding='utf-8') as f:
                model_data = json.load(f)
                if 'models_data' in model_data:
                    combined_models.extend(model_data['models_data'])

        # Combine into API format
        api_data = self.combine_json_data_for_api(overall_data, combined_models)
        
        if verbose:
            self.stdout.write(f"Combined data for {group_name}: {len(combined_models)} models")

        # Check for existing page
        existing_page = None
        source_url = api_data.get('source_url')
        if source_url:
            try:
                existing_page = LabEquipmentPage.objects.get(source_url=source_url)
            except LabEquipmentPage.DoesNotExist:
                pass

        if existing_page and not force_update:
            return {
                'action': 'skipped',
                'message': f'Page already exists (use --force to update): {existing_page.title}'
            }

        # Validate and create/update using API serializer
        if dry_run:
            # Just validate without saving
            serializer = LabEquipmentPageCreateUpdateSerializer(data=api_data)
            if not serializer.is_valid():
                raise ValueError(f"Validation errors: {serializer.errors}")
            
            action = 'updated' if existing_page else 'created'
            return {
                'action': f'{action} (dry-run)',
                'message': f'Would {action} page: {api_data.get("title", group_name)}'
            }

        with transaction.atomic():
            if existing_page:
                # Update existing page
                serializer = LabEquipmentPageCreateUpdateSerializer(
                    existing_page, data=api_data, partial=True
                )
                if not serializer.is_valid():
                    raise ValueError(f"Validation errors: {serializer.errors}")
                
                page = serializer.save()
                return {
                    'action': 'updated',
                    'message': f'Updated page: {page.title}',
                    'page_id': page.page_ptr_id
                }
            else:
                # Create new page
                serializer = LabEquipmentPageCreateUpdateSerializer(data=api_data)
                if not serializer.is_valid():
                    raise ValueError(f"Validation errors: {serializer.errors}")
                
                page = serializer.save()
                return {
                    'action': 'created',
                    'message': f'Created page: {page.title}',
                    'page_id': page.page_ptr_id
                }

    def combine_json_data_for_api(self, overall_data, models_data):
        """
        Combine overall details and models data into format expected by 
        LabEquipmentPageCreateUpdateSerializer.
        """
        # Start with overall data (remove any models_data if present)
        api_data = overall_data.copy()
        api_data.pop('models_data', None)
        
        # Add models data in the format expected by the serializer
        if models_data:
            api_data['models_data'] = models_data
        
        # Convert features_data list to proper format if needed
        if 'features_data' in api_data and isinstance(api_data['features_data'], list):
            # The serializer expects features_data as JSON field
            api_data['features_data'] = api_data['features_data']
        
        # Handle categorized_tags and create missing ones
        if 'categorized_tags' in api_data:
            tags = api_data['categorized_tags']
            if isinstance(tags, list) and tags and isinstance(tags[0], dict):
                # Convert from {category: ..., tag: ...} format to tag names
                tag_names = []
                for tag_info in tags:
                    if tag_info.get('tag'):
                        tag_name = tag_info['tag']
                        category = tag_info.get('category', 'General')
                        
                        # Create tag if it doesn't exist
                        from apps.categorized_tags.models import CategorizedTag
                        tag, created = CategorizedTag.objects.get_or_create(
                            name=tag_name,
                            defaults={'category': category}
                        )
                        tag_names.append(tag_name)
                
                api_data['categorized_tags'] = tag_names
        
        # Truncate fields that exceed database limits
        if 'meta_title' in api_data and len(api_data['meta_title']) > 60:
            api_data['meta_title'] = api_data['meta_title'][:57] + '...'
        
        if 'meta_description' in api_data and len(api_data['meta_description']) > 160:
            api_data['meta_description'] = api_data['meta_description'][:157] + '...'
        
        # Set defaults for required fields
        api_data.setdefault('source_type', 'new')
        api_data.setdefault('needs_review', True)
        api_data.setdefault('data_completeness', 0.9)
        api_data.setdefault('specification_confidence', 'high')
        
        return api_data 