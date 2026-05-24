# Quick Django API test
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from backend.models import UploadedImage
print(f"✅ Django models loaded successfully!")
print(f"Total images analyzed: {UploadedImage.objects.count()}")
