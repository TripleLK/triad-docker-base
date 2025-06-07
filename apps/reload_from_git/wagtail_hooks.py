# myapp/wagtail_hooks.py

from wagtail import hooks
from django.urls import reverse
from wagtail.admin.menu import MenuItem

@hooks.register('register_admin_menu_item')
def register_deploy_menu_item():
    return MenuItem('Deploy Latest Code', reverse('deploy_latest_code'), classnames='icon icon-upload', order=10000)
