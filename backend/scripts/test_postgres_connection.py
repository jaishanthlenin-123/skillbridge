"""
Test PostgreSQL connection using psycopg2.
"""
import psycopg2
import os

user = os.getenv('POSTGRES_USER', os.getenv('DB_USER', 'skillbridge_user'))
password = os.getenv('POSTGRES_PASSWORD', os.getenv('DB_PASSWORD', 'skillbridge_password'))
host = os.getenv('POSTGRES_HOST', os.getenv('DB_HOST', '127.0.0.1'))
port = int(os.getenv('POSTGRES_PORT', os.getenv('DB_PORT', '5432')))

for db in ['skillbridge', 'skillbridge_db', 'postgres']:
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=db,
            connect_timeout=3
        )
        print(f"Connected successfully to PostgreSQL database: '{db}'")
        cur = conn.cursor()
        cur.execute("SELECT version();")
        print("  Version:", cur.fetchone()[0])
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
        tables = cur.fetchall()
        print(f"  Existing public tables count: {len(tables)}")
        conn.close()
    except Exception as e:
        print(f"Failed to connect to '{db}': {e}")
