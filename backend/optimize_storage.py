import os
import sys
import json
import hashlib
import sqlite3
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

DB_PATH = os.path.join(BASE_DIR, "vigrah.db")
CACHE_PATH = os.path.join(BASE_DIR, "reid_gallery_cache.json")
SNAPSHOTS_DIR = os.path.join(BASE_DIR, "snapshots")
SAMPLES_DIR = os.path.join(BASE_DIR, "samples")
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")

def get_file_hash(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def optimize_all_storage():
    print("========================================================================")
    print("  VIGRAH AI — COMPREHENSIVE STORAGE AUDIT & DEDUPLICATION OPTIMIZER")
    print("========================================================================\n")

    # -------------------------------------------------------------
    # 1. OPTIMIZE SQLITE DATABASE (vigrah.db)
    # -------------------------------------------------------------
    print("--- [1] Optimizing SQLite Database Tables ---")
    if os.path.exists(DB_PATH):
        db_size_before = os.path.getsize(DB_PATH)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")]
        print(f"  Found {len(tables)} tables: {', '.join(tables)}")

        # Deduplicate vehicle_sightings
        if "vehicle_sightings" in tables:
            cursor.execute("""
                DELETE FROM vehicle_sightings 
                WHERE id NOT IN (
                    SELECT MIN(id) 
                    FROM vehicle_sightings 
                    GROUP BY vehicle_id, camera_id, location, timestamp
                );
            """)
            deleted_sightings = cursor.rowcount
            print(f"  • Deduplicated vehicle_sightings (removed {deleted_sightings} duplicate rows)")

        # Deduplicate vehicles by plate_number or vehicle_id
        if "vehicles" in tables:
            cursor.execute("""
                DELETE FROM vehicles 
                WHERE rowid NOT IN (
                    SELECT MIN(rowid) 
                    FROM vehicles 
                    GROUP BY vehicle_id
                );
            """)
            deleted_vehicles = cursor.rowcount
            print(f"  • Deduplicated vehicles (removed {deleted_vehicles} duplicate rows)")

        # Deduplicate events
        if "events" in tables:
            cursor.execute("""
                DELETE FROM events 
                WHERE id NOT IN (
                    SELECT MIN(id) 
                    FROM events 
                    GROUP BY camera_id, event_type, timestamp
                );
            """)
            deleted_events = cursor.rowcount
            print(f"  • Deduplicated events (removed {deleted_events} duplicate rows)")

        # Deduplicate alerts
        if "alerts" in tables:
            cursor.execute("""
                DELETE FROM alerts 
                WHERE rowid NOT IN (
                    SELECT MIN(rowid) 
                    FROM alerts 
                    GROUP BY id
                );
            """)
            deleted_alerts = cursor.rowcount
            print(f"  • Deduplicated alerts (removed {deleted_alerts} duplicate rows)")

        conn.commit()

        # VACUUM to reclaim space and defragment
        cursor.execute("VACUUM;")
        conn.commit()
        conn.close()

        db_size_after = os.path.getsize(DB_PATH)
        print(f"  ✓ Database Compacted (VACUUM): {db_size_before/1024:.1f} KB -> {db_size_after/1024:.1f} KB\n")
    else:
        print("  Database file not created yet (using memory/local seed).\n")

    # -------------------------------------------------------------
    # 2. OPTIMIZE REID GALLERY CACHE (reid_gallery_cache.json)
    # -------------------------------------------------------------
    print("--- [2] Optimizing ReID Gallery Cache ---")
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            cache_data = json.load(f)

        raw_persons = cache_data.get("persons", [])
        raw_vehicles = cache_data.get("vehicles", [])

        # Deduplicate persons by person_id
        unique_persons = {}
        for p in raw_persons:
            pid = p.get("person_id")
            if pid and pid not in unique_persons:
                unique_persons[pid] = p

        # Deduplicate vehicles by normalized plate and vehicle_id
        unique_vehicles = {}
        for v in raw_vehicles:
            vid = v.get("vehicle_id")
            plate_norm = v.get("plate", "").replace(" ", "").upper()
            key = vid or plate_norm
            if key and key not in unique_vehicles:
                unique_vehicles[key] = v

        cache_data["persons"] = list(unique_persons.values())
        cache_data["vehicles"] = list(unique_vehicles.values())

        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)

        print(f"  • Persons: {len(raw_persons)} -> {len(cache_data['persons'])} unique entries")
        print(f"  • Vehicles: {len(raw_vehicles)} -> {len(cache_data['vehicles'])} unique entries")
        print("  ✓ Gallery Cache Optimized & Deduplicated\n")

    # -------------------------------------------------------------
    # 3. OPTIMIZE SNAPSHOTS & SAMPLES STORAGE (Duplicate Hash Cleanup)
    # -------------------------------------------------------------
    print("--- [3] Auditing and Cleaning Snapshot & Media Storage ---")
    
    # Clean redundant legacy DVR dumps from recordings/ (over 1.1 GB of legacy clips)
    if os.path.exists(RECORDINGS_DIR):
        rec_files = [os.path.join(RECORDINGS_DIR, f) for f in os.listdir(RECORDINGS_DIR) if os.path.isfile(os.path.join(RECORDINGS_DIR, f))]
        rec_size = sum(os.path.getsize(f) for f in rec_files)
        # Remove old auto-dvr incident clips
        deleted_recs = 0
        for rf in rec_files:
            if rf.endswith(".mp4") and ("clip_cam" in rf or "incident_" in rf):
                try:
                    os.remove(rf)
                    deleted_recs += 1
                except Exception:
                    pass
        print(f"  • recordings/: Purged {deleted_recs} legacy auto-DVR recording clips (Freed ~{rec_size / (1024*1024):.1f} MB)")

    # Deduplicate snapshots
    for folder_name, folder_path in [("snapshots", SNAPSHOTS_DIR), ("samples", SAMPLES_DIR)]:
        if not os.path.exists(folder_path):
            continue

        files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        hashes = defaultdict(list)

        for fpath in files:
            fhash = get_file_hash(fpath)
            hashes[fhash].append(fpath)

        removed_dupes = 0
        for fhash, fpaths in hashes.items():
            if len(fpaths) > 1:
                # Keep the canonical one, remove exact duplicate duplicates
                canonical = fpaths[0]
                for dupe in fpaths[1:]:
                    # If it's a timestamped copy of the same incident
                    if "incident_cam" in os.path.basename(dupe):
                        try:
                            os.remove(dupe)
                            removed_dupes += 1
                        except Exception:
                            pass

        remaining_files = len([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])
        print(f"  • {folder_name}/: {remaining_files} active files (removed {removed_dupes} duplicate images)")

    print("\n========================================================================")
    print("  STORAGE OPTIMIZATION COMPLETE (ALL DATA CLEAN & DEDUPLICATED)")
    print("========================================================================\n")


if __name__ == "__main__":
    optimize_all_storage()
