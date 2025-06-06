from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from wagtail.admin import messages

from .management.commands.scrape_page import create_or_update_page
from .Scrapers import Scraper  # Import your scraper class

@staff_member_required
def scrape_view(request):
    context = {}
    if request.method == "POST":
        target_url = request.POST.get("target_url")
        # Hardcode your YAML path, adjust if needed
        yaml_path = "/Users/lucypatton/LLLK/triad-docker-base/apps/scrapers/airscience-yamls/mapping.yaml"
        scraper = Scraper(yaml_path)
        try:
            result = scraper.scrape(target_url)
            create_or_update_page(result)
            context["result"] = result
            messages.success(request, "Scrape complete!")
        except Exception as e:
            messages.error(request, "An error occurred: {}".format(e))
    return render(request, "wagtailadmin/scrapers/scrape_form.html", context)
