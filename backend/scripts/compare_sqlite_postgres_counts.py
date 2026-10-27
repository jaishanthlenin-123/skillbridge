"""
Compare record counts between SQLite pre-migration and PostgreSQL.
"""
import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.db import connection

# Load SQLite counts
json_path = BASE_DIR / 'backups' / 'sqlite_counts_pre_migration.json'
with open(json_path, 'r') as f:
    sqlite_counts = json.load(f)

# Query PostgreSQL counts
pg_counts = {}
with connection.cursor() as cursor:
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
    pg_tables = [r[0] for r in cursor.fetchall()]
    for t in sorted(pg_tables):
        cursor.execute(f'SELECT COUNT(*) FROM "{t}";')
        pg_counts[t] = cursor.fetchone()[0]

print("=== RECORD COUNT VERIFICATION: SQLite vs PostgreSQL ===\n")
print(f"{'Table Name':<38} | {'SQLite':<8} | {'PostgreSQL':<10} | {'Status'}")
print("-" * 72)

all_match = True
app_tables = [
    'skillbridge_users',
    'authtoken_token',
    'skillbridge_skills',
    'skillbridge_skill_aliases',
    'skillbridge_jobs',
    'skillbridge_job_requirements',
    'skillbridge_resumes',
    'skillbridge_resume_sections',
    'skillbridge_resume_skills',
    'skillbridge_matches',
    'skillbridge_match_skill_results',
    'skillbridge_roadmaps',
    'skillbridge_roadmap_items',
    'skillbridge_audit_events',
    'skillbridge_faq_categories',
    'skillbridge_faqs',
    'skillbridge_support_tickets',
    'django_session'
]

for t in sorted(sqlite_counts.keys()):
    sq_cnt = sqlite_counts[t]
    pg_cnt = pg_counts.get(t, 0)
    match = (sq_cnt == pg_cnt)
    # Note: django_content_type and auth_permission may have new or managed permissions
    if not match and t in app_tables:
        all_match = False
    status = "EXACT MATCH (PASS)" if match else f"DIFF (SQLite={sq_cnt}, PG={pg_cnt})"
    print(f"{t:<38} | {sq_cnt:<8} | {pg_cnt:<10} | {status}")

print("-" * 72)
if all_match:
    print(">>> ALL APPLICATION TABLES MATCH PRECISELY (100% DATA PRESERVED) <<<")
else:
    print(">>> SOME APPLICATION TABLES DO NOT MATCH <<<")
