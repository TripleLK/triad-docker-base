from django.conf import settings
from django.urls import include, path
from django.contrib import admin

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from apps.search import views as search_views
from apps.categorized_tags import views as tag_views
# Removed: from api import api  # Django Ninja API v3 - archived by Neon Dragon

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path('', include('apps.search.urls')),
    path("git-reload", include('apps.reload_from_git.urls')),
    path("api/tags/", tag_views.get_tags_api, name='api_tags'),
    path("api/v2/", include('apps.lab_equipment_api.urls')),  # Lab Equipment API v2 (DRF)
    # Removed: path("api/v3/", api.urls),  # Lab Equipment API v3 (Django Ninja) - archived by Neon Dragon
    path("content-extractor/", include('apps.content_extractor.urls')),  # Site Configuration Integration
    path("", include('apps.base_site.urls')),
]


if settings.DEBUG:

    # Serve static and media files from development server
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns = urlpatterns + [
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's page serving mechanism. This should be the last pattern in
    # the list:
    path("", include(wagtail_urls)),
    # Alternatively, if you want Wagtail pages to be served from a subpath
    # of your site, rather than the site root:
    #    path("pages/", include(wagtail_urls)),
]

