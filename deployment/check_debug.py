#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appraisal.settings_production')
django.setup()

from django.conf import settings

print(f'DEBUG: {settings.DEBUG}')
print(f'ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}') 