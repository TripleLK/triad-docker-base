from django.core.management.base import BaseCommand
from django.contrib.staticfiles.storage import staticfiles_storage

class Command(BaseCommand):
    help = 'Regenerate the staticfiles manifest'

    def handle(self, *args, **options):
        self.stdout.write('Regenerating staticfiles manifest...')
        # Force the manifest to be regenerated
        if hasattr(staticfiles_storage, 'hashed_files'):
            staticfiles_storage.hashed_files = {}
        if hasattr(staticfiles_storage, 'hashed_names'):
            staticfiles_storage.hashed_names = {}
        staticfiles_storage.save_manifest()
        self.stdout.write(self.style.SUCCESS('Regenerated staticfiles manifest'))
