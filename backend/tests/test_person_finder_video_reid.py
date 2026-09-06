import os, sys
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import os
import sys
import cv2
import numpy as np
from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.database import SessionLocal, Base, engine
from app.models import VideoEvidence, PersonVideoTrack, PersonVideoSighting
from app.video_person_engine import video_person_engine, SAMPLES_DIR, EVIDENCE_DIR

client = TestClient(app)

def run_person_finder_tests():
    print("==================================================================")
    print("VIGRAH AI — PERSON FINDER & VIDEO EVIDENCE RE-ID TEST SUITE")
    print("==================================================================")

    # 1. Initialize DB schema
    Base.metadata.create_all(bind=engine)
    
    # Process sample videos into real video evidence
    print("\n[TEST 1] Processing Video Evidence Sources from sample CCTV footage...")
    v1_path = os.path.join(SAMPLES_DIR, "fight_1.mp4")
    v2_path = os.path.join(SAMPLES_DIR, "blr_mg_road_metro.mp4")
    v3_path = os.path.join(SAMPLES_DIR, "mumbai_csmt_station.mp4")

    if os.path.exists(v1_path):
        res1 = video_person_engine.process_video_evidence(
            v1_path, "VIDEO-01", "CAM-01: Mumbai CSMT Concourse (CCTV)", "Mumbai CSMT Terminal", 18.9401, 72.8351
        )
        print(f"  ✓ Processed VIDEO-01: {res1['track_count']} person tracks, {res1['sighting_count']} sightings.")

    if os.path.exists(v2_path):
        res2 = video_person_engine.process_video_evidence(
            v2_path, "VIDEO-02", "CAM-02: Bengaluru MG Road Corridor", "Bengaluru MG Road", 12.9756, 77.6067
        )
        print(f"  ✓ Processed VIDEO-02: {res2['track_count']} person tracks, {res2['sighting_count']} sightings.")

    # 2. Test GET /api/person/videos Endpoint
    print("\n[TEST 2] Testing GET /api/person/videos API...")
    res_videos = client.get("/api/person/videos")
    assert res_videos.status_code == 200, f"Failed GET /api/person/videos: {res_videos.text}"
    v_list = res_videos.json()
    assert len(v_list) >= 2, f"Expected at least 2 video sources, got {len(v_list)}"
    source_ids = [v["source_id"] for v in v_list]
    assert "VIDEO-01" in source_ids and "VIDEO-02" in source_ids
    print(f"  ✓ GET /api/person/videos verified: Found {len(v_list)} indexed video feeds.")

    # 3. Create a Synthetic Missing-Person Reference Image for search
    print("\n[TEST 3] Creating Query Reference Photo and testing Re-ID Search API...")
    dummy_query = np.zeros((128, 64, 3), dtype=np.uint8)
    dummy_query[:40, :] = [180, 150, 120]  # Face / Head
    dummy_query[40:85, :] = [40, 120, 200]  # Blue torso shirt
    dummy_query[85:, :] = [30, 30, 30]     # Dark pants
    
    is_success, buffer = cv2.imencode(".jpg", dummy_query)
    query_bytes = buffer.tobytes()

    # Search with min_similarity = 0.20 and limit = 5
    res_search = client.post(
        "/api/person/search?min_similarity=0.20&limit=5",
        files={"file": ("reference_person.jpg", query_bytes, "image/jpeg")}
    )
    assert res_search.status_code == 200, f"Search failed: {res_search.text}"
    s_data = res_search.json()
    matches = s_data["matches"]
    assert len(matches) > 0, "Expected at least 1 match from processed video evidence"
    assert len(matches) <= 5, f"Expected Top-K <= 5 matches, got {len(matches)}"
    
    top_match = matches[0]
    print(f"  ✓ Top Match: {top_match['track_id']} ({top_match['source_name']})")
    print(f"    Similarity: {top_match['similarity']} ({top_match['similarity_percent']}%)")
    print(f"    Evidence URL: {top_match['evidence_image_url']}")
    print(f"    Rank #1 / Best Match: {top_match.get('is_best_match', False)}")
    print(f"    Occurrences / Sightings: {top_match['detection_count']}")

    # 4. Strict Similarity Validation (Must be 0.0 to 1.0; Percent must be 0 to 100, never 7000%)
    print("\n[TEST 4] Validating Similarity Score Normalization & Top-K Limit...")
    for idx, m in enumerate(matches):
        sim = m["similarity"]
        pct = m["similarity_percent"]
        assert 0.0 <= sim <= 1.0, f"Similarity {sim} out of bounds [0.0, 1.0]"
        assert 0 <= pct <= 100, f"Percentage {pct} out of bounds [0, 100]"
        assert pct != 7000 and pct != 7100, "7000% bug detected!"
        if idx > 0:
            assert matches[idx-1]["similarity"] >= m["similarity"], "Matches must be sorted descending"
    print(f"  ✓ Strict normalization verified: All {len(matches)} matches correctly ranked and bounded.")

    # 5. Direct Evidence HTTP Endpoint Verification (FastAPI FileResponse)
    print("\n[TEST 5] Verifying Direct GET /api/person/evidence HTTP Endpoints...")
    for m in matches[:3]:
        raw_track = m["raw_track_id"]
        source_id = m["source_id"]
        
        # Test representative crop endpoint
        ep_url = f"/api/person/evidence/{source_id}/{raw_track}"
        res_img = client.get(ep_url)
        assert res_img.status_code == 200, f"Failed GET {ep_url}: {res_img.status_code}"
        assert res_img.headers.get("content-type") == "image/jpeg", f"Wrong MIME: {res_img.headers.get('content-type')}"
        assert len(res_img.content) > 100, "Image content empty"

        # Test sighting endpoint if sightings exist
        if m.get("sightings"):
            s_first = m["sightings"][0]
            s_url = s_first["evidence_image_url"]
            res_s_img = client.get(s_url)
            assert res_s_img.status_code == 200, f"Failed GET {s_url}: {res_s_img.status_code}"
            assert res_s_img.headers.get("content-type") == "image/jpeg"

    print("  ✓ Direct evidence endpoints verified: Returned HTTP 200 with Content-Type: image/jpeg.")

    # 6. Testing Top-K Limit Capping (Even if 20 candidates exist, max 5 returned)
    print("\n[TEST 6] Testing Backend Enforcement of Top-K = 5 Result Limit...")
    res_all = client.post(
        "/api/person/search?min_similarity=0.01&limit=100",
        files={"file": ("reference.jpg", query_bytes, "image/jpeg")}
    ).json()
    assert res_all["returned_candidates"] <= 5, f"Expected <= 5 returned candidates, got {res_all['returned_candidates']}"
    assert len(res_all["matches"]) <= 5, f"Expected <= 5 matches, got {len(res_all['matches'])}"
    print(f"  ✓ Top-5 cap verified: {res_all['total_candidates']} candidates evaluated -> returned top {res_all['returned_candidates']}.")

    # 7. Testing Video Source / Camera Filter
    print("\n[TEST 7] Testing Video Source Filtering (VIDEO-01 vs VIDEO-02)...")
    res_v1 = client.post(
        "/api/person/search?min_similarity=0.10&location=VIDEO-01",
        files={"file": ("reference.jpg", query_bytes, "image/jpeg")}
    ).json()["matches"]

    res_v2 = client.post(
        "/api/person/search?min_similarity=0.10&location=VIDEO-02",
        files={"file": ("reference.jpg", query_bytes, "image/jpeg")}
    ).json()["matches"]

    for m in res_v1:
        assert m["source_id"] == "VIDEO-01", f"Expected VIDEO-01, got {m['source_id']}"
    for m in res_v2:
        assert m["source_id"] == "VIDEO-02", f"Expected VIDEO-02, got {m['source_id']}"
    print(f"  ✓ Source filter verified: VIDEO-01 returned {len(res_v1)} tracks; VIDEO-02 returned {len(res_v2)} tracks.")

    # 8. Testing Crop File Existence on Disk
    print("\n[TEST 8] Verifying Evidence Crops on Local Storage...")
    for m in matches[:3]:
        crop_disk = video_person_engine.get_evidence_crop_file_path(m["source_id"], m["raw_track_id"])
        assert crop_disk and os.path.exists(crop_disk), f"Evidence crop image missing on disk: {crop_disk}"
        img_check = cv2.imread(crop_disk)
        assert img_check is not None and img_check.shape[0] > 0 and img_check.shape[1] > 0
    print("  ✓ Verified: Evidence crop images exist on disk, are valid JPEG images with non-zero dimensions.")

    print("\n==================================================================")
    print("✓ ALL PERSON FINDER & VIDEO RE-ID TESTS PASSED (100%)!")
    print("==================================================================")

if __name__ == "__main__":
    run_person_finder_tests()
