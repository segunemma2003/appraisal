# Deployment Guide for api.techonstreet.com

This guide will help you deploy your appraisal system to your EC2 instance at `13.60.12.244` with the domain `api.techonstreet.com`.

## Prerequisites

1. **EC2 Instance**: Running Ubuntu at `13.60.12.244`
2. **Domain**: `api.techonstreet.com` pointing to your EC2 IP
3. **GitHub Repository**: With the appraisal system code
4. **SSH Access**: To your EC2 instance

## Step 1: Set up GitHub Secrets

Add these secrets to your GitHub repository (Settings > Secrets and variables > Actions):

- `EC2_USERNAME`: Your EC2 username (usually `ubuntu`)
- `EC2_SSH_KEY`: Your private SSH key for EC2 access
- `EC2_PORT`: SSH port (usually `22`)

## Step 2: Initial Server Setup

SSH into your EC2 instance and run the setup script:

```bash
ssh ubuntu@13.60.12.244
cd /opt/appraisal-system
sudo chmod +x deployment/setup_server.sh
./deployment/setup_server.sh
```

## Step 3: Configure Environment Variables

Create and edit the `.env` file:

```bash
cd /opt/appraisal-system
cp deployment/env_template.txt .env
nano .env
```

Add these essential variables:

```env
SECRET_KEY=your-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,api.techonstreet.com,13.60.12.244
DB_NAME=appraisal_db
DB_USER=appraisal_user
DB_PASSWORD=your-secure-db-password
DB_HOST=localhost
DB_PORT=5432
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## Step 4: Set up SSL Certificate

Run the SSL setup script:

```bash
cd /opt/appraisal-system
sudo chmod +x deployment/setup_ssl.sh
./deployment/setup_ssl.sh
```

**Important**: Update the email address in the script before running it.

## Step 5: Configure Domain DNS

Ensure your domain `api.techonstreet.com` points to your EC2 IP `13.60.12.244`:

- Add an A record: `api.techonstreet.com` → `13.60.12.244`
- Wait for DNS propagation (can take up to 48 hours)

## Step 6: Test the Pipeline

1. Push changes to the `main` branch to trigger production deployment
2. Push changes to the `develop` branch to trigger staging deployment
3. Monitor the GitHub Actions workflow

## Step 7: Verify Deployment

Check if everything is working:

```bash
# Check service status
sudo systemctl status appraisal-production
sudo systemctl status nginx

# Check logs
sudo journalctl -u appraisal-production -f
sudo tail -f /var/log/nginx/error.log

# Test the API
curl https://api.techonstreet.com/health/
```

## Troubleshooting

### Common Issues

1. **SSL Certificate Issues**:

   ```bash
   sudo certbot certificates
   sudo certbot renew --dry-run
   ```

2. **Nginx Configuration**:

   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

3. **Django Application**:

   ```bash
   cd /opt/appraisal-system
   source venv/bin/activate
   python manage.py check --deploy
   ```

4. **Database Issues**:
   ```bash
   sudo systemctl status postgresql
   sudo -u postgres psql -c "\l"
   ```

### Log Locations

- Django logs: `/opt/appraisal-system/logs/django.log`
- Nginx logs: `/var/log/nginx/`
- System logs: `sudo journalctl -u appraisal-production`

## Security Checklist

- [ ] Firewall configured (UFW)
- [ ] SSL certificate installed
- [ ] Database password is secure
- [ ] Django secret key is secure
- [ ] DEBUG=False in production
- [ ] Allowed hosts configured
- [ ] CORS settings configured

## Monitoring

Set up monitoring for your application:

```bash
# Monitor system resources
htop
df -h
free -h

# Monitor application logs
tail -f /opt/appraisal-system/logs/django.log
sudo journalctl -u appraisal-production -f
```

## Backup Strategy

Set up regular backups:

```bash
# Database backup
pg_dump appraisal_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Application backup
tar -czf app_backup_$(date +%Y%m%d_%H%M%S).tar.gz /opt/appraisal-system
```

Your application should now be accessible at `https://api.techonstreet.com`!
