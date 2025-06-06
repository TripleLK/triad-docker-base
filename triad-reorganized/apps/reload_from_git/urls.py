# reload_from_git/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('deploy/', views.deploy_latest_code, name='deploy_latest_code'),
]
