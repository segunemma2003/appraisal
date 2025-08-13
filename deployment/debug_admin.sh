#!/bin/bash

# Admin Debug Script
# Helps identify issues with Django admin

set -e

echo "🔍 Debugging Django admin 500 error..."

# 1. Check if we're in the right directory
cd /opt/appraisal-system
echo "📁 Current directory: $(pwd)"

# 2. Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# 3. Check Django configuration
echo "🔧 Checking Django configuration..."
python manage.py check --deploy

# 4. Check if admin app is installed
echo "📋 Checking installed apps..."
python manage.py shell -c "
from django.conf import settings
print('Installed apps:')
for app in settings.INSTALLED_APPS:
    print(f'  - {app}')
print()
print('Admin app installed:', 'django.contrib.admin' in settings.INSTALLED_APPS)
"

# 5. Check database connection
echo "🗄️ Checking database connection..."
python manage.py shell -c "
from django.db import connection
try:
    cursor = connection.cursor()
    cursor.execute('SELECT 1')
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"

# 6. Check if admin tables exist
echo "📊 Checking admin tables..."
python manage.py shell -c "
from django.db import connection
cursor = connection.cursor()
cursor.execute(\"\"\"
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name LIKE '%auth%' OR table_name LIKE '%admin%'
\"\"\")
tables = cursor.fetchall()
print('Admin/Auth tables found:')
for table in tables:
    print(f'  - {table[0]}')
"

# 7. Check if superuser exists
echo "👤 Checking superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
users = User.objects.filter(is_superuser=True)
print(f'Superusers found: {users.count()}')
for user in users:
    print(f'  - {user.username} ({user.email})')
"

# 8. Test admin URL locally
echo "🧪 Testing admin URL locally..."
if curl -s http://localhost:8000/admin/ > /dev/null; then
    echo "✅ Admin URL responds locally"
else
    echo "❌ Admin URL fails locally"
    echo "📝 Django error logs:"
    tail -n 20 logs/django.log 2>/dev/null || echo "No Django logs found"
fi

# 9. Check Django settings
echo "⚙️ Checking Django settings..."
python manage.py shell -c "
from django.conf import settings
print('DEBUG:', settings.DEBUG)
print('ALLOWED_HOSTS:', settings.ALLOWED_HOSTS)
print('DATABASES:', list(settings.DATABASES.keys()))
print('STATIC_URL:', settings.STATIC_URL)
print('STATIC_ROOT:', settings.STATIC_ROOT)
"

# 10. Check recent Django logs
echo "📝 Recent Django logs:"
if [ -f "logs/django.log" ]; then
    tail -n 30 logs/django.log
else
    echo "No Django logs found"
fi

# 11. Check system logs
echo "📋 Recent system logs:"
sudo journalctl -u appraisal-production --no-pager -n 20

# 12. Test admin with verbose output
echo "🧪 Testing admin with verbose output..."
curl -v http://localhost:8000/admin/ 2>&1 | head -20

echo ""
echo "🔍 Debug completed!"
echo ""
echo "📋 Common fixes for admin 500 errors:"
echo "1. Run migrations: python manage.py migrate"
echo "2. Create superuser: python manage.py createsuperuser"
echo "3. Collect static: python manage.py collectstatic --noinput"
echo "4. Check logs: tail -f logs/django.log" 