import os, sys
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import os
import sys
import cv2
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_suite")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from app.vehicle_intelligence import (
    VehicleIntelligenceEngine,
    VehicleColorClassifier,
    IndianPlateRecognizer,
    get_vehicle_intelligence_engine
)
from app.detection import DetectionEngine
from app.stream_manager import StreamManager, CameraStreamWorker

def test_color_classifier():
    print("\n--- [TEST 1] Vehicle Color Classifier ---")
    # Generate synthetic vehicle crop with known dominant colors
    test_colors = [
        ("White", (240, 240, 240), "white"),
        ("Black", (20, 20, 20), "black"),
        ("Red", (30, 30, 220), "red"),
        ("Blue", (210, 80, 20), "blue"),
        ("Yellow", (30, 220, 230), "yellow"),
        ("Silver", (180, 180, 180), "silver"),
    ]

    for label, bgr, expected in test_colors:
        crop = np.full((120, 160, 3), bgr, dtype=np.uint8)
        detected_color, conf = VehicleColorClassifier.classify(crop)
        print(f"  Color Sample: {label:8} -> Classified: {detected_color:8} (conf: {conf:.2f}) | Match: {detected_color == expected}")
        assert detected_color == expected, f"Expected {expected}, got {detected_color}"
    print("  ✓ Vehicle Color Classifier PASSED")


def test_indian_plate_normalization():
    print("\n--- [TEST 2] Indian Number Plate Normalization & Formatting ---")
    test_cases = [
        ("mh 12 ab 1234", "MH12AB1234", 0.92),
        ("DL-03-C-9999", "DL03C9999", 0.92),
        ("KA 01 MJ 4567", "KA01MJ4567", 0.92),
        ("22 BH 1234 AA", "22BH1234AA", 0.80),
        ("MH-12-0-1234", "MH1201234", 0.80),
    ]

    for raw, expected, min_conf in test_cases:
        norm, conf = IndianPlateRecognizer.normalize_indian_plate(raw, initial_conf=0.90)
        print(f"  Raw: {raw:18} -> Normalized: {norm:12} (conf: {conf:.2f})")
        assert norm == expected, f"Expected {expected}, got {norm}"
        assert conf >= min_conf, f"Confidence {conf} < {min_conf}"
    print("  ✓ Indian Number Plate Normalization PASSED")


def test_vehicle_intelligence_engine():
    print("\n--- [TEST 3] Unified Vehicle Intelligence Pipeline on Real CCTV Video ---")
    engine = get_vehicle_intelligence_engine()
    sample_video_path = os.path.join(BASE_DIR, "samples", "accident_1.mp4")

    if not os.path.exists(sample_video_path):
        sample_video_path = os.path.join(BASE_DIR, "samples", "fight_1.mp4")

    cap = cv2.VideoCapture(sample_video_path)
    assert cap.isOpened(), f"Cannot open test video: {sample_video_path}"

    all_tracked_vehicles = {}
    frame_count = 0

    while frame_count < 25:
        ret, frame = cap.read()
        if not ret or frame is None:
            break
        frame_count += 1

        records, annotated = engine.process_frame(frame, camera_id="1")
        for rec in records:
            vid = rec["vehicle_id"]
            all_tracked_vehicles[vid] = rec

    cap.release()

    print(f"  Processed {frame_count} frames | Unique Tracked Vehicles Found: {len(all_tracked_vehicles)}")
    for vid, data in all_tracked_vehicles.items():
        print(f"    • Track ID: {data['vehicle_id']} | Type: {data['vehicle_type']} | Color: {data['vehicle_color']} | Plate: {data['license_plate']} | Veh Conf: {data['vehicle_confidence']}")
        # Verify required structured keys
        assert "vehicle_id" in data
        assert "vehicle_type" in data
        assert "vehicle_color" in data
        assert "license_plate" in data
        assert "vehicle_confidence" in data
        assert "plate_confidence" in data
        assert "ocr_confidence" in data
        assert "camera_id" in data
        assert "timestamp" in data

    print("  ✓ Unified Vehicle Intelligence Output PASSED")


def test_dvr_complete_removal():
    print("\n--- [TEST 4] Verification of Complete Legacy DVR Removal ---")
    worker = CameraStreamWorker(1, "0", "webcam", None)
    
    # Check that legacy DVR attributes and recording methods are removed
    assert not hasattr(worker, "is_recording_dvr"), "is_recording_dvr still present in CameraStreamWorker!"
    assert not hasattr(worker, "frame_buffer"), "frame_buffer still present in CameraStreamWorker!"
    assert not hasattr(worker, "_record_incident_clip"), "_record_incident_clip still present in CameraStreamWorker!"
    
    print("  ✓ CameraStreamWorker has zero legacy DVR attributes or recording threads.")
    print("  ✓ Legacy Auto-DVR System completely removed PASSED")


if __name__ == "__main__":
    print("=================================================================")
    print("  VIGRAH AI — VEHICLE INTELLIGENCE & DVR REMOVAL TEST SUITE")
    print("=================================================================")
    test_color_classifier()
    test_indian_plate_normalization()
    test_vehicle_intelligence_engine()
    test_dvr_complete_removal()
    print("\n=================================================================")
    print("  ALL TESTS PASSED SUCCESSFULLY! (100% OPERATIONAL)")
    print("=================================================================\n")
