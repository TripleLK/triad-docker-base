#!/usr/bin/env python3
"""
Export to S3 - Direct export of existing AI JSON records to S3

This command exports existing AI JSON records from the database directly to S3
with Bedrock batch inference format support. No re-crawling or re-processing needed.

Created by: Digital Phoenix
Date: 2025-01-22
Project: Triad Docker Base
"""

import os
import json
import tempfile
import time
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.content_extractor.models import SiteConfiguration, SiteURL, AIJSONRecord
from apps.content_extractor.aws_utils import (
    upload_files_batch, 
    convert_json_to_bedrock_jsonl,
    convert_batch_json_to_bedrock_jsonl,
    delete_local_files,
    generate_s3_bucket_name,
    create_bucket_if_not_exists
)


class Command(BaseCommand):
    help = 'Export existing AI JSON records directly to S3 with Bedrock format support'

    def add_arguments(self, parser):
        parser.add_argument(
            'domain',
            type=str,
            help='Domain to export (e.g., www.airscience.com)'
        )
        parser.add_argument(
            '--s3-bucket',
            type=str,
            help='S3 bucket name (auto-generated if not provided)'
        )
        parser.add_argument(
            '--s3-prefix',
            type=str,
            default='batch-processing',
            help='S3 prefix/folder (default: batch-processing)'
        )
        parser.add_argument(
            '--bedrock-format',
            action='store_true',
            help='Convert to Bedrock JSONL format for batch inference'
        )
        parser.add_argument(
            '--bedrock-prompt-arn',
            type=str,
            help='Bedrock prompt ARN for batch inference (uses default if not provided)'
        )
        parser.add_argument(
            '--delete-local',
            action='store_true',
            help='Delete local temporary files after successful upload'
        )
        parser.add_argument(
            '--format',
            choices=['individual', 'batch', 'both'],
            default='batch',
            help='Export format: individual files, single batch file, or both (default: batch for Bedrock inference)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of records to export (for testing)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be uploaded without actually uploading'
        )

    def handle(self, *args, **options):
        self.domain = options['domain']
        self.s3_bucket = options['s3_bucket']
        self.s3_prefix = options['s3_prefix']
        self.bedrock_format = options['bedrock_format']
        self.bedrock_prompt_arn = options['bedrock_prompt_arn']
        self.delete_local = options['delete_local']
        self.format = options['format']
        self.limit = options['limit']
        self.dry_run = options['dry_run']

        start_time = time.time()

        # Get site configuration
        try:
            site_config = SiteConfiguration.objects.get(site_domain=self.domain)
        except SiteConfiguration.DoesNotExist:
            raise CommandError(f"Site configuration for domain '{self.domain}' not found")

        # Get existing AI JSON records
        records_query = AIJSONRecord.objects.filter(
            site_url__site_config=site_config,
            is_current=True
        ).select_related('site_url')

        if self.limit:
            records_query = records_query[:self.limit]

        records = list(records_query)

        if not records:
            raise CommandError(f"No AI JSON records found for domain '{self.domain}'")

        self.stdout.write(f"🎯 Found {len(records)} existing AI JSON records for {self.domain}")

        # Generate S3 bucket name if not provided
        if not self.s3_bucket:
            self.s3_bucket = generate_s3_bucket_name(self.domain)
            self.stdout.write(f"🪣 Generated S3 bucket name: {self.s3_bucket}")

        # Update S3 prefix to include domain for organization
        if not self.s3_prefix or self.s3_prefix == 'batch-processing':
            # Clean domain for use in S3 prefix
            clean_domain = self.domain.replace('www.', '').replace('.', '-').lower()
            self.s3_prefix = f"batch-processing/{clean_domain}"
            self.stdout.write(f"📂 Generated S3 prefix: {self.s3_prefix}")

        # Create temporary directory for files
        with tempfile.TemporaryDirectory() as temp_dir:
            self.stdout.write(f"📁 Using temporary directory: {temp_dir}")

            files_to_upload = []
            upload_results = {}

            try:
                # Export records to temporary files
                if self.format in ['individual', 'both']:
                    individual_files = self.export_individual_files(records, temp_dir)
                    files_to_upload.extend(individual_files)

                if self.format in ['batch', 'both']:
                    batch_file = self.export_batch_file(records, temp_dir, site_config)
                    files_to_upload.append(batch_file)

                if not files_to_upload:
                    raise CommandError("No files were generated for upload")

                self.stdout.write(f"📄 Generated {len(files_to_upload)} files for upload")

                # Convert to Bedrock format if requested
                if self.bedrock_format:
                    files_to_upload = self.convert_to_bedrock_format(files_to_upload, temp_dir)

                if self.dry_run:
                    self.show_dry_run_summary(files_to_upload, site_config)
                    return

                # Upload to S3
                upload_results = self.upload_to_s3(files_to_upload)

                # Clean up local files if requested
                if self.delete_local and upload_results:
                    successful_files = [f for f, result in upload_results.items() if result.get('success')]
                    if successful_files:
                        # Create success_uploads dict mapping file paths to S3 URLs
                        success_uploads = {f: result.get('s3_url') for f, result in upload_results.items() if result.get('success')}
                        deleted_count, failed_count = delete_local_files(successful_files, success_uploads)
                        self.stdout.write(f"🗑️  Deleted {deleted_count} local files")
                        if failed_count > 0:
                            self.stdout.write(f"⚠️  Failed to delete {failed_count} files")

                # Summary
                total_time = time.time() - start_time
                successful_uploads = sum(1 for result in upload_results.values() if result.get('success'))
                
                self.stdout.write(self.style.SUCCESS(
                    f"\n🎉 Export completed in {total_time:.2f} seconds"
                ))
                self.stdout.write(f"📊 Records exported: {len(records)}")
                self.stdout.write(f"📁 Files uploaded: {successful_uploads}/{len(files_to_upload)}")
                self.stdout.write(f"🪣 S3 bucket: {self.s3_bucket}")
                self.stdout.write(f"📂 S3 prefix: {self.s3_prefix}")

                if self.bedrock_format:
                    self.stdout.write(f"🤖 Bedrock format: Enabled")
                    if self.bedrock_prompt_arn:
                        self.stdout.write(f"🎯 Prompt ARN: {self.bedrock_prompt_arn}")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Export failed: {str(e)}"))
                raise

    def export_individual_files(self, records, temp_dir):
        """Export each AI JSON record as individual file."""
        individual_dir = os.path.join(temp_dir, 'individual')
        os.makedirs(individual_dir, exist_ok=True)
        
        self.stdout.write(f"📄 Exporting {len(records)} individual JSON files...")
        
        files = []
        for i, record in enumerate(records, 1):
            # Use page title as primary filename component
            page_title = record.site_url.page_title or f"page_{record.id}"
            safe_title = self.make_safe_filename(page_title)
            
            # Add timestamp for uniqueness
            timestamp = record.generation_timestamp.strftime('%Y%m%d_%H%M%S')
            filename = f"{safe_title}_{timestamp}.json"
            filepath = os.path.join(individual_dir, filename)
            
            # Prepare export data
            export_data = record.json_data.copy()
            export_data['export_metadata'] = {
                'record_id': record.id,
                'url': record.site_url.url,
                'generation_timestamp': record.generation_timestamp.isoformat(),
                'exported_at': timezone.now().isoformat(),
                'export_source': 'existing_database_record'
            }
            
            # Write file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            files.append(filepath)
            
            if i % 10 == 0:
                self.stdout.write(f"   ✓ Exported {i}/{len(records)} files...")
        
        self.stdout.write(f"   ✅ Completed {len(files)} individual files")
        return files

    def export_batch_file(self, records, temp_dir, site_config):
        """Export all records as single batch JSON file."""
        self.stdout.write(f"📦 Exporting batch JSON file...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_domain = self.make_safe_filename(site_config.site_domain)
        filename = f"{safe_domain}_batch_{timestamp}.json"
        filepath = os.path.join(temp_dir, filename)
        
        batch_data = {
            'site_info': {
                'domain': site_config.site_domain,
                'site_name': site_config.site_name,
                'total_records': len(records),
                'exported_at': timezone.now().isoformat(),
                'export_source': 'existing_database_records'
            },
            'records': []
        }
        
        for record in records:
            record_data = {
                'record_id': record.id,
                'url': record.site_url.url,
                'page_title': record.site_url.page_title,
                'generation_timestamp': record.generation_timestamp.isoformat(),
                'json_data': record.json_data
            }
            batch_data['records'].append(record_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, indent=2, ensure_ascii=False)
        
        self.stdout.write(f"   ✅ Batch file: {filename}")
        return filepath

    def convert_to_bedrock_format(self, files_to_upload, temp_dir):
        """Convert files to Bedrock JSONL format."""
        self.stdout.write("🔄 Converting to Bedrock JSONL format...")
        
        if self.bedrock_prompt_arn:
            self.stdout.write(f"🎯 Using prompt ARN: {self.bedrock_prompt_arn}")
        else:
            self.stdout.write("🎯 Using default prompt ARN")
        
        bedrock_files = []
        
        for file_path in files_to_upload:
            if '_batch_' in os.path.basename(file_path):
                # Handle batch file conversion
                jsonl_path = convert_batch_json_to_bedrock_jsonl(
                    file_path, 
                    temp_dir, 
                    self.bedrock_prompt_arn
                )
            else:
                # Handle individual file conversion - generate proper output path
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                jsonl_filename = f"{base_name}_bedrock.jsonl"
                jsonl_output_path = os.path.join(temp_dir, jsonl_filename)
                
                jsonl_path = convert_json_to_bedrock_jsonl(
                    file_path, 
                    jsonl_output_path, 
                    self.bedrock_prompt_arn
                )
            
            if jsonl_path:
                bedrock_files.append(jsonl_path)
        
        self.stdout.write(f"   ✅ Converted {len(bedrock_files)} files to Bedrock JSONL format")
        return bedrock_files

    def upload_to_s3(self, files_to_upload):
        """Upload files to S3."""
        self.stdout.write(f"☁️  Uploading {len(files_to_upload)} files to S3...")
        
        # Create bucket if it doesn't exist
        self.stdout.write(f"🔍 Checking/creating S3 bucket: {self.s3_bucket}")
        if not create_bucket_if_not_exists(self.s3_bucket, 'us-east-1'):
            raise Exception(f"Failed to create or access S3 bucket: {self.s3_bucket}")
        
        # Upload files
        upload_results = upload_files_batch(
            files_to_upload,
            self.s3_bucket,
            self.s3_prefix
        )
        
        # Report results
        successful = sum(1 for result in upload_results.values() if result.get('success'))
        failed = len(upload_results) - successful
        
        self.stdout.write(f"   ✅ Successful uploads: {successful}")
        if failed > 0:
            self.stdout.write(f"   ❌ Failed uploads: {failed}")
            for file_path, result in upload_results.items():
                if not result.get('success'):
                    self.stdout.write(f"      Failed: {os.path.basename(file_path)} - {result.get('error', 'Unknown error')}")
        
        return upload_results

    def show_dry_run_summary(self, files_to_upload, site_config):
        """Show what would be uploaded in dry run mode."""
        self.stdout.write(self.style.WARNING("\n🔍 DRY RUN - No files will be uploaded"))
        self.stdout.write(f"📊 Summary:")
        self.stdout.write(f"   Domain: {site_config.site_domain}")
        self.stdout.write(f"   S3 Bucket: {self.s3_bucket}")
        self.stdout.write(f"   S3 Prefix: {self.s3_prefix}")
        self.stdout.write(f"   Files to upload: {len(files_to_upload)}")
        self.stdout.write(f"   Bedrock format: {'Yes' if self.bedrock_format else 'No'}")
        
        if self.bedrock_format and self.bedrock_prompt_arn:
            self.stdout.write(f"   Prompt ARN: {self.bedrock_prompt_arn}")
        
        self.stdout.write(f"\n📁 Files that would be uploaded:")
        for file_path in files_to_upload:
            file_size = os.path.getsize(file_path) / 1024  # KB
            self.stdout.write(f"   • {os.path.basename(file_path)} ({file_size:.1f} KB)")

    def make_safe_filename(self, filename):
        """Convert filename to safe format for filesystem."""
        import re
        # Replace problematic characters
        safe = re.sub(r'[^\w\-_\.]', '_', filename)
        # Remove multiple underscores
        safe = re.sub(r'_+', '_', safe)
        # Remove leading/trailing underscores
        safe = safe.strip('_')
        # Limit length
        return safe[:100] if safe else 'unnamed' 