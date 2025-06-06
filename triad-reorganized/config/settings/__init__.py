"""
Django settings initialization.
This module loads the appropriate Django settings based on the environment.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file (always reload)
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(env_path, override=True)

# Clear any existing environment variables that might override our .env file
if 'DJANGO_ENV' in os.environ:
    current_env = os.environ['DJANGO_ENV']
    # Only clear if explicitly running this module
    if __name__ == '__main__':
        print(f"Warning: Clearing existing DJANGO_ENV={current_env} from environment")

# Get environment from .env file
django_env = os.getenv('DJANGO_ENV', 'development')
settings_module = os.getenv('DJANGO_SETTINGS_MODULE', '')

# Determine which settings to use
if settings_module:
    # If DJANGO_SETTINGS_MODULE is explicitly set in .env, use that
    module_name = settings_module.split('.')[-1]
    if module_name == 'production':
        from .production import *
        print("Using production settings (from DJANGO_SETTINGS_MODULE)")
    elif module_name in ('dev', 'development'):
        from .dev import *
        print("Using development settings (from DJANGO_SETTINGS_MODULE)")
    else:
        from .dev import *
        print(f"Using development settings (unknown module: {module_name})")
else:
    # Otherwise use DJANGO_ENV 
    if django_env == 'production':
        from .production import *
        print("Using production settings (from DJANGO_ENV)")
    else:
        from .dev import *
        print("Using development settings (from DJANGO_ENV)")

# Print a clear message about which database is being used
if 'postgresql' in DATABASES['default']['ENGINE']:
    db_name = DATABASES['default'].get('NAME', 'unknown')
    print(f"Connected to PostgreSQL database: {db_name}")
else:
    db_path = DATABASES['default'].get('NAME', 'unknown')
    print(f"Using SQLite database: {db_path}")
