#!/bin/bash

echo "🔍 Comprehensive 500 Error Debug Script"
echo "========================================"

# Navigate to app directory
cd /opt/appraisal-system

# Activate virtual environment
source venv/bin/activate

echo ""
echo "1. 🔧 Checking Django Configuration..."
echo "-------------------------------------"
python manage.py shell -c "
from django.conf import settings
print(f'DEBUG: {settings.DEBUG}')
print(f'ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}')
print(f'DATABASES: {settings.DATABASES}')
print(f'INSTALLED_APPS: {settings.INSTALLED_APPS}')
"

echo ""
echo "2. 🔍 Running Django Check..."
echo "----------------------------"
python manage.py check --deploy

echo ""
echo "3. 🗄️ Checking Database Connection..."
echo "-----------------------------------"
python manage.py shell -c "
from django.db import connection
try:
    cursor = connection.cursor()
    cursor.execute('SELECT version();')
    result = cursor.fetchone()
    print(f'Database connected: {result[0]}')
except Exception as e:
    print(f'Database error: {e}')
"

echo ""
echo "4. 📋 Checking Admin Tables..."
echo "----------------------------"
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

echo ""
echo "5. 👤 Checking Superuser..."
echo "-------------------------"
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
users = User.objects.filter(is_superuser=True)
print(f'Superusers: {users.count()}')
if users.count() > 0:
    for user in users:
        print(f'  - {user.username} ({user.email})')
else:
    print('  No superusers found')
"

echo ""
echo "6. 🔄 Checking Migrations..."
echo "---------------------------"
python manage.py showmigrations

echo ""
echo "7. 🧪 Testing Admin Route Locally..."
echo "----------------------------------"
echo "Testing with curl..."
curl -s -w "HTTP Status: %{http_code}\n" http://localhost:8000/admin/ -o /tmp/admin_response.html

echo ""
echo "8. 📝 Django Logs..."
echo "------------------"
if [ -f "logs/django.log" ]; then
    echo "Last 50 lines of Django log:"
    tail -50 logs/django.log
else
    echo "No Django log file found"
fi

echo ""
echo "9. 📊 System Service Status..."
echo "----------------------------"
sudo systemctl status appraisal-production --no-pager -l

echo ""
echo "10. 🌐 Network Status..."
echo "----------------------"
echo "Port 8000 listeners:"
sudo netstat -tlnp | grep :8000

echo ""
echo "11. 📄 Admin Response Content..."
echo "------------------------------"
if [ -f "/tmp/admin_response.html" ]; then
    echo "First 500 characters of admin response:"
    head -c 500 /tmp/admin_response.html
    echo ""
else
    echo "No admin response captured"
fi

echo ""
echo "12. 🔧 Environment Variables..."
echo "----------------------------"
echo "DEBUG setting in .env:"
grep "DEBUG=" .env || echo "DEBUG not found in .env"

echo ""
echo "13. 🐛 Manual Django Test..."
echo "---------------------------"
python manage.py shell -c "
from django.test import Client
from django.urls import reverse
client = Client()
try:
    response = client.get('/admin/')
    print(f'Admin response status: {response.status_code}')
    if response.status_code != 200:
        print(f'Response content: {response.content[:500]}')
except Exception as e:
    print(f'Error testing admin: {e}')
"

echo ""
echo "🔍 Debug Complete!"
echo "=================="
echo "Check the output above for any errors or issues."
echo "The most common issues are:"
echo "  - Missing migrations"
echo "  - Database connection problems"
echo "  - Missing admin tables"
echo "  - Incorrect DEBUG setting"
echo "  - Service not running" 