import os, sys
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

db_url = os.getenv("DATABASE_URL")
print(f"Connecting to Neon DB Host: {db_url.split('@')[-1] if db_url and '@' in db_url else 'Unknown'}")

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # 1. Fetch all public tables
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    print(f"\n[OK] Found {len(tables)} tables in Neon DB:")
    
    if len(tables) == 0:
        print("  ℹ️ Database is currently clean/fresh with 0 tables (Ready for schema initialization).")
    else:
        for t in tables:
            t_name = t["table_name"]
            cur.execute(f'SELECT count(*) FROM "{t_name}";')
            count = cur.fetchone()["count"]
            print(f"  - Table: {t_name} | Total Rows: {count}")

            if count > 0:
                cur.execute(f'SELECT * FROM "{t_name}" LIMIT 3;')
                sample_rows = cur.fetchall()
                for r in sample_rows:
                    print(f"      • {dict(r)}")

    cur.close()
    conn.close()
    print("\n[SUCCESS] Neon DB connection tested successfully!")

except Exception as e:
    print(f"\n[ERROR] Failed to connect or query Neon DB: {e}")
