import os, sys
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import os
import sys
import shutil
import cv2
import json
import datetime
from sqlalchemy.orm import Session

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from app.database import SessionLocal, Base, engine
from app.models import Vehicle, VehicleSighting

BRAIN_UPLOAD_DIR = "/Users/shubhashri/.gemini/antigravity-ide/brain/4c6a0947-c097-4508-9a4e-f307e99fa123/.user_uploaded"
SNAPSHOTS_DIR = os.path.join(BASE_DIR, "snapshots")
FRONTEND_SNAPSHOTS_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend", "public", "snapshots")
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
os.makedirs(FRONTEND_SNAPSHOTS_DIR, exist_ok=True)

# Image mapping from user uploaded files:
# media_1788415003225.jpg -> Image 1: Green Mahindra Thar (MH 46 CB 0005)
# media_1788415003338.jpg -> Image 2: Tata Punch (MH 43 CG 3824) + Honda City (MH 03 BK 8453)
# media_1788415003378.jpg -> Image 3: Auto-rickshaw on road
# media_1788415003399.jpg -> Image 4: Toyota Innova Crysta (MH 46 BK 0500) + Auto (MH 43 BF 3945)
# media_1788415003406.jpg -> Image 5: Green Sports Bike (MH 04 KY 5983)

UPLOADED_VEHICLES = [
    {
        "vehicle_id": "VEH-MH46CB0005",
        "plate_number": "MH 46 CB 0005",
        "vehicle_type": "Car (SUV)",
        "vehicle_model": "Mahindra Thar 4x4 SUV",
        "vehicle_color": "Green",
        "is_stolen": False,
        "bolo_status": "NORMAL: Verified Vehicle Registry",
        "source_image": "media_1788415003225.jpg",
        "snapshot_filename": "mahindra_thar_mh46cb0005.jpg",
        "crop_box": None,  # Full / Main vehicle
        "city": "Mumbai Safe City Grid",
        "location": "Navi Mumbai Rangoli Junction / Khandeshwar",
        "camera_id": "CAM-MUM-01",
        "camera_name": "CAM-01 Rangoli Intersection Intercept",
        "lat": 19.0125,
        "lon": 73.0880,
        "speed_kmh": 38.0
    },
    {
        "vehicle_id": "VEH-MH43CG3824",
        "plate_number": "MH 43 CG 3824",
        "vehicle_type": "Car (SUV)",
        "vehicle_model": "Tata Punch Compact SUV",
        "vehicle_color": "Blue",
        "is_stolen": False,
        "bolo_status": "NORMAL: Verified Vehicle Registry",
        "source_image": "media_1788415003338.jpg",
        "snapshot_filename": "tata_punch_mh43cg3824.jpg",
        "crop_box": (0, 0.35, 0.65, 0.95),  # (ymin, xmin, ymax, xmax) relative
        "city": "Mumbai Safe City Grid",
        "location": "Navi Mumbai Kharghar Sector 12",
        "camera_id": "CAM-MUM-02",
        "camera_name": "CAM-02 Kharghar Municipal Corridor",
        "lat": 19.0345,
        "lon": 73.0645,
        "speed_kmh": 32.5
    },
    {
        "vehicle_id": "VEH-MH03BK8453",
        "plate_number": "MH 03 BK 8453",
        "vehicle_type": "Car (Sedan)",
        "vehicle_model": "Honda City VTEC Sedan",
        "vehicle_color": "Black",
        "is_stolen": False,
        "bolo_status": "NORMAL: Verified Vehicle Registry",
        "source_image": "media_1788415003338.jpg",
        "snapshot_filename": "honda_city_mh03bk8453.jpg",
        "crop_box": (0.40, 0.55, 0.70, 0.85),  # (ymin, xmin, ymax, xmax) relative
        "city": "Mumbai Safe City Grid",
        "location": "Navi Mumbai Kharghar Arterial Corridor",
        "camera_id": "CAM-MUM-03",
        "camera_name": "CAM-03 Kharghar Arterial Gantry",
        "lat": 19.0380,
        "lon": 73.0690,
        "speed_kmh": 42.0
    },
    {
        "vehicle_id": "VEH-MH46BK0500",
        "plate_number": "MH 46 BK 0500",
        "vehicle_type": "Car (MPV)",
        "vehicle_model": "Toyota Innova Crysta MPV",
        "vehicle_color": "Maroon",
        "is_stolen": False,
        "bolo_status": "NORMAL: Verified Vehicle Registry",
        "source_image": "media_1788415003399.jpg",
        "snapshot_filename": "toyota_innova_mh46bk0500.jpg",
        "crop_box": (0.40, 0.50, 0.72, 0.82),  # (ymin, xmin, ymax, xmax)
        "city": "Mumbai Safe City Grid",
        "location": "Mumbai Western Expressway / Coastal Access",
        "camera_id": "CAM-MUM-04",
        "camera_name": "CAM-04 Western Expressway Intercept",
        "lat": 19.0657,
        "lon": 72.8683,
        "speed_kmh": 50.0
    },
    {
        "vehicle_id": "VEH-MH43BF3945",
        "plate_number": "MH 43 BF 3945",
        "vehicle_type": "Auto-Rickshaw (3-Wheeler)",
        "vehicle_model": "Bajaj RE Auto-Rickshaw",
        "vehicle_color": "Yellow",
        "is_stolen": False,
        "bolo_status": "NORMAL: Verified Vehicle Registry",
        "source_image": "media_1788415003399.jpg",
        "snapshot_filename": "autorickshaw_mh43bf3945.jpg",
        "crop_box": (0.40, 0.05, 0.78, 0.45),  # (ymin, xmin, ymax, xmax)
        "city": "Mumbai Safe City Grid",
        "location": "Navi Mumbai Urban Crossing Auto Stand",
        "camera_id": "CAM-MUM-05",
        "camera_name": "CAM-05 Urban Crossing Auto Stand",
        "lat": 19.0410,
        "lon": 73.0610,
        "speed_kmh": 24.0
    },
    {
        "vehicle_id": "VEH-MH04KY5983",
        "plate_number": "MH 04 KY 5983",
        "vehicle_type": "Motorcycle (Sports)",
        "vehicle_model": "Sports Motorcycle (Kawasaki / Dominar)",
        "vehicle_color": "Green",
        "is_stolen": False,
        "bolo_status": "NORMAL: Verified Vehicle Registry",
        "source_image": "media_1788415003406.jpg",
        "snapshot_filename": "sports_bike_mh04ky5983.jpg",
        "crop_box": None,  # Full image with green sports bike in foreground
        "city": "Mumbai Safe City Grid",
        "location": "Thane West Central Parking Bay / Transit Hub",
        "camera_id": "CAM-MUM-06",
        "camera_name": "CAM-06 Thane West Central Parking Hub",
        "lat": 19.1982,
        "lon": 72.9630,
        "speed_kmh": 45.0
    }
]

