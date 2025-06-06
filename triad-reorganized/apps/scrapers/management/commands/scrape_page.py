from django.core.management.base import BaseCommand, CommandError
from wagtail.models import Page
from apps.base_site.models import LabEquipmentPage, LabEquipmentGalleryImage, EquipmentModelSpecGroup, EquipmentModel, Spec
from scrapers.Scrapers import Scraper  # adjust the import based on your project structure

class Command(BaseCommand):
    help = 'Scrapes a given page and creates/updates Wagtail content'


    def add_arguments(self, parser):
        parser.add_argument('target_url', type=str, help='The URL to scrape')
        parser.add_argument('--config', type=str, default='default.yaml',
                            help='Path to the scraper YAML configuration file')

    def handle(self, *args, **options):
        target_url = options['target_url']
        config_path = options['config']
        self.stdout.write('Starting scraper for {} using config {}'.format(target_url, config_path))
        
        try:
            scraper = Scraper(config_path)
            result = scraper.scrape(target_url)
            # Process the result and integrate with your Wagtail pages here.
            self.stdout.write('Scrape successful. Result:')
            self.stdout.write(str(result))

            create_or_update_page(result)
        except Exception as e:
            raise CommandError('An error occurred: {}'.format(e))


def create_or_update_page(result):
    # Get the parent page where new pages should be added
    parent_page = Page.objects.get(id=2)
    
    # Create the new page instance using scraped data (adjust fields as necessary)
    new_page = LabEquipmentPage(
        title=result.get('name'),
        full_description=result.get('full_description'),
        short_description=result.get('short_description')
    )

    
    # Add the new page as a child of the parent then publish it
    parent_page.add_child(instance=new_page)
    new_page.save_revision().publish()
    import_gallery_images(new_page, result['imgs'])
    import_models(new_page, result['models'])

def import_gallery_images(page, image_urls):
    for url in image_urls:
        # Option A: create a LabEquipmentGalleryImage using the external URL
        LabEquipmentGalleryImage.objects.create(
            page=page,
            external_image_url=url,
        )

def import_models(page, models):
    for model_name, spec_groups in models.items():
        # Each spec group has only one key, the name of the group, and its value is a list of specs
        model = page.models.create(
            page= page,
            name= model_name,
            model_number= 'a10'
        )
        for spec_group in spec_groups:
            spec_group_name = next(iter(spec_group))
            sg = model.spec_groups.create(
                equipment_model=model,
                name= spec_group_name
            )
            for spec in spec_group[spec_group_name]:
                spec = sg.specs.create(
                    key= spec['spec_name'],
                    value= spec['spec_value']
                )
    page.save_revision().publish()




