"""
Django management command for checking status of metadata preservation batch inference job.

Created by: Quantum Ridge  
Date: 2025-06-17
Project: Triad Docker Base
"""

from django.core.management.base import BaseCommand

from apps.content_extractor.aws_utils import get_batch_job_status


class Command(BaseCommand):
    help = 'Check status of metadata preservation batch inference job'

    def add_arguments(self, parser):
        parser.add_argument(
            '--job-id',
            type=str,
            required=True,
            help='AWS Bedrock batch job ID to check'
        )

    def handle(self, *args, **options):
        job_id = options['job_id']
        
        self.stdout.write(f"🔍 Checking status of batch job: {job_id}")
        self.stdout.write("=" * 50)
        
        status = get_batch_job_status(job_id)
        
        if status:
            self.stdout.write(f"📊 Job Status: {status['status']}")
            self.stdout.write(f"🏷️  Job Name: {status['job_name']}")
            self.stdout.write(f"🤖 Model: {status['model_id']}")
            self.stdout.write(f"📥 Input: {status['input_s3_uri']}")
            self.stdout.write(f"📤 Output: {status['output_s3_uri']}")
            
            if status['creation_time']:
                self.stdout.write(f"🕐 Created: {status['creation_time']}")
            if status['end_time']:
                self.stdout.write(f"🏁 Ended: {status['end_time']}")
                
            if status['failure_messages']:
                self.stdout.write(self.style.ERROR(f"❌ Errors: {status['failure_messages']}"))
                
            self.stdout.write(f"\n🎯 NEXT STEPS:")
            if status['status'] == 'InProgress':
                self.stdout.write("   ⏳ Job is running - check back later")
            elif status['status'] == 'Completed':
                self.stdout.write(self.style.SUCCESS("   ✅ Job complete! Download outputs to verify metadata preservation"))
                self.stdout.write(f"   📥 Download from: {status['output_s3_uri']}")
            elif status['status'] == 'Failed':
                self.stdout.write(self.style.ERROR("   ❌ Job failed - check error messages above"))
            else:
                self.stdout.write(f"   ℹ️  Status: {status['status']}")
        else:
            self.stdout.write(self.style.ERROR("❌ Could not get job status")) 