#!/bin/bash
# Simple script to copy selector configurations from SQLite to PostgreSQL

echo "Copying selector configurations from SQLite to PostgreSQL..."

# Switch to production environment first to ensure PostgreSQL is used
python tools/switch_env.py prod mac

# Run the Python script to copy configurations
python tools/copy_selectors.py

echo "Done. Switching back to development environment..."
python tools/switch_env.py dev mac 