# Deployment Troubleshooting Guide

## Current Configuration Analysis

### URL Configuration

- **Domain**: `apes.techonstreet.com`
- **EC2 IP**: `13.60.12.244`
- **Port**: 8000 (Gunicorn) → 80/443 (Nginx)

## Potential Issues and Solutions

### 1. SSL Certificate Issues

**Problem**: The nginx configuration expects SSL certificates at `/etc/letsencrypt/live/apes.techonstreet.com/`

**Solution**:

```bash
# SSH into your EC2 instance and run:
sudo certbot --nginx -d apes.techonstreet.com
```

### 2. Environment Variables Not Set

**Problem**: The `.env` file might not be properly configured

**Solution**: Check and update your `.env` file:

```bash
# SSH into EC2 and check:
cd /opt/appraisal-system
cat .env

# Ensure these are properly set:
SECRET_KEY=your-actual-secret-key
DEBUG=False
ALLOWED_HOSTS=apes.techonstreet.com,13.60.12.244,localhost,127.0.0.1
```

### 3. Service Status Issues

**Check service status**:

```bash
# Check Django app status
sudo systemctl status appraisal-production

# Check Nginx status
sudo systemctl status nginx

# Check logs
sudo journalctl -u appraisal-production -f
sudo tail -f /var/log/nginx/error.log
```

### 4. Database Connection Issues

**Check database**:

```bash
# Test PostgreSQL connection
sudo -u postgres psql -d appraisal_db -c "SELECT 1;"

# Check if migrations are applied
cd /opt/appraisal-system
source venv/bin/activate
python manage.py showmigrations
```

### 5. Port and Firewall Issues

**Check ports**:

```bash
# Check if services are listening
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443

# Check firewall
sudo ufw status
```

### 6. DNS Configuration

**Problem**: Domain might not be pointing to the correct IP

**Solution**: Verify DNS settings point `apes.techonstreet.com` to `13.60.12.244`

## Quick Diagnostic Commands

Run these commands on your EC2 instance to diagnose the issue:

```bash
# 1. Check if the application is running
curl http://localhost:8000/health/

# 2. Check if nginx is serving
curl -I http://localhost

# 3. Check SSL certificate
sudo certbot certificates

# 4. Check application logs
tail -f /opt/appraisal-system/logs/django.log

# 5. Test database connection
cd /opt/appraisal-system
source venv/bin/activate
python manage.py check --deploy
```

## Common Fixes

### Fix 1: Restart All Services

```bash
sudo systemctl restart appraisal-production
sudo systemctl restart nginx
sudo systemctl restart redis-server
```

### Fix 2: Update ALLOWED_HOSTS

Add your domain to Django settings:

```python
# In settings_production.py or .env
ALLOWED_HOSTS = 'apes.techonstreet.com,13.60.12.244,localhost,127.0.0.1'
```

### Fix 3: Enable SSL Redirect

Uncomment these lines in `settings_production.py`:

```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### Fix 4: Check File Permissions

```bash
sudo chown -R ubuntu:ubuntu /opt/appraisal-system
sudo chmod -R 755 /opt/appraisal-system
```

## Emergency Access

If the site is completely down, you can temporarily access it via IP:

```bash
# Temporarily disable SSL redirect in nginx
sudo nano /etc/nginx/sites-available/appraisal-system
# Comment out the SSL redirect line
sudo systemctl reload nginx
```

## Monitoring Commands

```bash
# Monitor real-time logs
sudo journalctl -u appraisal-production -f &
sudo tail -f /var/log/nginx/access.log &
sudo tail -f /var/log/nginx/error.log &

# Check resource usage
htop
df -h
free -h
```

## Next Steps

1. SSH into your EC2 instance
2. Run the diagnostic commands above
3. Check the service status
4. Verify SSL certificate installation
5. Test the application locally on the server
6. Check DNS propagation

If you need immediate access, you can temporarily access the application via:

- `http://13.60.12.244` (if SSL is disabled)
- `http://13.60.12.244:8000` (direct to Gunicorn)
