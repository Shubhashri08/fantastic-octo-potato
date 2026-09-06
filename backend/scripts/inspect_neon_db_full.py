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
print(f"CONNECTING TO NEON POSTGRESQL DATABASE: {db_url.split('@')[-1] if db_url and '@' in db_url else 'Unknown'}")
print("=" * 80)

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
    tables = [t["table_name"] for t in cur.fetchall()]
    print(f"\n[OK] Found {len(tables)} Public Tables in Neon DB:\n")

    for t_name in tables:
        # Ignore PostGIS internal spatial reference table for brevity unless requested
        if t_name == "spatial_ref_sys":
            cur.execute('SELECT count(*) FROM "spatial_ref_sys";')
            cnt = cur.fetchone()["count"]
            print(f"📊 Table: [spatial_ref_sys] (PostGIS Spatial Coordinate Reference Registry)")
            print(f"   Total Pre-Loaded EPSG Coordinate Systems: {cnt:,} rows\n")
            continue

        # Get Column Metadata
        cur.execute(f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = '{t_name}'
            ORDER BY ordinal_position;
        """)
        cols = cur.fetchall()
        col_summary = ", ".join([f"{c['column_name']} ({c['data_type']})" for c in cols])

        # Get Row Count
        cur.execute(f'SELECT count(*) FROM "{t_name}";')
        count = cur.fetchone()["count"]

        print(f"📋 Table: [{t_name}] | Total Records: {count}")
        print(f"   Schema Columns: {col_summary}")

        if count > 0:
            cur.execute(f'SELECT * FROM "{t_name}" ORDER BY 1 LIMIT 50;')
            rows = cur.fetchall()
            print(f"   Data Contents ({len(rows)} rows):")
            for r_idx, r in enumerate(rows, 1):
                # Format datetimes to strings
                formatted_row = {}
                for k, v in r.items():
                    if hasattr(v, "isoformat"):
                        formatted_row[k] = v.isoformat()
                    else:
                        formatted_row[k] = v
                print(f"     [{r_idx}] {json.dumps(formatted_row, indent=6)}")
        else:
            print("   ℹ️ Table is currently empty (0 records).")
        print("-" * 80)

    cur.close()
    conn.close()
    print("\n[SUCCESS] Neon DB query completed successfully!")

except Exception as e:
    print(f"\n[ERROR] Failed to query Neon DB: {e}")
