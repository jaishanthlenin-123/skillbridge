"""
Verify Django's active database engine and connection.
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.db import connection
from django.conf import settings

db_conf = settings.DATABASES['default']
print(f"Django DB Engine: {db_conf['ENGINE']}")
print(f"Django DB Name: {db_conf['NAME']}")
print(f"Django DB User: {db_conf.get('USER')}")
print(f"Django DB Host: {db_conf.get('HOST')}:{db_conf.get('PORT')}")

with connection.cursor() as cursor:
    cursor.execute("SELECT version();")
    row = cursor.fetchone()
    print("Database Version query result:")
    print(" ", row[0])
