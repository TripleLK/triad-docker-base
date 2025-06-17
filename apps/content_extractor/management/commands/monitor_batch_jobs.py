"""
Django management command to monitor AWS Bedrock batch inference jobs.

Created by: Stellar Nexus
Date: 2025-01-22
Project: Triad Docker Base - Bedrock Batch Inference System
"""

import time
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.content_extractor.models import BatchInferenceJob
from apps.content_extractor.aws_utils import (
    get_batch_job_status,
    list_batch_jobs,
    stop_batch_job,
    extract_job_id_from_arn
)


class Command(BaseCommand):
    help = 'Monitor AWS Bedrock batch inference jobs and update their status'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--job-id',
            type=str,
            help='Monitor specific job by ID'
        )
        
        parser.add_argument(
            '--job-arn',
            type=str,
            help='Monitor specific job by ARN'
        )
        
        parser.add_argument(
            '--list-all',
            action='store_true',
            help='List all jobs in database'
        )
        
        parser.add_argument(
            '--list-active',
            action='store_true',
            help='List only active jobs (Submitted, InProgress)'
        )
        
        parser.add_argument(
            '--update-all',
            action='store_true',
            help='Update status for all active jobs'
        )
        
        parser.add_argument(
            '--watch',
            action='store_true',
            help='Continuously monitor jobs (update every 60 seconds)'
        )
        
        parser.add_argument(
            '--stop-job',
            type=str,
            help='Stop a running job by ID or ARN'
        )
        
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Watch mode update interval in seconds (default: 60)'
        )
    
    def handle(self, *args, **options):
        job_id = options.get('job_id')
        job_arn = options.get('job_arn')
        list_all = options['list_all']
        list_active = options['list_active']
        update_all = options['update_all']
        watch = options['watch']
        stop_job = options['stop_job']
        interval = options['interval']
        
        if stop_job:
            if not (job_id or job_arn):
                raise CommandError("Job ID or ARN required to stop a job")
            self.stop_job(job_id, job_arn)
            return
        
        if watch:
            if not (job_id or job_arn):
                raise CommandError("Job ID or ARN required for watch mode")
            self.watch_job(job_id, job_arn, interval)
            return
        
        if list_all:
            self.list_all_jobs()
            return
        
        if list_active:
            self.list_active_jobs()
            return
        
        if update_all:
            self.update_all_jobs()
            return
        
        if job_id or job_arn:
            # Try to find job in database first
            job = None
            if job_id:
                job = BatchInferenceJob.objects.filter(job_id=job_id).first()
            elif job_arn:
                job = BatchInferenceJob.objects.filter(job_arn=job_arn).first()
            
            if job:
                # Database job found - show detailed info
                self.show_job_status(job)
            else:
                # Standalone job - query AWS directly
                self.stdout.write(f"Job not found in database. Querying AWS directly...")
                self.show_standalone_job_status(job_id, job_arn)
            return
        
        # Default: show recent jobs
        self.show_recent_jobs()
    
    def list_jobs(self, active_only=True):
        """List batch inference jobs."""
        if active_only:
            jobs = BatchInferenceJob.objects.filter(
                status__in=['Submitted', 'InProgress']
            ).order_by('-submitted_at')
            self.stdout.write(self.style.SUCCESS("\n=== Active Batch Inference Jobs ==="))
        else:
            jobs = BatchInferenceJob.objects.all().order_by('-submitted_at')
            self.stdout.write(self.style.SUCCESS("\n=== All Batch Inference Jobs ==="))
        
        if not jobs.exists():
            self.stdout.write("No jobs found.")
            return
        
        for job in jobs:
            self.display_job_summary(job)
    
    def display_job_summary(self, job):
        """Display a summary of a batch job."""
        status_style = self.get_status_style(job.status)
        
        self.stdout.write(f"\n📋 {job.job_name}")
        self.stdout.write(f"   ID: {job.job_id}")
        self.stdout.write(f"   Status: {status_style(job.status)}")
        self.stdout.write(f"   Domain: {job.site_config.site_name}")
        self.stdout.write(f"   Model: {job.model_id}")
        self.stdout.write(f"   Records: {job.record_count or 'Unknown'}")
        self.stdout.write(f"   Submitted: {job.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if job.started_at:
            self.stdout.write(f"   Started: {job.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if job.completed_at:
            self.stdout.write(f"   Completed: {job.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if job.duration:
            self.stdout.write(f"   Duration: {job.duration}")
        
        if job.failure_reason:
            self.stdout.write(f"   Error: {self.style.ERROR(job.failure_reason)}")
    
    def get_status_style(self, status):
        """Get appropriate style for job status."""
        if status == 'Completed':
            return self.style.SUCCESS
        elif status in ['Failed', 'Stopped']:
            return self.style.ERROR
        elif status == 'InProgress':
            return self.style.WARNING
        else:
            return lambda x: x
    
    def monitor_specific_job(self, job_id=None, job_arn=None):
        """Monitor a specific job and update its status."""
        job = self.get_job(job_id, job_arn)
        if not job:
            return
        
        self.stdout.write(f"\n🔍 Monitoring job: {job.job_name}")
        
        # Get current status from AWS
        aws_status = get_batch_job_status(job.job_arn)
        if not aws_status:
            self.stdout.write(self.style.ERROR("Failed to get job status from AWS"))
            return
        
        # Update job status
        self.update_job_from_aws_response(job, aws_status)
        
        # Display updated information
        self.display_job_details(job, aws_status)
    
    def display_job_details(self, job, aws_response):
        """Display detailed job information."""
        self.stdout.write(f"\n=== Job Details: {job.job_name} ===")
        self.stdout.write(f"Job ID: {job.job_id}")
        self.stdout.write(f"Job ARN: {job.job_arn}")
        self.stdout.write(f"Status: {self.get_status_style(job.status)(job.status)}")
        self.stdout.write(f"Model: {job.model_id}")
        self.stdout.write(f"Input: {job.input_s3_uri}")
        self.stdout.write(f"Output: {job.output_s3_uri}")
        
        if aws_response:
            # Display AWS-specific information
            if 'inputDataConfig' in aws_response:
                input_records = aws_response.get('inputDataConfig', {}).get('s3InputDataConfig', {})
                if input_records:
                    self.stdout.write(f"Input Config: {input_records}")
            
            if 'outputDataConfig' in aws_response:
                output_config = aws_response.get('outputDataConfig', {}).get('s3OutputDataConfig', {})
                if output_config:
                    self.stdout.write(f"Output Config: {output_config}")
            
            # Show submission and completion times
            submit_time = aws_response.get('submitTime')
            if submit_time:
                self.stdout.write(f"AWS Submit Time: {submit_time}")
            
            end_time = aws_response.get('endTime')
            if end_time:
                self.stdout.write(f"AWS End Time: {end_time}")
            
            # Show failure reason if any
            failure_reason = aws_response.get('failureReason')
            if failure_reason:
                self.stdout.write(f"Failure Reason: {self.style.ERROR(failure_reason)}")
            
            # Error information
            if failure_reason == 'Failed':
                if 'failureMessage' in aws_response:
                    self.stdout.write(f"Failure Message: {aws_response['failureMessage']}")
                if 'message' in aws_response:
                    self.stdout.write(f"Message: {aws_response['message']}")
                # Show any other error-related fields
                for key in ['lastModifiedTime', 'clientRequestToken']:
                    if key in aws_response:
                        self.stdout.write(f"{key}: {aws_response[key]}")
    
    def update_all_active_jobs(self):
        """Update status for all active jobs."""
        active_jobs = BatchInferenceJob.objects.filter(
            status__in=['Submitted', 'InProgress']
        )
        
        if not active_jobs.exists():
            self.stdout.write("No active jobs to update.")
            return
        
        self.stdout.write(f"\n🔄 Updating {active_jobs.count()} active jobs...")
        
        updated_count = 0
        for job in active_jobs:
            aws_status = get_batch_job_status(job.job_arn)
            if aws_status:
                old_status = job.status
                self.update_job_from_aws_response(job, aws_status)
                if job.status != old_status:
                    self.stdout.write(f"  {job.job_name}: {old_status} → {job.status}")
                    updated_count += 1
                else:
                    self.stdout.write(f"  {job.job_name}: {job.status} (no change)")
            else:
                self.stdout.write(f"  {job.job_name}: Failed to get status")
        
        self.stdout.write(f"\n✅ Updated {updated_count} jobs")
    
    def watch_specific_job(self, job_id=None, job_arn=None, interval=60):
        """Continuously watch a specific job."""
        job = self.get_job(job_id, job_arn)
        if not job:
            return
        
        self.stdout.write(f"\n👀 Watching job: {job.job_name} (update every {interval}s)")
        self.stdout.write("Press Ctrl+C to stop watching\n")
        
        try:
            while True:
                self.monitor_specific_job(job_id, job_arn)
                
                # Reload job from database
                job.refresh_from_db()
                
                if job.is_complete:
                    self.stdout.write(f"\n🎉 Job completed with status: {job.status}")
                    break
                
                self.stdout.write(f"\n⏱️  Next update in {interval} seconds...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stdout.write("\n\n⏹️  Stopped watching")
    
    def watch_all_jobs(self, interval=60):
        """Continuously watch all active jobs."""
        self.stdout.write(f"\n👀 Watching all active jobs (update every {interval}s)")
        self.stdout.write("Press Ctrl+C to stop watching\n")
        
        try:
            while True:
                self.update_all_active_jobs()
                
                # Check if any jobs are still active
                active_count = BatchInferenceJob.objects.filter(
                    status__in=['Submitted', 'InProgress']
                ).count()
                
                if active_count == 0:
                    self.stdout.write("\n🎉 All jobs completed!")
                    break
                
                self.stdout.write(f"\n⏱️  Next update in {interval} seconds... ({active_count} jobs still active)")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stdout.write("\n\n⏹️  Stopped watching")
    
    def stop_job_command(self, job_identifier):
        """Stop a batch inference job."""
        job = self.get_job(job_identifier, job_identifier)
        if not job:
            return
        
        if job.status not in ['Submitted', 'InProgress']:
            self.stdout.write(f"Job {job.job_name} is not active (status: {job.status})")
            return
        
        self.stdout.write(f"🛑 Stopping job: {job.job_name}")
        
        if stop_batch_job(job.job_arn):
            job.update_status('Stopping')
            self.stdout.write(self.style.SUCCESS("Job stop request sent successfully"))
        else:
            self.stdout.write(self.style.ERROR("Failed to stop job"))
    
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
    
    def update_job_from_aws_response(self, job, aws_response):
        """Update job status based on AWS response."""
        aws_status = aws_response.get('status')
        if not aws_status:
            return
        
        # Map AWS status to our status
        status_mapping = {
            'Submitted': 'Submitted',
            'InProgress': 'InProgress',
            'Completed': 'Completed',
            'Failed': 'Failed',
            'Stopping': 'Stopping',
            'Stopped': 'Stopped'
        }
        
        new_status = status_mapping.get(aws_status, aws_status)
        failure_reason = aws_response.get('failureReason')
        
        if new_status != job.status:
            job.update_status(new_status, failure_reason)
            
            # Update additional timestamps from AWS if available
            if not job.started_at and aws_response.get('startTime'):
                job.started_at = aws_response['startTime']
                job.save(update_fields=['started_at'])
                
            if not job.completed_at and aws_response.get('endTime'):
                job.completed_at = aws_response['endTime']
                job.save(update_fields=['completed_at'])
    
    def show_standalone_job_status(self, job_id, job_arn):
        """Show status for a standalone job (not in database) by querying AWS directly."""
        try:
            # Determine what we have and construct what we need
            if job_arn:
                # We have the ARN, extract job ID if needed
                if not job_id:
                    job_id = extract_job_id_from_arn(job_arn)
                identifier = job_arn
            elif job_id:
                # We only have job ID, construct ARN
                import boto3
                sts_client = boto3.client('sts')
                account_id = sts_client.get_caller_identity()['Account']
                region = boto3.Session().region_name or 'us-east-1'
                job_arn = f"arn:aws:bedrock:{region}:{account_id}:model-invocation-job/{job_id}"
                identifier = job_arn
            else:
                raise CommandError("Either job_id or job_arn must be provided")
            
            # Get job status from AWS using the ARN as identifier
            job_status = get_batch_job_status(identifier)
            
            if not job_status:
                self.stdout.write(self.style.ERROR(f"❌ Could not retrieve job status from AWS"))
                return
            
            # Display job information
            self.stdout.write(f"\n=== Standalone Batch Inference Job Status ===")
            self.stdout.write(f"Job ID: {job_id}")
            self.stdout.write(f"Job ARN: {job_arn}")
            
            # Status with color coding
            status = job_status.get('status', 'Unknown')
            if status == 'Completed':
                status_display = self.style.SUCCESS(f"✅ {status}")
            elif status == 'InProgress':
                status_display = self.style.WARNING(f"🔄 {status}")
            elif status == 'Failed':
                status_display = self.style.ERROR(f"❌ {status}")
            elif status == 'Stopped':
                status_display = self.style.ERROR(f"⏹️  {status}")
            else:
                status_display = f"📋 {status}"
            
            self.stdout.write(f"Status: {status_display}")
            
            # Job details
            if 'jobName' in job_status:
                self.stdout.write(f"Job Name: {job_status['jobName']}")
            if 'modelId' in job_status:
                self.stdout.write(f"Model ID: {job_status['modelId']}")
            
            # Timestamps
            if 'submitTime' in job_status:
                submit_time = job_status['submitTime'].strftime('%Y-%m-%d %H:%M:%S UTC')
                self.stdout.write(f"Submitted: {submit_time}")
            
            if 'startTime' in job_status:
                start_time = job_status['startTime'].strftime('%Y-%m-%d %H:%M:%S UTC')
                self.stdout.write(f"Started: {start_time}")
            
            if 'endTime' in job_status:
                end_time = job_status['endTime'].strftime('%Y-%m-%d %H:%M:%S UTC')
                self.stdout.write(f"Ended: {end_time}")
            
            # Input/Output information
            if 'inputDataConfig' in job_status:
                input_config = job_status['inputDataConfig']
                if 's3InputDataConfig' in input_config:
                    input_uri = input_config['s3InputDataConfig'].get('s3Uri')
                    if input_uri:
                        self.stdout.write(f"Input S3 URI: {input_uri}")
            
            if 'outputDataConfig' in job_status:
                output_config = job_status['outputDataConfig']
                if 's3OutputDataConfig' in output_config:
                    output_uri = output_config['s3OutputDataConfig'].get('s3Uri')
                    if output_uri:
                        self.stdout.write(f"Output S3 URI: {output_uri}")
            
            # Error information
            if status == 'Failed':
                if 'failureMessage' in job_status:
                    self.stdout.write(f"Failure Message: {job_status['failureMessage']}")
                if 'message' in job_status:
                    self.stdout.write(f"Message: {job_status['message']}")
                # Show any other error-related fields
                for key in ['lastModifiedTime', 'clientRequestToken']:
                    if key in job_status:
                        self.stdout.write(f"{key}: {job_status[key]}")
            
            # Next steps
            self.stdout.write(f"\nNext steps:")
            if status == 'Completed':
                self.stdout.write(f"1. Process results: python manage.py process_batch_results --job-id {job_id}")
                self.stdout.write(f"2. Check output in S3 bucket")
            elif status == 'InProgress':
                self.stdout.write(f"1. Watch progress: python manage.py monitor_batch_jobs --job-id {job_id} --watch")
                self.stdout.write(f"2. Check AWS Console for detailed progress")
            elif status == 'Failed':
                self.stdout.write(f"1. Check error details in AWS Console")
                self.stdout.write(f"2. Review input data and job configuration")
            
            self.stdout.write(f"3. AWS Console: https://console.aws.amazon.com/bedrock/home?region=us-east-1#/batch-inference")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error retrieving job status: {str(e)}")) 