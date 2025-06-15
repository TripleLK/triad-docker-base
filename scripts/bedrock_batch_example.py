#!/usr/bin/env python3
"""
Example script demonstrating batch processing with Bedrock integration.

This script shows how to use the batch site processor with your specific
Bedrock prompt ARN for automated website processing and S3 upload.

Created by: Digital Phoenix
Date: 2025-01-22
Project: Triad Docker Base
"""

import os
import subprocess
import sys

# Your Bedrock prompt ARN
BEDROCK_PROMPT_ARN = "arn:aws:bedrock:us-east-1:891377295311:prompt/H52151JSYK"

def run_batch_processing_example():
    """
    Example of running batch processing with Bedrock integration.
    
    This demonstrates the complete workflow:
    1. Crawl website and filter by selector success
    2. Generate AI JSON files
    3. Convert to Bedrock JSONL format with your prompt ARN
    4. Upload to S3
    5. Clean up local files
    """
    
    print("🚀 Bedrock Batch Processing Example")
    print("=" * 50)
    print(f"🎯 Using Bedrock Prompt ARN: {BEDROCK_PROMPT_ARN}")
    print()
    
    # Example domain (replace with your target domain)
    domain = "airscience.com"
    
    # Build the command
    cmd = [
        "python", "manage.py", "batch_site_processor",
        domain,
        "--threshold", "0.9",
        "--max-pages", "10",
        "--max-depth", "2",
        "--upload-to-s3",
        "--bedrock-format",
        "--bedrock-prompt-arn", BEDROCK_PROMPT_ARN,
        "--s3-prefix", "bedrock-batch-processing",
        "--delete-local",
        "--verbose"
    ]
    
    print("📋 Command to run:")
    print(" ".join(cmd))
    print()
    
    # Check if AWS credentials are available
    aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    
    if not aws_access_key or not aws_secret_key:
        print("⚠️  AWS credentials not found in environment variables!")
        print("   Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        print("   Example:")
        print("   export AWS_ACCESS_KEY_ID='your-access-key'")
        print("   export AWS_SECRET_ACCESS_KEY='your-secret-key'")
        print("   export AWS_REGION='us-east-1'")
        print()
        print("🧪 Running in DRY RUN mode instead...")
        
        # Add dry-run flag
        cmd.append("--dry-run")
    
    print("🏃 Running batch processor...")
    print("-" * 50)
    
    try:
        # Run the command
        result = subprocess.run(cmd, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                              capture_output=False, text=True)
        
        if result.returncode == 0:
            print("-" * 50)
            print("✅ Batch processing completed successfully!")
        else:
            print("-" * 50)
            print(f"❌ Batch processing failed with exit code: {result.returncode}")
            
    except Exception as e:
        print(f"❌ Error running batch processor: {str(e)}")


def show_command_options():
    """Show all available command options for the batch processor."""
    
    print("📚 Batch Site Processor Command Options")
    print("=" * 50)
    print()
    
    options = [
        ("domain", "Target domain to process (required)", "airscience.com"),
        ("--threshold", "Selector success rate threshold (0.0-1.0)", "0.9"),
        ("--max-pages", "Maximum pages to crawl", "50"),
        ("--max-depth", "Maximum crawl depth", "3"),
        ("--upload-to-s3", "Upload files to S3", "flag"),
        ("--bedrock-format", "Convert to Bedrock JSONL format", "flag"),
        ("--bedrock-prompt-arn", "Your Bedrock prompt ARN", BEDROCK_PROMPT_ARN),
        ("--s3-bucket", "S3 bucket name (auto-generated if not provided)", "optional"),
        ("--s3-prefix", "S3 key prefix", "batch-processing"),
        ("--delete-local", "Delete local files after S3 upload", "flag"),
        ("--dry-run", "Test mode - no files generated", "flag"),
        ("--verbose", "Detailed output", "flag"),
    ]
    
    for option, description, example in options:
        if example == "flag":
            print(f"  {option:<25} {description}")
        else:
            print(f"  {option:<25} {description}")
            print(f"  {'':<25} Example: {example}")
        print()


def show_bedrock_format_example():
    """Show what the Bedrock JSONL format looks like."""
    
    print("📄 Bedrock JSONL Format Example")
    print("=" * 50)
    print()
    print("Your JSON files will be converted to this format for Bedrock batch inference:")
    print()
    
    example = {
        "recordId": "airscience_product_123",
        "modelInput": {
            "promptArn": BEDROCK_PROMPT_ARN,
            "promptVariables": {
                "content": '{"url": "https://airscience.com/product/...", "field_configurations": {...}}'
            }
        }
    }
    
    import json
    print(json.dumps(example, indent=2))
    print()
    print("🔍 Key components:")
    print(f"  • recordId: Unique identifier for each record")
    print(f"  • promptArn: Your Bedrock prompt ARN")
    print(f"  • content: Original JSON data as a string in promptVariables")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "options":
            show_command_options()
        elif sys.argv[1] == "format":
            show_bedrock_format_example()
        else:
            print("Usage: python bedrock_batch_example.py [options|format]")
    else:
        run_batch_processing_example() 