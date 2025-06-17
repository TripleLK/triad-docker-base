"""
AWS Bedrock Batch Processing Utility for Lab Equipment Data.

This module provides utilities for:
1. Converting batch JSON to Bedrock Messages API format
2. Uploading to S3 with timestamped directories
3. Creating and monitoring batch inference jobs
4. Processing batch results and creating lab equipment pages

Created by: Thunder Ridge
Date: 2025-06-17
Project: Triad Docker Base
"""

import os
import sys
import json
import logging
import tempfile
import glob
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Django imports
import django
from django.core.management import call_command
from django.conf import settings

# Local imports
from .aws_utils import (
    create_bedrock_jsonl_from_batch_file,
    upload_files_batch,
    generate_s3_bucket_name,
    create_bucket_if_not_exists,
    create_batch_inference_job,
    generate_s3_directory_path,
    get_batch_job_status
)

logger = logging.getLogger(__name__)


class BedrockBatchProcessor:
    """
    Main class for handling AWS Bedrock batch processing workflows.
    """
    
    def __init__(self, bucket_name: Optional[str] = None, region: str = 'us-east-1'):
        self.region = region
        self.bucket_name = bucket_name or generate_s3_bucket_name("lab-equipment-processing")
        self.s3_client = boto3.client('s3', region_name=region)
        self.bedrock_client = boto3.client('bedrock', region_name=region)
        
    def process_batch_export_to_pages(
        self, 
        batch_file_path: str,
        model_id: str = "anthropic.claude-3-haiku-20240307-v1:0",
        role_arn: str = "arn:aws:iam::891377295311:role/BedrockBatchInferenceServiceRole",
        create_pages: bool = True,
        dry_run: bool = False,
        force_update: bool = False
    ) -> Dict[str, Any]:
        """
        Complete workflow: process batch JSON -> upload to S3 -> run batch inference -> create pages.
        
        Args:
            batch_file_path: Path to the batch JSON export file
            model_id: AWS Bedrock model ID to use
            role_arn: IAM role ARN for batch processing
            create_pages: Whether to automatically create lab equipment pages from results
            dry_run: Whether to perform a dry run (no actual page creation)
            force_update: Whether to force update existing pages
            
        Returns:
            Dict with processing results and statistics
        """
        logger.info(f"Starting complete batch processing workflow for: {batch_file_path}")
        
        results = {
            'success': False,
            'batch_file': batch_file_path,
            'upload_results': {},
            'job_info': {},
            'processing_stats': {},
            'page_creation_results': {},
            'errors': []
        }
        
        try:
            # Step 1: Upload and create batch job
            job_results = self.upload_and_start_batch_job(
                batch_file_path=batch_file_path,
                model_id=model_id,
                role_arn=role_arn
            )
            
            if not job_results['success']:
                results['errors'].append(f"Failed to start batch job: {job_results.get('error', 'Unknown error')}")
                return results
                
            results['upload_results'] = job_results['upload_results']
            results['job_info'] = job_results['job_info']
            
            # Step 2: Wait for completion (if requested)
            if create_pages:
                logger.info("Waiting for batch job completion...")
                job_id = job_results['job_info']['job_id']
                
                # Monitor job status
                completion_results = self.wait_for_job_completion(job_id)
                results['processing_stats'] = completion_results
                
                if completion_results['status'] == 'Completed' and completion_results['success_count'] > 0:
                    # Step 3: Download and process results
                    page_results = self.process_batch_results_to_pages(
                        job_id=job_id,
                        output_s3_url=job_results['job_info']['output_s3_uri'],
                        dry_run=dry_run,
                        force_update=force_update
                    )
                    results['page_creation_results'] = page_results
                    
                    if page_results['success']:
                        results['success'] = True
                else:
                    results['errors'].append(f"Batch job failed or had no successful records")
                    
        except Exception as e:
            logger.exception("Error in complete batch processing workflow")
            results['errors'].append(f"Workflow error: {str(e)}")
            
        return results
    
    def upload_and_start_batch_job(
        self,
        batch_file_path: str,
        model_id: str = "anthropic.claude-3-haiku-20240307-v1:0",
        role_arn: str = "arn:aws:iam::891377295311:role/BedrockBatchInferenceServiceRole",
        timeout_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Upload batch JSON to S3 and start Bedrock batch inference job.
        
        Args:
            batch_file_path: Path to the batch JSON export file
            model_id: AWS Bedrock model ID
            role_arn: IAM role ARN for batch processing
            timeout_hours: Job timeout in hours
            
        Returns:
            Dict with upload results and job information
        """
        logger.info(f"Starting batch upload and job creation for: {batch_file_path}")
        
        results = {
            'success': False,
            'upload_results': {},
            'job_info': {},
            'error': None
        }
        
        try:
            # Validate input file
            if not os.path.exists(batch_file_path):
                raise FileNotFoundError(f"Batch file not found: {batch_file_path}")
            
            # Create temporary directory for processing
            with tempfile.TemporaryDirectory() as temp_dir:
                # Convert to Messages API format
                jsonl_path = create_bedrock_jsonl_from_batch_file(
                    batch_file_path, 
                    os.path.join(temp_dir, "batch_bedrock.jsonl")
                )
                
                if not jsonl_path:
                    raise ValueError("Failed to convert batch file to Messages API format")
                
                # Count records
                with open(jsonl_path, 'r') as f:
                    record_count = len(f.readlines())
                
                logger.info(f"Created Messages API JSONL with {record_count} records")
                
                # Set up S3 configuration
                dir_path = generate_s3_directory_path()
                
                # Create bucket if needed
                if not create_bucket_if_not_exists(self.bucket_name, self.region):
                    raise RuntimeError("Failed to create or access S3 bucket")
                
                # Upload to S3
                upload_results = upload_files_batch([jsonl_path], self.bucket_name, "input")
                
                success_uploads = {path: result['s3_url'] for path, result in upload_results.items() if result['success']}
                failed_uploads = {path: result['error'] for path, result in upload_results.items() if not result['success']}
                
                if failed_uploads:
                    raise RuntimeError(f"Failed uploads: {failed_uploads}")
                
                if not success_uploads:
                    raise RuntimeError("No files uploaded successfully")
                
                # Get S3 URLs
                input_s3_url = list(success_uploads.values())[0]
                output_s3_url = input_s3_url.replace('/input/', '/output/').rsplit('/', 1)[0] + '/'
                
                results['upload_results'] = {
                    'input_s3_url': input_s3_url,
                    'output_s3_url': output_s3_url,
                    'record_count': record_count,
                    'bucket_name': self.bucket_name,
                    'directory_path': dir_path
                }
                
                # Create batch inference job
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                job_name = f"lab-equipment-{timestamp}"
                
                job_config = {
                    "job_name": job_name,
                    "model_id": model_id,
                    "input_s3_uri": input_s3_url,
                    "output_s3_uri": output_s3_url,
                    "role_arn": role_arn,
                    "timeout_hours": timeout_hours
                }
                
                response = create_batch_inference_job(**job_config)
                
                if response:
                    job_id = response['jobArn'].split('/')[-1]
                    
                    results['job_info'] = {
                        'job_arn': response['jobArn'],
                        'job_id': job_id,
                        'job_name': job_name,
                        'model_id': model_id,
                        'input_s3_uri': input_s3_url,
                        'output_s3_uri': output_s3_url,
                        'record_count': record_count
                    }
                    
                    results['success'] = True
                    logger.info(f"Successfully created batch job: {job_id}")
                    
                else:
                    raise RuntimeError("Failed to create batch inference job")
                    
        except Exception as e:
            logger.exception("Error in upload and job creation")
            results['error'] = str(e)
            
        return results
    
    def wait_for_job_completion(
        self, 
        job_id: str, 
        check_interval: int = 30, 
        max_wait_time: int = 3600
    ) -> Dict[str, Any]:
        """
        Wait for batch job completion with periodic status checks.
        
        Args:
            job_id: Batch inference job ID
            check_interval: Seconds between status checks
            max_wait_time: Maximum wait time in seconds
            
        Returns:
            Dict with final job status and statistics
        """
        import time
        
        logger.info(f"Monitoring job {job_id} for completion...")
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                status = get_batch_job_status(job_id)
                
                logger.info(f"Job {job_id} status: {status.get('status', 'Unknown')}")
                
                if status['status'] in ['Completed', 'Failed', 'Stopping', 'Stopped']:
                    # Job finished
                    return {
                        'status': status['status'],
                        'total_records': status.get('total_records', 0),
                        'success_count': status.get('success_count', 0),
                        'error_count': status.get('error_count', 0),
                        'wait_time': time.time() - start_time
                    }
                
                # Still running, wait before next check
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error checking job status: {e}")
                time.sleep(check_interval)
        
        # Timeout
        return {
            'status': 'Timeout',
            'wait_time': max_wait_time,
            'error': f'Job monitoring timed out after {max_wait_time} seconds'
        }
    
    def process_batch_results_to_pages(
        self,
        job_id: str,
        output_s3_url: str,
        dry_run: bool = False,
        force_update: bool = False
    ) -> Dict[str, Any]:
        """
        Download batch results and create lab equipment pages.
        
        Args:
            job_id: Batch inference job ID
            output_s3_url: S3 URL for output files
            dry_run: Whether to perform a dry run
            force_update: Whether to force update existing pages
            
        Returns:
            Dict with page creation results
        """
        logger.info(f"Processing batch results for job {job_id}")
        
        results = {
            'success': False,
            'output_directory': None,
            'processed_files': [],
            'page_stats': {},
            'errors': []
        }
        
        try:
            # Create temporary directory for downloads
            with tempfile.TemporaryDirectory() as temp_dir:
                output_dir = Path(temp_dir) / "batch_output"
                output_dir.mkdir()
                
                # Download batch results
                download_success = self.download_batch_results(job_id, output_s3_url, str(output_dir))
                
                if not download_success:
                    raise RuntimeError("Failed to download batch results")
                
                # Convert batch output to individual JSON files
                json_files = self.convert_batch_output_to_json_files(output_dir)
                
                if not json_files:
                    raise RuntimeError("No valid JSON files created from batch output")
                
                results['processed_files'] = json_files
                
                # Create lab equipment pages using existing command
                if not dry_run:
                    page_results = self.create_pages_from_json_files(
                        json_files, 
                        force_update=force_update
                    )
                    results['page_stats'] = page_results
                else:
                    results['page_stats'] = {'dry_run': True, 'files_processed': len(json_files)}
                
                results['success'] = True
                results['output_directory'] = str(output_dir)
                
        except Exception as e:
            logger.exception("Error processing batch results to pages")
            results['errors'].append(str(e))
            
        return results
    
    def download_batch_results(self, job_id: str, output_s3_url: str, local_dir: str) -> bool:
        """Download batch inference results from S3."""
        try:
            # Parse S3 URL
            parsed_url = urlparse(output_s3_url)
            bucket = parsed_url.netloc
            prefix = parsed_url.path.lstrip('/')
            
            # Add job ID to prefix
            job_prefix = f"{prefix}{job_id}/"
            
            # List and download all files
            response = self.s3_client.list_objects_v2(Bucket=bucket, Prefix=job_prefix)
            
            if 'Contents' not in response:
                logger.warning(f"No output files found for job {job_id}")
                return False
            
            for obj in response['Contents']:
                key = obj['Key']
                filename = os.path.basename(key)
                local_path = os.path.join(local_dir, filename)
                
                logger.info(f"Downloading {key} to {local_path}")
                self.s3_client.download_file(bucket, key, local_path)
            
            return True
            
        except Exception as e:
            logger.exception("Error downloading batch results")
            return False
    
    def convert_batch_output_to_json_files(self, output_dir: Path) -> List[str]:
        """
        Convert batch output JSONL to individual JSON files for import command.
        """
        json_files = []
        
        try:
            # Find the batch output file
            output_files = list(output_dir.glob("*.jsonl.out"))
            
            if not output_files:
                logger.error("No batch output files found")
                return []
            
            output_file = output_files[0]
            logger.info(f"Processing batch output file: {output_file}")
            
            # Create individual JSON files directory
            json_dir = output_dir / "json_files"
            json_dir.mkdir(exist_ok=True)
            
            # Process each line in the output file
            with open(output_file, 'r') as f:
                for i, line in enumerate(f):
                    try:
                        record = json.loads(line.strip())
                        
                        # Extract the AI response
                        if 'modelOutput' in record and 'content' in record['modelOutput']:
                            content = record['modelOutput']['content']
                            if content and len(content) > 0 and 'text' in content[0]:
                                ai_response = json.loads(content[0]['text'])
                                
                                # Create filename based on record ID or index
                                record_id = record.get('recordId', f'record_{i}')
                                filename = f"{record_id}.json"
                                
                                # Save as individual JSON file
                                json_path = json_dir / filename
                                with open(json_path, 'w') as json_file:
                                    json.dump(ai_response, json_file, indent=2)
                                
                                json_files.append(str(json_path))
                                
                    except Exception as e:
                        logger.error(f"Error processing record {i}: {e}")
                        continue
            
            logger.info(f"Created {len(json_files)} JSON files from batch output")
            
        except Exception as e:
            logger.exception("Error converting batch output to JSON files")
            
        return json_files
    
    def create_pages_from_json_files(
        self, 
        json_files: List[str], 
        force_update: bool = False
    ) -> Dict[str, Any]:
        """
        Create lab equipment pages from JSON files using existing Django management command.
        """
        try:
            # Group files by directory since the import command expects directory input
            file_dirs = {}
            for json_file in json_files:
                file_dir = os.path.dirname(json_file)
                if file_dir not in file_dirs:
                    file_dirs[file_dir] = []
                file_dirs[file_dir].append(json_file)
            
            total_created = 0
            total_updated = 0
            total_errors = 0
            
            # Process each directory
            for dir_path, files in file_dirs.items():
                logger.info(f"Processing {len(files)} files in {dir_path}")
                
                try:
                    # Use the existing import_ai_json_to_equipment command
                    from io import StringIO
                    from django.core.management import call_command
                    
                    # Capture command output
                    output = StringIO()
                    
                    # Build command arguments
                    cmd_args = [dir_path]
                    cmd_options = {
                        'verbosity': 1,
                        'stdout': output
                    }
                    
                    if force_update:
                        cmd_options['force'] = True
                    
                    # Execute the command
                    call_command('import_ai_json_to_equipment', *cmd_args, **cmd_options)
                    
                    # Parse output for statistics (basic parsing)
                    output_text = output.getvalue()
                    
                    # Count successes and errors in output
                    created_count = output_text.count('created')
                    updated_count = output_text.count('updated') 
                    error_count = output_text.count('Error')
                    
                    total_created += created_count
                    total_updated += updated_count
                    total_errors += error_count
                    
                except Exception as e:
                    logger.exception(f"Error processing directory {dir_path}")
                    total_errors += len(files)
            
            return {
                'success': total_errors == 0,
                'total_created': total_created,
                'total_updated': total_updated,
                'total_errors': total_errors,
                'files_processed': len(json_files)
            }
            
        except Exception as e:
            logger.exception("Error creating pages from JSON files")
            return {
                'success': False,
                'error': str(e),
                'files_processed': 0
            }


def find_latest_batch_export() -> Optional[str]:
    """Find the most recent batch export file in temp_batch_export directory."""
    try:
        batch_files = glob.glob("./temp_batch_export/ai_json_batch_*.json")
        
        if not batch_files:
            return None
        
        # Return the most recent file
        latest_file = max(batch_files, key=os.path.getctime)
        return latest_file
        
    except Exception as e:
        logger.error(f"Error finding latest batch export: {e}")
        return None


def run_complete_batch_workflow(
    batch_file_path: Optional[str] = None,
    model_id: str = "anthropic.claude-3-haiku-20240307-v1:0",
    create_pages: bool = True,
    dry_run: bool = False,
    force_update: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to run the complete batch processing workflow.
    
    Args:
        batch_file_path: Path to batch file (if None, finds latest export)
        model_id: AWS Bedrock model to use
        create_pages: Whether to create lab equipment pages from results
        dry_run: Whether to perform a dry run
        force_update: Whether to force update existing pages
        
    Returns:
        Dict with complete workflow results
    """
    # Find batch file if not provided
    if not batch_file_path:
        batch_file_path = find_latest_batch_export()
        if not batch_file_path:
            return {
                'success': False,
                'error': 'No batch export file found in ./temp_batch_export/'
            }
    
    # Initialize processor
    processor = BedrockBatchProcessor()
    
    # Run complete workflow
    return processor.process_batch_export_to_pages(
        batch_file_path=batch_file_path,
        model_id=model_id,
        create_pages=create_pages,
        dry_run=dry_run,
        force_update=force_update
    ) 