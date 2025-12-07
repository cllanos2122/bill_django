# initialize.py
import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bill.settings')
django.setup()

User = get_user_model()

if not User.objects.filter(username=os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')).exists():
    User.objects.create_superuser(
        username=os.getenv('DJANGO_SUPERUSER_USERNAME'),
        email=os.getenv('DJANGO_SUPERUSER_EMAIL'),
        password=os.getenv('DJANGO_SUPERUSER_PASSWORD')
    )
    print("✅ Superusuario creado.")
else:
    print("ℹ️ Ya existe un superusuario.")
