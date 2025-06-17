"""
AWS utilities for content extractor app.

Created by: Thunder Ridge
Date: 2025-01-22
Project: Triad Docker Base
"""

import os
import boto3
import json
import logging
from typing import List, Dict, Optional, Tuple
from botocore.exceptions import ClientError, NoCredentialsError
from django.conf import settings
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# Default Bedrock prompt ARN - can be overridden
DEFAULT_BEDROCK_PROMPT_ARN = "arn:aws:bedrock:us-east-1:891377295311:prompt/H52151JSYK"


def get_s3_client():
    """
    Get an AWS S3 client using boto3's default credential chain.
    This will check AWS CLI config, environment variables, IAM roles, etc.
    """
    try:
        # Use boto3's default credential chain - this will automatically
        # check AWS CLI config files, environment variables, IAM roles, etc.
        client = boto3.client('s3', region_name='us-east-1')
        
        # Test the credentials by making a simple call
        client.list_buckets()
        
        logger.info("AWS S3 client created successfully using default credential chain")
        return client
        
    except Exception as e:
        logger.error(f"Error creating S3 client: {str(e)}")
        raise


def get_bedrock_client():
    """
    Get an AWS Bedrock client using boto3's default credential chain.
    This will check AWS CLI config, environment variables, IAM roles, etc.
    """
    try:
        # Use boto3's default credential chain
        client = boto3.client('bedrock', region_name='us-east-1')
        
        logger.info("AWS Bedrock client created successfully using default credential chain")
        return client
        
    except Exception as e:
        logger.error(f"Error creating Bedrock client: {str(e)}")
        raise


def create_bucket_if_not_exists(bucket_name: str, region: str = 'us-east-1') -> bool:
    """
    Create S3 bucket if it doesn't exist.
    
    Args:
        bucket_name: Name of the S3 bucket
        region: AWS region for the bucket
        
    Returns:
        bool: True if bucket exists or was created successfully
    """
    try:
        s3_client = get_s3_client()
        
        # Check if bucket exists
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"Bucket {bucket_name} already exists")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket doesn't exist, create it
                logger.info(f"Creating bucket {bucket_name} in region {region}")
                
                if region == 'us-east-1':
                    # us-east-1 doesn't need LocationConstraint
                    s3_client.create_bucket(Bucket=bucket_name)
                else:
                    s3_client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': region}
                    )
                
                logger.info(f"Successfully created bucket {bucket_name}")
                return True
            else:
                logger.error(f"Error checking bucket {bucket_name}: {str(e)}")
                return False
                
    except Exception as e:
        logger.error(f"Error creating bucket {bucket_name}: {str(e)}")
        return False


def generate_s3_directory_path() -> str:
    """
    Generate a timestamped directory path for S3 uploads.
    
    Returns:
        str: Directory path in format YYYY-MM-DD/HHMMSS/
    """
    now = datetime.now()
    date_dir = now.strftime("%Y-%m-%d")
    time_dir = now.strftime("%H%M%S")
    return f"{date_dir}/{time_dir}/"


def upload_file_to_s3(file_path: str, bucket_name: str, s3_key: str) -> Optional[str]:
    """
    Upload a file to S3.
    
    Args:
        file_path: Local path to the file
        bucket_name: S3 bucket name
        s3_key: S3 object key (path in bucket)
        
    Returns:
        str: S3 URL if successful, None if failed
    """
    try:
        s3_client = get_s3_client()
        
        # Upload the file
        s3_client.upload_file(file_path, bucket_name, s3_key)
        
        # Generate S3 URL
        s3_url = f"s3://{bucket_name}/{s3_key}"
        logger.info(f"Successfully uploaded {file_path} to {s3_url}")
        
        return s3_url
        
    except Exception as e:
        logger.error(f"Error uploading {file_path} to S3: {str(e)}")
        return None


