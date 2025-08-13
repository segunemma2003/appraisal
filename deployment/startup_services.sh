#!/bin/bash

# Startup Services Script
# Handles nginx startup and SSL certificate setup

set -e

echo "🚀 Starting services and handling SSL setup..."

# 1. Check if we're in the right directory
cd /opt/appraisal-system

# 2. Check if Django app is running
echo "🔍 Checking Django app status..."
if ! sudo systemctl is-active --quiet appraisal-production; then
    echo "⚠️ Django app is not running. Starting it..."
    sudo systemctl start appraisal-production
    sleep 3
fi

# 3. Check if Django app is listening on port 8000
echo "🔍 Checking if Django is listening on port 8000..."
if ! sudo netstat -tlnp | grep -q ":8000"; then
    echo "❌ Django app is not listening on port 8000"
    echo "📝 Checking Django app logs:"
    sudo journalctl -u appraisal-production --no-pager -n 20
    exit 1
else
    echo "✅ Django app is listening on port 8000"
fi

# 4. Test Django app locally
echo "🧪 Testing Django app locally..."
if curl -s http://localhost:8000/health/ > /dev/null; then
    echo "✅ Django app is responding"
else
    echo "❌ Django app is not responding"
    exit 1
fi

# 5. Check if SSL certificate exists
echo "🔒 Checking SSL certificate..."
if [ -f "/etc/letsencrypt/live/apes.techonstreet.com/fullchain.pem" ]; then
    echo "✅ SSL certificate found"
    SSL_AVAILABLE=true
else
    echo "⚠️ SSL certificate not found"
    SSL_AVAILABLE=false
fi

# 6. Update nginx configuration
echo "🌐 Updating nginx configuration..."
sudo cp deployment/nginx.conf /etc/nginx/sites-available/appraisal-system

# 7. Test nginx configuration
echo "🧪 Testing nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration has errors"
    exit 1
fi

# 8. Check if port 80 is already in use
echo "🔍 Checking port 80 usage..."
if sudo netstat -tlnp | grep -q ":80 "; then
    echo "⚠️ Port 80 is already in use by another service"
    echo "📋 Current port 80 listeners:"
    sudo netstat -tlnp | grep ":80 "
    echo "🔄 Using port 8080 instead"
    PORT_CONFLICT=true
else
    echo "✅ Port 80 is available"
    PORT_CONFLICT=false
fi

# 9. Start/restart nginx
echo "🔄 Starting nginx..."
if sudo systemctl is-active --quiet nginx; then
    echo "🔄 Restarting nginx..."
    sudo systemctl restart nginx
else
    echo "🚀 Starting nginx..."
    sudo systemctl start nginx
fi

# 10. Enable nginx to start on boot
echo "🔧 Enabling nginx to start on boot..."
sudo systemctl enable nginx

# 11. Check nginx status
echo "📊 Checking nginx status..."
if sudo systemctl is-active --quiet nginx; then
    echo "✅ Nginx is running"
else
    echo "❌ Nginx failed to start"
    sudo systemctl status nginx --no-pager -l
    exit 1
fi

# 12. Test nginx connectivity
echo "🧪 Testing nginx connectivity..."
if [ "$PORT_CONFLICT" = true ]; then
    # Test port 8080
    if curl -s -I http://localhost:8080 > /dev/null; then
        echo "✅ Nginx is responding on port 8080"
    else
        echo "❌ Nginx is not responding on port 8080"
        exit 1
    fi
else
    # Test port 80
    if curl -s -I http://localhost > /dev/null; then
        echo "✅ Nginx is responding on port 80"
    else
        echo "❌ Nginx is not responding on port 80"
        exit 1
    fi
fi

# 13. Setup SSL certificate if not available
if [ "$SSL_AVAILABLE" = false ]; then
    echo "🔒 Setting up SSL certificate..."
    echo "📝 Checking if domain is accessible for SSL setup..."
    
    # Test if domain resolves and is accessible
    if curl -s -I http://apes.techonstreet.com > /dev/null 2>&1; then
        echo "✅ Domain is accessible, setting up SSL automatically..."
        chmod +x deployment/setup_ssl.sh
        ./deployment/setup_ssl.sh
        SSL_AVAILABLE=true
    else
        echo "⚠️ Domain is not accessible for SSL setup"
        echo "📝 You may need to run this manually after ensuring DNS is configured:"
        echo "   ./deployment/setup_ssl.sh"
    fi
fi

# 14. Show final status
echo ""
echo "📋 Final Status:"
echo "   Django App: $(sudo systemctl is-active appraisal-production)"
echo "   Nginx: $(sudo systemctl is-active nginx)"
echo "   Django Port 8000: $(sudo netstat -tlnp | grep :8000 | wc -l) listeners"
if [ "$PORT_CONFLICT" = true ]; then
    echo "   Nginx Port 8080: $(sudo netstat -tlnp | grep :8080 | wc -l) listeners"
else
    echo "   Nginx Port 80: $(sudo netstat -tlnp | grep :80 | wc -l) listeners"
fi
echo "   SSL Certificate: $SSL_AVAILABLE"

# 15. Show access URLs
echo ""
echo "🔗 Access URLs:"
echo "   Direct Django: http://13.60.12.244:8000"
if [ "$PORT_CONFLICT" = true ]; then
    echo "   Via Nginx: http://13.60.12.244:8080"
else
    echo "   Via Nginx: http://13.60.12.244"
fi
if [ "$SSL_AVAILABLE" = true ]; then
    echo "   HTTPS: https://apes.techonstreet.com"
fi

echo ""
echo "✅ Startup completed successfully!" 