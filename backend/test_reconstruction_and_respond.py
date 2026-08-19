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

def run_tests():
    print("==================================================")
    print("VIGRAH AI — RECONSTRUCTION & RESPOND INTEGRITY TESTS")
    print("==================================================")

    init_db_and_seed()
    db = SessionLocal()

    # 1. Test Event Reconstruction API POST
    print("\n[TEST 1] Testing Event Reconstruction API POST (/api/reconstruction/analyze)...")
    res1 = client.post("/api/reconstruction/analyze", json={"event_id": 5568})
    assert res1.status_code == 200, f"Expected 200, got {res1.status_code}: {res1.text}"
    data1 = res1.json()
    assert "event" in data1, "Missing event metadata"
    assert "candidate_paths" in data1, "Missing candidate_paths"
    assert len(data1["candidate_paths"]) >= 3, "Expected at least 3 candidate paths"
    assert "observed_path" in data1, "Missing observed_path"
    assert "next_checkpoints" in data1, "Missing next_checkpoints"
    assert data1["candidate_paths"][0]["is_most_likely"] == True, "First candidate must be most likely"
    print(f"  ✓ Mumbai Event #5568 Reconstructed: {len(data1['candidate_paths'])} routes, Most likely likelihood: {data1['candidate_paths'][0]['likelihood_percent']}%")

    # 2. Test Bengaluru Event Reconstruction
    print("\n[TEST 2] Testing Bengaluru Event Reconstruction (/api/reconstruction/analyze)...")
    res2 = client.post("/api/reconstruction/analyze", json={"event_id": 5569})
    assert res2.status_code == 200, f"Expected 200, got {res2.status_code}: {res2.text}"
    data2 = res2.json()
    assert data2["event"]["camera_id"] == "CAM-02"
    assert len(data2["candidate_paths"]) >= 3
    print(f"  ✓ Bengaluru Event #5569 Reconstructed: Top checkpoint: {data2['next_checkpoints'][0]['camera_name']}")

    # 3. Test Events API and Severity Filtering
    print("\n[TEST 3] Testing Events Query and Severity Filter (/api/events)...")
    res3 = client.get("/api/events?severity=Critical")
    assert res3.status_code == 200
    events_crit = res3.json()
    for ev in events_crit:
        assert ev["severity"] == "Critical"
    print(f"  ✓ Filtered {len(events_crit)} Critical events correctly.")

    print("\n==================================================")
    print("✓ ALL RECONSTRUCTION & RESPOND INTEGRITY TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
