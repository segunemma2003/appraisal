#!/bin/bash

# Quick Fix Script for Deployment Issues
# Run this on your EC2 instance to fix common deployment problems

set -e

echo "🔧 Running deployment fix script..."

# 1. Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Not in the correct directory. Please run this from /opt/appraisal-system"
    exit 1
fi

# 2. Check and fix environment variables
echo "📝 Checking environment variables..."
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Creating from template..."
    cp deployment/env_template.txt .env
    echo "⚠️  Please edit .env file with your actual values!"
fi

# 3. Update ALLOWED_HOSTS to include the domain
echo "🌐 Updating ALLOWED_HOSTS..."
if grep -q "apes.techonstreet.com" .env; then
    echo "✅ ALLOWED_HOSTS already includes domain"
else
    echo "📝 Adding domain to ALLOWED_HOSTS..."
    sed -i 's/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=apes.techonstreet.com,13.60.12.244,localhost,127.0.0.1/' .env
fi

# 4. Activate virtual environment and install dependencies
echo "🐍 Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing/updating dependencies..."
pip install -r requirements.txt

# 5. Run database migrations
echo "🔄 Running database migrations..."
python manage.py migrate

# 5.5. Run seed data script
echo "🌱 Running seed data script..."
python seed_data.py

# 6. Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# 7. Check and fix permissions
echo "🔐 Fixing permissions..."
sudo chown -R ubuntu:ubuntu /opt/appraisal-system
chmod -R 755 /opt/appraisal-system

# 8. Restart services
echo "🔄 Restarting services..."
sudo systemctl restart appraisal-production
sudo systemctl restart nginx

# 9. Check service status
echo "📊 Checking service status..."
echo "=== Django App Status ==="
sudo systemctl status appraisal-production --no-pager -l

echo "=== Nginx Status ==="
sudo systemctl status nginx --no-pager -l

# 10. Test local connectivity
echo "🧪 Testing local connectivity..."
echo "Testing Django app on port 8000..."
if curl -s http://localhost:8000/health/ > /dev/null; then
    echo "✅ Django app is responding on port 8000"
else
    echo "❌ Django app is not responding on port 8000"
fi

echo "Testing Nginx on port 80..."
if curl -s -I http://localhost > /dev/null; then
    echo "✅ Nginx is responding on port 80"
else
    echo "❌ Nginx is not responding on port 80"
fi

# 11. Check SSL certificate
echo "🔒 Checking SSL certificate..."
if sudo certbot certificates | grep -q "apes.techonstreet.com"; then
    echo "✅ SSL certificate found"
else
    echo "⚠️  SSL certificate not found. Run: sudo certbot --nginx -d apes.techonstreet.com"
fi

# 12. Check firewall
echo "🔥 Checking firewall..."
sudo ufw status

echo ""
echo "✅ Fix script completed!"
echo ""
echo "📋 Next steps:"
echo "1. Check if the site is accessible at https://apes.techonstreet.com"
echo "2. If SSL is not working, run: sudo certbot --nginx -d apes.techonstreet.com"
echo "3. Check logs: sudo journalctl -u appraisal-production -f"
echo "4. If still not working, check DNS settings for apes.techonstreet.com"
echo ""
echo "🔗 Alternative access methods:"
echo "- http://13.60.12.244 (if SSL disabled)"
echo "- http://13.60.12.244:8000 (direct to Django)" 