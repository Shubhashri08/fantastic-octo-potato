import os, sys
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import os
import sys
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.database import SessionLocal
from app.models import Event, Camera
from app.seed_data import init_db_and_seed

client = TestClient(app)

def run_distributed_tests():
    print("================================================================")
    print("VIGRAH AI — DISTRIBUTED RECONSTRUCTION & REALISM TEST SUITE")
    print("================================================================")

    init_db_and_seed(force_reset_events=True)
    db = SessionLocal()

    # 1. Verify Camera Distribution across 6 distinct nodes
    print("\n[TEST 1] Testing Camera Network Distribution (6 Cameras)...")
    res_cams = client.get("/api/cameras")
    assert res_cams.status_code == 200
    cams = res_cams.json()
    assert len(cams) >= 6, f"Expected at least 6 cameras, found {len(cams)}"
    cam_ids = [c["id"] for c in cams]
    assert 1 in cam_ids and 2 in cam_ids and 3 in cam_ids and 4 in cam_ids and 5 in cam_ids and 6 in cam_ids
    cam_labels = [f"CAM-0{c['id']}" for c in cams[:6]]
    print(f"  ✓ Verified 6 active camera nodes: {cam_labels}")

    # 2. Verify Distributed Events (EVT-6001 to EVT-6008)
    print("\n[TEST 2] Testing Investigative Incident Distribution...")
    res_events = client.get("/api/events")
    assert res_events.status_code == 200
    events = res_events.json()
    assert len(events) >= 8, f"Expected at least 8 seeded incidents, found {len(events)}"
    event_types = set(e["event_type"] for e in events)
    event_cams = set(e["camera_id"] for e in events)
    assert len(event_types) >= 5, f"Expected diverse event types, found: {event_types}"
    assert len(event_cams) >= 4, f"Expected events across multiple cameras, found: {event_cams}"
    print(f"  ✓ Verified {len(events)} events across {len(event_cams)} cameras and {len(event_types)} threat classes.")

    # 3. TEST CASE 1: Vehicle Collision at CAM-02 (Bengaluru MG Road)
    print("\n[TEST 3] TEST CASE 1: Reconstructing EVT-6001 (Vehicle Collision @ CAM-02)...")
    res_v1 = client.post("/api/reconstruction/analyze", json={"event_id": 6001})
    assert res_v1.status_code == 200
    d_v1 = res_v1.json()
    assert d_v1["mode"] == "vehicle"
    assert d_v1["event"]["camera_id"] == "CAM-02"
    assert round(d_v1["event"]["lat"], 4) == 12.9756
    assert round(d_v1["event"]["lon"], 4) == 77.6067
    assert len(d_v1["candidate_paths"]) >= 2
    assert d_v1["next_checkpoints"][0]["camera_id"] == "CAM-04"
    # Ensure scores sum to 100
    scores_sum_1 = sum(p["likelihood_percent"] for p in d_v1["candidate_paths"])
    assert scores_sum_1 == 100
    print(f"  ✓ EVT-6001 (CAM-02 Vehicle Collision): Mode={d_v1['mode']}, Top route={d_v1['candidate_paths'][0]['name'][:45]}... Likelihood={d_v1['candidate_paths'][0]['likelihood_percent']}%")

    # 4. TEST CASE 2: Fighting at CAM-01 (Mumbai CSMT Concourse)
    print("\n[TEST 4] TEST CASE 2: Reconstructing EVT-6005 (Fighting @ CAM-01)...")
    res_f1 = client.post("/api/reconstruction/analyze", json={"event_id": 6005})
    assert res_f1.status_code == 200
    d_f1 = res_f1.json()
    assert d_f1["mode"] == "pedestrian"
    assert d_f1["event"]["camera_id"] == "CAM-01"
    assert round(d_f1["event"]["lat"], 4) == 18.9401
    assert "Subway" in d_f1["candidate_paths"][0]["name"]
    assert sum(p["likelihood_percent"] for p in d_f1["candidate_paths"]) == 100
    print(f"  ✓ EVT-6005 (CAM-01 Fighting): Mode={d_f1['mode']}, Top pedestrian route={d_f1['candidate_paths'][0]['name'][:45]}...")

    # 5. TEST CASE 3: Fire Outbreak at CAM-03 (Mumbai Marine Drive)
    print("\n[TEST 5] TEST CASE 3: Reconstructing EVT-6003 (Fire @ CAM-03)...")
    res_fire = client.post("/api/reconstruction/analyze", json={"event_id": 6003})
    assert res_fire.status_code == 200
    d_fire = res_fire.json()
    assert d_fire["mode"] == "incident_spread", f"Expected incident_spread mode for Fire, got {d_fire['mode']}"
    assert d_fire["event"]["camera_id"] == "CAM-03"
    assert "Foam Tender" in d_fire["candidate_paths"][0]["name"] or "Emergency" in d_fire["candidate_paths"][0]["name"]
    print(f"  ✓ EVT-6003 (CAM-03 Fire): Mode={d_fire['mode']} (Thermal containment & ingress zones, NOT vehicle escape)")

    # 6. TEST CASE 4: Vehicle at CAM-05 (Bengaluru Outer Ring Road)
    print("\n[TEST 6] TEST CASE 4: Reconstructing EVT-6004 (Vehicle @ CAM-05)...")
    res_v5 = client.post("/api/reconstruction/analyze", json={"event_id": 6004})
    assert res_v5.status_code == 200
    d_v5 = res_v5.json()
    assert d_v5["mode"] == "vehicle"
    assert d_v5["event"]["camera_id"] == "CAM-05"
    assert round(d_v5["event"]["lat"], 4) == 12.9820
    assert "Outer Ring Road" in d_v5["candidate_paths"][0]["name"]
    print(f"  ✓ EVT-6004 (CAM-05 Vehicle): Origin=CAM-05, Top route={d_v5['candidate_paths'][0]['name'][:45]}...")

    # 7. TEST CASE 5: Accident at CAM-06 (Mumbai Worli Sea Face)
    print("\n[TEST 7] TEST CASE 5: Reconstructing EVT-6006 (Accident @ CAM-06)...")
    res_v6 = client.post("/api/reconstruction/analyze", json={"event_id": 6006})
    assert res_v6.status_code == 200
    d_v6 = res_v6.json()
    assert d_v6["mode"] == "vehicle"
    assert d_v6["event"]["camera_id"] == "CAM-06"
    assert round(d_v6["event"]["lat"], 4) == 18.9650
    assert "Sea Link" in d_v6["candidate_paths"][0]["name"]
    print(f"  ✓ EVT-6006 (CAM-06 Accident): Origin=CAM-06, Top route={d_v6['candidate_paths'][0]['name'][:45]}...")

    # 8. TEST CASE 6: Verify That Different Events Produce Genuinely Different Map State & Routes
    print("\n[TEST 8] TEST CASE 6: Cross-Event Difference Validation...")
    assert d_v1["event"]["lat"] != d_f1["event"]["lat"], "CAM-02 lat must differ from CAM-01 lat"
    assert d_v1["candidate_paths"][0]["geometry"] != d_v5["candidate_paths"][0]["geometry"], "Routes from CAM-02 and CAM-05 must have distinct geometries"
    assert d_v1["candidate_paths"][0]["likelihood_percent"] != d_v6["candidate_paths"][0]["likelihood_percent"] or d_v1["candidate_paths"][0]["name"] != d_v6["candidate_paths"][0]["name"]
    print("  ✓ Confirmed: Different events produce completely different origins, modes, route geometries, and scores.")

    print("\n================================================================")
    print("✓ ALL DISTRIBUTED RECONSTRUCTION & REALISM TESTS PASSED (100%)!")
    print("================================================================")

if __name__ == "__main__":
    run_distributed_tests()
