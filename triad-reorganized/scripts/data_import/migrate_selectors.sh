#!/bin/bash
# Script to migrate only selector configurations from SQLite to PostgreSQL

# Enable verbose mode to see commands as they execute
set -x

echo "Migrating ONLY selector configurations from SQLite to PostgreSQL..."

# First, make sure we're in the correct environment
echo "Switching to production environment..."
python tools/switch_env.py prod mac
if [ $? -ne 0 ]; then
  echo "Error: Failed to switch to production environment"
  exit 1
fi

# Check if postgres is running (assuming using default port)
nc -z localhost 5432
if [ $? -ne 0 ]; then
  echo "Error: PostgreSQL doesn't seem to be running on port 5432"
  echo "Please start PostgreSQL before running this script"
  exit 1
fi

# Run the migration tool focusing only on the selector configuration tables
# Disable foreign key constraints to avoid issues with auth_user references
echo "Running migration..."
python tools/migrations/migrate_direct.py --tables=ai_processing_selectorconfiguration --disable-fk --platform=mac
if [ $? -ne 0 ]; then
  echo "Error: Migration failed"
  exit 1
fi

echo "Migration completed! Check for any errors above."
echo "Note: Foreign key constraints were disabled, so created_by user references may be invalid."
echo "You may need to manually update the created_by fields in the PostgreSQL database."
echo "Now switching back to development environment..."

python tools/switch_env.py dev mac

echo "Done."

# Disable verbose mode
set +x 