#!/usr/bin/env python3
"""
Direct SQLite to PostgreSQL Migration

This script:
1. Extracts data directly from SQLite
2. Inserts it directly into PostgreSQL
3. Bypasses Django's serialization/deserialization to avoid print statement issues

Usage:
    python tools/migrations/migrate_direct.py [options]

Options:
    --tables TABLE1,TABLE2   Comma-separated list of tables to migrate
    --skip-tables TABLE1,TABLE2   Comma-separated list of tables to skip
    --disable-fk             Disable foreign key constraints during migration
    --platform PLATFORM      Platform to use (mac or ec2, default: mac)
"""
import os
import sys
import sqlite3
import time
import argparse
import subprocess
from pathlib import Path

# Set up base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

def switch_environment(env_type, platform="ec2"):
    """Switch to the specified environment"""
    script_path = str(BASE_DIR / "tools" / "migrations" / "switch_env.py")
    
    try:
        result = subprocess.run(
            ["python", script_path, env_type, platform],
            capture_output=True, 
            text=True,
            check=True
        )
        print(f"Successfully switched to {env_type} environment on {platform}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error switching environment: {e.stderr}")
        return False

def verify_environment():
    """Make sure we're in production mode with PostgreSQL configured"""
    # Check if .env points to production
    env_link = BASE_DIR / ".env"
    if not env_link.is_symlink():
        print("ERROR: .env is not a symlink. Run tools/migrations/switch_env.py prod first.")
        return False

    # Check if linked to prod environment
    if not os.readlink(env_link).endswith(("prod.mac.env", "prod.ec2.env")):
        print("ERROR: Not using production environment. Run tools/migrations/switch_env.py prod first.")
        return False
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
    
    import django
    django.setup()
    
    # Check database engine
    from django.conf import settings
    db_engine = settings.DATABASES['default']['ENGINE']
    
    if 'postgresql' not in db_engine:
        print(f"ERROR: Not using PostgreSQL! Current engine: {db_engine}")
        return False
    
    print(f"✅ Environment verified: Using {db_engine}")
    return True

def connect_to_databases():
    """Connect to both SQLite and PostgreSQL databases"""
    # SQLite connection
    sqlite_path = BASE_DIR / 'db.sqlite3'
    if not sqlite_path.exists():
        print(f"ERROR: SQLite database not found at {sqlite_path}")
        return None, None
    
    sqlite_conn = sqlite3.connect(str(sqlite_path))
    sqlite_conn.row_factory = sqlite3.Row  # Use row factory to get column names
    
    # PostgreSQL connection via Django
    import django
    from django.db import connections
    
    # Get the PostgreSQL connection from Django
    pg_conn = connections['default']
    
    print(f"✅ Connected to both databases")
    print(f"   SQLite: {sqlite_path}")
    print(f"   PostgreSQL: {pg_conn.settings_dict['NAME']} on {pg_conn.settings_dict['HOST']}")
    
    return sqlite_conn, pg_conn

def get_table_list(sqlite_conn):
    """Get a list of tables from SQLite database"""
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    
    # Skip Django migration tables
    tables = [t for t in tables if not t.startswith('django_migrations')]
    
    print(f"Found {len(tables)} tables in SQLite database")
    return tables

def clear_postgresql_table(pg_conn, table_name):
    """Clear all data from a PostgreSQL table"""
    with pg_conn.cursor() as cursor:
        try:
            cursor.execute(f'TRUNCATE TABLE "{table_name}" CASCADE;')
            print(f"Cleared PostgreSQL table: {table_name}")
            return True
        except Exception as e:
            print(f"Error clearing table {table_name}: {str(e)}")
            return False

def get_table_columns_with_types(sqlite_conn, table_name):
    """Get column names and their data types for a specific table"""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = [(row[1], row[2]) for row in cursor.fetchall()]
    cursor.close()
    return columns

def disable_foreign_keys(pg_conn):
    """Temporarily disable foreign key constraints in PostgreSQL"""
    with pg_conn.cursor() as cursor:
        cursor.execute("SET session_replication_role = 'replica';")
    print("✅ Foreign key constraints temporarily disabled")

def enable_foreign_keys(pg_conn):
    """Re-enable foreign key constraints in PostgreSQL"""
    with pg_conn.cursor() as cursor:
        cursor.execute("SET session_replication_role = 'origin';")
    print("✅ Foreign key constraints re-enabled")

def convert_value_for_postgresql(value, sqlite_type, column_name):
    """
    Convert SQLite values to PostgreSQL compatible values
    Especially handle booleans in SQLite (stored as 0/1) for PostgreSQL (true/false)
    Also truncate long values for spec.value
    """
    # Handle None values
    if value is None:
        return None
    
    # Handle boolean values (convert SQLite 0/1 to PostgreSQL boolean)
    if 'bool' in sqlite_type.lower() or sqlite_type == 'tinyint(1)':
        # Convert any integers in SQLite that represent booleans
        if isinstance(value, int):
            return True if value == 1 else False
    
    # Handle long text in base_site_spec.value column (max length 256)
    if column_name == 'value' and isinstance(value, str) and len(value) > 255:
        return value[:255]  # Truncate to 255 chars (PostgreSQL varchar(256))
    
    # Return the value as is for other types
    return value