def upload_files_batch(file_paths: List[str], bucket_name: str, s3_prefix: str = "") -> Dict[str, Dict]:
    """
    Upload multiple files to S3 in batch with timestamped directory structure.
    
    Args:
        file_paths: List of local file paths
        bucket_name: S3 bucket name
        s3_prefix: Base prefix for S3 keys (optional)
        
    Returns:
        dict: Mapping of local file path to result dict with 'success', 's3_url', and 'error' keys
    """
    results = {}
    
    # Generate timestamped directory for this batch
    timestamp_dir = generate_s3_directory_path()
    
    for file_path in file_paths:
        try:
            # Generate S3 key with timestamped directory
            file_name = os.path.basename(file_path)
            if s3_prefix:
                s3_key = f"{s3_prefix.rstrip('/')}/{timestamp_dir}{file_name}"
            else:
                s3_key = f"{timestamp_dir}{file_name}"
            
            # Upload file
            s3_url = upload_file_to_s3(file_path, bucket_name, s3_key)
            
            if s3_url:
                results[file_path] = {
                    'success': True,
                    's3_url': s3_url,
                    'error': None
                }
            else:
                results[file_path] = {
                    'success': False,
                    's3_url': None,
                    'error': 'Upload failed'
                }
            
        except Exception as e:
            logger.error(f"Error uploading {file_path}: {str(e)}")
            results[file_path] = {
                'success': False,
                's3_url': None,
                'error': str(e)
            }
    
    return results


def create_bedrock_messages_jsonl(json_data_list: List[Dict], output_path: str, prompt_text: str = None) -> str:
    """
    Create JSONL file in Bedrock Messages API format directly from JSON data.
    
    Args:
        json_data_list: List of JSON data objects to process
        output_path: Path for output JSONL file
        prompt_text: The actual prompt text to use (optional, uses default if not provided)
        
    Returns:
        str: Path to generated JSONL file
    """
    try:
        # Default prompt text if not provided
        if not prompt_text:
            # Read the prompt from the markdown file
            prompt_file_path = ".project_management/ai_prompts/ai_json_to_lab_equipment_api.md"
            try:
                with open(prompt_file_path, 'r', encoding='utf-8') as prompt_file:
                    prompt_template = prompt_file.read()
            except Exception as e:
                logger.warning(f"Could not read prompt file {prompt_file_path}: {str(e)}")
                prompt_template = "Transform this JSON data into the required format: {{INPUT_JSON_DATA}}"
        else:
            prompt_template = prompt_text
        
        # Create output directory if needed
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write JSONL file with Messages API format
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, json_data in enumerate(json_data_list):
                # Generate record ID
                record_id = f"record_{i+1}_{datetime.now().strftime('%H%M%S')}"
                
                # Replace template variable with actual data
                actual_prompt = prompt_template.replace('{{INPUT_JSON_DATA}}', json.dumps(json_data, ensure_ascii=False))
                
                # Create Bedrock Messages API format record
                bedrock_record = {
                    "recordId": record_id,
                    "modelInput": {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 64000,
                        "temperature": 0.2,
                        "top_p": 0.9,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": actual_prompt
                                    }
                                ]
                            }
                        ]
                    }
                }
                
                f.write(json.dumps(bedrock_record, ensure_ascii=False) + '\n')
        
        logger.info(f"Created Bedrock Messages API JSONL with {len(json_data_list)} records: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error creating Bedrock Messages API JSONL: {str(e)}")
        raise


def create_bedrock_jsonl_from_batch_file(batch_json_path: str, output_path: str = None, prompt_text: str = None) -> Optional[str]:
    """
    Create Bedrock Messages API JSONL file from batch JSON file.
    
    Args:
        batch_json_path: Path to batch JSON file containing multiple records
        output_path: Path for output JSONL file (optional, auto-generated if not provided)
        prompt_text: The actual prompt text to use (optional, uses default if not provided)
        
    Returns:
        str: Path to generated JSONL file, None if failed
    """
    try:
        with open(batch_json_path, 'r', encoding='utf-8') as f:
            batch_data = json.load(f)
        
        # Handle both formats: direct list or object with 'records' key
        if isinstance(batch_data, list):
            records = batch_data
        elif isinstance(batch_data, dict) and 'records' in batch_data:
            records = batch_data['records']
        else:
            logger.error(f"Batch JSON file {batch_json_path} should contain a list of records or an object with 'records' key")
            return None
        
        if not records:
            logger.error(f"No records found in batch JSON file {batch_json_path}")
            return None
        
        # Generate output path if not provided
        if not output_path:
            basename = os.path.splitext(os.path.basename(batch_json_path))[0]
            output_dir = os.path.dirname(batch_json_path)
            output_path = os.path.join(output_dir, f"{basename}_bedrock.jsonl")
            
        # Extract JSON data from records
        json_data_list = []
        for record in records:
            # Extract the actual JSON data from the record structure
            if isinstance(record, dict) and 'json_data' in record:
                # This is the structure from export_batch_file
                json_data_list.append(record['json_data'])
            else:
                # Direct record data
                json_data_list.append(record)
        
        # Create JSONL file
        result_path = create_bedrock_messages_jsonl(json_data_list, output_path, prompt_text)
        return result_path
        
    except Exception as e:
        logger.error(f"Error creating Bedrock JSONL from batch file: {str(e)}")
        return None


