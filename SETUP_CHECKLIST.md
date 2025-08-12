# 🚀 Quick Setup Checklist

## Pre-Deployment Checklist

### ✅ GitHub Repository Setup

- [ ] Repository is public or GitHub Actions has access
- [ ] Code is pushed to `main` and `develop` branches
- [ ] SSH keys are set up for local → GitHub access

### ✅ AWS EC2 Setup

- [ ] EC2 instance launched (Ubuntu 22.04 LTS)
- [ ] Security group allows SSH (22), HTTP (80), HTTPS (443)
- [ ] SSH key pair downloaded and accessible
- [ ] Instance has at least 20GB storage

### ✅ Domain Setup (Optional)

- [ ] Domain name purchased
- [ ] DNS A record points to EC2 public IP
- [ ] Domain propagation completed (can take 24-48 hours)

## Deployment Steps

### 1. 🔑 SSH Key Setup for GitHub Actions

```bash
# On your local machine
ssh-keygen -t ed25519 -f ~/.ssh/github_actions_key -N ""
cat ~/.ssh/github_actions_key.pub
# Copy this to EC2 ~/.ssh/authorized_keys

cat ~/.ssh/github_actions_key
# Copy this to GitHub Secrets as EC2_SSH_KEY
```

### 2. 📝 GitHub Secrets Configuration

Add these to your GitHub repository → Settings → Secrets and variables → Actions:

- `STAGING_HOST`: Your staging EC2 IP
- `PRODUCTION_HOST`: Your production EC2 IP
- `EC2_USERNAME`: ubuntu
- `EC2_SSH_KEY`: Your private key content
- `EC2_PORT`: 22

### 3. 🖥️ EC2 Server Setup

```bash
# SSH to your EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Upload and run setup script
scp -i your-key.pem deployment/setup_server.sh ubuntu@your-ec2-ip:~/
ssh -i your-key.pem ubuntu@your-ec2-ip
chmod +x setup_server.sh
./setup_server.sh
```

### 4. ⚙️ Environment Configuration

Edit `.env` file on EC2 with your actual values:

- Database credentials (PostgreSQL on same EC2)
- Email settings
- CORS settings (allowing all origins)
- Secret key

### 5. 🔒 SSL Certificate (Optional)

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

## Post-Deployment Verification

### ✅ Service Status Check

```bash
sudo systemctl status appraisal-production
sudo systemctl status nginx
sudo systemctl status redis-server
sudo systemctl status celery
```

### ✅ Application Access

- [ ] Website loads at `http://your-domain.com` or `http://your-ec2-ip`
- [ ] Health check returns 200: `curl http://your-domain.com/health/`
- [ ] Admin panel accessible at `/admin/`

### ✅ CI/CD Pipeline Test

- [ ] Push to `develop` branch triggers staging deployment
- [ ] Push to `main` branch triggers production deployment
- [ ] Tests pass in GitHub Actions

## 🆘 Quick Troubleshooting

### Service Won't Start

```bash
sudo journalctl -u appraisal-production -n 50
sudo systemctl status appraisal-production
```

### Permission Issues

```bash
sudo chown -R ubuntu:ubuntu /opt/appraisal-system
```

### Database Issues

```bash
sudo -u postgres psql -c "SELECT version();"
python manage.py dbshell
```

### Static Files Not Loading

```bash
python manage.py collectstatic --noinput
sudo systemctl restart nginx
```

## 📞 Support Commands

### View Logs

```bash
# Application logs
sudo journalctl -u appraisal-production -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log

# Django logs
tail -f /opt/appraisal-system/logs/django.log
```

### Restart Services

```bash
sudo systemctl restart appraisal-production
sudo systemctl restart nginx
sudo systemctl restart celery
```

### Update Application

```bash
cd /opt/appraisal-system
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart appraisal-production
```

## 🎯 Success Indicators

- ✅ Website loads without errors
- ✅ Database migrations completed
- ✅ Static files served correctly
- ✅ Email functionality works
- ✅ Background tasks (Celery) running
- ✅ SSL certificate installed (if using domain)
- ✅ GitHub Actions pipeline successful
- ✅ Monitoring and logging working

## 📚 Next Steps

1. **Set up monitoring** (CloudWatch, New Relic, etc.)
2. **Configure backups** (database, files)
3. **Set up alerts** for service failures
4. **Performance optimization** (caching, CDN)
5. **Security hardening** (firewall rules, updates)
6. **Documentation** for team members
