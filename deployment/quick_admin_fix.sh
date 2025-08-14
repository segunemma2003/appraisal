#!/bin/bash

echo "🚀 Quick fix for admin 500 error..."

# Navigate to app directory
cd /opt/appraisal-system

# Activate virtual environment
source venv/bin/activate

echo "🔄 Running migrations..."
python manage.py makemigrations
python manage.py migrate

echo "👤 Creating admin user..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@apes.techonstreet.com', 'admin123')
    print('Admin user created')
else:
    print('Admin user already exists')
"

echo "🔄 Restarting service..."
sudo systemctl restart appraisal-production

echo "✅ Fix completed! Try accessing:"
echo "   http://13.60.12.244:8000/admin/"
echo "   Username: admin"
echo "   Password: admin123" 