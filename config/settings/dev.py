"""
Development settings for the project.
"""
import os
from .base import *

# Debug settings
DEBUG = True

# Database settings - using SQLite by default
db_engine = os.getenv('DATABASE_ENGINE', 'django.db.backends.sqlite3')
db_name = os.getenv('DATABASE_NAME', 'db.sqlite3')

# For SQLite, use full path; for others like PostgreSQL, just use the name
if db_engine == 'django.db.backends.sqlite3':
    db_path = os.path.join(BASE_DIR, db_name)
else:
    db_path = db_name

DATABASES = {
    'default': {
        'ENGINE': db_engine,
        'NAME': db_path,
        'USER': os.getenv('DATABASE_USER', ''),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', ''),
        'HOST': os.getenv('DATABASE_HOST', ''),
        'PORT': os.getenv('DATABASE_PORT', ''),
    }
}

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-key-change-this-in-production')

# Allow all hosts in development
ALLOWED_HOSTS = ['*']

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Disable HTTPS/SSL settings
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = None
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Static files configuration
STATIC_URL = os.getenv('STATIC_URL', '/static/')
STATICFILES_STORAGE = os.getenv('STATICFILES_STORAGE', 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage')
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Disable password validation in development
AUTH_PASSWORD_VALIDATORS = []

# Debug toolbar
try:
    import debug_toolbar
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']
except ImportError:
    pass 
