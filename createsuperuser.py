#!/bin/python
from django.contrib.auth import get_user_model
from dotenv import load_dotenv
import os
import django


load_dotenv()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
django.setup()

User = get_user_model()

django_username = os.getenv("DJANGO_SUPERUSER_USERNAME")
email = os.getenv("DJANGO_SUPERUSER_EMAIL")
password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

if not User.objects.filter(username=django_username).exists():
    if django_username:
        User.objects.create_superuser(
            username=django_username,
            email=email,
            password=password
        )
    print("Superusuário criado.")
else:
    print("Superusuário já existe.")
