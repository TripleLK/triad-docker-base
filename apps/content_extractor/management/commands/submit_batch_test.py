"""
Django management command for submitting metadata preservation test to AWS Bedrock batch inference.

Created by: Quantum Ridge  
Date: 2025-06-17
Project: Triad Docker Base
"""

import time
import boto3
from pathlib import Path
from django.core.management.base import BaseCommand

from apps.content_extractor.aws_utils import (
    upload_file_to_s3, 
    create_batch_inference_job, 
    generate_s3_bucket_name, 
    create_bucket_if_not_exists
)


class Command(BaseCommand):
    help = 'Submit metadata preservation test to AWS Bedrock batch inference'

    def add_arguments(self, parser):
        parser.add_argument(
            '--jsonl-file',
            type=str,
            default='apps/content_extractor/test_data/test_metadata_preservation/test_batch_input.jsonl',
            help='Path to JSONL input file'
        )
        parser.add_argument(
            '--model-id',
            type=str,
            default='anthropic.claude-3-sonnet-20240229-v1:0',
            help='AWS Bedrock model ID to use'
        )
        parser.add_argument(
            '--use-all-records',
            action='store_true',
            help='Generate test with all 107 records to meet AWS minimum batch size requirement'
        )

    def handle(self, *args, **options):
        jsonl_file = options['jsonl_file']
        model_id = options['model_id']
        use_all_records = options['use_all_records']
        
        self.stdout.write(self.style.SUCCESS("🚀 SUBMITTING METADATA PRESERVATION TEST TO AWS BEDROCK"))
        self.stdout.write("=" * 60)
        
        # Handle the batch size issue
        if use_all_records:
            self.stdout.write(self.style.WARNING("⚠️  Previous batch failed due to minimum 100 record requirement"))
            self.stdout.write("🔄 Generating test with all 107 records...")
            from django.core.management import call_command
            call_command('test_metadata_preservation', record_count=107)
            self.stdout.write(self.style.SUCCESS("✅ Generated full batch test data"))
        
        # Configuration
        bucket_name = generate_s3_bucket_name('test')
        model_id = model_id
        
        # Get account ID for IAM role ARN
        try:
            sts_client = boto3.client('sts')
            account_id = sts_client.get_caller_identity()['Account']
            role_arn = f"arn:aws:iam::{account_id}:role/BedrockBatchInferenceRole"
            self.stdout.write(f"🔑 IAM Role: {role_arn}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Could not get account ID: {e}"))
            self.stdout.write("💡 Using default role ARN")
            role_arn = "arn:aws:iam::891377295311:role/BedrockBatchInferenceRole"
        
        self.stdout.write(f"📝 Input file: {jsonl_file}")
        self.stdout.write(f"🪣 Bucket: {bucket_name}")
        self.stdout.write(f"🤖 Model: {model_id}")
        self.stdout.write(f"🔑 Role: {role_arn}")
        
        # Step 1: Create bucket if needed
        self.stdout.write("\n📦 Step 1: Ensuring S3 bucket exists...")
        bucket_created = create_bucket_if_not_exists(bucket_name)
        if not bucket_created:
            self.stdout.write(self.style.ERROR("❌ Failed to create/access bucket"))
            return
        self.stdout.write(self.style.SUCCESS(f"✅ Bucket ready: {bucket_name}"))
        
        # Step 2: Upload input file
        self.stdout.write("\n📤 Step 2: Uploading input JSONL file...")
        input_s3_key = 'batch_inputs/metadata_test_input.jsonl'
        input_s3_uri = f's3://{bucket_name}/{input_s3_key}'
        upload_result = upload_file_to_s3(jsonl_file, bucket_name, input_s3_key)
        
        if not upload_result:
            self.stdout.write(self.style.ERROR("❌ Failed to upload input file"))
            return
        self.stdout.write(self.style.SUCCESS(f"✅ Input uploaded to: {input_s3_uri}"))
        
        # Step 3: Create batch inference job
        self.stdout.write("\n🤖 Step 3: Creating batch inference job...")
        job_name = f'metadata-preservation-test-{int(time.time())}'
        output_s3_uri = f's3://{bucket_name}/batch_outputs/{job_name}/'
        
        job_result = create_batch_inference_job(
            job_name=job_name,
            model_id=model_id,
            input_s3_uri=input_s3_uri,
            output_s3_uri=output_s3_uri,
            role_arn=role_arn,
            timeout_hours=24  # AWS minimum is 24 hours
        )
        
        if not job_result:
            self.stdout.write(self.style.ERROR("❌ Failed to create batch job"))
            return
        
        self.stdout.write(self.style.SUCCESS(f"\n🎯 BATCH JOB SUBMITTED SUCCESSFULLY!"))
        self.stdout.write(f"Job Name: {job_name}")
        self.stdout.write(f"Job ARN: {job_result['jobArn']}")
        self.stdout.write(f"Input: {input_s3_uri}")
        self.stdout.write(f"Output: {output_s3_uri}")
        
        self.stdout.write(f"\n📊 NEXT STEPS:")
        self.stdout.write(f"1. Monitor job status: python manage.py check_batch_status --job-id={job_result['jobArn'].split('/')[-1]}")
        self.stdout.write(f"2. When complete, check outputs for metadata preservation")
        self.stdout.write(f"3. Test import with preserved metadata")
        
        self.stdout.write(f"\n🔍 WHAT TO VERIFY IN OUTPUTS:")
        self.stdout.write(f"   ✓ _processing_mode field preserved")
        self.stdout.write(f"   ✓ _batch_info object intact")
        self.stdout.write(f"   ✓ _page_info details maintained")
        self.stdout.write(f"   ✓ target_model_names array preserved")
        self.stdout.write(f"   ✓ extracted_specification_groups preserved")
        self.stdout.write(f"   ✓ _specification_instructions preserved") 