def migrate_table(sqlite_conn, pg_conn, table_name, batch_size=100):
    """Migrate a single table from SQLite to PostgreSQL"""
    print(f"\nMigrating table: {table_name}")
    
    # Get column names and types
    columns_with_types = get_table_columns_with_types(sqlite_conn, table_name)
    columns = [col[0] for col in columns_with_types]
    print(f"Columns: {', '.join(columns)}")
    
    # Create a dictionary to map column name to its SQLite type
    column_types = {col[0]: col[1] for col in columns_with_types}
    
    # Skip if no columns
    if not columns:
        print(f"No columns found for table {table_name}, skipping")
        return 0
    
    # Clear the PostgreSQL table first
    if not clear_postgresql_table(pg_conn, table_name):
        return 0
    
    # Count records
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    total_records = sqlite_cursor.fetchone()[0]
    
    if total_records == 0:
        print(f"No records in {table_name}, skipping")
        sqlite_cursor.close()
        return 0
    
    print(f"Migrating {total_records} records from {table_name}")
    
    # Read all data from SQLite
    sqlite_cursor.execute(f"SELECT * FROM {table_name};")
    
    # Process in batches to prevent memory issues
    batch_count = 0
    record_count = 0
    
    with pg_conn.cursor() as pg_cursor:
        while True:
            rows = sqlite_cursor.fetchmany(batch_size)
            if not rows:
                break
            
            # Convert rows to list of dictionaries
            records = [dict(row) for row in rows]
            
            # Skip if no records
            if not records:
                continue
            
            # Insert into PostgreSQL
            try:
                # Construct placeholders for the query
                placeholders = ", ".join(["%s"] * len(columns))
                column_str = ", ".join([f'"{col}"' for col in columns])
                
                # Prepare the insert query
                insert_query = f'INSERT INTO "{table_name}" ({column_str}) VALUES ({placeholders})'
                
                # Prepare the data to insert with conversion
                for record in records:
                    # Convert values for PostgreSQL - especially booleans and long values
                    values = [convert_value_for_postgresql(record[col], column_types.get(col, ''), col) for col in columns]
                    pg_cursor.execute(insert_query, values)
                
                batch_count += 1
                record_count += len(records)
                
                # Print progress
                progress = (record_count / total_records) * 100
                print(f"Progress: {record_count}/{total_records} records ({progress:.1f}%)", end="\r")
                
            except Exception as e:
                print(f"\nError inserting batch into {table_name}: {str(e)}")
                # Continue with next batch
    
    print(f"\n✅ Migrated {record_count} records from {table_name} in {batch_count} batches")
    
    # Update sequence if there's an ID column (auto-increment)
    if 'id' in columns:
        try:
            with pg_conn.cursor() as pg_cursor:
                pg_cursor.execute(f"""
                    SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), 
                                 (SELECT MAX(id) FROM {table_name}));
                """)
                print(f"Updated ID sequence for {table_name}")
        except Exception as e:
            print(f"Error updating sequence for {table_name}: {str(e)}")
    
    sqlite_cursor.close()
    return record_count

