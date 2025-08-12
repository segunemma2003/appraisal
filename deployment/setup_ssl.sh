#!/bin/bash

# SSL Certificate Setup Script for api.techonstreet.com
# Run this script on your EC2 instance after the initial setup

set -e

echo "🔒 Setting up SSL certificate for api.techonstreet.com..."

# Install certbot if not already installed
if ! command -v certbot &> /dev/null; then
    echo "📦 Installing certbot..."
    sudo apt update
    sudo apt install -y certbot python3-certbot-nginx
fi

# Stop nginx temporarily to avoid conflicts
echo "⏸️ Stopping nginx temporarily..."
sudo systemctl stop nginx

# Obtain SSL certificate
echo "🎫 Obtaining SSL certificate..."
sudo certbot certonly --standalone -d api.techonstreet.com --non-interactive --agree-tos --email your-email@example.com

# Start nginx again
echo "▶️ Starting nginx..."
sudo systemctl start nginx

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
sudo nginx -t

# Reload nginx to apply changes
echo "🔄 Reloading nginx..."
sudo systemctl reload nginx

# Set up automatic renewal
echo "🔄 Setting up automatic certificate renewal..."
sudo crontab -l 2>/dev/null | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet"; } | sudo crontab -

echo "✅ SSL certificate setup completed!"
echo "🌐 Your application should now be available at: https://api.techonstreet.com"
echo "📝 Certificate will auto-renew every 60 days" 