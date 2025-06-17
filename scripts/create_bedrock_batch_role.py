#!/usr/bin/env python3
"""
Create IAM service role for AWS Bedrock batch inference jobs.

This script creates the necessary IAM role that Bedrock can assume to:
- Read from your S3 input bucket
- Write to your S3 output bucket  
- Use Bedrock models for inference

Created by: Stellar Nexus
Date: 2025-01-22
Project: Triad Docker Base - Bedrock Batch Inference System
"""

import json
import boto3
import sys
from botocore.exceptions import ClientError


def create_bedrock_batch_role(role_name="BedrockBatchInferenceRole", bucket_name="triad-bedrock-batch-processing"):
    """Create IAM role for Bedrock batch inference jobs."""
    
    iam_client = boto3.client('iam')
    
    # Trust policy - allows Bedrock to assume this role
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    # Permissions policy - what the role can do
    permissions_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:PutObject",
                    "s3:PutObjectAcl"
                ],
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel"
                ],
                "Resource": "*"
            }
        ]
    }
    
    try:
        # Get current account ID
        sts_client = boto3.client('sts')
        account_id = sts_client.get_caller_identity()['Account']
        
        print(f"Creating IAM role for Bedrock batch inference...")
        print(f"Account ID: {account_id}")
        print(f"Role Name: {role_name}")
        print(f"S3 Bucket: {bucket_name}")
        
        # Create the role
        try:
            role_response = iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Service role for AWS Bedrock batch inference jobs",
                MaxSessionDuration=3600
            )
            print(f"✅ Created IAM role: {role_response['Role']['Arn']}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                print(f"⚠️  Role {role_name} already exists, updating policies...")
                role_response = iam_client.get_role(RoleName=role_name)
            else:
                raise
        
        role_arn = role_response['Role']['Arn']
        
        # Create and attach the permissions policy
        policy_name = f"{role_name}Policy"
        
        try:
            policy_response = iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(permissions_policy),
                Description="Permissions for Bedrock batch inference jobs"
            )
            policy_arn = policy_response['Policy']['Arn']
            print(f"✅ Created IAM policy: {policy_arn}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"
                print(f"⚠️  Policy {policy_name} already exists: {policy_arn}")
            else:
                raise
        
        # Attach policy to role
        try:
            iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            print(f"✅ Attached policy to role")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                print(f"⚠️  Policy already attached to role")
            else:
                raise
        
        print(f"\n🎉 SUCCESS! Bedrock batch inference role is ready:")
        print(f"Role ARN: {role_arn}")
        print(f"\nYou can now use this role ARN with the batch inference command:")
        print(f"python manage.py submit_batch_inference \\")
        print(f"  --input-s3-uri s3://{bucket_name}/batch-processing/airscience.com/airscience_com_batch_20250122_143045.jsonl \\")
        print(f"  --role-arn {role_arn} \\")
        print(f"  --record-count 107")
        
        return role_arn
        
    except Exception as e:
        print(f"❌ Error creating Bedrock batch role: {str(e)}")
        return None


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Create IAM role for Bedrock batch inference")
    parser.add_argument(
        '--role-name',
        default='BedrockBatchInferenceRole',
        help='Name for the IAM role (default: BedrockBatchInferenceRole)'
    )
    parser.add_argument(
        '--bucket-name',
        default='triad-bedrock-batch-processing',
        help='S3 bucket name for batch processing (default: triad-bedrock-batch-processing)'
    )
    
    args = parser.parse_args()
    
    role_arn = create_bedrock_batch_role(args.role_name, args.bucket_name)
    
    if role_arn:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main() 