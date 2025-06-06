from django.urls import path
from apps.search import views

urlpatterns = [
    path("search/", views.search, name="search"),
    path("category/<str:category_slug>/<str:value_slug>/", views.category_view, name="category_view"),
] 