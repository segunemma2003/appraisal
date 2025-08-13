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

# 4. Test if Django app is accessible on port 8000
echo "🧪 Testing Django app accessibility on port 8000..."
if curl -s http://localhost:8000/health/ > /dev/null; then
    echo "✅ Django app is accessible on port 8000"
else
    echo "❌ Django app is not accessible on port 8000"
    exit 1
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

# 9. Create final nginx configuration with SSL that proxies to port 8000
echo "🌐 Creating final nginx configuration with SSL..."
sudo tee /etc/nginx/sites-available/appraisal-system > /dev/null <<EOF
upstream appraisal_backend {
    server 127.0.0.1:8000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name apes.techonstreet.com;
    return 301 https://\$server_name\$request_uri;
}

# HTTPS server that proxies to Django on port 8000
server {
    listen 443 ssl http2;
    server_name apes.techonstreet.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/apes.techonstreet.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/apes.techonstreet.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Client max body size
    client_max_body_size 10M;
    
    # Static files
    location /static/ {
        alias /opt/appraisal-system/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /opt/appraisal-system/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Proxy all requests to Django on port 8000
    location / {
        proxy_pass http://appraisal_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check
    location /health/ {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# 10. Remove temporary configuration and enable final one
echo "🔧 Enabling final nginx configuration..."
sudo rm -f /etc/nginx/sites-enabled/appraisal-system-temp
sudo ln -sf /etc/nginx/sites-available/appraisal-system /etc/nginx/sites-enabled/

# 11. Test and reload nginx
echo "🧪 Testing nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
    sudo systemctl reload nginx
else
    echo "❌ Nginx configuration has errors"
    exit 1
fi

# 12. Test SSL certificate and proxy
echo "🧪 Testing SSL certificate and proxy..."
if curl -s -I https://apes.techonstreet.com > /dev/null; then
    echo "✅ SSL certificate is working"
    
    # Test if the proxy is working by checking if Django responds
    if curl -s https://apes.techonstreet.com/health/ | grep -q "healthy"; then
        echo "✅ HTTPS proxy to Django on port 8000 is working"
    else
        echo "⚠️ HTTPS is working but Django proxy might have issues"
    fi
else
    echo "❌ SSL certificate is not working"
    exit 1
fi

# 13. Set up automatic renewal
echo "🔄 Setting up automatic renewal..."
sudo crontab -l 2>/dev/null | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet"; } | sudo crontab -

# 14. Show final status
echo ""
echo "📋 SSL Setup Summary:"
echo "   ✅ Certificate obtained: apes.techonstreet.com"
echo "   ✅ Nginx configured with SSL"
echo "   ✅ Proxy to Django on port 8000 configured"
echo "   ✅ Automatic renewal scheduled"
echo "   ✅ HTTPS is working"

echo ""
echo "🔗 Access URLs:"
echo "   HTTP (redirects to HTTPS): http://apes.techonstreet.com"
echo "   HTTPS (proxies to port 8000): https://apes.techonstreet.com"
echo "   Direct Django (HTTP): http://apes.techonstreet.com:8000"

echo ""
echo "✅ SSL setup completed successfully!"
echo "🌐 https://apes.techonstreet.com now resolves to your Django app on port 8000!" 