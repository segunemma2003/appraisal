# Appraisal System Deployment Guide

This guide will help you deploy the Django Appraisal System to EC2 instances with a complete CI/CD pipeline.

## 🏗️ Architecture Overview

```
GitHub Repository
       ↓
GitHub Actions (CI/CD)
       ↓
EC2 Instance (Ubuntu) - All Services on Same Instance
├── Nginx (Reverse Proxy)
├── Gunicorn (WSGI Server)
├── Django Application
├── PostgreSQL (Database - Local)
├── Redis (Cache/Queue - Local)
└── Celery (Background Tasks)
```

## 📋 Prerequisites

1. **AWS Account** with EC2 access
2. **Domain Name** (optional, for SSL)
3. **GitHub Repository** with your code
4. **SSH Key Pair** for EC2 access

## 🚀 Step-by-Step Deployment

### 1. Set Up EC2 Instance

1. **Launch EC2 Instance:**

   - AMI: Ubuntu 22.04 LTS
   - Instance Type: t3.medium (minimum)
   - Storage: 20GB GP3
   - Security Group: Allow SSH (22), HTTP (80), HTTPS (443)

2. **Connect to Instance:**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-public-ip
   ```

### 2. Set Up SSH Keys for GitHub Actions

1. **Generate SSH Key for GitHub Actions:**

   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/github_actions_key -N ""
   ```

2. **Add Public Key to EC2:**

   ```bash
   cat ~/.ssh/github_actions_key.pub
   # Copy this to ~/.ssh/authorized_keys on your EC2 instance
   ```

3. **Add Private Key to GitHub Secrets:**
   - Go to your GitHub repository → Settings → Secrets and variables → Actions
   - Create secret: `EC2_SSH_KEY`
   - Value: Content of `~/.ssh/github_actions_key`

### 3. Configure GitHub Secrets

Add these secrets to your GitHub repository:

```
STAGING_HOST=your-staging-ec2-ip
PRODUCTION_HOST=your-production-ec2-ip
EC2_USERNAME=ubuntu
EC2_SSH_KEY=your-private-key-content
EC2_PORT=22
```

### 4. Run Server Setup Script

1. **Upload setup script to EC2:**

   ```bash
   scp -i your-key.pem deployment/setup_server.sh ubuntu@your-ec2-ip:~/
   ```

2. **Run the script:**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   chmod +x setup_server.sh
   ./setup_server.sh
   ```

### 5. Configure Environment Variables

Edit the `.env` file on your EC2 instance:

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=*,localhost,127.0.0.1

# Database Settings (PostgreSQL on same EC2)
DB_NAME=appraisal_db
DB_USER=appraisal_user
DB_PASSWORD=your-secure-password
DB_HOST=localhost
DB_PORT=5432

# Redis Settings (Redis on same EC2)
REDIS_URL=redis://localhost:6379/0

# Email Settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# CORS Settings (Allow all origins)
CORS_ALLOWED_ORIGINS=*
CORS_ALLOW_ALL_ORIGINS=True
```

### 6. Set Up Domain and SSL (Optional)

1. **Point domain to EC2 IP:**

   - Add A record: `your-domain.com` → `your-ec2-ip`

2. **Install SSL certificate:**
   ```bash
   sudo certbot --nginx -d your-domain.com -d www.your-domain.com
   ```

### 7. Test Deployment

1. **Check services:**

   ```bash
   sudo systemctl status appraisal-production
   sudo systemctl status nginx
   sudo systemctl status redis-server
   sudo systemctl status celery
   ```

2. **Test application:**
   - Visit: `http://your-domain.com` or `http://your-ec2-ip`
   - Health check: `http://your-domain.com/health/`

## 🔄 CI/CD Pipeline

The GitHub Actions workflow will:

1. **Test:** Run tests on every push/PR
2. **Deploy Staging:** Deploy to staging on `develop` branch
3. **Deploy Production:** Deploy to production on `main` branch

### Manual Deployment

```bash
# SSH to your EC2 instance
ssh ubuntu@your-ec2-ip

# Navigate to app directory
cd /opt/appraisal-system

# Pull latest changes
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart services
sudo systemctl restart appraisal-production
sudo systemctl restart celery
```

## 📊 Monitoring and Logs

### View Logs

```bash
# Application logs
sudo journalctl -u appraisal-production -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Celery logs
sudo journalctl -u celery -f

# Django logs
tail -f /opt/appraisal-system/logs/django.log
```

### Health Checks

```bash
# Check application health
curl http://your-domain.com/health/

# Check database connection
python manage.py dbshell

# Check Redis connection
redis-cli ping
```

## 🔧 Troubleshooting

### Common Issues

1. **Permission Denied:**

   ```bash
   sudo chown -R ubuntu:ubuntu /opt/appraisal-system
   ```

2. **Database Connection Error:**

   ```bash
   sudo -u postgres psql -c "ALTER USER appraisal_user PASSWORD 'new-password';"
   ```

3. **Static Files Not Loading:**

   ```bash
   python manage.py collectstatic --noinput
   sudo systemctl restart nginx
   ```

4. **Service Won't Start:**
   ```bash
   sudo systemctl status appraisal-production
   sudo journalctl -u appraisal-production -n 50
   ```

### Performance Optimization

1. **Enable Gzip compression in Nginx**
2. **Set up Redis caching**
3. **Configure database connection pooling**
4. **Enable CDN for static files**

## 🔒 Security Checklist

- [ ] Change default SSH port
- [ ] Disable password authentication
- [ ] Set up firewall rules
- [ ] Enable SSL/TLS
- [ ] Regular security updates
- [ ] Database backups
- [ ] Monitor logs for suspicious activity

## 📈 Scaling

### Horizontal Scaling

- Use multiple EC2 instances behind a load balancer
- Set up database replication
- Use Redis cluster for caching

### Vertical Scaling

- Increase EC2 instance size
- Optimize database queries
- Add more workers to Celery

## 🆘 Support

For issues or questions:

1. Check the logs first
2. Review this documentation
3. Check Django and system documentation
4. Create an issue in the repository
