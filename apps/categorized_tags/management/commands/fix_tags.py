from django.core.management.base import BaseCommand
from apps.categorized_tags.models import CategorizedTag
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Identify and fix malformed tags in the database'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting tag cleanup process...'))
        
        # 1. Find malformed tags (empty category)
        malformed_tags = CategorizedTag.objects.filter(category='')
        self.stdout.write(f'Found {len(malformed_tags)} tags with empty categories')
        
        # 2. Fix tags with category information in the name
        fixed_count = 0
        for tag in malformed_tags:
            if ':' in tag.name:
                try:
                    category, name = [part.strip() for part in tag.name.split(':', 1)]
                    tag.category = category
                    tag.name = name
                    tag.save()
                    fixed_count += 1
                    self.stdout.write(self.style.SUCCESS(f'Fixed tag: {tag}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error fixing tag {tag.id}: {str(e)}'))
            else:
                # If no category separator, use "General" as the default category
                try:
                    tag.category = "General"
                    tag.save()
                    fixed_count += 1
                    self.stdout.write(self.style.SUCCESS(f'Set default category for tag: {tag}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error fixing tag {tag.id}: {str(e)}'))
        
        # 3. Check for single-character tags (likely corrupt)
        single_char_tags = CategorizedTag.objects.filter(name__regex=r'^.$')
        if single_char_tags.exists():
            count = single_char_tags.count()
            self.stdout.write(f'Found {count} single-character tags. These are likely corrupt and should be deleted.')
            if self.confirm('Delete these tags?'):
                single_char_tags.delete()
                self.stdout.write(self.style.SUCCESS(f'Deleted {count} single-character tags'))
        
        # 4. Check for duplicate tags (same category and name but different case)
        self.stdout.write('Checking for duplicate tags with different case...')
        all_tags = CategorizedTag.objects.all()
        processed = set()
        duplicates = []
        
        for tag in all_tags:
            key = (tag.category.lower(), tag.name.lower())
            if key in processed:
                duplicates.append(tag)
            else:
                processed.add(key)
        
        if duplicates:
            self.stdout.write(f'Found {len(duplicates)} duplicate tags')
            if self.confirm('Do you want to see the list of duplicates?'):
                for tag in duplicates:
                    self.stdout.write(f'  {tag.id}: {tag} (slug: {tag.slug})')
            
            if self.confirm('Attempt to merge duplicates?'):
                # Merging logic here (complex, involving page reassignment)
                self.stdout.write('Merging not implemented yet, please delete manually if needed')
        
        # Summary
        self.stdout.write(self.style.SUCCESS(f'Tag cleanup complete. Fixed {fixed_count} tags.'))
        
        # Remaining malformed tags
        remaining = CategorizedTag.objects.filter(category='')
        if remaining.exists():
            self.stdout.write(self.style.WARNING(f'There are still {remaining.count()} tags with empty categories:'))
            for tag in remaining:
                self.stdout.write(f'  {tag.id}: {tag.name} (slug: {tag.slug})')
    
    def confirm(self, question):
        """Ask a yes/no question via input() and return the answer."""
        valid = {"yes": True, "y": True, "no": False, "n": False}
        while True:
            self.stdout.write(question + " [y/n] ")
            choice = input().lower()
            if choice in valid:
                return valid[choice] 