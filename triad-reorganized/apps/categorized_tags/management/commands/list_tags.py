from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from apps.categorized_tags.models import CategorizedTag, TagCategory
from wagtail.models import Page
import json

class Command(BaseCommand):
    help = 'List all tags in a hierarchical format by category'

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            choices=['text', 'json'],
            default='text',
            help='Output format (text or json)'
        )
        parser.add_argument(
            '--min-count',
            type=int,
            default=0,
            help='Minimum number of pages using a tag to include it in the output'
        )
        parser.add_argument(
            '--category',
            type=str,
            help='Filter tags by specific category'
        )

    def handle(self, *args, **options):
        output_format = options['format']
        min_count = options['min_count']
        category_filter = options.get('category')
        
        # Get all tag categories
        categories = TagCategory.objects.all().order_by('name')
        
        # If category filter is provided, filter the categories
        if category_filter:
            categories = categories.filter(name__iexact=category_filter)
        
        # Dictionary to store the hierarchical tag data
        tag_hierarchy = {}
        
        for category in categories:
            # Get tags for this category
            tags = CategorizedTag.objects.filter(category=category.name)
            
            # Sort tags by name
            tags = tags.order_by('name')
            
            # Create a list for tag data
            tag_data = []
            
            # For each tag, calculate its usage count directly
            for tag in tags:
                # Get the direct count of related page tags
                page_count = tag.categorized_tags_categorizedpagetag_items.count()
                
                # Filter by minimum count if specified
                if page_count >= min_count:
                    tag_data.append({'name': tag.name, 'count': page_count})
            
            # Add to hierarchy if there are any tags
            if tag_data:
                tag_hierarchy[category.name] = {
                    'color': category.color,
                    'tags': tag_data
                }
        
        # Output in the specified format
        if output_format == 'json':
            self.stdout.write(json.dumps(tag_hierarchy, indent=2))
        else:
            # Text format
            if not tag_hierarchy:
                self.stdout.write("No tags found matching the criteria.")
            else:
                for category, data in tag_hierarchy.items():
                    self.stdout.write(f"[{category}]")
                    for tag in data['tags']:
                        self.stdout.write(f"- {tag['name']} ({tag['count']})")
                    self.stdout.write("")  # Empty line between categories 