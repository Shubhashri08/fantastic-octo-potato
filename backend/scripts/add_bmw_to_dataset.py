import os, sys
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import os
import sys
import json
import datetime
from sqlalchemy.orm import Session

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from app.database import SessionLocal
from app.models import Vehicle, VehicleSighting

def add_bmw_to_dataset():
    db: Session = SessionLocal()
    try:
        vehicle_id = "VEH-MH46CT5126"
        existing = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()

        now = datetime.datetime.now()

        if not existing:
            new_veh = Vehicle(
                vehicle_id=vehicle_id,
                plate_number="MH 46 CT 5126",
                vehicle_type="Car (Sedan)",
                vehicle_model="BMW 2 Series Gran Coupe",
                vehicle_color="Blue",
                snapshot="/snapshots/bmw_mh46ct5126.jpg",
                is_stolen=False,
                plate_confidence=0.98,
                bolo_status="NORMAL: Verified Vehicle Registry",
                created_at=now - datetime.timedelta(hours=2)
            )
            db.add(new_veh)
            db.commit()
            print(f"✓ Added Vehicle {vehicle_id} (MH 46 CT 5126) to database.")
        else:
            existing.snapshot = "/snapshots/bmw_mh46ct5126.jpg"
            existing.vehicle_color = "Blue"
            existing.vehicle_model = "BMW 2 Series Gran Coupe"
            existing.plate_number = "MH 46 CT 5126"
            db.commit()
            print(f"✓ Updated Vehicle {vehicle_id} (MH 46 CT 5126) in database.")

        # Add Sightings
        sightings_to_add = [
            VehicleSighting(
                vehicle_id=vehicle_id,
                camera_id="CAM-01",
                camera_name="CAM-01 Mumbai Western Coastal Corridor",
                location="Mumbai Western Coastal Corridor",
                city="Mumbai",
                latitude=19.0440,
                longitude=72.8258,
                speed_kmh=54.5,
                timestamp=now - datetime.timedelta(minutes=15),
                evidence_image="/snapshots/bmw_mh46ct5126.jpg"
            ),
            VehicleSighting(
                vehicle_id=vehicle_id,
                camera_id="CAM-03",
                camera_name="CAM-03 Bandra-Worli Sea Link Toll",
                location="Bandra-Worli Sea Link Toll Plaza",
                city="Mumbai",
                latitude=19.0410,
                longitude=72.8220,
                speed_kmh=62.0,
                timestamp=now - datetime.timedelta(minutes=8),
                evidence_image="/snapshots/bmw_mh46ct5126.jpg"
            )
        ]

        for s in sightings_to_add:
            existing_s = db.query(VehicleSighting).filter(
                VehicleSighting.vehicle_id == vehicle_id,
                VehicleSighting.camera_id == s.camera_id
            ).first()
            if not existing_s:
                db.add(s)
        db.commit()
        print(f"✓ Added sighting checkpoints for {vehicle_id}.")

        # Also update reid_gallery_cache.json
        cache_path = os.path.join(BASE_DIR, "reid_gallery_cache.json")
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            
            vehicles_list = cache_data.get("vehicles", [])
            found = False
            for v in vehicles_list:
                if v.get("vehicle_id") == vehicle_id or "MH46CT5126" in v.get("plate", "").replace(" ", ""):
                    found = True
                    break
            
            if not found:
                vehicles_list.insert(0, {
                    "vehicle_id": vehicle_id,
                    "plate": "MH 46 CT 5126",
                    "type": "Car (Sedan)",
                    "model": "BMW 2 Series Gran Coupe",
                    "color": "Blue",
                    "snapshot": "/snapshots/bmw_mh46ct5126.jpg",
                    "is_stolen": False,
                    "location": "Mumbai Western Coastal Corridor",
                    "camera_id": "CAM-01",
                    "speed_kmh": 54.5
                })
                cache_data["vehicles"] = vehicles_list
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(cache_data, f, indent=2)
                print("✓ Added BMW record to reid_gallery_cache.json.")

    finally:
        db.close()

if __name__ == "__main__":
    add_bmw_to_dataset()
