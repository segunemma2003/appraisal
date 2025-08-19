#!/bin/bash

echo "🔍 Getting Detailed 500 Error Information"
echo "========================================="

# Navigate to app directory
cd /opt/appraisal-system

# Activate virtual environment
source venv/bin/activate

echo ""
echo "1. 🐛 Enabling DEBUG mode..."
sed -i 's/DEBUG=.*/DEBUG=True/' .env

echo ""
echo "2. 🔄 Restarting service with DEBUG enabled..."
sudo systemctl restart appraisal-production
sleep 5

echo ""
echo "3. 🧪 Testing admin route with DEBUG enabled..."
echo "Testing: http://localhost:8000/admin/"
curl -s -w "\nHTTP Status: %{http_code}\n" http://localhost:8000/admin/

echo ""
echo "4. 📝 Django Service Logs..."
echo "---------------------------"
sudo journalctl -u appraisal-production --no-pager -n 30

echo ""
echo "5. 📄 Django Application Logs..."
echo "-------------------------------"
if [ -f "logs/django.log" ]; then
    echo "Last 50 lines of Django log:"
    tail -50 logs/django.log
else
    echo "No Django log file found"
fi

echo ""
echo "6. 🔧 Django Configuration Check..."
echo "--------------------------------"
python manage.py shell -c "from django.conf import settings; print(f'DEBUG: {settings.DEBUG}'); print(f'ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}')"

echo ""
echo "7. 🗄️ Database Connection Test..."
echo "-------------------------------"
python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT version();'); print(f'Database: {cursor.fetchone()[0]}')"

echo ""
echo "8. 📋 Checking Admin Tables..."
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
echo "9. 🔄 Migration Status..."
echo "----------------------"
python manage.py showmigrations

echo ""
echo "10. 🧪 Manual Django Test..."
echo "---------------------------"
python manage.py shell -c "
from django.test import Client
client = Client()
try:
    response = client.get('/admin/')
    print(f'Admin response status: {response.status_code}')
    if response.status_code != 200:
        print(f'Response content (first 1000 chars): {response.content[:1000]}')
except Exception as e:
    print(f'Error testing admin: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "11. 🌐 External Access Test..."
echo "----------------------------"
echo "Testing external access..."
curl -s -w "\nHTTP Status: %{http_code}\n" http://13.60.12.244:8000/admin/

echo ""
echo "12. 📊 Service Status..."
echo "----------------------"
sudo systemctl status appraisal-production --no-pager -l

echo ""
echo "🔍 Debug Information Complete!"
echo "=============================="
echo ""
echo "🔗 Now visit these URLs to see the detailed error:"
echo "   - http://13.60.12.244:8000/admin/"
echo "   - http://apes.techonstreet.com:8000/admin/"
echo ""
echo "With DEBUG=True, you should see a detailed Django error page"
echo "instead of a generic 500 error. Please share the error details." 