def migrate_all_tables(sqlite_conn, pg_conn, tables=None, skip_tables=None):
    """Migrate all tables from SQLite to PostgreSQL"""
    if tables is None:
        tables = get_table_list(sqlite_conn)
    
    if skip_tables:
        tables = [t for t in tables if t not in skip_tables]
    
    print(f"Will migrate {len(tables)} tables")
    
    # Define table dependencies - this helps migrate tables in the right order
    # Format: table_name: [list of tables it depends on]
    dependencies = {
        'auth_user_groups': ['auth_user', 'auth_group'],
        'auth_user_user_permissions': ['auth_user', 'auth_permission'],
        'auth_group_permissions': ['auth_group', 'auth_permission'],
        'wagtailcore_site': ['wagtailcore_page'],
        'wagtailcore_page': ['auth_user', 'django_content_type'],
        'wagtailcore_groupcollectionpermission': ['auth_group', 'auth_permission', 'wagtailcore_collection'],
        'wagtailcore_grouppagepermission': ['auth_group', 'wagtailcore_page'],
        'wagtailcore_pagerevision': ['auth_user', 'wagtailcore_page'],
        'wagtailcore_pageviewrestriction_groups': ['wagtailcore_pageviewrestriction', 'auth_group'],
        'wagtailcore_pageviewrestriction': ['wagtailcore_page'],
        'wagtailcore_collectionviewrestriction_groups': ['wagtailcore_collectionviewrestriction', 'auth_group'],
        'wagtailcore_workflow': [],
        'wagtailcore_task': ['django_content_type'],
        'wagtailcore_groupapprovaltask': ['wagtailcore_task'],
        'wagtailcore_groupapprovaltask_groups': ['wagtailcore_groupapprovaltask', 'auth_group'],
        'wagtailcore_workflowtask': ['wagtailcore_workflow', 'wagtailcore_task'],
        'wagtailcore_workflowpage': ['wagtailcore_page', 'wagtailcore_workflow'],
        'base_site_labequipmentpage': ['wagtailcore_page'],
        'base_site_homepage': ['wagtailcore_page'],
        'base_site_contactpage': ['wagtailcore_page'],
        'base_site_equipmentmodel': ['base_site_labequipmentpage'],
        'base_site_specgroup': [],
        'base_site_equipmentmodelspecgroup': ['base_site_specgroup', 'base_site_equipmentmodel'],
        'base_site_spec': ['base_site_specgroup'],
        'base_site_labequipmentgalleryimage': ['base_site_labequipmentpage'],
        'categorized_tags_tagcategory': [],
        'categorized_tags_categorizedtag': ['categorized_tags_tagcategory'],
        'categorized_tags_categorizedpagetag': ['categorized_tags_categorizedtag', 'wagtailcore_page'],
    }
    
    # Basic dependency resolution - create a sorted list based on dependencies
    # The basic idea is to order tables so that we import tables before their dependencies
    ordered_tables = []
    remaining_tables = set(tables)
    
    # First pass: tables with no dependencies
    core_tables = ['django_content_type', 'auth_permission', 'auth_group', 'auth_user', 'wagtailcore_collection', 
                  'wagtailcore_locale', 'categorized_tags_tagcategory', 'base_site_specgroup']
    for table in core_tables:
        if table in remaining_tables:
            ordered_tables.append(table)
            remaining_tables.remove(table)
    
    # Second pass: tables with dependencies on core tables
    for _ in range(5):  # Limit iterations to prevent infinite loops
        for table in list(remaining_tables):
            deps = dependencies.get(table, [])
            if not deps or all(dep in ordered_tables for dep in deps):
                ordered_tables.append(table)
                remaining_tables.remove(table)
    
    # Add any remaining tables
    ordered_tables.extend(list(remaining_tables))
    
    # Start migration
    start_time = time.time()
    total_records = 0
    migrated_tables = 0
    
    for table in ordered_tables:
        try:
            records = migrate_table(sqlite_conn, pg_conn, table)
            if records > 0:
                total_records += records
                migrated_tables += 1
        except Exception as e:
            print(f"Error migrating table {table}: {str(e)}")
    
    elapsed_time = time.time() - start_time
    print(f"\nMigration completed in {elapsed_time:.2f} seconds")
    print(f"Migrated {total_records} records across {migrated_tables} tables")
    
    return migrated_tables, total_records

def main():
    """Main function to run the migration process"""
    parser = argparse.ArgumentParser(description="Migrate data from SQLite to PostgreSQL")
    parser.add_argument("--tables", help="Comma-separated list of tables to migrate")
    parser.add_argument("--skip-tables", help="Comma-separated list of tables to skip")
    parser.add_argument("--disable-fk", action="store_true", help="Disable foreign key checks during migration")
    parser.add_argument("--platform", choices=["mac", "ec2"], default="ec2", help="Platform to use (mac or ec2)")
    args = parser.parse_args()
    
    print("SQLite to PostgreSQL Direct Migration")
    print("====================================\n")
    
    # Ensure we're using SQLite environment first to read data
    if not switch_environment("dev", args.platform):
        print("ERROR: Failed to switch to development environment for SQLite export")
        return False
    
    # Now switch to production environment for PostgreSQL import
    if not switch_environment("prod", args.platform):
        print("ERROR: Failed to switch to production environment for PostgreSQL import")
        return False
    
    # Verify environment
    if not verify_environment():
        return False
    
    # Connect to databases
    sqlite_conn, pg_conn = connect_to_databases()
    if not sqlite_conn or not pg_conn:
        return False
    
    # Get target tables
    target_tables = None
    if args.tables:
        target_tables = args.tables.split(',')
        print(f"Will only migrate these tables: {', '.join(target_tables)}")
    
    # Get skip tables
    skip_tables = None
    if args.skip_tables:
        skip_tables = args.skip_tables.split(',')
        print(f"Will skip these tables: {', '.join(skip_tables)}")
    
    # Migrate tables
    try:
        # Disable foreign key constraints if requested
        if args.disable_fk:
            print("Warning: Foreign key constraints will be disabled during migration.")
            print("This may lead to data integrity issues if not handled carefully.")
            disable_foreign_keys(pg_conn)
        
        # Perform migration
        migrate_all_tables(sqlite_conn, pg_conn, target_tables, skip_tables)
        
        # Re-enable foreign key constraints if they were disabled
        if args.disable_fk:
            enable_foreign_keys(pg_conn)
    finally:
        # Close connections
        sqlite_conn.close()
        # Django will close the PostgreSQL connection
    
    print("\nMigration completed!")
    print("You can now run your application with PostgreSQL:")
    print(f"  python manage.py runserver 0.0.0.0:{os.environ.get('PORT', '7000')}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 