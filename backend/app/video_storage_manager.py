import os
import cv2
import json
import time
import shutil
import logging
from typing import Optional, List, Dict, Any
import numpy as np

logger = logging.getLogger("video_storage_manager")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_DIR = os.path.join(BASE_DIR, "video_storage")
VIOLENT_DIR = os.path.join(STORAGE_DIR, "violent")
NON_VIOLENT_DIR = os.path.join(STORAGE_DIR, "non_violent")
UNCLASSIFIED_DIR = os.path.join(STORAGE_DIR, "unclassified")
REPORTS_DIR = os.path.join(STORAGE_DIR, "reports")
SNAPSHOTS_DIR = os.path.join(REPORTS_DIR, "snapshots")
INDEX_FILE = os.path.join(STORAGE_DIR, "dataset_index.json")

for d in [STORAGE_DIR, VIOLENT_DIR, NON_VIOLENT_DIR, UNCLASSIFIED_DIR, REPORTS_DIR, SNAPSHOTS_DIR]:
    os.makedirs(d, exist_ok=True)

# Lazy model references
_coco_model = None
_threat_model = None

def get_detection_models():
    global _coco_model, _threat_model
    if _coco_model is None or _threat_model is None:
        from ultralytics import YOLO
        import torch

        device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
        yolo_cache = os.path.join(BASE_DIR, "Ultralytics")
        os.environ["YOLO_CONFIG_DIR"] = yolo_cache

        coco_path = os.path.join(BASE_DIR, "yolo11n.pt")
        if not os.path.exists(coco_path):
            coco_path = "yolo11n.pt"
        try:
            _coco_model = YOLO(coco_path)
        except Exception as e:
            logger.error(f"Error loading COCO model: {e}")
            _coco_model = None

        threat_path = os.path.join(BASE_DIR, "weights", "best.onnx")
        if os.path.exists(threat_path):
            try:
                _threat_model = YOLO(threat_path)
            except Exception as e:
                logger.error(f"Error loading threat ONNX model: {e}")
                _threat_model = None

    return _coco_model, _threat_model


def calculate_iou(b1, b2):
    """Calculates Intersection over Union between bounding boxes [x1, y1, x2, y2]."""
    x1 = max(b1[0], b2[0])
    y1 = max(b1[1], b2[1])
    x2 = min(b1[2], b2[2])
    y2 = min(b1[3], b2[3])
    inter_w = max(0, x2 - x1)
    inter_h = max(0, y2 - y1)
    inter_area = inter_w * inter_h
    area1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
    area2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
    union = area1 + area2 - inter_area
    return (inter_area / union) if union > 0 else 0.0


