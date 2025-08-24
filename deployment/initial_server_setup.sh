#!/bin/bash

# Initial Server Setup Script
# Complete setup for a fresh EC2 instance

set -e

echo "🚀 Starting complete server setup..."

# 1. Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# 2. Install required packages
echo "🔧 Installing required packages..."
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server git curl wget unzip certbot python3-certbot-nginx

# 3. Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p /opt/appraisal-system
sudo chown ubuntu:ubuntu /opt/appraisal-system

# 4. Clone repository
echo "📥 Cloning repository..."
cd /opt/appraisal-system
git clone https://github.com/segunemma2003/appraisal.git .

# 5. Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 6. Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 7. Set up PostgreSQL
echo "🗄️ Setting up PostgreSQL..."
sudo -u postgres psql -c "CREATE DATABASE appraisal_db;" || echo "Database might already exist"
sudo -u postgres psql -c "CREATE USER appraisal_user WITH PASSWORD 'appraisal123';" || echo "User might already exist"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE appraisal_db TO appraisal_user;" || echo "Privileges might already be granted"
sudo -u postgres psql -c "ALTER USER appraisal_user CREATEDB;" || echo "User might already have CREATEDB"

# 8. Create environment file
echo "⚙️ Creating environment configuration..."
cp deployment/env_template.txt .env

# 9. Update environment variables
echo "🔧 Updating environment variables..."
sed -i 's/SECRET_KEY=.*/SECRET_KEY=django-insecure-'$(openssl rand -hex 32)'/' .env
sed -i 's/DEBUG=.*/DEBUG=False/' .env
sed -i 's/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=apes.techonstreet.com,13.60.12.244,localhost,127.0.0.1/' .env
sed -i 's/DB_PASSWORD=.*/DB_PASSWORD=appraisal123/' .env

# 10. Run Django migrations
echo "🔄 Running database migrations..."
python manage.py migrate --noinput

# 11. Create superuser (non-interactive)
echo "👤 Creating superuser..."
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@apes.techonstreet.com', 'admin123') if not User.objects.filter(username='admin').exists() else None" | python manage.py shell

# 12. Run seed data script
echo "🌱 Running seed data script..."
python seed_data.py

# 13. Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# 14. Set up systemd services
echo "🔧 Setting up systemd services..."
sudo cp deployment/appraisal-production.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable appraisal-production

# 15. Set up Nginx (only for SSL termination)
echo "🌐 Setting up Nginx for SSL termination..."
sudo cp deployment/nginx.conf /etc/nginx/sites-available/appraisal-system
sudo ln -sf /etc/nginx/sites-available/appraisal-system /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# 16. Set up firewall (allow port 8000, don't interfere with port 80)
echo "🔥 Configuring firewall..."
sudo ufw allow ssh
sudo ufw allow 8000
sudo ufw allow 443
sudo ufw --force enable

# 17. Create log directory
echo "📝 Setting up logging..."
mkdir -p logs
sudo chown -R ubuntu:ubuntu logs

# 18. Set up Redis
echo "🔴 Configuring Redis..."
sudo systemctl enable redis-server
sudo systemctl start redis-server

# 19. Set up Celery (if using)
echo "🐐 Setting up Celery..."
sudo cp deployment/celery.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable celery

# 20. Set proper permissions
echo "🔐 Setting proper permissions..."
sudo chown -R ubuntu:ubuntu /opt/appraisal-system
chmod +x deployment/*.sh

# 21. Start services
echo "🚀 Starting services..."
sudo systemctl start appraisal-production
sudo systemctl start celery

# 22. Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# 23. Test services
echo "🧪 Testing services..."
if sudo systemctl is-active --quiet appraisal-production; then
    echo "✅ Django app is running"
else
    echo "❌ Django app failed to start"
    sudo systemctl status appraisal-production --no-pager -l
fi

if sudo systemctl is-active --quiet nginx; then
    echo "✅ Nginx is running"
else
    echo "❌ Nginx failed to start"
    sudo systemctl status nginx --no-pager -l
fi

# 24. Test connectivity
echo "🧪 Testing connectivity..."
if curl -s http://localhost:8000/health/ > /dev/null; then
    echo "✅ Django app is responding on port 8000"
else
    echo "❌ Django app is not responding on port 8000"
fi

# 25. Show final status
echo ""
echo "📋 Final Setup Status:"
echo "   Django App: $(sudo systemctl is-active appraisal-production)"
echo "   Nginx: $(sudo systemctl is-active nginx)"
echo "   PostgreSQL: $(sudo systemctl is-active postgresql)"
echo "   Redis: $(sudo systemctl is-active redis-server)"
echo "   Celery: $(sudo systemctl is-active celery)"
echo "   Port 8000: $(sudo netstat -tlnp | grep :8000 | wc -l) listeners"

echo ""
echo "🔗 Access URLs:"
echo "   Direct Django (HTTP): http://13.60.12.244:8000"
echo "   Direct Django (HTTP): http://apes.techonstreet.com:8000"
echo "   HTTPS (when SSL is set up): https://apes.techonstreet.com"

echo ""
echo "👤 Admin credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo "   Email: admin@apes.techonstreet.com"

echo ""
echo "✅ Initial server setup completed!"
echo "🌐 Your application should now be accessible on port 8000!" 