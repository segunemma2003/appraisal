#!/bin/bash

# Quick Admin Fix Script
# Run this on the server to diagnose and fix admin 500 errors

set -e

echo "🔍 Quick admin 500 error diagnosis..."

# 1. Go to app directory
cd /opt/appraisal-system
source venv/bin/activate

# 2. Check Django configuration
echo "🔧 Checking Django configuration..."
python manage.py check --deploy

# 3. Check if admin app is in INSTALLED_APPS
echo "📋 Checking admin app installation..."
python manage.py shell -c "
from django.conf import settings
admin_installed = 'django.contrib.admin' in settings.INSTALLED_APPS
print('Admin app installed:', admin_installed)
if not admin_installed:
    print('❌ Admin app not in INSTALLED_APPS!')
else:
    print('✅ Admin app is installed')
"

# 4. Check database tables
echo "🗄️ Checking database tables..."
python manage.py shell -c "
from django.db import connection
cursor = connection.cursor()
cursor.execute(\"\"\"
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND (table_name LIKE '%auth%' OR table_name LIKE '%admin%' OR table_name LIKE '%django%')
    ORDER BY table_name
\"\"\")
tables = cursor.fetchall()
print('Django/Auth/Admin tables:')
for table in tables:
    print(f'  - {table[0]}')
"

# 5. Check if migrations are applied
echo "🔄 Checking migrations..."
python manage.py showmigrations | grep -E "(admin|auth)" || echo "No admin/auth migrations found"

# 6. Run any pending migrations
echo "🔄 Running migrations..."
python manage.py migrate

# 7. Check superuser
echo "👤 Checking superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
users = User.objects.filter(is_superuser=True)
print(f'Superusers: {users.count()}')
if users.count() == 0:
    print('Creating superuser...')
    User.objects.create_superuser('admin', 'admin@apes.techonstreet.com', 'admin123')
    print('✅ Superuser created: admin/admin123')
else:
    for user in users:
        print(f'  - {user.username} ({user.email})')
"

# 8. Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# 9. Test admin locally
echo "🧪 Testing admin locally..."
if curl -s -I http://localhost:8000/admin/ | grep -q "200\|302"; then
    echo "✅ Admin works locally"
else
    echo "❌ Admin still has issues locally"
    echo "📝 Django error logs:"
    tail -n 20 logs/django.log 2>/dev/null || echo "No Django logs found"
fi

# 10. Restart Django service
echo "🔄 Restarting Django service..."
sudo systemctl restart appraisal-production
sleep 3

# 11. Final test
echo "🧪 Final admin test..."
if curl -s -I http://localhost:8000/admin/ | grep -q "200\|302"; then
    echo "✅ Admin is now working!"
else
    echo "❌ Admin still has issues"
    echo "📝 Recent Django logs:"
    sudo journalctl -u appraisal-production --no-pager -n 10
fi

echo ""
echo "🔗 Admin URLs to test:"
echo "   - http://13.60.12.244:8000/admin/"
echo "   - http://apes.techonstreet.com:8000/admin/"
echo "   - https://apes.techonstreet.com/admin/"
echo ""
echo "👤 Admin credentials: admin/admin123" 