def generate_s3_bucket_name(domain: str) -> str:
    """
    Generate a unique S3 bucket name for batch processing.
    Uses a generic bucket name that can handle multiple sites.
    
    Args:
        domain: Domain being processed
        
    Returns:
        str: Generated bucket name
    """
    # Use a generic bucket name for all batch processing
    # This allows the same bucket to be used for multiple sites
    bucket_name = "triad-bedrock-batch-processing"
    
    # Ensure bucket name meets S3 requirements
    # - 3-63 characters
    # - lowercase letters, numbers, hyphens
    # - start and end with letter or number
    return bucket_name


def delete_local_files(file_paths: List[str], success_uploads: Dict[str, str]) -> Tuple[int, int]:
    """
    Delete local files that were successfully uploaded to S3.
    
    Args:
        file_paths: List of local file paths
        success_uploads: Dict mapping file paths to S3 URLs (successful uploads only)
        
    Returns:
        Tuple[int, int]: (deleted_count, failed_count)
    """
    deleted_count = 0
    failed_count = 0
    
    for file_path in file_paths:
        if file_path in success_uploads and success_uploads[file_path]:
            try:
                os.remove(file_path)
                logger.info(f"Deleted local file: {file_path}")
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete {file_path}: {str(e)}")
                failed_count += 1
        else:
            logger.warning(f"Skipping deletion of {file_path} (upload failed or not attempted)")
            failed_count += 1
    
    return deleted_count, failed_count


def create_batch_inference_job(
    job_name: str,
    model_id: str,
    input_s3_uri: str,
    output_s3_uri: str,
    role_arn: str = None,
    timeout_hours: int = 24,
    prompt_arn: str = None
) -> Optional[Dict]:
    """
    Create a Bedrock batch inference job.
    
    Args:
        job_name: Name for the batch inference job
        model_id: Bedrock model ID to use
        input_s3_uri: S3 URI of input JSONL file
        output_s3_uri: S3 URI for output location
        role_arn: IAM role ARN with permissions for the job (optional)
        timeout_hours: Job timeout in hours (default 24)
        prompt_arn: Prompt ARN to use (for reference only, model_id is still required)
    
    Returns:
        Dict with job details if successful, None if failed
    """
    try:
        client = get_bedrock_client()
        
        # Use the provided model_id directly
        # When using prompts, the input data contains promptArn and promptVariables
        # but the API still requires the actual model ID, not the prompt ARN
        effective_model_id = model_id
        
        # Build the job configuration
        job_config = {
            'jobName': job_name,
            'modelId': effective_model_id,
            'inputDataConfig': {
                's3InputDataConfig': {
                    's3Uri': input_s3_uri
                }
            },
            'outputDataConfig': {
                's3OutputDataConfig': {
                    's3Uri': output_s3_uri
                }
            },
            'timeoutDurationInHours': timeout_hours
        }
        
        # Add role ARN if provided
        if role_arn:
            job_config['roleArn'] = role_arn
        
        print(f"Creating batch inference job with config:")
        print(f"  Job Name: {job_name}")
        print(f"  Model ID: {effective_model_id}")
        print(f"  Using Prompt: {'Yes' if prompt_arn else 'No'}")
        print(f"  Input: {input_s3_uri}")
        print(f"  Output: {output_s3_uri}")
        
        response = client.create_model_invocation_job(**job_config)
        
        print(f"✅ Batch inference job created successfully!")
        print(f"Job ARN: {response['jobArn']}")
        print(f"Job ID: {extract_job_id_from_arn(response['jobArn'])}")
        
        return response
        
    except Exception as e:
        print(f"❌ Error creating batch inference job: {str(e)}")
        return None


