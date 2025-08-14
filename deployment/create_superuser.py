#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appraisal.settings_production')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@apes.techonstreet.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists') 