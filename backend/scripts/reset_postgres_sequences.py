"""
Reset all PostgreSQL sequences after loaddata.
"""
import os
import sys
from io import StringIO
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.core.management import call_command
from django.db import connection
from django.apps import apps

app_labels = [app.label for app in apps.get_app_configs() if app.models_module is not None]

print("Resetting PostgreSQL sequences for apps:", app_labels)

sql_statements = []
for label in app_labels:
    out = StringIO()
    try:
        call_command('sqlsequencereset', label, stdout=out, no_color=True)
        sql = out.getvalue().strip()
        if sql:
            sql_statements.append((label, sql))
    except Exception as e:
        print(f"  Note for app {label}: {e}")

executed_count = 0
with connection.cursor() as cursor:
    for label, sql in sql_statements:
        print(f"\n--- App: {label} ---")
        for line in sql.splitlines():
            line_clean = line.strip()
            if line_clean and not line_clean.startswith('--'):
                cursor.execute(line_clean)
                print(f"  Executed: {line_clean[:80]}...")
                executed_count += 1

print(f"\nSuccessfully executed {executed_count} sequence reset statements.")
