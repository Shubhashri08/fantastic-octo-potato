import os, sys
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import os
import sys
import json
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

db_url = os.getenv("DATABASE_URL")
print("=" * 80)
print("AUDITING NEON DB MIGRATION & INSERTION TIMESTAMPS")
print("=" * 80)

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    tables_to_check = [
        ("alerts", "created_at"),
        ("entities", "created_at"),
        ("entity_sightings", "created_at"),
        ("event_entity_mapping", "created_at"),
        ("cameras", "created_at"),
        ("events", "timestamp")
    ]

    for t_name, time_col in tables_to_check:
        try:
            cur.execute(f"""
                SELECT 
                    COUNT(*) as total_count,
                    MIN({time_col}) as earliest_timestamp,
                    MAX({time_col}) as latest_timestamp
                FROM "{t_name}";
            """)
            summary = cur.fetchone()
            print(f"\n📁 TABLE: [{t_name}] | Records: {summary['total_count']}")
            print(f"   🕒 Earliest Timestamp: {summary['earliest_timestamp']}")
            print(f"   🕒 Latest Timestamp:   {summary['latest_timestamp']}")

            # Fetch distinct timestamps and sample records
            cur.execute(f'SELECT * FROM "{t_name}" ORDER BY {time_col} DESC LIMIT 5;')
            rows = cur.fetchall()
            print("   🔍 Sample Records:")
            for r in rows:
                row_clean = {}
                for k, v in r.items():
                    if hasattr(v, "isoformat"):
                        row_clean[k] = v.isoformat()
                    else:
                        row_clean[k] = v
                print(f"      • {json.dumps(row_clean)}")

        except Exception as e:
            print(f"   ❌ Error checking {t_name}: {e}")

    cur.close()
    conn.close()
    print("\n" + "=" * 80)
    print("MIGRATION AUDIT COMPLETED")
    print("=" * 80)

except Exception as e:
    print(f"Failed to connect to database: {e}")
