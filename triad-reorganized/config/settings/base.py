"""
Base settings for the project.
"""
import os
import sys
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_DIR = BASE_DIR / 'config'
APPS_DIR = BASE_DIR / "apps"

if APPS_DIR not in sys.path:
    sys.path.insert(0, str(APPS_DIR))

# Security settings
SECRET_KEY = os.getenv('SECRET_KEY', 'default-insecure-key-for-dev')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'wagtail.contrib.forms',
    'wagtail.contrib.redirects',
    'wagtail_modeladmin',
    'wagtail.embeds',
    'wagtail.sites',
    'wagtail.users',
    'wagtail.snippets',
    'wagtail.documents',
    'wagtail.images',
    'wagtail.search',
    'wagtail.admin',
    'wagtail',
    'modelcluster',
    'taggit',
    'django_filters',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

# Loop through apps directory
for app_name in os.listdir(APPS_DIR):
    app_path = os.path.join(APPS_DIR, app_name)
    if (
        os.path.isdir(app_path)
        and app_name != "base_site" 
        and os.path.exists(os.path.join(app_path, "__init__.py"))
    ):
        INSTALLED_APPS.insert(-1, f"apps.{app_name}")

INSTALLED_APPS.insert(-1, "apps.base_site")
# print("Installed apps: " + str(INSTALLED_APPS))  # Commented out print statement

# Check for shared apps directory
SHARED_APPS_DIR = os.path.join(APPS_DIR, "shared")
if (os.path.isdir(SHARED_APPS_DIR)):
    for app_name in os.listdir(SHARED_APPS_DIR):
        app_path = os.path.join(SHARED_APPS_DIR, app_name)
        if (
            os.path.isdir(app_path)
            and os.path.exists(os.path.join(app_path, "__init__.py"))
        ):
            INSTALLED_APPS.insert(0, f"apps.{app_name}")

# Middleware
MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'apps.base_site.middleware.AdminPageRedirectMiddleware',
    'wagtail.contrib.redirects.middleware.RedirectMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, "apps", "base_site", "templates", "base_site"),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.base_site.context_processors.quote_cart',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

STATICFILES_DIRS = []
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = os.getenv('STATIC_URL', '/static/')

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = os.getenv('MEDIA_URL', '/media/')

# Default storage settings
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
    },
}

# Wagtail settings
WAGTAIL_SITE_NAME = "triad-wagtail"
WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": "wagtail.search.backends.database",
    }
}
WAGTAILADMIN_BASE_URL = "http://example.com"
WAGTAILDOCS_EXTENSIONS = ['csv', 'docx', 'key', 'odt', 'pdf', 'pptx', 'rtf', 'txt', 'xlsx', 'zip']

# Default auto field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Explicitly set SSL redirect to False to prevent Safari HTTPS issues
SECURE_SSL_REDIRECT = False
