"""
Django management command for testing Option A: Metadata Preservation in Batch Processing

Created by: Quantum Ridge  
Date: 2025-06-17
Project: Triad Docker Base

This command tests whether the enhanced AI prompt preserves critical metadata fields
during batch processing workflows.
"""

import json
from pathlib import Path
from django.core.management.base import BaseCommand

from apps.content_extractor.models import AIJSONRecord
from apps.content_extractor.aws_utils import create_bedrock_messages_jsonl


class Command(BaseCommand):
    help = 'Test metadata preservation in batch processing for Option A implementation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--record-count',
            type=int,
            default=5,
            help='Number of test records to generate (default: 5)'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='apps/content_extractor/test_data/test_metadata_preservation',
            help='Output directory for test files'
        )

    def handle(self, *args, **options):
        record_count = options['record_count']
        output_dir = Path(options['output_dir'])
        
        self.stdout.write(self.style.SUCCESS("🧪 TESTING OPTION A: Metadata Preservation in Batch Processing"))
        self.stdout.write("=" * 60)
        
        self.stdout.write(f"\n📊 Step 1: Creating {record_count} test records with metadata from database...")
        test_data, test_dir = self.create_test_data_with_metadata(record_count, output_dir)
        
        self.stdout.write("\n🔄 Step 2: Generating batch input JSONL with enhanced prompt...")
        jsonl_path = self.generate_batch_input_jsonl(test_data, test_dir)
        
        self.stdout.write(self.style.SUCCESS("\n✅ Test Setup Complete!"))
        self.stdout.write(f"📁 Test files created in: {test_dir}")
        self.stdout.write(f"📝 Batch input file: {jsonl_path}")
        self.stdout.write("\n🎯 NEXT STEPS:")
        self.stdout.write("1. Submit this JSONL to AWS Bedrock batch processing")
        self.stdout.write("2. Check if Claude 3 outputs preserve _processing_mode, _batch_info, etc.")
        self.stdout.write("3. Test import with preserved metadata")
        
        # Show metadata summary
        self.stdout.write("\n🔍 METADATA FIELDS TO VERIFY IN OUTPUTS:")
        for field in ["_processing_mode", "_batch_info", "_page_info", "target_model_names", 
                      "extracted_specification_groups", "_specification_instructions"]:
            self.stdout.write(f"   ✓ {field}")

    def create_test_data_with_metadata(self, record_count, output_dir):
        """Create test input files with proper metadata fields from database records."""
        # Get recent records
        records = AIJSONRecord.objects.all()[:record_count]
        
        test_data = []
        
        for i, record in enumerate(records):
            # Add critical metadata fields that must be preserved
            test_json = {
                # CRITICAL METADATA - These MUST be preserved by AI
                "_processing_mode": "OVERALL_DETAILS" if i % 2 == 0 else "MODEL_SUBSET",
                "_batch_info": {
                    "batch_number": (i % 3) + 1,
                    "total_batches": 3,
                    "models_in_batch": [f"model_{i}_1", f"model_{i}_2"],
                    "total_models": 6
                },
                "_page_info": {
                    "page_title": record.site_url.page_title,
                    "safe_directory_name": record.site_url.page_title.replace(" ", "_"),
                    "ai_json_record_id": record.id
                },
                "target_model_names": [f"model_{i}_1", f"model_{i}_2"],
                "extracted_specification_groups": ["Construction", "Dimensions & Weights", "Electrical"],
                "_specification_instructions": {
                    "use_exact_group_names": True,
                    "no_underscores_in_names": True,
                    "extract_all_available_data": True
                },
                
                # Add the actual extracted data
                **record.json_data
            }
            
            test_data.append(test_json)
        
        self.stdout.write(f"✅ Created {len(test_data)} test records with metadata")
        
        # Create test directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save individual test files
        for i, data in enumerate(test_data):
            test_file = output_dir / f"test_record_{i+1}_with_metadata.json"
            with open(test_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.stdout.write(f"💾 Saved: {test_file}")
        
        return test_data, output_dir

    def generate_batch_input_jsonl(self, test_data, test_dir):
        """Generate Bedrock Messages API JSONL file using the enhanced prompt."""
        jsonl_path = test_dir / "test_batch_input.jsonl"
        
        # Use the enhanced prompt with metadata preservation requirements
        result_path = create_bedrock_messages_jsonl(
            json_data_list=test_data,
            output_path=str(jsonl_path)
        )
        
        self.stdout.write(f"📝 Generated batch input JSONL: {result_path}")
        
        # Show a sample of the input to verify metadata is included
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            first_record = json.loads(f.readline())
            
        self.stdout.write("\n🔍 Sample batch input record:")
        self.stdout.write(f"Record ID: {first_record['recordId']}")
        
        # Extract the JSON data from the prompt
        prompt_text = first_record['modelInput']['messages'][0]['content'][0]['text']
        if "{{INPUT_JSON_DATA}}" in prompt_text:
            self.stdout.write(self.style.ERROR("❌ Template variable not replaced!"))
        else:
            # Find the JSON data in the prompt
            if '"_processing_mode":' in prompt_text:
                self.stdout.write(self.style.SUCCESS("✅ Metadata found in prompt:"))
                start = prompt_text.find('"_processing_mode":')
                snippet = prompt_text[start:start+200] + "..."
                self.stdout.write(f"   {snippet}")
            else:
                self.stdout.write(self.style.ERROR("❌ Metadata NOT found in prompt!"))
        
        return jsonl_path 