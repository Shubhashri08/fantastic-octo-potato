"""
Multi-Camera Real CCTV Indexing Script for Acceptance Verification.
"""

import os
import sys
import logging
from backend.app.video_person_engine import video_person_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("index_acceptance_cctv")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES_DIR = os.path.join(BASE_DIR, "samples")

CCTV_SOURCES = [
    {
        "video": os.path.join(SAMPLES_DIR, "mumbai_csmt_station.mp4"),
        "source_id": "CCTV-CAM01",
        "source_name": "CAM-01: Mumbai CSMT Main Concourse",
        "camera_id": "CAM-01",
        "location": "CSMT Terminal Concourse East"
    },
    {
        "video": os.path.join(SAMPLES_DIR, "fight_1.mp4"),
        "source_id": "CCTV-CAM02",
        "source_name": "CAM-02: Mumbai CSMT Platform 1",
        "camera_id": "CAM-02",
        "location": "CSMT Platform 1 Passenger Transit Area"
    },
    {
        "video": os.path.join(SAMPLES_DIR, "fight_2.mp4"),
        "source_id": "CCTV-CAM03",
        "source_name": "CAM-03: Dadar Railway Transit",
        "camera_id": "CAM-03",
        "location": "Dadar FOB Sector 4"
    }
]


def run_acceptance_indexing():
    print("=" * 80)
    print("  VIGRAH AI — INDEXING MULTI-CAMERA CCTV FOOTAGE")
    print("=" * 80)

    for src in CCTV_SOURCES:
        if not os.path.exists(src["video"]):
            print(f"❌ Video not found: {src['video']}")
            continue

        print(f"\nProcessing {src['source_name']} ({src['camera_id']})...")
        res = video_person_engine.process_video_evidence(
            video_path=src["video"],
            source_id=src["source_id"],
            source_name=src["source_name"],
            camera_id=src["camera_id"],
            location=src["location"],
            target_fps=3.0
        )
        print(f"  ✓ Status: {res['status']}")
        print(f"  ✓ Tracks Detected: {res['track_count']}")
        print(f"  ✓ Sightings Indexed: {res['sighting_count']}")

    print("\n" + "=" * 80)
    print("  ALL CCTV FEEDS INDEXED.")
    print("=" * 80)


if __name__ == "__main__":
    run_acceptance_indexing()
