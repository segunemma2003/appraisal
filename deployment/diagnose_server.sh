#!/bin/bash

# Server Diagnostic Script
# Run this on your EC2 instance to diagnose deployment issues

echo "🔍 Running server diagnostics..."
echo "=================================="

# 1. Check system status
echo "📊 System Status:"
echo "   - Uptime: $(uptime)"
echo "   - Load: $(cat /proc/loadavg)"
echo "   - Memory: $(free -h | grep Mem | awk '{print $3"/"$2}')"
echo "   - Disk: $(df -h / | tail -1 | awk '{print $5}') used"

# 2. Check if we're in the right directory
echo ""
echo "📁 Application Directory:"
if [ -d "/opt/appraisal-system" ]; then
    echo "   ✅ /opt/appraisal-system exists"
    cd /opt/appraisal-system
    echo "   📂 Current directory: $(pwd)"
    echo "   📄 Files: $(ls -la | wc -l) files"
else
    echo "   ❌ /opt/appraisal-system does not exist"
    exit 1
fi

# 3. Check environment file
echo ""
echo "⚙️ Environment Configuration:"
if [ -f ".env" ]; then
    echo "   ✅ .env file exists"
    echo "   🔍 ALLOWED_HOSTS: $(grep ALLOWED_HOSTS .env || echo 'Not found')"
    echo "   🔍 DEBUG: $(grep DEBUG .env || echo 'Not found')"
else
    echo "   ❌ .env file missing"
fi

# 4. Check virtual environment
echo ""
echo "🐍 Python Environment:"
if [ -d "venv" ]; then
    echo "   ✅ Virtual environment exists"
    source venv/bin/activate
    echo "   🐍 Python version: $(python --version)"
    echo "   📦 Installed packages: $(pip list | wc -l)"
else
    echo "   ❌ Virtual environment missing"
fi

# 5. Check database
echo ""
echo "🗄️ Database Status:"
if sudo -u postgres psql -d appraisal_db -c "SELECT 1;" > /dev/null 2>&1; then
    echo "   ✅ Database connection successful"
else
    echo "   ❌ Database connection failed"
fi

# 6. Check Django app
echo ""
echo "🐍 Django Application:"
if [ -f "manage.py" ]; then
    echo "   ✅ manage.py exists"
    source venv/bin/activate
    if python manage.py check --deploy > /dev/null 2>&1; then
        echo "   ✅ Django configuration is valid"
    else
        echo "   ❌ Django configuration has issues"
        python manage.py check --deploy
    fi
else
    echo "   ❌ manage.py missing"
fi

# 7. Check services
echo ""
echo "🔧 Service Status:"
echo "   Django App: $(sudo systemctl is-active appraisal-production 2>/dev/null || echo 'not found')"
echo "   Nginx: $(sudo systemctl is-active nginx 2>/dev/null || echo 'not found')"
echo "   PostgreSQL: $(sudo systemctl is-active postgresql 2>/dev/null || echo 'not found')"
echo "   Redis: $(sudo systemctl is-active redis-server 2>/dev/null || echo 'not found')"

# 8. Check ports
echo ""
echo "🔌 Port Status:"
echo "   Port 8000 (Django): $(sudo netstat -tlnp | grep :8000 | wc -l) listeners"
echo "   Port 80 (HTTP): $(sudo netstat -tlnp | grep :80 | wc -l) listeners"
echo "   Port 443 (HTTPS): $(sudo netstat -tlnp | grep :443 | wc -l) listeners"

# 9. Test connectivity
echo ""
echo "🧪 Connectivity Tests:"
echo "   Local Django (8000): $(curl -s http://localhost:8000/health/ > /dev/null && echo '✅' || echo '❌')"
echo "   Local Nginx (80): $(curl -s -I http://localhost > /dev/null && echo '✅' || echo '❌')"
echo "   External Django (8000): $(curl -s http://13.60.12.244:8000/health/ > /dev/null && echo '✅' || echo '❌')"
echo "   External Nginx (80): $(curl -s -I http://13.60.12.244 > /dev/null && echo '✅' || echo '❌')"

# 10. Check firewall
echo ""
echo "🔥 Firewall Status:"
sudo ufw status

# 11. Check recent logs
echo ""
echo "📝 Recent Service Logs (last 10 lines):"
echo "   Django App:"
sudo journalctl -u appraisal-production --no-pager -n 10 2>/dev/null || echo "   No logs found"

echo ""
echo "   Nginx:"
sudo tail -n 10 /var/log/nginx/error.log 2>/dev/null || echo "   No logs found"

# 12. Check SSL certificate
echo ""
echo "🔒 SSL Certificate:"
if sudo certbot certificates 2>/dev/null | grep -q "apes.techonstreet.com"; then
    echo "   ✅ SSL certificate found"
else
    echo "   ❌ SSL certificate not found"
fi

echo ""
echo "=================================="
echo "🔍 Diagnostic completed!"
echo ""
echo "📋 Quick fixes to try:"
echo "1. If Django app is not running: sudo systemctl start appraisal-production"
echo "2. If Nginx is not running: sudo systemctl start nginx"
echo "3. If .env is missing: cp deployment/env_template.txt .env"
echo "4. If SSL is missing: sudo certbot --nginx -d apes.techonstreet.com"
echo "5. If firewall is blocking: sudo ufw allow 8000" 