#!/bin/bash

echo "🚀 Quick Debug - Enable DEBUG and Check Error"
echo "============================================="

# Navigate to app directory
cd /opt/appraisal-system

# Enable DEBUG mode
echo "🐛 Enabling DEBUG mode..."
sed -i 's/DEBUG=.*/DEBUG=True/' .env

# Restart service
echo "🔄 Restarting service with DEBUG enabled..."
sudo systemctl restart appraisal-production
sleep 3

# Test admin route and capture error
echo "🧪 Testing admin route with DEBUG enabled..."
curl -s -v http://localhost:8000/admin/ 2>&1

echo ""
echo "📝 Service logs:"
sudo journalctl -u appraisal-production --no-pager -n 20

echo ""
echo "📄 Django logs:"
if [ -f "logs/django.log" ]; then
    tail -20 logs/django.log
else
    echo "No Django log file found"
fi

echo ""
echo "🔍 Now visit: http://13.60.12.244:8000/admin/"
echo "You should see the detailed error page instead of a generic 500 error." 