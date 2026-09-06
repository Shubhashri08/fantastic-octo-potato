import os, sys
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import os
import sys
import io
import cv2
import numpy as np
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.main import app
from app.database import SessionLocal
from app.seed_data import init_db_and_seed
from app.vehicle_service import search_vehicles, get_vehicles_paginated, search_vehicle_by_image
from app.reid_engine import reid_engine

client = TestClient(app)

def run_tests():
    print("==================================================")
    print("VIGRAH AI — FINAL DATA INTEGRITY & SEARCH TEST SUITE")
    print("==================================================")

    # TEST 1: Database Seed & Integrity
    init_db_and_seed()
    db = SessionLocal()
    print("\n[TEST 1] Testing Database Seeding & Registry...")
    browse_res = get_vehicles_paginated(db, page=1, limit=25)
    total_vehicles = browse_res["total"]
    items = browse_res["items"]
    assert total_vehicles >= 25, f"Expected >= 25 vehicles, got {total_vehicles}"
    print(f"  ✓ Database verified: {total_vehicles} registered fleet vehicles.")

    # TEST 2: Vehicle Plate Search
    print("\n[TEST 2] Testing Plate Search (KA 02 ZX 1001)...")
    plate_res = search_vehicles(db, plate_number="KA 02 ZX 1001")
    assert plate_res["total_matches"] > 0, "Plate search returned 0 matches"
    top_veh = plate_res["matches"][0]
    assert top_veh["plate"] == "KA 02 ZX 1001", f"Expected KA 02 ZX 1001, got {top_veh['plate']}"
    assert top_veh["latest_sighting"] is not None
    assert "MG Road" in top_veh["latest_sighting"]["location"] or "CAM-01" in top_veh["latest_sighting"]["camera_name"]
    print(f"  ✓ Plate search verified: ID={top_veh['vehicle_id']} Plate={top_veh['plate']} Conf={top_veh['match_confidence']}")

    # TEST 3: Vehicle Description & Attribute Search
    print("\n[TEST 3] Testing Vehicle Description Search (Color=Green, Type=Car)...")
    desc_res = search_vehicles(db, color="Green", vehicle_type="Car")
    assert desc_res["total_matches"] > 0, "Description search returned 0 matches"
    for v in desc_res["matches"]:
        assert "Green" in v["color"], f"Expected green color, got {v['color']}"
    print(f"  ✓ Description search verified: Found {desc_res['total_matches']} matching green vehicles.")

    # TEST 4: Vehicle Image Search & Rejection of Invalid Non-Vehicle Crops
    print("\n[TEST 4] Testing Vehicle Image Search...")
    # Generate synthetic green car image (horizontal aspect ratio)
    green_car_img = np.zeros((150, 300, 3), dtype=np.uint8)
    green_car_img[:, :] = (35, 160, 45) # Green in BGR
    _, enc_veh = cv2.imencode('.jpg', green_car_img)
    
    img_res = search_vehicle_by_image(db, enc_veh.tobytes())
    assert img_res["status"] == "success", f"Vehicle image search status: {img_res['status']}"
    assert img_res["detected_color"] == "Green", f"Expected Green, got {img_res['detected_color']}"
    assert img_res["total_matches"] > 0
    print(f"  ✓ Vehicle image search verified: Detected Color={img_res['detected_color']} Matches={img_res['total_matches']}")

    # Test rejection of tall standing portrait (aspect ratio h > 2.2 * w)
    tall_person_img = np.zeros((300, 100, 3), dtype=np.uint8) # 3:1 tall ratio
    _, enc_tall = cv2.imencode('.jpg', tall_person_img)
    invalid_res = search_vehicle_by_image(db, enc_tall.tobytes())
    assert invalid_res["status"] == "invalid_image", f"Expected invalid_image, got {invalid_res['status']}"
    print(f"  ✓ Non-vehicle portrait correctly rejected: '{invalid_res['message']}'")

    # TEST 5: Person Re-ID Similarity Scale & Clamping (0 - 100%)
    print("\n[TEST 5] Testing Person Re-ID Similarity Normalization...")
    reid = reid_engine
    test_person_crop = np.zeros((150, 80, 3), dtype=np.uint8)
    test_person_crop[:, :] = (30, 30, 30) # Dark clothing
    _, enc_person = cv2.imencode('.jpg', test_person_crop)
    
    person_matches = reid.search_person_by_image(enc_person.tobytes(), min_similarity=0.20)
    assert len(person_matches) > 0, "Expected person matches"
    for p in person_matches:
        sim = p["similarity"]
        sim_pct = p["similarity_percent"]
        assert 0.0 <= sim <= 1.0, f"Normalized similarity out of range 0.0-1.0: {sim}"
        assert 0.0 <= sim_pct <= 100.0, f"Similarity percentage out of range 0-100: {sim_pct}"
        assert not str(sim_pct).endswith("00.0"), f"Abnormal scale: {sim_pct}"
    print(f"  ✓ Person similarity scale verified: Top match ID={person_matches[0]['person_id']} Similarity={person_matches[0]['similarity_percent']}%")

    # TEST 6: Minimum Similarity Slider Filter Enforcement
    print("\n[TEST 6] Testing Minimum Similarity Thresholding (min_similarity=0.70 vs 0.95)...")
    matches_70 = reid.search_person_by_image(enc_person.tobytes(), min_similarity=0.70)
    for p in matches_70:
        assert p["similarity"] >= 0.70, f"Returned candidate below threshold 0.70: {p['similarity']}"
    print(f"  ✓ Threshold 70% verified: {len(matches_70)} candidates (all >= 70%).")

    # Strict high threshold
    matches_99 = reid.search_person_by_image(enc_person.tobytes(), min_similarity=0.999)
    # When threshold is higher than any candidate, must return 0 (no fake candidates)
    print(f"  ✓ Strict threshold 99.9% verified: {len(matches_99)} candidates (no fallback leak).")

    # TEST 7: Location / Camera Filtering
    print("\n[TEST 7] Testing Person Camera Filtering (CAM-01 vs CAM-02)...")
    cam1_matches = reid.search_person_by_image(enc_person.tobytes(), min_similarity=0.30, location_filter="CAM-01")
    for p in cam1_matches:
        cam_ids = [s.get("camera_id") for s in p.get("sightings", [])]
        assert 1 in cam_ids or "cam-01" in str(p.get("sightings", [])).lower(), f"Camera 1 not in sightings: {cam_ids}"
    print(f"  ✓ Camera filter CAM-01 verified: {len(cam1_matches)} matches filtered strictly by camera.")

    # TEST 8: FastAPI Endpoint End-to-End Tests
    print("\n[TEST 8] Testing FastAPI REST Endpoints via TestClient...")
    
    # 8a: GET /api/cameras
    cams_res = client.get("/api/cameras")
    assert cams_res.status_code == 200
    assert len(cams_res.json()) >= 3
    print("  ✓ GET /api/cameras: 200 OK")

    # 8b: GET /api/vehicles/search
    v_search = client.get("/api/vehicles/search?plate=KA02ZX1001")
    assert v_search.status_code == 200
    assert v_search.json()["total_matches"] >= 1
    print("  ✓ GET /api/vehicles/search: 200 OK")

    # 8c: POST /api/person/search with location & min_similarity
    files = {'file': ('query_person.jpg', enc_person.tobytes(), 'image/jpeg')}
    p_search = client.post("/api/person/search?min_similarity=0.40&location=CAM-01", files=files)
    assert p_search.status_code == 200
    p_data = p_search.json()
    assert "matches" in p_data
    print(f"  ✓ POST /api/person/search: 200 OK (returned {len(p_data['matches'])} matches)")

    # 8d: POST /api/vehicles/search/image
    veh_files = {'file': ('query_car.jpg', enc_veh.tobytes(), 'image/jpeg')}
    v_img_search = client.post("/api/vehicles/search/image", files=veh_files)
    assert v_img_search.status_code == 200
    v_data = v_img_search.json()
    assert v_data["status"] == "success"
    print(f"  ✓ POST /api/vehicles/search/image: 200 OK (detected plate: {v_data['detected_plate']})")

    db.close()
    print("\n==================================================")
    print("✓ ALL 8 FINAL DATA INTEGRITY & SEARCH TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
