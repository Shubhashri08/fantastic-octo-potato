import cv2
import os
from ultralytics import YOLO
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SNAPSHOTS_DIR = os.path.join(BASE_DIR, "snapshots")
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

detector = YOLO("yolo11n.pt")

print("Extracting authentic reference targets from AIRTLab dataset clips...")

extracted_targets = []

clips = [
    ("fight_1.mp4", "Target A (CSMT Stairwell Subject 1)"),
    ("fight_2.mp4", "Target B (Street Combatant in Jacket)"),
    ("mumbai_csmt_station.mp4", "Target C (Concourse Transit Subject)")
]

for clip_name, desc in clips:
    path = os.path.join(BASE_DIR, "samples", clip_name)
    if not os.path.exists(path):
        continue
    cap = cv2.VideoCapture(path)
    frame_idx = 0
    while cap.isOpened() and frame_idx < 120:
        ret, frame = cap.read()
        frame_idx += 1
        if not ret or frame is None:
            break

        if frame_idx in [20, 50, 80]:
            results = detector.predict(frame, classes=[0], conf=0.45, verbose=False)
            p_idx = 0
            for r in results:
                for box in r.boxes:
                    p_idx += 1
                    x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                    crop = frame[max(0, y1):min(frame.shape[0], y2), max(0, x1):min(frame.shape[1], x2)]
                    if crop.shape[0] > 60 and crop.shape[1] > 30:
                        safe_name = clip_name.replace(".mp4", "")
                        out_name = f"ref_target_{safe_name}_p{p_idx}_f{frame_idx}.jpg"
                        out_path = os.path.join(SNAPSHOTS_DIR, out_name)
                        cv2.imwrite(out_path, crop)
                        extracted_targets.append((out_name, out_path, desc, crop))
                        print(f"  ✓ Extracted {desc}: {out_name} ({crop.shape[1]}x{crop.shape[0]}px)")
    cap.release()

print(f"\nTotal Reference Targets Extracted: {len(extracted_targets)}")
