"""
Inspect SQLite tables and record counts.
"""
import sqlite3
import json
from pathlib import Path

db_path = Path(__file__).resolve().parent.parent / 'db.sqlite3'
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
tables = [row[0] for row in cursor.fetchall()]

results = {}
for t in sorted(tables):
    cursor.execute(f'SELECT COUNT(*) FROM "{t}";')
    cnt = cursor.fetchone()[0]
    results[t] = cnt

conn.close()

print(f"Total tables in SQLite: {len(results)}")
print("\nTable record counts:")
for t, cnt in results.items():
    print(f"  {t}: {cnt}")

with open(db_path.parent / 'backups' / 'sqlite_counts_pre_migration.json', 'w') as f:
    json.dump(results, f, indent=2)
