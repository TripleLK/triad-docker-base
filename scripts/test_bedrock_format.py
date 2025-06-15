#!/usr/bin/env python3
"""
Test script for Bedrock JSONL format conversion with specific prompt ARN.

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
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
import django
django.setup()

from apps.content_extractor.aws_utils import convert_json_to_bedrock_jsonl, DEFAULT_BEDROCK_PROMPT_ARN


def test_bedrock_conversion():
    """Test the Bedrock JSONL conversion with the user's prompt ARN"""
    
    # Create a sample JSON file
    sample_data = {
        "url": "https://example.com/product/test-product",
        "site_domain": "example.com",
        "site_name": "Example Site",
        "field_configurations": {
            "product_name": "Test Product",
            "price": "$99.99",
            "description": "This is a test product for Bedrock conversion"
        },
        "batch_processing_info": {
            "processed_at": "2025-01-22T10:00:00Z",
            "processor": "batch_site_processor",
            "threshold_used": 0.9
        }
    }
    
    # Create temporary JSON file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        json.dump(sample_data, temp_file, indent=2)
        temp_json_path = temp_file.name
    
    try:
        print("🧪 Testing Bedrock JSONL conversion...")
        print(f"📄 Sample JSON file: {temp_json_path}")
        print(f"🎯 Using prompt ARN: {DEFAULT_BEDROCK_PROMPT_ARN}")
        
        # Convert to Bedrock JSONL format
        jsonl_path = convert_json_to_bedrock_jsonl(temp_json_path)
        
        print(f"✅ Converted to JSONL: {jsonl_path}")
        
        # Read and display the JSONL content
        with open(jsonl_path, 'r') as f:
            jsonl_content = f.read()
        
        print("\n📋 Generated JSONL content:")
        print("-" * 50)
        print(jsonl_content)
        print("-" * 50)
        
        # Parse and validate the JSONL structure
        jsonl_data = json.loads(jsonl_content.strip())
        
        print("\n🔍 Validation:")
        print(f"✓ Record ID: {jsonl_data.get('recordId')}")
        print(f"✓ Has modelInput: {'modelInput' in jsonl_data}")
        print(f"✓ Has promptArn: {'promptArn' in jsonl_data.get('modelInput', {})}")
        print(f"✓ Prompt ARN: {jsonl_data.get('modelInput', {}).get('promptArn')}")
        print(f"✓ Has promptVariables: {'promptVariables' in jsonl_data.get('modelInput', {})}")
        print(f"✓ Has content: {'content' in jsonl_data.get('modelInput', {}).get('promptVariables', {})}")
        
        # Test with custom prompt ARN
        print("\n🧪 Testing with custom prompt ARN...")
        custom_arn = "arn:aws:bedrock:us-east-1:891377295311:prompt/CUSTOM123"
        custom_jsonl_path = convert_json_to_bedrock_jsonl(temp_json_path, None, custom_arn)
        
        with open(custom_jsonl_path, 'r') as f:
            custom_jsonl_content = f.read()
        
        custom_jsonl_data = json.loads(custom_jsonl_content.strip())
        print(f"✓ Custom prompt ARN used: {custom_jsonl_data.get('modelInput', {}).get('promptArn')}")
        
        print("\n✅ All tests passed! Bedrock JSONL format is working correctly.")
        
        # Cleanup
        if os.path.exists(temp_json_path):
            os.unlink(temp_json_path)
        if os.path.exists(jsonl_path):
            os.unlink(jsonl_path)
        if os.path.exists(custom_jsonl_path):
            os.unlink(custom_jsonl_path)
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        # Cleanup on error
        if os.path.exists(temp_json_path):
            os.unlink(temp_json_path)
        raise


if __name__ == "__main__":
    test_bedrock_conversion() 