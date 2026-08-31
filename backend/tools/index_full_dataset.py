"""
Indexes all CCTV surveillance camera feeds in backend/samples into the active database.
"""

import os
import sys
import logging
from backend.app.database import SessionLocal, DATABASE_URL
from backend.app.video_person_engine import video_person_engine
from backend.app.models import VideoEvidence

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("index_full_dataset")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES_DIR = os.path.join(BASE_DIR, "samples")

FEEDS = [
    {
        "video": os.path.join(SAMPLES_DIR, "fight_1.mp4"),
        "source_id": "CCTV-CAM01",
        "source_name": "CAM-01: Mumbai CSMT Platform 1",
        "camera_id": "CAM-01",
        "location": "CSMT Platform 1 Passenger Transit Area"
    },
    {
        "video": os.path.join(SAMPLES_DIR, "fight_2.mp4"),
        "source_id": "CCTV-CAM02",
        "source_name": "CAM-02: Dadar Railway Foot Overbridge",
        "camera_id": "CAM-02",
        "location": "Dadar FOB Sector 4"
    },
    {
        "video": os.path.join(SAMPLES_DIR, "mumbai_csmt_station.mp4"),
        "source_id": "CCTV-CAM03",
        "source_name": "CAM-03: Mumbai CSMT Main Concourse",
        "camera_id": "CAM-03",
        "location": "CSMT Concourse East Corridor"
    },
    {
        "video": os.path.join(SAMPLES_DIR, "blr_mg_road_metro.mp4"),
        "source_id": "CCTV-CAM04",
        "source_name": "CAM-04: Bengaluru MG Road Metro",
        "camera_id": "CAM-04",
        "location": "MG Road Station Gate 2"
    }
]


def index_all():
    print("=" * 80)
    print(f"  VIGRAH AI — INDEXING FULL CCTV DATASET INTO {DATABASE_URL}")
    print("=" * 80)

    for feed in FEEDS:
        if not os.path.exists(feed["video"]):
            print(f"Skipping {feed['source_id']} (file not found: {feed['video']})")
            continue

        print(f"\nIndexing {feed['source_name']}...")
        res = video_person_engine.process_video_evidence(
            video_path=feed["video"],
            source_id=feed["source_id"],
            source_name=feed["source_name"],
            camera_id=feed["camera_id"],
            location=feed["location"],
            target_fps=3.0
        )
        print(f"  ✓ Status: {res['status']}")
        print(f"  ✓ Tracks: {res['track_count']}")
        print(f"  ✓ Sightings: {res['sighting_count']}")

    print("\n" + "=" * 80)
    print("  DATASET INDEXING COMPLETE.")
    print("=" * 80)


if __name__ == "__main__":
    index_all()
