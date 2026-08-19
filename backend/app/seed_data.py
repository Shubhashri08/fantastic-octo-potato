import os
import cv2
import json
import numpy as np
import datetime
from sqlalchemy.orm import Session
from .database import engine, Base, SessionLocal
from .models import Camera, Event, Entity, EntitySighting, EventEntityMapping, Alert, Vehicle, VehicleSighting

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES_DIR = os.path.join(BASE_DIR, "samples")
SNAPSHOTS_DIR = os.path.join(BASE_DIR, "snapshots")
os.makedirs(SAMPLES_DIR, exist_ok=True)
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

def init_db_and_seed(force_reset_events: bool = False):
    """
    Initializes schema and seeds distributed CCTV mesh across 6 distinct camera nodes:
    - CAM-01: Mumbai CSMT Concourse (Altercation Node)
    - CAM-02: Bengaluru MG Road Commercial Corridor (Road Incident Node)
    - CAM-03: Mumbai Marine Drive / Coastal Unit (Fire/Smoke Sensor)
    - CAM-04: Bengaluru Trinity Circle Transit Checkpoint (Vehicle & Pedestrian Node)
    - CAM-05: Bengaluru Outer Ring Road Hub (High-Speed Transit Arterial)
    - CAM-06: Mumbai Worli Sea Face Intercept (Expressway Perimeter)
    """
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    # Ensure new columns exist on SQLite events table if migrated
    from sqlalchemy import text
    try:
        db.execute(text("ALTER TABLE events ADD COLUMN status VARCHAR(20) DEFAULT 'Active'"))
        db.commit()
    except Exception:
        db.rollback()
    try:
        db.execute(text("ALTER TABLE events ADD COLUMN is_demo BOOLEAN DEFAULT 0"))
        db.commit()
    except Exception:
        db.rollback()
    try:
        db.execute(text("ALTER TABLE events ADD COLUMN confirmation_count INTEGER DEFAULT 1"))
        db.commit()
    except Exception:
        db.rollback()

    fight_1_path = os.path.join(SAMPLES_DIR, "fight_1.mp4")
    fire_1_path = os.path.join(SAMPLES_DIR, "fire_1.mp4")

    cameras_to_seed = [
        {
            "id": 1,
            "name": "CAM-01: Mumbai CSMT Concourse Altercation",
            "source": fight_1_path,
            "source_type": "video",
            "lat": 18.9401,
            "lon": 72.8351,
            "is_active": True
        },
        {
            "id": 2,
            "name": "CAM-02: Bengaluru MG Road Commercial Corridor",
            "source": fire_1_path,
            "source_type": "video",
            "lat": 12.9756,
            "lon": 77.6067,
            "is_active": True
        },
        {
            "id": 3,
            "name": "CAM-03: Mumbai Marine Drive Coastal Unit",
            "source": "http://192.168.31.216:8080/video",
            "source_type": "rtsp",
            "lat": 18.9438,
            "lon": 72.8233,
            "is_active": True
        },
        {
            "id": 4,
            "name": "CAM-04: Bengaluru Trinity Circle Transit Node",
            "source": fire_1_path,
            "source_type": "video",
            "lat": 12.9725,
            "lon": 77.6200,
            "is_active": True
        },
        {
            "id": 5,
            "name": "CAM-05: Bengaluru Outer Ring Road Hub",
            "source": fight_1_path,
            "source_type": "video",
            "lat": 12.9820,
            "lon": 77.6200,
            "is_active": True
        },
        {
            "id": 6,
            "name": "CAM-06: Mumbai Worli Sea Face Intercept",
            "source": fight_1_path,
            "source_type": "video",
            "lat": 18.9650,
            "lon": 72.8180,
            "is_active": True
        }
    ]

    for cam_info in cameras_to_seed:
        existing_cam = db.query(Camera).filter(Camera.id == cam_info["id"]).first()
        if existing_cam:
            existing_cam.name = cam_info["name"]
            existing_cam.source = cam_info["source"]
            existing_cam.source_type = cam_info["source_type"]
            existing_cam.lat = cam_info["lat"]
            existing_cam.lon = cam_info["lon"]
            existing_cam.is_active = cam_info["is_active"]
        else:
            new_cam = Camera(**cam_info)
            db.add(new_cam)

    # 2. Seed Vehicle Records & Historical Sightings if empty
    CACHE_FILE = os.path.join(BASE_DIR, "reid_gallery_cache.json")
    existing_veh_count = db.query(Vehicle).count()
    if existing_veh_count == 0 and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            
            raw_vehicles = cache_data.get("vehicles", [])
            for v_data in raw_vehicles:
                v_id = v_data.get("vehicle_id")
                plate = v_data.get("plate", "")
                v_type = v_data.get("type", "Car (Sedan)")
                v_color = v_data.get("color", "Silver")
                
                # Derive Model
                if "Sedan" in v_type or v_type == "Car":
                    v_model = "Toyota Corolla Sedan"
                elif "Motorcycle" in v_type:
                    v_model = "Bajaj Pulsar 150cc"
                elif "Bus" in v_type:
                    v_model = "Ashok Leyland City Transit"
                elif "Truck" in v_type:
                    v_model = "Tata 407 Cargo Hauler"
                elif "SUV" in v_type:
                    v_model = "Mahindra Scorpio SUV"
                else:
                    v_model = "Standard Fleet Vehicle"

                is_stolen = bool(v_data.get("is_stolen", False))
                bolo = "CRITICAL BOLO: Reported Stolen" if is_stolen else "NORMAL: Verified Vehicle Registry"
                snapshot = v_data.get("snapshot", "")
                
                veh_record = Vehicle(
                    vehicle_id=v_id,
                    plate_number=plate,
                    plate_confidence=0.96,
                    vehicle_type=v_type,
                    vehicle_model=v_model,
                    color=v_color,
                    is_stolen=is_stolen,
                    bolo_status=bolo,
                    snapshot_url=snapshot,
                    match_confidence=0.96
                )
                db.add(veh_record)

                # Seed 3 Historical Sightings per vehicle
                now = datetime.datetime.now()
                loc_name = "Bengaluru MG Road Commercial Corridor" if "KA" in plate else "Mumbai CSMT Concourse Corridor"
                city = "Bengaluru Safe City Grid" if "KA" in plate else "Mumbai Safe City Grid"
                lat = 12.9756 if "KA" in plate else 18.9401
                lon = 77.6067 if "KA" in plate else 72.8351
                speed = 52.0 if "KA" in plate else 44.0
                cam_code = "CAM-02" if "KA" in plate else "CAM-01"
                ts = (now - datetime.timedelta(minutes=14)).strftime("%Y-%m-%d %I:%M:%S %p")

                s1 = VehicleSighting(
                    sighting_id=f"SIGHT-{v_id}-01",
                    vehicle_id=v_id,
                    camera_id="CAM-TC-01" if "MH" in plate else "CAM-BLR-01",
                    location="Transit Corridor Entry Gate 1",
                    city=city,
                    latitude=lat - 0.008,
                    longitude=lon - 0.006,
                    speed_kmh=speed - 8.0,
                    timestamp=(now - datetime.timedelta(minutes=35)).strftime("%Y-%m-%d %I:%M:%S %p"),
                    evidence_image=snapshot
                )
                s2 = VehicleSighting(
                    sighting_id=f"SIGHT-{v_id}-02",
                    vehicle_id=v_id,
                    camera_id="CAM-EW-03" if "MH" in plate else "CAM-BLR-02",
                    location="Expressway Midway Checkpoint",
                    city=city,
                    latitude=lat - 0.004,
                    longitude=lon - 0.002,
                    speed_kmh=speed + 5.0,
                    timestamp=(now - datetime.timedelta(minutes=22)).strftime("%Y-%m-%d %I:%M:%S %p"),
                    evidence_image=snapshot
                )
                s3 = VehicleSighting(
                    sighting_id=f"SIGHT-{v_id}-03",
                    vehicle_id=v_id,
                    camera_id=cam_code,
                    location=loc_name,
                    city=city,
                    latitude=lat,
                    longitude=lon,
                    speed_kmh=speed,
                    timestamp=ts,
                    evidence_image=snapshot
                )
                db.add_all([s1, s2, s3])

            db.commit()
            print(f"✓ Seeded {len(raw_vehicles)} vehicles and sighting routes into database.")
        except Exception as e:
            print(f"Error seeding vehicles: {e}")

    # 3. Seed Verified, Distributed Investigative Incidents
    # Clear fragmented duplicate frames if resetting or empty
    existing_events_count = db.query(Event).count()
    if existing_events_count == 0 or force_reset_events:
        if force_reset_events:
            db.query(Event).delete()
            db.commit()

        now = datetime.datetime.now()
        seeded_events = [
            Event(
                id=6001,
                camera_id=2,
                event_type="Vehicle Collision",
                severity="Critical",
                confidence=0.96,
                timestamp=now - datetime.timedelta(minutes=8),
                is_demo=True,
                status="Active",
                confirmation_count=6,
                snapshot_path="/snapshots/crop_vehicle_cam2_1.jpg"
            ),
            Event(
                id=6002,
                camera_id=4,
                event_type="Person",
                severity="High",
                confidence=0.91,
                timestamp=now - datetime.timedelta(minutes=18),
                is_demo=True,
                status="Active",
                confirmation_count=4,
                snapshot_path="/snapshots/crop_person_cam1_1.jpg"
            ),
            Event(
                id=6003,
                camera_id=3,
                event_type="Fire",
                severity="Critical",
                confidence=0.98,
                timestamp=now - datetime.timedelta(minutes=27),
                is_demo=True,
                status="Active",
                confirmation_count=7,
                snapshot_path="/snapshots/crop_vehicle_cam2_1.jpg"
            ),
            Event(
                id=6004,
                camera_id=5,
                event_type="Vehicle",
                severity="High",
                confidence=0.94,
                timestamp=now - datetime.timedelta(minutes=38),
                is_demo=True,
                status="Active",
                confirmation_count=4,
                snapshot_path="/snapshots/crop_vehicle_cam2_1.jpg"
            ),
            Event(
                id=6005,
                camera_id=1,
                event_type="Fighting",
                severity="Critical",
                confidence=0.97,
                timestamp=now - datetime.timedelta(minutes=45),
                is_demo=True,
                status="Active",
                confirmation_count=6,
                snapshot_path="/snapshots/crop_person_cam1_1.jpg"
            ),
            Event(
                id=6006,
                camera_id=6,
                event_type="Accident",
                severity="High",
                confidence=0.93,
                timestamp=now - datetime.timedelta(minutes=58),
                is_demo=True,
                status="Active",
                confirmation_count=3,
                snapshot_path="/snapshots/crop_vehicle_cam2_1.jpg"
            ),
            Event(
                id=6007,
                camera_id=3,
                event_type="Smoke",
                severity="Medium",
                confidence=0.89,
                timestamp=now - datetime.timedelta(minutes=72),
                is_demo=True,
                status="Active",
                confirmation_count=4,
                snapshot_path="/snapshots/crop_vehicle_cam2_1.jpg"
            ),
            Event(
                id=6008,
                camera_id=5,
                event_type="Vehicle Collision",
                severity="Critical",
                confidence=0.95,
                timestamp=now - datetime.timedelta(minutes=85),
                is_demo=True,
                status="Active",
                confirmation_count=5,
                snapshot_path="/snapshots/crop_vehicle_cam2_1.jpg"
            )
        ]
        db.add_all(seeded_events)
        db.commit()
        print(f"✓ Seeded {len(seeded_events)} distributed investigative incidents into database.")

    db.close()

if __name__ == "__main__":
    init_db_and_seed(force_reset_events=True)
