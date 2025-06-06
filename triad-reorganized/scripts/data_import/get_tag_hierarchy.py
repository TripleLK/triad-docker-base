#!/usr/bin/env python
"""
Script to generate a hierarchical list of tags for the AI prompt template.
This script uses the Django ORM to retrieve tags and format them for insertion
into the prompt template's {{existing_tags}} placeholder.
"""

import os
import sys
import django
from django.db.models import Count

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

# Import Django models after setup
from apps.categorized_tags.models import TagCategory, CategorizedTag

def get_tag_hierarchy_text(min_count=0, category_filter=None):
    """
    Generate a text representation of the tag hierarchy to be inserted
    into the AI prompt template.
    
    Args:
        min_count: Minimum number of pages using a tag
        category_filter: Filter by category name
    
    Returns:
        str: Text representation of the tag hierarchy
    """
    # Get all tag categories
    categories = TagCategory.objects.all().order_by('name')
    
    # If category filter is provided, filter the categories
    if category_filter:
        categories = categories.filter(name__iexact=category_filter)
    
    # Build text output
    output = []
    
    for category in categories:
        # Get tags for this category
        tags = CategorizedTag.objects.filter(category=category.name)
        
        # Sort tags by name
        tags = tags.order_by('name')
        
        # Create a list to collect tags with their counts
        category_tags = []
        
        # For each tag, calculate its usage count directly
        for tag in tags:
            # Get the direct count of related page tags
            page_count = tag.categorized_tags_categorizedpagetag_items.count()
            
            # Filter by minimum count if specified
            if page_count >= min_count:
                category_tags.append((tag.name, page_count))
        
        # Add to output if there are any tags
        if category_tags:
            output.append(f"[{category.name}]")
            for tag_name, count in category_tags:
                output.append(f"- {tag_name} ({count})")
            output.append("")  # Empty line between categories
    
    if not output:
        return "No existing tags found. Create appropriate tags as needed."
    
    return "\n".join(output)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate tag hierarchy for AI prompt')
    parser.add_argument('--min-count', type=int, default=0,
                      help='Minimum number of pages using a tag')
    parser.add_argument('--category', type=str, help='Filter tags by category')
    parser.add_argument('--output', type=str, help='Output file (default: stdout)')
    
    args = parser.parse_args()
    
    # Generate tag hierarchy text
    output = get_tag_hierarchy_text(
        min_count=args.min_count,
        category_filter=args.category
    )
    
    # Output to file or stdout
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
    else:
        print(output)

if __name__ == "__main__":
    main() 