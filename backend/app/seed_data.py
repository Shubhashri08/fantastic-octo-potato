import os
import cv2
import json
import numpy as np
import datetime
from sqlalchemy.orm import Session
from .database import engine, Base, SessionLocal
from .models import Camera, Event

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES_DIR = os.path.join(BASE_DIR, "samples")
SNAPSHOTS_DIR = os.path.join(BASE_DIR, "snapshots")
os.makedirs(SAMPLES_DIR, exist_ok=True)
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

def init_db_and_seed():
    """
    Initializes schema and seeds 3 focused streams:
    - Cam 1: Case A (CCTV Altercation / Fighting)
    - Cam 2: Case B (CCTV Road Collision / Fire)
    - Cam 3: Case C (Mumbai Field Unit - Live Webcam)
    """
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

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
            "name": "CAM-03: Mumbai Field Unit (Phone IP Cam)",
            "source": "http://192.168.31.216:8080/video",
            "source_type": "rtsp",
            "lat": 18.9438,
            "lon": 72.8233,
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

    # Deactivate any higher camera IDs so only 3 clean feeds remain active
    extra_cams = db.query(Camera).filter(Camera.id > 3).all()
    for extra in extra_cams:
        extra.is_active = False

    db.commit()
    db.close()
