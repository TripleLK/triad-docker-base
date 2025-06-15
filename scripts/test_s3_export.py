#!/usr/bin/env python3
"""
Test S3 Export - Demonstration of exporting existing AI JSON records to S3

This script shows how to use the export_to_s3 command with your existing
processed pages from the database.

Created by: Digital Phoenix
Date: 2025-01-22
Project: Triad Docker Base
"""

import subprocess
import sys

# Your Bedrock prompt ARN
BEDROCK_PROMPT_ARN = "arn:aws:bedrock:us-east-1:891377295311:prompt/H52151JSYK"

def show_available_data():
    """Show what data is available for export"""
    print("🔍 Checking available data...")
    
    cmd = [
        sys.executable, "manage.py", "shell", "-c",
        "from apps.content_extractor.models import SiteConfiguration, AIJSONRecord; "
        "print('Available sites:'); "
        "[print(f'  {sc.site_domain}: {AIJSONRecord.objects.filter(site_url__site_config=sc, is_current=True).count()} records') for sc in SiteConfiguration.objects.all()]"
    ]
    
    subprocess.run(cmd)

def run_dry_run_test():
    """Run a dry run test with 5 records"""
    print("\n🧪 Running dry run test with 5 records...")
    
    cmd = [
        sys.executable, "manage.py", "export_to_s3", "www.airscience.com",
        "--bedrock-format",
        "--bedrock-prompt-arn", BEDROCK_PROMPT_ARN,
        "--limit", "5",
        "--dry-run"
    ]
    
    subprocess.run(cmd)

def run_small_batch_test():
    """Run actual S3 upload with 3 records (small test)"""
    print("\n🚀 Running small batch test (3 records) - ACTUAL UPLOAD...")
    
    response = input("This will upload to S3. Continue? (y/N): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    cmd = [
        sys.executable, "manage.py", "export_to_s3", "www.airscience.com",
        "--bedrock-format",
        "--bedrock-prompt-arn", BEDROCK_PROMPT_ARN,
        "--limit", "3",
        "--delete-local"
    ]
    
    subprocess.run(cmd)

def run_full_export():
    """Run full export of all records"""
    print("\n🎯 Running FULL export (all 107 records) - ACTUAL UPLOAD...")
    
    response = input("This will upload ALL 107 records to S3. Continue? (y/N): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    cmd = [
        sys.executable, "manage.py", "export_to_s3", "www.airscience.com",
        "--bedrock-format",
        "--bedrock-prompt-arn", BEDROCK_PROMPT_ARN,
        "--delete-local"
    ]
    
    subprocess.run(cmd)

def show_usage_examples():
    """Show usage examples"""
    print("\n📚 Usage Examples:")
    print("=" * 50)
    
    examples = [
        {
            "title": "Dry Run (Test without uploading)",
            "command": f"python manage.py export_to_s3 www.airscience.com --bedrock-format --bedrock-prompt-arn \"{BEDROCK_PROMPT_ARN}\" --limit 5 --dry-run"
        },
        {
            "title": "Small Test (3 records)",
            "command": f"python manage.py export_to_s3 www.airscience.com --bedrock-format --bedrock-prompt-arn \"{BEDROCK_PROMPT_ARN}\" --limit 3"
        },
        {
            "title": "Individual Files Only",
            "command": f"python manage.py export_to_s3 www.airscience.com --bedrock-format --format individual --limit 10"
        },
        {
            "title": "Batch File Only",
            "command": f"python manage.py export_to_s3 www.airscience.com --bedrock-format --format batch"
        },
        {
            "title": "Full Export (All Records)",
            "command": f"python manage.py export_to_s3 www.airscience.com --bedrock-format --bedrock-prompt-arn \"{BEDROCK_PROMPT_ARN}\" --delete-local"
        },
        {
            "title": "Custom S3 Bucket",
            "command": f"python manage.py export_to_s3 www.airscience.com --s3-bucket my-custom-bucket --s3-prefix my-data --bedrock-format"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['title']}:")
        print(f"   {example['command']}")

def main():
    """Main test menu"""
    print("🎯 S3 Export Test Script")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Show available data")
        print("2. Run dry run test (5 records)")
        print("3. Run small batch test (3 records - ACTUAL UPLOAD)")
        print("4. Run full export (107 records - ACTUAL UPLOAD)")
        print("5. Show usage examples")
        print("6. Exit")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == '1':
            show_available_data()
        elif choice == '2':
            run_dry_run_test()
        elif choice == '3':
            run_small_batch_test()
        elif choice == '4':
            run_full_export()
        elif choice == '5':
            show_usage_examples()
        elif choice == '6':
            print("Goodbye! 👋")
            break
        else:
            print("Invalid choice. Please select 1-6.")

if __name__ == "__main__":
    main() 