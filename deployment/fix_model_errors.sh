#!/bin/bash

echo "🔧 Fixing model errors and admin 500 error..."

# Navigate to the application directory
cd /opt/appraisal-system

# Activate virtual environment
source venv/bin/activate

echo "📋 Checking Django configuration..."
python manage.py check --deploy

echo "🔄 Creating migrations for all apps..."
python manage.py makemigrations core
python manage.py makemigrations evaluations
python manage.py makemigrations users
python manage.py makemigrations notifications

echo "🔄 Running migrations..."
python manage.py migrate

echo "🧹 Collecting static files..."
python manage.py collectstatic --noinput

echo "👤 Ensuring admin user exists..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('Creating superuser...')
    User.objects.create_superuser('admin', 'admin@apes.techonstreet.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

echo "🌱 Running seed data..."
python seed_data.py

echo "🔄 Restarting Django service..."
sudo systemctl restart appraisal-production

echo "⏳ Waiting for service to start..."
sleep 5

echo "🧪 Testing admin route..."
if curl -s -I http://localhost:8000/admin/ | grep -q "200\|302"; then
    echo "✅ Admin route is working"
else
    echo "❌ Admin route still has issues"
    echo "📝 Recent Django logs:"
    sudo journalctl -u appraisal-production --no-pager -n 20
fi

echo "📊 Service status:"
sudo systemctl status appraisal-production --no-pager -l

echo "🔗 Admin URLs:"
echo "   - Local: http://localhost:8000/admin/"
echo "   - External: http://13.60.12.244:8000/admin/"
echo "   - HTTPS: https://apes.techonstreet.com/admin/"
echo ""
echo "🔑 Admin credentials:"
echo "   Username: admin"
echo "   Password: admin123" 