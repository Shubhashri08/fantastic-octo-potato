import os, sys
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import os
import sys
import json
from sqlalchemy.orm import Session

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from app.database import SessionLocal
from app.models import Vehicle, VehicleSighting

def purge_ka_data():
    print("=================================================================")
    print("  PURGING ALL 'KA' (KARNATAKA) VEHICLE DATA FROM VIGRAH AI")
    print("=================================================================\n")

    db: Session = SessionLocal()

    # 1. Find all KA vehicle IDs in SQLite
    ka_vehicles = db.query(Vehicle).filter(
        (Vehicle.plate_number.ilike("KA%")) | (Vehicle.vehicle_id.ilike("VEH-00%"))
    ).all()
    ka_v_ids = [v.vehicle_id for v in ka_vehicles]

    print(f"Found {len(ka_vehicles)} 'KA' vehicle dossier(s) in SQLite database: {ka_v_ids}")

    # 2. Delete sightings associated with KA vehicles
    if ka_v_ids:
        deleted_sightings = db.query(VehicleSighting).filter(VehicleSighting.vehicle_id.in_(ka_v_ids)).delete(synchronize_session=False)
        print(f"✓ Deleted {deleted_sightings} associated sightings from 'vehicle_sightings' table.")

    # 3. Delete vehicles
    deleted_vehicles = db.query(Vehicle).filter(
        (Vehicle.plate_number.ilike("KA%")) | (Vehicle.vehicle_id.ilike("VEH-00%"))
    ).delete(synchronize_session=False)
    db.commit()
    print(f"✓ Deleted {deleted_vehicles} 'KA' vehicles from 'vehicles' table.")

    # 4. Clean reid_gallery_cache.json
    cache_path = os.path.join(BASE_DIR, "reid_gallery_cache.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            cache_data = json.load(f)

        initial_count = len(cache_data.get("vehicles", []))
        filtered_vehicles = [
            v for v in cache_data.get("vehicles", [])
            if not (v.get("plate", "").startswith("KA") or v.get("plate_number", "").startswith("KA") or v.get("vehicle_id", "").startswith("VEH-00"))
        ]
        cache_data["vehicles"] = filtered_vehicles
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)

        print(f"✓ Cleaned gallery cache: Removed {initial_count - len(filtered_vehicles)} 'KA' records. {len(filtered_vehicles)} active MH vehicles remaining.")

    # 5. List remaining vehicles in DB
    remaining = db.query(Vehicle).all()
    print("\n--- ACTIVE REGISTERED VEHICLES IN DATABASE ---")
    for r in remaining:
        print(f"  • [{r.vehicle_id}] {r.plate_number} | {r.vehicle_model} ({r.vehicle_color}) | {r.bolo_status}")

    db.close()
    print("\n✓ ALL 'KA' VEHICLE DATA SUCCESSFULLY PURGED!")

if __name__ == "__main__":
    purge_ka_data()
