#!/usr/bin/env python
"""
Test script for S3 integration functionality.

Created by: Digital Phoenix
Date: 2025-01-22
Project: Triad Docker Base
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Add Django project to path
sys.path.append('/Users/lucypatton/LLLK/triad-docker-base')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
import django
django.setup()

from apps.content_extractor.aws_utils import (
    get_s3_client, create_bucket_if_not_exists, upload_file_to_s3,
    convert_json_to_bedrock_jsonl, generate_s3_bucket_name
)


def test_s3_integration():
    """Test S3 integration functionality"""
    print("🧪 Testing S3 Integration")
    print("=" * 50)
    
    # Test 1: Check AWS credentials
    print("1. Testing AWS credentials...")
    try:
        client = get_s3_client()
        print("✅ AWS S3 client created successfully")
    except Exception as e:
        print(f"❌ AWS credentials not available: {str(e)}")
        print("   Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        return False
    
    # Test 2: Generate bucket name
    print("\n2. Testing bucket name generation...")
    bucket_name = generate_s3_bucket_name("www.airscience.com")
    print(f"✅ Generated bucket name: {bucket_name}")
    
    # Test 3: Create test JSON file
    print("\n3. Creating test JSON file...")
    test_data = {
        "url": "https://www.example.com/test",
        "site_domain": "www.example.com",
        "field_configurations": {
            "title": {"extracted_content": [{"text": "Test Product"}]},
            "description": {"extracted_content": [{"text": "Test description"}]}
        },
        "batch_processing_info": {
            "processed_at": "2025-01-22T10:30:00",
            "processor": "test_script"
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_data, f, indent=2)
        test_json_path = f.name
    
    print(f"✅ Created test JSON file: {test_json_path}")
    
    # Test 4: Convert to Bedrock JSONL format
    print("\n4. Testing Bedrock JSONL conversion...")
    try:
        jsonl_path = convert_json_to_bedrock_jsonl(test_json_path)
        print(f"✅ Converted to JSONL: {jsonl_path}")
        
        # Verify JSONL format
        with open(jsonl_path, 'r') as f:
            jsonl_content = f.read().strip()
            jsonl_data = json.loads(jsonl_content)
            
        if 'recordId' in jsonl_data and 'modelInput' in jsonl_data:
            print("✅ JSONL format is correct")
            print(f"   Record ID: {jsonl_data['recordId']}")
        else:
            print("❌ JSONL format is incorrect")
            return False
            
    except Exception as e:
        print(f"❌ JSONL conversion failed: {str(e)}")
        return False
    
    # Test 5: Test bucket creation (if credentials available)
    print("\n5. Testing bucket creation...")
    try:
        bucket_exists = create_bucket_if_not_exists(bucket_name, 'us-east-2')
        if bucket_exists:
            print(f"✅ Bucket {bucket_name} is available")
        else:
            print(f"❌ Failed to create/access bucket {bucket_name}")
            return False
    except Exception as e:
        print(f"❌ Bucket creation test failed: {str(e)}")
        print("   This might be due to permissions or existing bucket with same name")
        return False
    
    # Test 6: Test file upload
    print("\n6. Testing file upload...")
    try:
        s3_key = f"test-uploads/{os.path.basename(test_json_path)}"
        s3_url = upload_file_to_s3(test_json_path, bucket_name, s3_key)
        
        if s3_url:
            print(f"✅ File uploaded successfully: {s3_url}")
        else:
            print("❌ File upload failed")
            return False
            
    except Exception as e:
        print(f"❌ File upload test failed: {str(e)}")
        return False
    
    # Cleanup
    print("\n7. Cleaning up test files...")
    try:
        os.unlink(test_json_path)
        os.unlink(jsonl_path)
        print("✅ Test files cleaned up")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 All S3 integration tests passed!")
    print(f"📦 Bucket: {bucket_name}")
    print("🔄 Bedrock JSONL conversion: Working")
    print("☁️  S3 upload: Working")
    
    return True


if __name__ == "__main__":
    success = test_s3_integration()
    sys.exit(0 if success else 1) 