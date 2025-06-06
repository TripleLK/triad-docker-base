from wagtail import hooks
from wagtail.admin.menu import MenuItem
from django.urls import path, reverse
from .views import scrape_view

@hooks.register('register_admin_urls')
def register_scrape_url():
    return [
        path('scrape/', scrape_view, name='scrape'),
    ]

# Commented out to remove the Scrape URL button from the main menu
# @hooks.register('construct_main_menu')
# def add_scrape_menu_item(request, menu_items):
#     menu_items.append(
#         MenuItem('Scrape a URL', reverse('scrape'), classnames='icon icon-site', order=10000)
#     )
