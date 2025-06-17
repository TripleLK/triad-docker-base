"""
Import AWS Bedrock batch processing results into Django database.

This script processes batch results that contain:
- One OVERALL_DETAILS record per equipment page (main equipment data)
- Multiple MODEL_SUBSET records per equipment page (individual model data)

Created by: Arctic Dawn
Date: 2025-01-27
Project: Triad Docker Base
"""

import json
import os
import sys
import django
from collections import defaultdict
from django.utils.text import slugify

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.base_site.models import LabEquipmentPage
from apps.lab_equipment_api.serializers import LabEquipmentPageCreateUpdateSerializer
from apps.categorized_tags.models import CategorizedTag


def preprocess_categorized_tags(equipment_data):
    """Preprocess categorized tags to ensure they exist in the database."""
    if 'categorized_tags' not in equipment_data:
        return equipment_data
    
    tags = equipment_data['categorized_tags']
    if isinstance(tags, list) and tags and isinstance(tags[0], dict):
        # Convert from {category: ..., tag: ...} format to tag names
        tag_names = []
        for tag_info in tags:
            if tag_info.get('tag'):
                tag_name = tag_info['tag']
                category = tag_info.get('category', 'General')
                
                # Create tag if it doesn't exist using get_or_create like the existing command
                tag, created = CategorizedTag.objects.get_or_create(
                    name=tag_name,
                    defaults={'category': category}
                )
                if created:
                    print(f"✅ Created tag: {category} -> {tag_name}")
                
                tag_names.append(tag_name)
        
        equipment_data['categorized_tags'] = tag_names
    
    return equipment_data


def load_batch_results(results_file):
    """Load and parse batch results from JSONL file."""
    records = []
    with open(results_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                # Extract the actual Claude response
                model_output = record.get('modelOutput', {})
                content = model_output.get('content', [])
                if content and content[0].get('type') == 'text':
                    try:
                        parsed_response = json.loads(content[0]['text'])
                        records.append(parsed_response)
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse response JSON: {e}")
                        continue
    return records


def group_records_by_equipment(records):
    """Group records by equipment page using _page_info.ai_json_record_id."""
    equipment_groups = defaultdict(lambda: {'overall': None, 'models': []})
    
    for record in records:
        page_info = record.get('_page_info', {})
        record_id = page_info.get('ai_json_record_id')
        
        if not record_id:
            print(f"Warning: Record missing ai_json_record_id: {record.get('title', 'Unknown')}")
            continue
            
        processing_mode = record.get('_processing_mode')
        
        if processing_mode == 'OVERALL_DETAILS':
            equipment_groups[record_id]['overall'] = record
        elif processing_mode == 'MODEL_SUBSET':
            equipment_groups[record_id]['models'].append(record)
        else:
            print(f"Warning: Unknown processing mode '{processing_mode}' for record {record_id}")
    
    return dict(equipment_groups)


def merge_equipment_data(overall_record, model_records):
    """Merge OVERALL_DETAILS with MODEL_SUBSET records into complete equipment data."""
    if not overall_record:
        print("Error: No OVERALL_DETAILS record found")
        return None
    
    # Start with the overall record
    merged_data = overall_record.copy()
    
    # Collect all models from MODEL_SUBSET records
    all_models = []
    for model_record in model_records:
        models_data = model_record.get('models_data', [])
        all_models.extend(models_data)
    
    # Add the combined models to the merged data
    if all_models:
        merged_data['models_data'] = all_models
    
    # Clean up processing mode metadata for final record
    merged_data.pop('_processing_mode', None)
    merged_data.pop('_batch_info', None)
    merged_data.pop('target_model_names', None)
    
    return merged_data


def truncate_field(value, max_length):
    """Truncate field to max length if needed."""
    if isinstance(value, str) and len(value) > max_length:
        return value[:max_length-3] + "..."
    return value


def import_equipment_record(equipment_data, record_id):
    """Import a single equipment record using the Django serializer."""
    try:
        # Preprocess categorized tags
        equipment_data = preprocess_categorized_tags(equipment_data)
        
        # Truncate fields that are too long
        if 'meta_title' in equipment_data:
            equipment_data['meta_title'] = truncate_field(equipment_data['meta_title'], 60)
        
        if 'meta_description' in equipment_data:
            equipment_data['meta_description'] = truncate_field(equipment_data['meta_description'], 160)
        
        # Check if equipment already exists
        existing_equipment = LabEquipmentPage.objects.filter(
            source_url=equipment_data.get('source_url')
        ).first()
        
        if existing_equipment:
            print(f"Updating existing equipment: {equipment_data.get('title', 'Unknown')}")
            serializer = LabEquipmentPageCreateUpdateSerializer(
                existing_equipment, 
                data=equipment_data, 
                partial=True
            )
        else:
            print(f"Creating new equipment: {equipment_data.get('title', 'Unknown')}")
            serializer = LabEquipmentPageCreateUpdateSerializer(data=equipment_data)
        
        if serializer.is_valid():
            equipment = serializer.save()
            print(f"✅ Successfully imported: {equipment.title}")
            return equipment
        else:
            print(f"❌ Validation errors for record {record_id}:")
            for field, errors in serializer.errors.items():
                print(f"  {field}: {errors}")
            return None
            
    except Exception as e:
        print(f"❌ Error importing record {record_id}: {str(e)}")
        return None


def main():
    """Main import process."""
    results_file = 'batch_results/metadata-preservation-test-1750180172/metadata_test_input.jsonl.out'
    
    if not os.path.exists(results_file):
        print(f"Error: Results file not found: {results_file}")
        return
    
    print("🔄 Loading batch results...")
    records = load_batch_results(results_file)
    print(f"📊 Loaded {len(records)} records")
    
    print("🔄 Grouping records by equipment...")
    equipment_groups = group_records_by_equipment(records)
    print(f"📊 Found {len(equipment_groups)} equipment pages")
    
    # Show grouping statistics
    overall_count = sum(1 for group in equipment_groups.values() if group['overall'])
    model_count = sum(len(group['models']) for group in equipment_groups.values())
    print(f"📊 OVERALL_DETAILS records: {overall_count}")
    print(f"📊 MODEL_SUBSET records: {model_count}")
    
    successful_imports = 0
    failed_imports = 0
    
    for record_id, group_data in equipment_groups.items():
        print(f"\n🔄 Processing equipment record {record_id}...")
        
        overall_record = group_data['overall']
        model_records = group_data['models']
        
        if not overall_record:
            print(f"❌ No OVERALL_DETAILS record found for equipment {record_id}")
            failed_imports += 1
            continue
        
        print(f"📋 Found OVERALL_DETAILS + {len(model_records)} MODEL_SUBSET records")
        
        # Merge the data
        merged_data = merge_equipment_data(overall_record, model_records)
        
        if not merged_data:
            print(f"❌ Failed to merge data for equipment {record_id}")
            failed_imports += 1
            continue
        
        # Import to database
        equipment = import_equipment_record(merged_data, record_id)
        
        if equipment:
            successful_imports += 1
        else:
            failed_imports += 1
    
    print(f"\n🎉 Import Summary:")
    print(f"✅ Successful imports: {successful_imports}")
    print(f"❌ Failed imports: {failed_imports}")
    print(f"📊 Total equipment pages: {len(equipment_groups)}")


if __name__ == '__main__':
    main() 