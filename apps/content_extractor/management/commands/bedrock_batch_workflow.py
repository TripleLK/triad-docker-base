"""
Django management command for AWS Bedrock batch processing workflow.

This command handles the complete workflow:
1. Export AI JSON data (optional)
2. Upload to S3 and start batch inference
3. Monitor job completion
4. Download results and create lab equipment pages

Created by: Thunder Ridge
Date: 2025-06-17
Project: Triad Docker Base
"""

import os
import sys
import json
import time
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

from apps.content_extractor.batch_processing import (
    BedrockBatchProcessor, 
    run_complete_batch_workflow,
    find_latest_batch_export
)


class Command(BaseCommand):
    help = 'Run complete AWS Bedrock batch processing workflow for lab equipment data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-file',
            type=str,
            help='Path to batch JSON file (if not provided, finds latest export)'
        )
        parser.add_argument(
            '--export-new',
            action='store_true',
            help='Export new AI JSON batch data before processing'
        )
        parser.add_argument(
            '--export-format',
            type=str,
            default='batch',
            choices=['batch', 'individual'],
            help='Format for new export (batch or individual files)'
        )
        parser.add_argument(
            '--model-id',
            type=str,
            default='anthropic.claude-3-haiku-20240307-v1:0',
            help='AWS Bedrock model ID to use'
        )
        parser.add_argument(
            '--upload-only',
            action='store_true',
            help='Only upload and start batch job, do not wait for completion or create pages'
        )
        parser.add_argument(
            '--no-pages',
            action='store_true',
            help='Do not create lab equipment pages from results'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a dry run for page creation (no actual database changes)'
        )
        parser.add_argument(
            '--force-update',
            action='store_true',
            help='Force update existing lab equipment pages'
        )
        parser.add_argument(
            '--monitor-job',
            type=str,
            help='Monitor an existing job ID instead of starting a new one'
        )
        parser.add_argument(
            '--check-interval',
            type=int,
            default=30,
            help='Seconds between job status checks'
        )
        parser.add_argument(
            '--max-wait',
            type=int,
            default=3600,
            help='Maximum wait time for job completion (seconds)'
        )

    def handle(self, *args, **options):
        batch_file = options.get('batch_file')
        export_new = options['export_new']
        export_format = options['export_format']
        model_id = options['model_id']
        upload_only = options['upload_only']
        no_pages = options['no_pages']
        dry_run = options['dry_run']
        force_update = options['force_update']
        monitor_job = options.get('monitor_job')
        check_interval = options['check_interval']
        max_wait = options['max_wait']

        self.stdout.write(self.style.SUCCESS("AWS Bedrock Batch Processing Workflow"))
        self.stdout.write("=" * 50)

        try:
            # Handle job monitoring mode
            if monitor_job:
                self.monitor_existing_job(
                    job_id=monitor_job,
                    create_pages=not no_pages,
                    dry_run=dry_run,
                    force_update=force_update,
                    check_interval=check_interval,
                    max_wait=max_wait
                )
                return

            # Step 1: Export new data if requested
            if export_new:
                self.stdout.write("\n📤 Exporting AI JSON data...")
                batch_file = self.export_ai_json_data(export_format)
                if not batch_file:
                    raise CommandError("Failed to export AI JSON data")
                self.stdout.write(self.style.SUCCESS(f"✅ Exported to: {batch_file}"))

            # Step 2: Find batch file if not provided
            if not batch_file:
                batch_file = find_latest_batch_export()
                if not batch_file:
                    raise CommandError(
                        "No batch file found. Use --export-new to create one or specify --batch-file"
                    )
                self.stdout.write(f"📁 Using latest export: {batch_file}")

            # Validate batch file exists
            if not os.path.exists(batch_file):
                raise CommandError(f"Batch file not found: {batch_file}")

            # Count records in batch file
            record_count = self.count_batch_records(batch_file)
            self.stdout.write(f"📊 Processing {record_count} records")

            # Step 3: Run workflow
            if upload_only:
                # Upload and start job only
                results = self.upload_and_start_only(batch_file, model_id)
            else:
                # Complete workflow
                create_pages = not no_pages
                results = run_complete_batch_workflow(
                    batch_file_path=batch_file,
                    model_id=model_id,
                    create_pages=create_pages,
                    dry_run=dry_run,
                    force_update=force_update
                )

            # Display results
            self.display_workflow_results(results)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Workflow failed: {str(e)}"))
            raise CommandError(f"Batch processing workflow failed: {str(e)}")

    def export_ai_json_data(self, export_format='batch'):
        """Export AI JSON data using existing management command."""
        try:
            self.stdout.write(f"Calling export_ai_json with format: {export_format}")
            
            # Use the existing export command
            call_command('export_ai_json', format=export_format, verbosity=1)
            
            # Find the exported file
            if export_format == 'batch':
                batch_file = find_latest_batch_export()
                return batch_file
            else:
                # For individual format, we'd need to find the directory
                # For now, default to batch format
                self.stdout.write(self.style.WARNING(
                    "Individual format exports need directory processing - using batch format"
                ))
                call_command('export_ai_json', format='batch', verbosity=1)
                return find_latest_batch_export()
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Export failed: {str(e)}"))
            return None

    def count_batch_records(self, batch_file):
        """Count records in batch JSON file."""
        try:
            with open(batch_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return len(data)
                elif isinstance(data, dict) and 'records' in data:
                    return len(data['records'])
                else:
                    return 1  # Single record file
        except Exception:
            return 0

    def upload_and_start_only(self, batch_file, model_id):
        """Upload to S3 and start batch job without waiting for completion."""
        processor = BedrockBatchProcessor()
        
        self.stdout.write("\n🚀 Starting upload and job creation...")
        
        results = processor.upload_and_start_batch_job(
            batch_file_path=batch_file,
            model_id=model_id
        )
        
        return {
            'success': results['success'],
            'upload_only': True,
            'upload_results': results.get('upload_results', {}),
            'job_info': results.get('job_info', {}),
            'error': results.get('error')
        }

    def monitor_existing_job(self, job_id, create_pages=True, dry_run=False, force_update=False, check_interval=30, max_wait=3600):
        """Monitor an existing job and optionally create pages when complete."""
        self.stdout.write(f"\n👀 Monitoring job: {job_id}")
        
        processor = BedrockBatchProcessor()
        
        # Wait for completion
        completion_results = processor.wait_for_job_completion(
            job_id=job_id,
            check_interval=check_interval,
            max_wait_time=max_wait
        )
        
        self.stdout.write(f"Job Status: {completion_results['status']}")
        
        if create_pages and completion_results['status'] == 'Completed' and completion_results.get('success_count', 0) > 0:
            # Get job details to find output S3 URL
            from apps.content_extractor.aws_utils import get_batch_job_status
            job_details = get_batch_job_status(job_id)
            
            if 'output_s3_uri' in job_details:
                self.stdout.write("\n📝 Creating lab equipment pages from results...")
                
                page_results = processor.process_batch_results_to_pages(
                    job_id=job_id,
                    output_s3_url=job_details['output_s3_uri'],
                    dry_run=dry_run,
                    force_update=force_update
                )
                
                self.display_page_creation_results(page_results)
            else:
                self.stdout.write(self.style.WARNING("Could not find output S3 URI for job"))
        
        self.display_job_completion_results(completion_results)

    def display_workflow_results(self, results):
        """Display comprehensive workflow results."""
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("WORKFLOW RESULTS")
        self.stdout.write("=" * 50)
        
        if results.get('success'):
            self.stdout.write(self.style.SUCCESS("✅ Workflow completed successfully!"))
        else:
            self.stdout.write(self.style.ERROR("❌ Workflow failed"))
            
        # Upload results
        if 'upload_results' in results:
            upload = results['upload_results']
            if upload:
                self.stdout.write(f"\n📤 UPLOAD RESULTS:")
                self.stdout.write(f"   Records: {upload.get('record_count', 'Unknown')}")
                self.stdout.write(f"   S3 Input: {upload.get('input_s3_url', 'Not available')}")
                self.stdout.write(f"   S3 Output: {upload.get('output_s3_url', 'Not available')}")
        
        # Job info
        if 'job_info' in results:
            job = results['job_info']
            if job:
                self.stdout.write(f"\n🔧 JOB INFORMATION:")
                self.stdout.write(f"   Job ID: {job.get('job_id', 'Unknown')}")
                self.stdout.write(f"   Job ARN: {job.get('job_arn', 'Unknown')}")
                self.stdout.write(f"   Model: {job.get('model_id', 'Unknown')}")
        
        # Processing stats
        if 'processing_stats' in results:
            stats = results['processing_stats']
            if stats:
                self.stdout.write(f"\n📊 PROCESSING STATISTICS:")
                self.stdout.write(f"   Status: {stats.get('status', 'Unknown')}")
                self.stdout.write(f"   Total Records: {stats.get('total_records', 0)}")
                self.stdout.write(f"   Successful: {stats.get('success_count', 0)}")
                self.stdout.write(f"   Errors: {stats.get('error_count', 0)}")
                self.stdout.write(f"   Wait Time: {stats.get('wait_time', 0):.1f} seconds")
        
        # Page creation results
        if 'page_creation_results' in results:
            self.display_page_creation_results(results['page_creation_results'])
        
        # Upload only results
        if results.get('upload_only'):
            self.stdout.write(f"\n⏸️  UPLOAD ONLY MODE:")
            self.stdout.write("   Job started but not monitored for completion")
            self.stdout.write("   Use --monitor-job to check status later")
        
        # Errors
        if 'errors' in results and results['errors']:
            self.stdout.write(f"\n⚠️  ERRORS:")
            for error in results['errors']:
                self.stdout.write(f"   • {error}")

    def display_page_creation_results(self, page_results):
        """Display page creation results."""
        if not page_results:
            return
            
        self.stdout.write(f"\n📝 PAGE CREATION RESULTS:")
        
        if page_results.get('dry_run'):
            self.stdout.write("   DRY RUN MODE - No actual pages created")
            self.stdout.write(f"   Files Processed: {page_results.get('files_processed', 0)}")
        else:
            stats = page_results.get('page_stats', {})
            self.stdout.write(f"   Created: {stats.get('total_created', 0)}")
            self.stdout.write(f"   Updated: {stats.get('total_updated', 0)}")
            self.stdout.write(f"   Errors: {stats.get('total_errors', 0)}")
            self.stdout.write(f"   Files Processed: {stats.get('files_processed', 0)}")
            
            if stats.get('success'):
                self.stdout.write(self.style.SUCCESS("   ✅ All pages created successfully"))
            elif stats.get('total_errors', 0) > 0:
                self.stdout.write(self.style.ERROR("   ❌ Some pages failed to create"))

    def display_job_completion_results(self, completion_results):
        """Display job completion monitoring results."""
        self.stdout.write(f"\n⏱️  JOB MONITORING RESULTS:")
        self.stdout.write(f"   Final Status: {completion_results.get('status', 'Unknown')}")
        self.stdout.write(f"   Wait Time: {completion_results.get('wait_time', 0):.1f} seconds")
        
        if completion_results.get('status') == 'Completed':
            self.stdout.write(self.style.SUCCESS("   ✅ Job completed successfully"))
        elif completion_results.get('status') == 'Failed':
            self.stdout.write(self.style.ERROR("   ❌ Job failed"))
        elif completion_results.get('status') == 'Timeout':
            self.stdout.write(self.style.WARNING("   ⏰ Monitoring timed out")) 