def process_and_register_all():
    print("========================================================================")
    print("  PROCESSING & REGISTERING USER UPLOADED VEHICLES INTO VIGRAH AI DATASET")
    print("========================================================================\n")

    db: Session = SessionLocal()
    now = datetime.datetime.now()

    cache_path = os.path.join(BASE_DIR, "reid_gallery_cache.json")
    cache_data = {"persons": [], "vehicles": []}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
        except Exception as e:
            print(f"Error reading cache: {e}")

    existing_v_ids = {v.get("vehicle_id") for v in cache_data.get("vehicles", [])}

    for v_info in UPLOADED_VEHICLES:
        src_path = os.path.join(BRAIN_UPLOAD_DIR, v_info["source_image"])
        out_backend_path = os.path.join(SNAPSHOTS_DIR, v_info["snapshot_filename"])
        out_frontend_path = os.path.join(FRONTEND_SNAPSHOTS_DIR, v_info["snapshot_filename"])

        if os.path.exists(src_path):
            img = cv2.imread(src_path)
            if img is not None:
                h, w = img.shape[:2]
                if v_info["crop_box"]:
                    ymin, xmin, ymax, xmax = v_info["crop_box"]
                    y1 = max(0, int(ymin * h))
                    y2 = min(h, int(ymax * h))
                    x1 = max(0, int(xmin * w))
                    x2 = min(w, int(xmax * w))
                    cropped = img[y1:y2, x1:x2]
                    cv2.imwrite(out_backend_path, cropped)
                    cv2.imwrite(out_frontend_path, cropped)
                    print(f"✓ Cropped and saved: {v_info['snapshot_filename']}")
                else:
                    cv2.imwrite(out_backend_path, img)
                    cv2.imwrite(out_frontend_path, img)
                    print(f"✓ Copied full image: {v_info['snapshot_filename']}")
            else:
                shutil.copyfile(src_path, out_backend_path)
                shutil.copyfile(src_path, out_frontend_path)
        else:
            print(f"⚠ Source image not found: {src_path}")

        snapshot_url = f"/snapshots/{v_info['snapshot_filename']}"

        # 1. Update/Add in Database
        existing = db.query(Vehicle).filter(Vehicle.vehicle_id == v_info["vehicle_id"]).first()
        if existing:
            existing.plate_number = v_info["plate_number"]
            existing.plate_confidence = 0.98
            existing.vehicle_type = v_info["vehicle_type"]
            existing.vehicle_model = v_info["vehicle_model"]
            existing.vehicle_color = v_info["vehicle_color"]
            existing.snapshot = snapshot_url
            existing.is_stolen = v_info["is_stolen"]
            existing.bolo_status = v_info["bolo_status"]
        else:
            new_v = Vehicle(
                vehicle_id=v_info["vehicle_id"],
                plate_number=v_info["plate_number"],
                plate_confidence=0.98,
                vehicle_type=v_info["vehicle_type"],
                vehicle_model=v_info["vehicle_model"],
                vehicle_color=v_info["vehicle_color"],
                is_stolen=v_info["is_stolen"],
                bolo_status=v_info["bolo_status"],
                snapshot=snapshot_url,
                created_at=now - datetime.timedelta(minutes=45)
            )
            db.add(new_v)
        db.commit()

        # 2. Add 3 Historical Sightings per vehicle
        db.query(VehicleSighting).filter(VehicleSighting.vehicle_id == v_info["vehicle_id"]).delete()
        db.commit()

        s1 = VehicleSighting(
            vehicle_id=v_info["vehicle_id"],
            camera_id=f"{v_info['camera_id']}-ENTRY",
            camera_name=f"{v_info['camera_name']} (Corridor Ingress)",
            location=f"{v_info['location']} - Toll Ingress",
            city=v_info["city"],
            latitude=v_info["lat"] - 0.008,
            longitude=v_info["lon"] - 0.006,
            speed_kmh=v_info["speed_kmh"] + 6.0,
            timestamp=now - datetime.timedelta(minutes=30),
            evidence_image=snapshot_url
        )
        s2 = VehicleSighting(
            vehicle_id=v_info["vehicle_id"],
            camera_id=f"{v_info['camera_id']}-MID",
            camera_name=f"{v_info['camera_name']} (Midway Gantry)",
            location=f"{v_info['location']} - Expressway Gantry",
            city=v_info["city"],
            latitude=v_info["lat"] - 0.003,
            longitude=v_info["lon"] - 0.002,
            speed_kmh=v_info["speed_kmh"] + 2.0,
            timestamp=now - datetime.timedelta(minutes=15),
            evidence_image=snapshot_url
        )
        s3 = VehicleSighting(
            vehicle_id=v_info["vehicle_id"],
            camera_id=v_info["camera_id"],
            camera_name=v_info["camera_name"],
            location=v_info["location"],
            city=v_info["city"],
            latitude=v_info["lat"],
            longitude=v_info["lon"],
            speed_kmh=v_info["speed_kmh"],
            timestamp=now - datetime.timedelta(minutes=4),
            evidence_image=snapshot_url
        )
        db.add_all([s1, s2, s3])
        db.commit()

        # 3. Add to Gallery Cache
        gallery_entry = {
            "vehicle_id": v_info["vehicle_id"],
            "plate": v_info["plate_number"],
            "plate_number": v_info["plate_number"],
            "type": v_info["vehicle_type"],
            "model": v_info["vehicle_model"],
            "color": v_info["vehicle_color"],
            "is_stolen": v_info["is_stolen"],
            "bolo_status": v_info["bolo_status"],
            "snapshot": snapshot_url,
            "camera_id": v_info["camera_id"],
            "camera_name": v_info["camera_name"],
            "location": v_info["location"],
            "city": v_info["city"],
            "lat": v_info["lat"],
            "lon": v_info["lon"],
            "speed_kmh": v_info["speed_kmh"],
            "timestamp": (now - datetime.timedelta(minutes=4)).strftime("%Y-%m-%d %I:%M:%S %p"),
            "embedding": [0.05] * 128  # Placeholder feature vector
        }

        # Replace or append in cache
        if "vehicles" not in cache_data:
            cache_data["vehicles"] = []
        cache_data["vehicles"] = [v for v in cache_data["vehicles"] if v.get("vehicle_id") != v_info["vehicle_id"]]
        cache_data["vehicles"].insert(0, gallery_entry)
        print(f"✓ Registered in Database & Gallery Cache: {v_info['vehicle_id']} · {v_info['plate_number']} ({v_info['vehicle_model']})")

    # Write back cache
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2)

    db.close()
    print("\n✓ ALL 6 VEHICLES FROM UPLOADED IMAGES SUCCESSFULLY REGISTERED AND INDEXED!")

if __name__ == "__main__":
    process_and_register_all()
