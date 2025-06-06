#!/usr/bin/env python3
"""
Simple script to copy selector configurations from SQLite to PostgreSQL

This script directly extracts the selector configurations from the SQLite database
and inserts them into the PostgreSQL database without affecting other tables.
"""
import os
import sys
import sqlite3
import json
from pathlib import Path

# Set up base directory
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Load Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
import django
django.setup()

# Import Django models
from django.db import connections
from django.db import transaction
from apps.ai_processing.models import SelectorConfiguration

def copy_configurations():
    """Copy selector configurations from SQLite to PostgreSQL"""
    print("Starting selector configuration copy...")
    
    # Connect to SQLite
    sqlite_path = BASE_DIR / 'db.sqlite3'
    if not sqlite_path.exists():
        print(f"ERROR: SQLite database not found at {sqlite_path}")
        return False
    
    sqlite_conn = sqlite3.connect(str(sqlite_path))
    sqlite_conn.row_factory = sqlite3.Row  # Use row factory to get column names
    
    # Get existing selector configurations
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute("""
        SELECT id, name, description, selector_config, created_at, updated_at 
        FROM ai_processing_selectorconfiguration
    """)
    
    configurations = [dict(row) for row in sqlite_cursor.fetchall()]
    
    if not configurations:
        print("No selector configurations found in SQLite database")
        return False
    
    print(f"Found {len(configurations)} selector configurations")
    
    # Convert selector_config from JSON string to Python object
    for config in configurations:
        if isinstance(config['selector_config'], str):
            config['selector_config'] = json.loads(config['selector_config'])
    
    # Clear existing configurations in PostgreSQL
    print("Clearing existing configurations in PostgreSQL...")
    SelectorConfiguration.objects.all().delete()
    
    # Import configurations to PostgreSQL
    print("Importing configurations to PostgreSQL...")
    with transaction.atomic():
        for config in configurations:
            # Create new configuration 
            new_config = SelectorConfiguration(
                name=config['name'],
                description=config['description'],
                selector_config=config['selector_config'],
                created_at=config['created_at'],
                updated_at=config['updated_at']
            )
            new_config.save()
            print(f"Imported: {new_config.name}")
    
    print(f"Successfully imported {len(configurations)} selector configurations")
    return True

if __name__ == "__main__":
    success = copy_configurations()
    sys.exit(0 if success else 1) 