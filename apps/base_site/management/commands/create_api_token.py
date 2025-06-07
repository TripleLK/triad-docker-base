from django.core.management.base import BaseCommand
from apps.base_site.models import APIToken

class Command(BaseCommand):
    help = 'Creates a new API token for accessing the lab equipment API'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str, help='A friendly name for the token')
        parser.add_argument('--description', type=str, help='Optional description of what this token is used for')

    def handle(self, *args, **options):
        name = options['name']
        description = options.get('description', '')
        
        token = APIToken.objects.create(
            name=name,
            description=description
        )
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created API token: {token.name}'))
        self.stdout.write(self.style.WARNING(f'Token value (keep this secure): {token.token}'))
        self.stdout.write(self.style.WARNING('This token will not be shown again, so make sure to copy it now.')) 