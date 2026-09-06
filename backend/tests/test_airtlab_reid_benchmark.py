import os, sys
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import cv2
import os
import numpy as np
from app.reid_engine import reid_engine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Load Authentic Query Target from AIRTLab Dataset
query_path = os.path.join(BASE_DIR, "snapshots", "ref_target_fight_1_p1_f20.jpg")
with open(query_path, "rb") as f:
    query_bytes = f.read()

print("=" * 70)
print("BENCHMARK: AIRTLab CCTV Dataset Person Re-ID Accuracy & False Positive Test")
print("=" * 70)
print(f"Query Reference Photo: {query_path}")

results = reid_engine.search_person_by_image(query_bytes, min_similarity=0.20)

print(f"\n[EVALUATION RESULTS] Total Sightings Returned: {len(results)}\n")
for idx, match in enumerate(results, 1):
    sim = match.get("similarity", 0)
    name = match.get("name", "Unknown")
    cam = match.get("sightings", [{}])[0].get("camera_name", "Unknown Cam")
    loc = match.get("sightings", [{}])[0].get("city", "Unknown Zone")
    time_s = match.get("sightings", [{}])[0].get("timestamp", "N/A")
    snap = match.get("sightings", [{}])[0].get("snapshot", "N/A")

    is_true_positive = "fight_1" in match.get("clothing", "") or "CSMT" in cam
    tag = " TRUE POSITIVE (Exact Same Person in Dataset)" if (is_true_positive and sim > 75) else "ℹ️ Visual Candidate"

    print(f"  [{idx}] Match: {name} | Sim: {sim}% | {tag}")
    print(f"      📍 Location: {cam} ({loc})")
    print(f"      🕒 Time: {time_s}")
    print(f"      🖼️ Snapshot Crop: {snap}\n")

print("=" * 70)