def get_batch_job_status(job_identifier: str) -> Optional[Dict]:
    """
    Get the status of a Bedrock batch inference job.
    
    Args:
        job_identifier: Either job ID or full ARN of the batch inference job
        
    Returns:
        dict: Job status information with standardized keys, or None if failed
    """
    try:
        bedrock_client = get_bedrock_client()
        
        # If it's just a job ID, construct the full ARN
        if not job_identifier.startswith('arn:aws:bedrock:'):
            # Get current region and account from client
            session = boto3.Session()
            region = session.region_name or 'us-east-1'
            sts_client = boto3.client('sts')
            account_id = sts_client.get_caller_identity()['Account']
            
            # Construct full ARN
            job_identifier = f"arn:aws:bedrock:{region}:{account_id}:model-invocation-job/{job_identifier}"
        
        response = bedrock_client.get_model_invocation_job(
            jobIdentifier=job_identifier
        )
        
        # Standardize the response format for the batch processing utility
        job_details = {
            'status': response.get('status', 'Unknown'),
            'job_arn': response.get('jobArn', job_identifier),
            'job_name': response.get('jobName', ''),
            'model_id': response.get('modelId', ''),
            'input_s3_uri': response.get('inputDataConfig', {}).get('s3InputDataConfig', {}).get('s3Uri', ''),
            'output_s3_uri': response.get('outputDataConfig', {}).get('s3OutputDataConfig', {}).get('s3Uri', ''),
            'creation_time': response.get('creationTime'),
            'end_time': response.get('endTime'),
            'failure_messages': response.get('failureMessages', [])
        }
        
        # Add statistics if available
        if 'outputDataConfig' in response:
            output_stats = response['outputDataConfig']
            job_details.update({
                'total_records': output_stats.get('s3OutputDataConfig', {}).get('s3Uri', '').count('\n') if 'total' in str(output_stats) else 0,
                'success_count': 0,  # Will be filled from manifest if available
                'error_count': 0     # Will be filled from manifest if available
            })
        
        # Try to get detailed statistics from job statistics if available
        if 'jobStatistics' in response:
            stats = response['jobStatistics']
            job_details.update({
                'total_records': stats.get('inputTokenCount', 0),
                'success_count': stats.get('outputTokenCount', 0) if stats.get('outputTokenCount', 0) > 0 else job_details.get('success_count', 0),
                'error_count': job_details.get('total_records', 0) - job_details.get('success_count', 0)
            })
        
        return job_details
        
    except Exception as e:
        logger.error(f"Error getting batch job status: {str(e)}")
        return None


def list_batch_jobs(status_filter: Optional[str] = None, max_results: int = 50) -> Optional[List[Dict]]:
    """
    List Bedrock batch inference jobs.
    
    Args:
        status_filter: Filter by job status (optional)
        max_results: Maximum number of results to return
        
    Returns:
        list: List of job summaries, or None if failed
    """
    try:
        bedrock_client = get_bedrock_client()
        
        kwargs = {
            'maxResults': max_results,
            'sortOrder': 'Descending'
        }
        
        if status_filter:
            kwargs['statusEquals'] = status_filter
        
        response = bedrock_client.list_model_invocation_jobs(**kwargs)
        
        return response.get('invocationJobSummaries', [])
        
    except Exception as e:
        logger.error(f"Error listing batch jobs: {str(e)}")
        return None


def stop_batch_job(job_arn: str) -> bool:
    """
    Stop a running Bedrock batch inference job.
    
    Args:
        job_arn: ARN of the batch inference job
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        bedrock_client = get_bedrock_client()
        
        bedrock_client.stop_model_invocation_job(
            jobIdentifier=job_arn
        )
        
        logger.info(f"Successfully stopped batch job: {job_arn}")
        return True
        
    except Exception as e:
        logger.error(f"Error stopping batch job: {str(e)}")
        return False


def download_s3_file(s3_uri: str, local_path: str) -> bool:
    """
    Download a file from S3.
    
    Args:
        s3_uri: S3 URI (s3://bucket/key)
        local_path: Local file path to save to
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        s3_client = get_s3_client()
        
        # Parse S3 URI
        if not s3_uri.startswith('s3://'):
            logger.error(f"Invalid S3 URI: {s3_uri}")
            return False
            
        parts = s3_uri[5:].split('/', 1)
        bucket_name = parts[0]
        s3_key = parts[1] if len(parts) > 1 else ''
        
        # Create directory if needed
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # Download file
        s3_client.download_file(bucket_name, s3_key, local_path)
        
        logger.info(f"Successfully downloaded {s3_uri} to {local_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error downloading S3 file: {str(e)}")
        return False


def extract_job_id_from_arn(job_arn: str) -> Optional[str]:
    """
    Extract job ID from batch inference job ARN.
    
    Args:
        job_arn: Full ARN of the batch inference job
        
    Returns:
        str: Job ID, or None if extraction failed
    """
    try:
        # ARN format: arn:aws:bedrock:region:account:model-invocation-job/job-id
        if '/model-invocation-job/' in job_arn:
            return job_arn.split('/model-invocation-job/')[-1]
        else:
            # Fallback: take the last part after the last /
            return job_arn.split('/')[-1]
    except Exception as e:
        logger.error(f"Error extracting job ID from ARN: {str(e)}")
        return None 