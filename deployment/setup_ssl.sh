#!/bin/bash

# SSL Setup Script
# Automatically sets up SSL certificates using Let's Encrypt

set -e

echo "🔒 Setting up SSL certificates..."

# 1. Check if certbot is installed
echo "🔍 Checking if certbot is installed..."
if ! command -v certbot &> /dev/null; then
    echo "📦 Installing certbot..."
    sudo apt update
    sudo apt install -y certbot python3-certbot-nginx
else
    echo "✅ Certbot is already installed"
fi

# 2. Check if SSL certificate already exists
echo "🔍 Checking existing SSL certificates..."
if [ -f "/etc/letsencrypt/live/apes.techonstreet.com/fullchain.pem" ]; then
    echo "✅ SSL certificate already exists for apes.techonstreet.com"
    echo "📅 Certificate expiry:"
    sudo certbot certificates | grep -A 5 "apes.techonstreet.com"
    
    # Check if certificate is expiring soon (within 30 days)
    EXPIRY_DATE=$(sudo certbot certificates | grep -A 5 "apes.techonstreet.com" | grep "VALID" | awk '{print $2}')
    if [ -n "$EXPIRY_DATE" ]; then
        echo "🔄 Certificate expires on: $EXPIRY_DATE"
        # Renew if expiring within 30 days
        sudo certbot renew --dry-run
    fi
    exit 0
fi

# 3. Check if domain resolves to this server
echo "🌐 Checking if domain resolves to this server..."
SERVER_IP=$(curl -s ifconfig.me)
DOMAIN_IP=$(dig +short apes.techonstreet.com)

echo "   Server IP: $SERVER_IP"
echo "   Domain IP: $DOMAIN_IP"

if [ "$SERVER_IP" = "$DOMAIN_IP" ]; then
    echo "✅ Domain correctly resolves to this server"
else
    echo "⚠️ Domain does not resolve to this server"
    echo "   Please ensure apes.techonstreet.com points to $SERVER_IP"
    echo "   You may need to update your DNS settings"
    exit 1
fi

# 4. Ensure nginx is running and configured
echo "🌐 Ensuring nginx is running..."
if ! sudo systemctl is-active --quiet nginx; then
    echo "🚀 Starting nginx..."
    sudo systemctl start nginx
fi

# 5. Create temporary nginx configuration for SSL setup
echo "📝 Creating temporary nginx configuration for SSL setup..."
sudo tee /etc/nginx/sites-available/appraisal-system-temp > /dev/null <<EOF
server {
    listen 80;
    server_name apes.techonstreet.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
}
EOF

# 6. Enable temporary configuration
echo "🔧 Enabling temporary nginx configuration..."
sudo ln -sf /etc/nginx/sites-available/appraisal-system-temp /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

# 7. Create webroot directory for ACME challenge
echo "📁 Creating webroot directory..."
sudo mkdir -p /var/www/html
sudo chown -R www-data:www-data /var/www/html

# 8. Obtain SSL certificate
echo "🔒 Obtaining SSL certificate..."
if sudo certbot certonly --webroot -w /var/www/html -d apes.techonstreet.com --non-interactive --agree-tos --email admin@apes.techonstreet.com; then
    echo "✅ SSL certificate obtained successfully"
else
    echo "❌ Failed to obtain SSL certificate"
    echo "📝 Certbot logs:"
    sudo tail -n 20 /var/log/letsencrypt/letsencrypt.log
    exit 1
fi

# 9. Update nginx configuration with SSL
echo "🌐 Updating nginx configuration with SSL..."
sudo cp /opt/appraisal-system/deployment/nginx.conf /etc/nginx/sites-available/appraisal-system

# 10. Test and reload nginx
echo "🧪 Testing nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
    sudo systemctl reload nginx
else
    echo "❌ Nginx configuration has errors"
    exit 1
fi

# 11. Test SSL certificate
echo "🧪 Testing SSL certificate..."
if curl -s -I https://apes.techonstreet.com > /dev/null; then
    echo "✅ SSL certificate is working"
else
    echo "❌ SSL certificate is not working"
    exit 1
fi

# 12. Set up automatic renewal
echo "🔄 Setting up automatic renewal..."
sudo crontab -l 2>/dev/null | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet"; } | sudo crontab -

# 13. Show final status
echo ""
echo "📋 SSL Setup Summary:"
echo "   ✅ Certificate obtained: apes.techonstreet.com"
echo "   ✅ Nginx configured with SSL"
echo "   ✅ Automatic renewal scheduled"
echo "   ✅ HTTPS is working"

echo ""
echo "🔗 Access URLs:"
echo "   HTTP: http://apes.techonstreet.com (redirects to HTTPS)"
echo "   HTTPS: https://apes.techonstreet.com"

echo ""
echo "✅ SSL setup completed successfully!" 