class BackendVideoStorageManager:
    def __init__(self):
        self.index_file = INDEX_FILE

    def get_index(self) -> Dict[str, Any]:
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"total_videos": 0, "violent_count": 0, "non_violent_count": 0, "videos": []}

    def _save_index(self, data: Dict[str, Any]):
        try:
            with open(self.index_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write index file: {e}")

    def inspect_and_store_video(
        self,
        source_video_path: str,
        custom_name: Optional[str] = None,
        force_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Inspects a video for violent altercations vs normal pedestrian walking,
        detects behavioral abnormalities, generates diagnostic keyframes,
        and moves/stores the video into backend/video_storage/(violent or non_violent).
        """
        if not os.path.exists(source_video_path):
            raise FileNotFoundError(f"Video file not found: {source_video_path}")

        filename = custom_name or os.path.basename(source_video_path)
        base_name = os.path.splitext(filename)[0]

        cap = cv2.VideoCapture(source_video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not decode video file: {source_video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = round(total_frames / fps, 2) if fps > 0 else 0.0

        coco, threat = get_detection_models()

        # Sample frames evenly across the clip
        sample_count = min(30, max(8, total_frames // 12))
        sample_indices = np.linspace(0, max(0, total_frames - 1), num=sample_count, dtype=int)

        frame_results = []
        fighting_frame_count = 0
        walking_frame_count = 0
        max_threat_conf = 0.0
        max_pedestrian_count = 0
        pedestrian_counts = []
        abnormal_conflict_overlaps = 0
        abnormality_reasons = []

        # 4 Keyframe snapshots to save
        keyframe_indices = set(np.linspace(0, max(0, total_frames - 1), num=4, dtype=int))
        saved_snapshots = []

        for idx, f_idx in enumerate(sample_indices):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(f_idx))
            ret, frame = cap.read()
            if not ret:
                continue

            annotated = frame.copy()
            timestamp_sec = round(f_idx / fps, 2)
            person_boxes = []
            neural_fight_boxes = []

            # 1. Detect Pedestrians
            if coco:
                try:
                    res = coco.predict(frame, classes=[0], conf=0.32, verbose=False)[0]
                    for b in res.boxes:
                        conf = float(b.conf[0].item())
                        xyxy = [int(v) for v in b.xyxy[0].tolist()]
                        person_boxes.append({"bbox": xyxy, "conf": conf})
                except Exception:
                    pass

            num_persons = len(person_boxes)
            pedestrian_counts.append(num_persons)
            max_pedestrian_count = max(max_pedestrian_count, num_persons)
            if num_persons > 0:
                walking_frame_count += 1

            # 2. Detect Physical Fighting Threats
            if threat:
                try:
                    t_res = threat.predict(frame, conf=0.25, verbose=False)[0]
                    for b in t_res.boxes:
                        cls_name = threat.names.get(int(b.cls[0].item()), "").lower()
                        if "fight" in cls_name or "violence" in cls_name:
                            c = float(b.conf[0].item())
                            xyxy = [int(v) for v in b.xyxy[0].tolist()]
                            neural_fight_boxes.append({"bbox": xyxy, "conf": c})
                            max_threat_conf = max(max_threat_conf, c)
                except Exception:
                    pass

            # 3. Check Abnormality: Conflict & Physical Collision Overlap between subjects
            has_physical_clinch = False
            if num_persons >= 2:
                for i in range(num_persons):
                    for j in range(i + 1, num_persons):
                        iou = calculate_iou(person_boxes[i]["bbox"], person_boxes[j]["bbox"])
                        if iou > 0.18:
                            has_physical_clinch = True
                            abnormal_conflict_overlaps += 1
                            break
                    if has_physical_clinch:
                        break

            frame_has_violence = (len(neural_fight_boxes) > 0) or (has_physical_clinch and len(neural_fight_boxes) > 0)
            if frame_has_violence:
                fighting_frame_count += 1

            # Draw annotations if this is a keyframe
            if f_idx in keyframe_indices:
                # Green boxes for walking pedestrians
                for p in person_boxes:
                    bx = p["bbox"]
                    cv2.rectangle(annotated, (bx[0], bx[1]), (bx[2], bx[3]), (0, 230, 115), 2)
                    p_lbl = f"WALKING {p['conf']*100:.0f}%"
                    cv2.putText(annotated, p_lbl, (bx[0] + 3, max(15, bx[1] - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 230, 115), 1, cv2.LINE_AA)

                # Red boxes for fighting
                for f_box in neural_fight_boxes:
                    bx = f_box["bbox"]
                    cv2.rectangle(annotated, (bx[0], bx[1]), (bx[2], bx[3]), (35, 35, 235), 3)
                    f_lbl = f"ALERT: FIGHTING {f_box['conf']*100:.0f}%"
                    cv2.putText(annotated, f_lbl, (bx[0] + 3, max(20, bx[1] - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (35, 35, 235), 2, cv2.LINE_AA)

                status_str = "ALERT: VIOLENT FIGHTING" if frame_has_violence else "NORMAL: PEDESTRIANS WALKING"
                status_clr = (35, 35, 235) if frame_has_violence else (0, 230, 115)
                cv2.putText(annotated, f"TIME: {timestamp_sec}s | {status_str}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_clr, 2, cv2.LINE_AA)

                snap_name = f"{base_name}_frame{f_idx}.jpg"
                snap_path = os.path.join(SNAPSHOTS_DIR, snap_name)
                cv2.imwrite(snap_path, annotated)
                snap_rel_path = os.path.relpath(snap_path, BASE_DIR)
                saved_snapshots.append({
                    "frame": int(f_idx),
                    "timestamp": timestamp_sec,
                    "path": snap_rel_path,
                    "has_violence": frame_has_violence,
                    "persons": num_persons
                })

        cap.release()

        # Decision & Abnormality Analysis
        total_inspected = len(sample_indices)
        violence_ratio = (fighting_frame_count / total_inspected) if total_inspected > 0 else 0.0
        walking_ratio = (walking_frame_count / total_inspected) if total_inspected > 0 else 0.0

        if fighting_frame_count >= 2 or violence_ratio >= 0.20:
            is_violent = True
            category = "violent"
            abnormality_reasons.append("Hostile physical combat detected (punches, wrestling, brawl motion).")
        else:
            is_violent = False
            category = "non_violent"

        if abnormal_conflict_overlaps > 3 and is_violent:
            abnormality_reasons.append(f"Violent bodily collision & physical struggle confirmed ({abnormal_conflict_overlaps} contact instances).")

        has_abnormalities = is_violent or (len(abnormality_reasons) > 0)

        if not has_abnormalities:
            abnormality_summary = "Normal Pedestrians Walking: No hostile contacts, standard pedestrian walking and browsing dynamics."
            verdict = "NON_VIOLENT_WALKING"
        else:
            abnormality_summary = "Abnormal / Threat Behavior Detected: " + " ".join(abnormality_reasons)
            verdict = "VIOLENT_FIGHTING" if is_violent else "ABNORMAL_PHYSICAL_COLLISION"

        if force_category:
            category = force_category
            is_violent = (force_category == "violent")

        # Move/Copy video into backend destination directory
        dest_dir = VIOLENT_DIR if category == "violent" else NON_VIOLENT_DIR
        dest_path = os.path.join(dest_dir, filename)

        # Copy source video into structured backend storage
        if os.path.abspath(source_video_path) != os.path.abspath(dest_path):
            shutil.copy2(source_video_path, dest_path)

        dest_rel_path = os.path.relpath(dest_path, BASE_DIR)
        report_file = os.path.join(REPORTS_DIR, f"{base_name}_report.json")
        report_rel_path = os.path.relpath(report_file, BASE_DIR)

        # Build analysis report
        report = {
            "video_id": f"vid_{int(time.time())}_{base_name[:15]}",
            "filename": filename,
            "category": category,
            "verdict": verdict,
            "is_violent": is_violent,
            "has_abnormalities": has_abnormalities,
            "abnormality_summary": abnormality_summary,
            "abnormality_details": abnormality_reasons,
            "metrics": {
                "violence_score": round(violence_ratio * (max_threat_conf or 0.85), 3),
                "walking_flow_score": round(walking_ratio, 3),
                "max_threat_confidence": round(max_threat_conf, 3),
                "fighting_frames": fighting_frame_count,
                "walking_frames": walking_frame_count,
                "total_frames": total_frames,
                "inspected_frames": total_inspected,
                "duration_sec": duration,
                "fps": round(fps, 2),
                "resolution": f"{width}x{height}",
                "avg_pedestrians": round(float(np.mean(pedestrian_counts)), 1) if pedestrian_counts else 0,
                "max_pedestrians": max_pedestrian_count
            },
            "stored_location": dest_rel_path,
            "evidence_snapshots": saved_snapshots,
            "analyzed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Save individual JSON report
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        # Update dataset index
        index = self.get_index()
        # Remove any existing record with this filename
        index["videos"] = [v for v in index.get("videos", []) if v.get("filename") != filename]
        index["videos"].insert(0, {
            "filename": filename,
            "category": category,
            "verdict": verdict,
            "is_violent": is_violent,
            "stored_location": dest_rel_path,
            "report_path": report_rel_path,
            "duration_sec": duration,
            "analyzed_at": report["analyzed_at"]
        })
        index["violent_count"] = len([v for v in index["videos"] if v.get("category") == "violent"])
        index["non_violent_count"] = len([v for v in index["videos"] if v.get("category") == "non_violent"])
        index["total_videos"] = len(index["videos"])
        self._save_index(index)

        logger.info(f"Stored & Classified: {filename} -> {category.upper()} ({verdict})")
        return report

    def list_stored_videos(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        index = self.get_index()
        videos = index.get("videos", [])
        if category in ["violent", "non_violent"]:
            return [v for v in videos if v.get("category") == category]
        return videos


backend_video_storage = BackendVideoStorageManager()
