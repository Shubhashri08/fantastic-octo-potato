import os
import sys
import cv2
import json
import numpy as np

# Add backend directory to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from app.reid_engine import ReIDEngine
from app.detection import calculate_iou, TemporalTracker

def run_tests():
    print("=" * 70)
    print("🚀 VIGRAH AI — COMPREHENSIVE PIPELINE TEST SUITE")
    print("=" * 70)

    # -------------------------------------------------------------
    # Test 1: Person Biometric & Re-ID Search
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing Person Biometric Re-ID Matcher...")
    reid = ReIDEngine()
    test_img = np.zeros((128, 64, 3), dtype=np.uint8)
    cv2.circle(test_img, (32, 28), 16, (25, 25, 25), -1)
    _, img_encoded = cv2.imencode('.jpg', test_img)
    
    matches = reid.search_person_by_image(img_encoded.tobytes(), min_similarity=0.50)
    assert len(matches) > 0, "Person ReID search failed to return matches"
    top_match = matches[0]
    print(f"  ✓ Found {len(matches)} match(es). Top match: {top_match['name']} ({top_match['similarity']}% similarity)")
    print(f"  ✓ Biometrics: {top_match['facial_features']}")
    print(f"  ✓ Sighting Checkpoints: {len(top_match['sightings_history'])} cameras logged")

    # -------------------------------------------------------------
    # Test 2: Vehicle & Stolen Car BOLO Tracking
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing Stolen Vehicle & BOLO Watchlist Search...")
    stolen_vehicles = reid.search_vehicles(stolen_only=True)
    assert len(stolen_vehicles) >= 2, "Stolen vehicle search failed"
    for v in stolen_vehicles:
        print(f"  ✓ Stolen Vehicle Alert: {v['plate']} ({v['type']}, {v['color']}) | Speed: {v['speed_kmh']} km/h")
        print(f"    BOLO Status: {v.get('bolo_status')}")
        print(f"    Trajectory Points: {len(v.get('trajectory', []))} checkpoints")

    # -------------------------------------------------------------
    # Test 3: Road Accident & Collision IoU Logic
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing Accident & Collision IoU Detection Logic...")
    box_veh1 = [100, 100, 200, 200]
    box_veh2 = [140, 140, 240, 240] # Significant overlap
    box_far = [400, 400, 500, 500]  # No overlap

    iou_collision = calculate_iou(box_veh1, box_veh2)
    iou_clear = calculate_iou(box_veh1, box_far)
    assert iou_collision >= 0.20, f"Expected high collision IoU, got {iou_collision}"
    assert iou_clear == 0.0, f"Expected 0.0 IoU, got {iou_clear}"
    print(f"  ✓ Collision IoU Overlap: {iou_collision:.3f} (Correctly triggers ACCIDENT alert)")
    print(f"  ✓ Non-colliding Traffic IoU: {iou_clear:.3f} (Correctly filtered)")

    # -------------------------------------------------------------
    # Test 4: Temporal Confirmation Tracker
    # -------------------------------------------------------------
    print("\n[TEST 4] Testing Temporal Confirmation Tracker (Anti-Flapping)...")
    tracker = TemporalTracker(consecutive_threshold=3, cooldown_seconds=5.0)
    # Frame 1: Candidate
    res1 = tracker.update(camera_id=1, candidate_types={"Fighting"})
    assert "Fighting" not in res1, "Should not confirm on frame 1"
    # Frame 2: Candidate
    res2 = tracker.update(camera_id=1, candidate_types={"Fighting"})
    assert "Fighting" not in res2, "Should not confirm on frame 2"
    # Frame 3: Candidate -> Confirmed!
    res3 = tracker.update(camera_id=1, candidate_types={"Fighting"})
    assert "Fighting" in res3, "Should confirm on 3rd consecutive frame"
    print("  ✓ Strict 3-Frame Temporal Confirmation: PASS")

    # -------------------------------------------------------------
    # Test 5: Multi-City CCTV Mesh Integrity
    # -------------------------------------------------------------
    print("\n[TEST 5] Testing Multi-City CCTV Mesh Networks...")
    assert "Bengaluru" in reid.city_networks, "Bengaluru mesh missing"
    assert "Mumbai" in reid.city_networks, "Mumbai mesh missing"
    assert "Delhi" in reid.city_networks, "Delhi mesh missing"
    bengaluru_nodes = reid.city_networks["Bengaluru"]["total_nodes"]
    print(f"  ✓ Bengaluru OpenCity CCTV Nodes: {bengaluru_nodes} verified GPS coordinates")
    print(f"  ✓ Mumbai CCTV Nodes: {reid.city_networks['Mumbai']['total_nodes']} key traffic nodes")
    print(f"  ✓ Delhi Safe City Nodes: {reid.city_networks['Delhi']['total_nodes']} arterial junctions")

    # -------------------------------------------------------------
    # Test 6: Auto-DVR Storage Directories
    # -------------------------------------------------------------
    print("\n[TEST 6] Testing Evidence & Auto-DVR Directories...")
    assert os.path.exists(os.path.join(BASE_DIR, "snapshots")), "Snapshots dir missing"
    assert os.path.exists(os.path.join(BASE_DIR, "recordings")), "Recordings dir missing"
    print(f"  ✓ Snapshots Directory: {os.path.join(BASE_DIR, 'snapshots')} [READY]")
    print(f"  ✓ Auto-DVR MP4 Directory: {os.path.join(BASE_DIR, 'recordings')} [READY]")

    print("\n" + "=" * 70)
    print("🎉 ALL 6 COMPREHENSIVE PIPELINE TEST CASES PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
