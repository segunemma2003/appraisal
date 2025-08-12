#!/bin/bash

# Appraisal System Server Setup Script
# Run this script on your EC2 instance to set up the environment

set -e

echo "🚀 Starting Appraisal System server setup..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "🔧 Installing required packages..."
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server git curl wget unzip

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p /opt/appraisal-system
sudo chown ubuntu:ubuntu /opt/appraisal-system

# Clone repository (you'll need to set up SSH keys first)
echo "📥 Cloning repository..."
cd /opt/appraisal-system
git clone https://github.com/yourusername/appraisal-system.git .

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Set up PostgreSQL
echo "🗄️ Setting up PostgreSQL..."
sudo -u postgres psql -c "CREATE DATABASE appraisal_db;"
sudo -u postgres psql -c "CREATE USER appraisal_user WITH PASSWORD 'your-secure-password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE appraisal_db TO appraisal_user;"
sudo -u postgres psql -c "ALTER USER appraisal_user CREATEDB;"

# Create environment file
echo "⚙️ Creating environment configuration..."
cp deployment/env_template.txt .env
echo "📝 Please edit the .env file with your actual values:"
echo "   - Generate a new SECRET_KEY"
echo "   - Set your database password"
echo "   - Configure your email settings"
echo "   - Update any other settings as needed"
echo ""
echo "Press Enter to continue after editing..."
read -p "Press Enter to continue..."

# Run Django migrations
echo "🔄 Running database migrations..."
python manage.py migrate

# Create superuser
echo "👤 Creating superuser..."
python manage.py createsuperuser

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# Set up systemd services
echo "🔧 Setting up systemd services..."
sudo cp deployment/appraisal-production.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable appraisal-production

# Set up Nginx
echo "🌐 Setting up Nginx..."
sudo cp deployment/nginx.conf /etc/nginx/sites-available/appraisal-system
sudo ln -s /etc/nginx/sites-available/appraisal-system /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Set up SSL with Let's Encrypt (optional)
echo "🔒 Setting up SSL certificate..."
sudo apt install -y certbot python3-certbot-nginx
# sudo certbot --nginx -d api.techonstreet.com

# Set up firewall
echo "🔥 Configuring firewall..."
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Create log directory
echo "📝 Setting up logging..."
mkdir -p logs
sudo chown -R ubuntu:ubuntu logs

# Set up Redis
echo "🔴 Configuring Redis..."
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Set up Celery (if using)
echo "🐐 Setting up Celery..."
sudo cp deployment/celery.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable celery

# Set proper permissions
echo "🔐 Setting proper permissions..."
sudo chown -R ubuntu:ubuntu /opt/appraisal-system
chmod +x deployment/setup_server.sh

# Start services
echo "🚀 Starting services..."
sudo systemctl start appraisal-production
sudo systemctl start celery

echo "✅ Server setup completed!"
echo "🌐 Your application should be available at: https://api.techonstreet.com"
echo "📊 Check service status with: sudo systemctl status appraisal-production"
echo "📝 View logs with: sudo journalctl -u appraisal-production -f" 