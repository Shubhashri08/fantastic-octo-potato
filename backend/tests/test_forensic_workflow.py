import os, sys
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.main import app
from app.database import SessionLocal
from app.vehicle_service import search_vehicles, get_vehicle_sightings
from app.reid_engine import reid_engine

from app.seed_data import init_db_and_seed

client = TestClient(app)

def run_workflow_tests():
    print("==================================================")
    print("VIGRAH AI — FORENSIC WORKFLOW SPECIFICATION TESTS")
    print("==================================================")

    init_db_and_seed()
    db = SessionLocal()

    # 1. Plate Search with Camera filter and time window
    print("\n[TEST 1] Testing Plate Search with Filters...")
    res = search_vehicles(db, plate_number="KA 02 ZX 1001", location="CAM-01")
    assert res["total_matches"] >= 1
    assert res["matches"][0]["plate"] == "KA 02 ZX 1001"
    print(f"  ✓ Found plate {res['matches'][0]['plate']} with location CAM-01")

    # 2. Vehicle sightings trajectory API
    print("\n[TEST 2] Testing Vehicle Sightings Trajectory API...")
    sightings = get_vehicle_sightings(db, "VEH-0001")
    assert len(sightings) >= 1
    print(f"  ✓ Retrieved {len(sightings)} historical sightings for VEH-0001")

    # 3. Person ReID with Camera filtering
    print("\n[TEST 3] Testing Person ReID Camera Filter (CAM-02 vs CAM-03)...")
    import numpy as np, cv2
    sample_crop = np.zeros((150, 80, 3), dtype=np.uint8)
    _, enc = cv2.imencode('.jpg', sample_crop)
    
    matches_cam2 = reid_engine.search_person_by_image(enc.tobytes(), location_filter="CAM-02", min_similarity=0.20)
    for p in matches_cam2:
        for s in p.get("sightings", []):
            assert "cam-02" in str(s).lower() or "mg road" in str(s).lower() or 2 == s.get("camera_id")
    print(f"  ✓ CAM-02 filtered correctly ({len(matches_cam2)} candidates)")

    # 4. Events API
    print("\n[TEST 4] Testing Events Retrieval...")
    events_res = client.get("/api/events")
    assert events_res.status_code == 200
    events = events_res.json()
    assert len(events) >= 1
    print(f"  ✓ Events API verified ({len(events)} events loaded)")

    db.close()
    print("\n==================================================")
    print("✓ ALL WORKFLOW SPECIFICATION TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    run_workflow_tests()
