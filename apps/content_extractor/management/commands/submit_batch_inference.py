"""
Django management command to submit AWS Bedrock batch inference jobs.

Created by: Stellar Nexus
Date: 2025-01-22
Project: Triad Docker Base - Bedrock Batch Inference System
"""

import os
import json
import re
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.content_extractor.models import SiteConfiguration, BatchInferenceJob
from apps.content_extractor.aws_utils import (
    create_batch_inference_job,
    extract_job_id_from_arn,
    DEFAULT_BEDROCK_PROMPT_ARN
)


class Command(BaseCommand):
    help = 'Submit AWS Bedrock batch inference jobs for processing uploaded JSONL files'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            type=str,
            help='Site domain for tracking purposes (optional, extracted from S3 URI if not provided)'
        )
        
        parser.add_argument(
            '--input-s3-uri',
            type=str,
            required=True,
            help='S3 URI of the input JSONL file (e.g., s3://bucket/path/file.jsonl)'
        )
        
        parser.add_argument(
            '--output-s3-uri',
            type=str,
            help='S3 URI for output location (defaults to input location with /results/ prefix)'
        )
        
        parser.add_argument(
            '--model-id',
            type=str,
            default='anthropic.claude-3-haiku-20240307-v1:0',
            help='Bedrock model ID to use (default: Claude 3 Haiku)'
        )
        
        parser.add_argument(
            '--role-arn',
            type=str,
            help='IAM role ARN for batch inference job (will attempt to use default credentials if not provided)'
        )
        
        parser.add_argument(
            '--job-name',
            type=str,
            help='Custom job name (auto-generated if not provided, must match AWS pattern)'
        )
        
        parser.add_argument(
            '--prompt-arn',
            type=str,
            default=DEFAULT_BEDROCK_PROMPT_ARN,
            help=f'Bedrock prompt ARN (default: {DEFAULT_BEDROCK_PROMPT_ARN})'
        )
        
        parser.add_argument(
            '--timeout-hours',
            type=int,
            default=24,
            help='Job timeout in hours (default: 24)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually submitting the job'
        )
        
        parser.add_argument(
            '--record-count',
            type=int,
            help='Number of records in the input file (for tracking purposes)'
        )
        
        parser.add_argument(
            '--skip-site-config',
            action='store_true',
            help='Skip site configuration lookup and create job without database tracking'
        )
    
    def handle(self, *args, **options):
        domain = options.get('domain')
        input_s3_uri = options['input_s3_uri']
        model_id = options['model_id']
        role_arn = options.get('role_arn')
        prompt_arn = options['prompt_arn']
        timeout_hours = options['timeout_hours']
        dry_run = options['dry_run']
        record_count = options.get('record_count')
        skip_site_config = options.get('skip_site_config')
        
        # Validate input S3 URI
        if not input_s3_uri.startswith('s3://'):
            raise CommandError(f"Invalid S3 URI: {input_s3_uri}")
        
        # Extract domain from S3 URI if not provided
        if not domain:
            domain = self.extract_domain_from_s3_uri(input_s3_uri)
        
        # Try to get site configuration, but don't require it
        site_config = None
        if not skip_site_config and domain:
            try:
                site_config = SiteConfiguration.objects.get(site_domain=domain)
                self.stdout.write(f"Found site configuration: {site_config}")
            except SiteConfiguration.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f"No site configuration found for domain: {domain}\n"
                        f"Job will be created without database tracking. Use --skip-site-config to suppress this warning."
                    )
                )
        
        # Generate output S3 URI if not provided
        output_s3_uri = options.get('output_s3_uri')
        if not output_s3_uri:
            # Convert input path to output path
            # s3://bucket/batch-processing/domain/file.jsonl -> s3://bucket/batch-processing/domain/results/
            parts = input_s3_uri.replace('s3://', '').split('/')
            bucket = parts[0]
            path_parts = parts[1:-1]  # Remove filename
            output_s3_uri = f"s3://{bucket}/{'/'.join(path_parts)}/results/"
        
        # Generate job name if not provided
        job_name = options.get('job_name')
        if not job_name:
            job_name = self.generate_valid_job_name(domain or 'batch')
        else:
            # Validate provided job name
            if not self.validate_job_name(job_name):
                raise CommandError(
                    f"Invalid job name: {job_name}\n"
                    f"Job name must match pattern: [a-zA-Z0-9]{{1,63}}(-*[a-zA-Z0-9\\+\\-\\.])*\n"
                    f"Use --job-name with a valid name or let the system auto-generate one."
                )
        
        # Display job configuration
        self.stdout.write("\n=== Bedrock Batch Inference Job Configuration ===")
        self.stdout.write(f"Domain: {domain or 'Not specified'}")
        if site_config:
            self.stdout.write(f"Site Config: {site_config}")
        else:
            self.stdout.write("Site Config: None (standalone job)")
        self.stdout.write(f"Job Name: {job_name}")
        self.stdout.write(f"Model ID: {model_id}")
        self.stdout.write(f"Prompt ARN: {prompt_arn}")
        self.stdout.write(f"Input S3 URI: {input_s3_uri}")
        self.stdout.write(f"Output S3 URI: {output_s3_uri}")
        if role_arn:
            self.stdout.write(f"IAM Role ARN: {role_arn}")
        else:
            self.stdout.write("IAM Role ARN: Using default credentials")
        self.stdout.write(f"Timeout Hours: {timeout_hours}")
        if record_count:
            self.stdout.write(f"Record Count: {record_count}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n[DRY RUN] Job configuration validated. No job submitted."))
            return
        
        # Check if job already exists for this input (only if we have site config)
        if site_config:
            existing_job = BatchInferenceJob.objects.filter(
                site_config=site_config,
                input_s3_uri=input_s3_uri,
                status__in=['Submitted', 'InProgress']
            ).first()
            
            if existing_job:
                self.stdout.write(
                    self.style.WARNING(
                        f"Active job already exists for this input: {existing_job.job_name} ({existing_job.status})"
                    )
                )
                self.stdout.write(f"Job ARN: {existing_job.job_arn}")
                return
        
        # Submit the batch inference job
        self.stdout.write(f"\nSubmitting batch inference job...")
        
        # Handle role ARN - if not provided, let AWS use default credentials
        job_kwargs = {
            'job_name': job_name,
            'model_id': model_id,
            'input_s3_uri': input_s3_uri,
            'output_s3_uri': output_s3_uri,
            'timeout_hours': timeout_hours,
            'prompt_arn': prompt_arn
        }
        
        if role_arn:
            job_kwargs['role_arn'] = role_arn
        else:
            # For root user credentials, we might need to create a service role
            # For now, let's try without role_arn and see what AWS says
            self.stdout.write(
                self.style.WARNING(
                    "No IAM role specified. This may fail if your credentials don't have direct Bedrock permissions.\n"
                    "Consider creating a Bedrock service role or use --role-arn to specify one."
                )
            )
            # We'll need to modify the aws_utils function to handle optional role_arn
        
        job_response = create_batch_inference_job(**job_kwargs)
        
        if not job_response:
            raise CommandError("Failed to create batch inference job")
        
        job_arn = job_response.get('jobArn')
        if not job_arn:
            raise CommandError("No job ARN returned from Bedrock")
        
        # Extract job ID from ARN
        job_id = extract_job_id_from_arn(job_arn)
        
        # Create database record only if we have site config
        if site_config:
            batch_job = BatchInferenceJob.objects.create(
                site_config=site_config,
                job_name=job_name,
                job_arn=job_arn,
                job_id=job_id or job_arn.split('/')[-1],
                model_id=model_id,
                prompt_arn=prompt_arn,
                input_s3_uri=input_s3_uri,
                output_s3_uri=output_s3_uri,
                record_count=record_count,
                status='Submitted'
            )
            
            self.stdout.write(f"Database Record ID: {batch_job.id}")
        else:
            self.stdout.write("Database Record: None (standalone job)")
        
        self.stdout.write(
            self.style.SUCCESS(f"\n✅ Successfully submitted batch inference job!")
        )
        self.stdout.write(f"Job ARN: {job_arn}")
        self.stdout.write(f"Job ID: {job_id or job_arn.split('/')[-1]}")
        self.stdout.write(f"Status: Submitted")
        
        self.stdout.write(f"\nNext steps:")
        if job_id:
            self.stdout.write(f"1. Monitor job status: python manage.py monitor_batch_jobs --job-id {job_id}")
        self.stdout.write(f"2. Check AWS Console: https://console.aws.amazon.com/bedrock/home?region=us-east-1#/batch-inference")
        if site_config:
            self.stdout.write(f"3. List all jobs: python manage.py monitor_batch_jobs --list-all")
    
    def extract_domain_from_s3_uri(self, s3_uri):
        """Extract domain from S3 URI path."""
        try:
            # s3://bucket/batch-processing/domain/file.jsonl -> domain
            parts = s3_uri.replace('s3://', '').split('/')
            if len(parts) >= 3 and parts[1] == 'batch-processing':
                return parts[2]
            return None
        except:
            return None
    
    def generate_valid_job_name(self, domain):
        """Generate a valid AWS job name that matches the required pattern."""
        # AWS pattern: [a-zA-Z0-9]{1,63}(-*[a-zA-Z0-9\+\-\.])*
        # Simplified: alphanumeric with hyphens, max 63 chars
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        clean_domain = re.sub(r'[^a-zA-Z0-9]', '', domain.replace('.', ''))[:20]  # Remove non-alphanumeric, limit length
        
        job_name = f"batch-{clean_domain}-{timestamp}"
        
        # Ensure it's within 63 character limit
        if len(job_name) > 63:
            job_name = job_name[:63]
        
        return job_name
    
    def validate_job_name(self, job_name):
        """Validate job name against AWS pattern."""
        # AWS pattern: [a-zA-Z0-9]{1,63}(-*[a-zA-Z0-9\+\-\.])*
        pattern = r'^[a-zA-Z0-9]{1,63}(-*[a-zA-Z0-9\+\-\.])*$'
        return re.match(pattern, job_name) is not None and len(job_name) <= 63 