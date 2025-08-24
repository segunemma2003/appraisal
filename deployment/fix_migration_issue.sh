#!/bin/bash

# Fix Migration Issue Script
# Run this on the production server to fix the "no such table" error

set -e

echo "🔧 Fixing migration issue..."

# 1. Check if we're in the right directory
cd /opt/appraisal-system

# 2. Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# 3. Check current migration status
echo "📊 Checking current migration status..."
python manage.py showmigrations

# 4. Run migrations to ensure all tables are created
echo "🔄 Running database migrations..."
python manage.py migrate --noinput

# 5. Check if tables exist
echo "🔍 Checking if tables exist..."
python manage.py shell -c "
from django.db import connection
cursor = connection.cursor()
cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%evaluationquestion%'\")
tables = cursor.fetchall()
print('Tables found:', tables)
"

# 6. Run seed data script
echo "🌱 Running seed data script..."
python seed_data.py

# 7. Restart the service
echo "🔄 Restarting appraisal-production service..."
sudo systemctl restart appraisal-production

# 8. Check service status
echo "📊 Checking service status..."
sudo systemctl status appraisal-production --no-pager -l

echo "✅ Migration fix completed!" 