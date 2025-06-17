"""
Django management command to process completed AWS Bedrock batch inference results.

Created by: Stellar Nexus
Date: 2025-01-22
Project: Triad Docker Base - Bedrock Batch Inference System
"""

import os
import json
import tempfile
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.content_extractor.models import BatchInferenceJob, AIJSONRecord, SiteURL
from apps.content_extractor.aws_utils import (
    download_s3_file,
    get_batch_job_status
)


class Command(BaseCommand):
    help = 'Process completed AWS Bedrock batch inference results and store them in the database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--job-id',
            type=str,
            help='Process results for specific job by ID'
        )
        
        parser.add_argument(
            '--job-arn',
            type=str,
            help='Process results for specific job by ARN'
        )
        
        parser.add_argument(
            '--process-all-completed',
            action='store_true',
            help='Process results for all completed jobs that haven\'t been processed yet'
        )
        
        parser.add_argument(
            '--output-dir',
            type=str,
            default='./batch_results',
            help='Local directory to download results to (default: ./batch_results)'
        )
        
        parser.add_argument(
            '--keep-local-files',
            action='store_true',
            help='Keep downloaded result files after processing'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually doing it'
        )
    
    def handle(self, *args, **options):
        job_id = options.get('job_id')
        job_arn = options.get('job_arn')
        process_all = options.get('process_all_completed')
        output_dir = options.get('output_dir')
        keep_files = options.get('keep_local_files')
        dry_run = options.get('dry_run')
        
        if job_id or job_arn:
            job = self.get_job(job_id, job_arn)
            if job:
                self.process_job_results(job, output_dir, keep_files, dry_run)
        elif process_all:
            self.process_all_completed_jobs(output_dir, keep_files, dry_run)
        else:
            self.list_processable_jobs()
    
    def list_processable_jobs(self):
        """List jobs that have completed and can be processed."""
        completed_jobs = BatchInferenceJob.objects.filter(
            status='Completed'
        ).order_by('-completed_at')
        
        if not completed_jobs.exists():
            self.stdout.write("No completed jobs found.")
            return
        
        self.stdout.write(self.style.SUCCESS("\n=== Completed Jobs Available for Processing ==="))
        
        for job in completed_jobs:
            # Check if results have been processed
            processed = self.check_if_results_processed(job)
            status_indicator = "✅" if processed else "⏳"
            
            self.stdout.write(f"\n{status_indicator} {job.job_name}")
            self.stdout.write(f"   Job ID: {job.job_id}")
            self.stdout.write(f"   Domain: {job.site_config.site_name}")
            self.stdout.write(f"   Records: {job.record_count or 'Unknown'}")
            self.stdout.write(f"   Completed: {job.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")
            self.stdout.write(f"   Output: {job.output_s3_uri}")
            
            if processed:
                self.stdout.write(f"   Status: Results already processed")
            else:
                self.stdout.write(f"   Status: Ready for processing")
    
    def process_all_completed_jobs(self, output_dir, keep_files, dry_run):
        """Process results for all completed jobs."""
        completed_jobs = BatchInferenceJob.objects.filter(
            status='Completed'
        ).order_by('-completed_at')
        
        if not completed_jobs.exists():
            self.stdout.write("No completed jobs found.")
            return
        
        processable_jobs = []
        for job in completed_jobs:
            if not self.check_if_results_processed(job):
                processable_jobs.append(job)
        
        if not processable_jobs:
            self.stdout.write("No unprocessed completed jobs found.")
            return
        
        self.stdout.write(f"\n🔄 Processing {len(processable_jobs)} completed jobs...")
        
        for job in processable_jobs:
            self.stdout.write(f"\n--- Processing: {job.job_name} ---")
            self.process_job_results(job, output_dir, keep_files, dry_run)
    
    def process_job_results(self, job, output_dir, keep_files, dry_run):
        """Process results for a specific job."""
        if job.status != 'Completed':
            self.stdout.write(f"Job {job.job_name} is not completed (status: {job.status})")
            return
        
        # Get job details from AWS to find output files
        aws_status = get_batch_job_status(job.job_arn)
        if not aws_status:
            self.stdout.write(self.style.ERROR("Failed to get job status from AWS"))
            return
        
        # Find output files
        output_config = aws_status.get('outputDataConfig', {}).get('s3OutputDataConfig', {})
        output_s3_uri = output_config.get('s3Uri', job.output_s3_uri)
        
        self.stdout.write(f"📁 Job output location: {output_s3_uri}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] Would process results from this location"))
            return
        
        # Create output directory
        job_output_dir = os.path.join(output_dir, f"job_{job.job_id}")
        os.makedirs(job_output_dir, exist_ok=True)
        
        # Download and process result files
        try:
            # List and download result files from S3
            result_files = self.download_result_files(output_s3_uri, job_output_dir)
            
            if not result_files:
                self.stdout.write(self.style.WARNING("No result files found"))
                return
            
            # Process each result file
            processed_count = 0
            for result_file in result_files:
                count = self.process_result_file(result_file, job)
                processed_count += count
            
            self.stdout.write(
                self.style.SUCCESS(f"✅ Processed {processed_count} inference results")
            )
            
            # Update job to mark results as processed
            job.notes = f"{job.notes}\nResults processed: {timezone.now().isoformat()}"
            job.save(update_fields=['notes'])
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error processing results: {str(e)}"))
        
        finally:
            # Clean up downloaded files unless requested to keep them
            if not keep_files and os.path.exists(job_output_dir):
                import shutil
                shutil.rmtree(job_output_dir)
                self.stdout.write(f"🗑️  Cleaned up temporary files: {job_output_dir}")
    
    def download_result_files(self, output_s3_uri, local_dir):
        """Download result files from S3."""
        # For now, we'll assume the result file has a predictable name
        # In practice, you might need to list S3 objects to find the actual files
        
        # Bedrock typically creates files with names like:
        # s3://bucket/path/results.jsonl.out
        
        result_files = []
        potential_filenames = [
            'results.jsonl.out',
            'batch-results.jsonl.out',
            f'results_{datetime.now().strftime("%Y%m%d")}.jsonl.out'
        ]
        
        for filename in potential_filenames:
            s3_uri = f"{output_s3_uri.rstrip('/')}/{filename}"
            local_path = os.path.join(local_dir, filename)
            
            if download_s3_file(s3_uri, local_path):
                result_files.append(local_path)
                self.stdout.write(f"📥 Downloaded: {filename}")
            else:
                # Try without the .out extension
                alt_filename = filename.replace('.out', '')
                s3_uri = f"{output_s3_uri.rstrip('/')}/{alt_filename}"
                local_path = os.path.join(local_dir, alt_filename)
                
                if download_s3_file(s3_uri, local_path):
                    result_files.append(local_path)
                    self.stdout.write(f"📥 Downloaded: {alt_filename}")
        
        return result_files
    
    def process_result_file(self, result_file_path, job):
        """Process a single result file."""
        processed_count = 0
        
        try:
            with open(result_file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    
                    try:
                        result = json.loads(line)
                        if self.process_single_result(result, job):
                            processed_count += 1
                    except json.JSONDecodeError as e:
                        self.stdout.write(
                            self.style.WARNING(f"Invalid JSON on line {line_num}: {str(e)}")
                        )
                        continue
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"Error processing line {line_num}: {str(e)}")
                        )
                        continue
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading result file: {str(e)}"))
        
        return processed_count
    
    def process_single_result(self, result, job):
        """Process a single inference result."""
        try:
            # Bedrock result format:
            # {
            #   "recordId": "domain_batch_timestamp_record_N",
            #   "modelOutput": {
            #     "content": [
            #       {
            #         "text": "processed response text"
            #       }
            #     ]
            #   }
            # }
            
            record_id = result.get('recordId')
            model_output = result.get('modelOutput', {})
            
            if not record_id:
                self.stdout.write(self.style.WARNING("Result missing recordId"))
                return False
            
            # Extract the processed content
            content = model_output.get('content', [])
            if content and isinstance(content, list) and len(content) > 0:
                processed_text = content[0].get('text', '')
            else:
                processed_text = str(model_output)
            
            # Try to find the corresponding original record
            # The record ID format should match what we generated: domain_batch_timestamp_record_N
            site_url = self.find_original_site_url(record_id, job)
            
            if site_url:
                # Create a new AI JSON record with the processed results
                # This would be the "enhanced" version from Bedrock
                ai_record = AIJSONRecord.objects.create(
                    site_url=site_url,
                    json_data={
                        'original_record_id': record_id,
                        'bedrock_response': processed_text,
                        'batch_job_id': job.job_id,
                        'processed_at': timezone.now().isoformat(),
                        'model_used': job.model_id
                    },
                    content_hash=f"bedrock_{record_id}",
                    is_current=True
                )
                
                self.stdout.write(f"💾 Saved result for {record_id}")
                return True
            else:
                self.stdout.write(
                    self.style.WARNING(f"Could not find original record for: {record_id}")
                )
                return False
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error processing result: {str(e)}"))
            return False
    
    def find_original_site_url(self, record_id, job):
        """Find the original SiteURL record based on the record ID."""
        try:
            # The record ID might contain information to trace back to original record
            # For now, we'll try to find any SiteURL from the same site configuration
            # In a production system, you'd want a more robust mapping
            
            site_urls = SiteURL.objects.filter(
                site_config=job.site_config
            )
            
            if site_urls.exists():
                # For now, return the first one
                # In practice, you'd want to maintain a mapping between record IDs and original URLs
                return site_urls.first()
            
            return None
            
        except Exception:
            return None
    
    def check_if_results_processed(self, job):
        """Check if results for this job have already been processed."""
        # Look for AI JSON records that reference this batch job
        processed_records = AIJSONRecord.objects.filter(
            json_data__batch_job_id=job.job_id
        )
        
        return processed_records.exists()
    
    def get_job(self, job_id=None, job_arn=None):
        """Get a job by ID or ARN."""
        try:
            if job_id:
                return BatchInferenceJob.objects.get(job_id=job_id)
            elif job_arn:
                return BatchInferenceJob.objects.get(job_arn=job_arn)
            else:
                raise CommandError("Must provide either job_id or job_arn")
        except BatchInferenceJob.DoesNotExist:
            identifier = job_id or job_arn
            self.stdout.write(self.style.ERROR(f"Job not found: {identifier}"))
            return None 