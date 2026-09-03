import os
import cv2
import json
import time
import datetime
import logging
from collections import defaultdict
import numpy as np
import torch
from sqlalchemy.orm import Session
from ultralytics import YOLO

from .models import Event
from .database import SessionLocal
from .vehicle_intelligence import get_vehicle_intelligence_engine

logger = logging.getLogger("detection_engine")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOTS_DIR = os.path.join(BASE_DIR, "snapshots")
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

EVENT_COLORS = {
    "Fighting": (0, 35, 230),   # Sharp Crimson Red (Threat)
    "Fire": (0, 90, 255),       # Vivid Fire Orange-Red (Threat)
    "Accident": (0, 140, 255),  # High-Alert Amber Orange (Collision/Crash)
    "Person": (0, 180, 0),      # Muted Green (Normal Passive Pedestrian)
    "Vehicle": (3, 183, 255),   # Electric Amber (Normal Traffic)
    "Default": (140, 140, 140)
}

def calculate_iou(box1, box2):
    """Calculates Intersection over Union (IoU) between two bounding boxes [x1, y1, x2, y2]."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter_w = max(0, x2 - x1)
    inter_h = max(0, y2 - y1)
    inter_area = inter_w * inter_h

    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union_area = area1 + area2 - inter_area

    if union_area <= 0:
        return 0.0
    return inter_area / union_area

class TemporalTracker:
    """
    Strict Temporal Confirmation:
    Requires candidate threat in >= 3 consecutive frames with 10s cooldown per camera.
    """
    def __init__(self, consecutive_threshold: int = 3, cooldown_seconds: float = 10.0):
        self.consecutive_threshold = consecutive_threshold
        self.cooldown_seconds = cooldown_seconds
        self.consecutive_counts = defaultdict(int)
        self.last_triggered = defaultdict(float)

    def update(self, camera_id: int, candidate_types: set):
        all_tracked_keys = [k for k in self.consecutive_counts.keys() if k[0] == camera_id]

        for k in all_tracked_keys:
            ev_type = k[1]
            if ev_type not in candidate_types:
                self.consecutive_counts[k] = 0

        confirmed_types = set()
        current_time = time.time()

        for ev_type in candidate_types:
            key = (camera_id, ev_type)
            self.consecutive_counts[key] += 1

            if self.consecutive_counts[key] >= self.consecutive_threshold:
                if current_time - self.last_triggered[key] >= self.cooldown_seconds:
                    confirmed_types.add(ev_type)
                    self.last_triggered[key] = current_time

        return confirmed_types


class DetectionEngine:
    def __init__(self, models_dict: dict):
        self.models = models_dict
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Load standard detector for humans
        try:
            self.coco_detector = YOLO("yolo11n.pt")
            logger.info("Loaded YOLO11n COCO Detector for Pedestrian & Threat Analytics.")
        except Exception:
            self.coco_detector = None

        # Unified Vehicle Intelligence Engine
        self.vehicle_engine = get_vehicle_intelligence_engine()

        logger.info(f"VIGRAH AI Detection Engine Initialized | Device: {self.device}")
        self.temporal_tracker = TemporalTracker(consecutive_threshold=3, cooldown_seconds=10.0)

    def process_frame(self, frame, camera_id: int):
        if frame is None:
            return None, []

        h, w = frame.shape[:2]
        annotated_frame = frame.copy()
        raw_detections = []
        candidate_incident_types = set()

        person_boxes = []

        # 1. Step 1: Detect Pedestrians / Humans (Class 0)
        if self.coco_detector:
            try:
                coco_res = self.coco_detector.predict(
                    source=frame,
                    device=self.device,
                    classes=[0],  # 0=Person
                    conf=0.35,
                    imgsz=416,
                    verbose=False
                )
                for res in coco_res:
                    for box in res.boxes:
                        conf = float(box.conf[0].item())
                        xyxy = [int(v) for v in box.xyxy[0].tolist()]
                        person_boxes.append({"bbox": xyxy, "conf": conf})
            except Exception as e:
                logger.error(f"COCO pedestrian detector error: {e}")

        # 2. Step 2: Unified Vehicle Intelligence (Tracking, Type, Color, Plate, OCR)
        vehicle_records = []
        if self.vehicle_engine:
            vehicle_records, annotated_frame = self.vehicle_engine.process_frame(
                annotated_frame, 
                camera_id=str(camera_id)
            )

        vehicle_boxes = [{"bbox": v["bbox"], "conf": v["vehicle_confidence"]} for v in vehicle_records]

        # 3. Step 3: Custom Threat Model (best.onnx) for Fighting & Fire
        neural_fight_boxes = []
        if "base" in self.models:
            try:
                base_results = self.models["base"].predict(
                    source=frame,
                    device=self.device,
                    conf=0.35,
                    imgsz=640,
                    verbose=False
                )
                for res in base_results:
                    for box in res.boxes:
                        cls_id = int(box.cls[0].item())
                        cls_name = self.models["base"].names.get(cls_id, "unknown").lower()
                        conf = float(box.conf[0].item())
                        xyxy = [int(v) for v in box.xyxy[0].tolist()]

                        if "fire" in cls_name or "flame" in cls_name:
                            raw_detections.append({
                                "event_type": "Fire",
                                "confidence": round(conf, 2),
                                "bbox": xyxy,
                                "is_incident": True
                            })
                            candidate_incident_types.add("Fire")
                        elif "fight" in cls_name or "violence" in cls_name:
                            neural_fight_boxes.append({"bbox": xyxy, "conf": conf})
            except Exception as e:
                logger.error(f"Neural threat inference error: {e}")

        # 4. Step 4: Road Accident & Collision Analysis
        num_vehicles = len(vehicle_boxes)
        is_accident = False

        # Check Vehicle-to-Vehicle Collisions (IoU >= 0.22)
        if num_vehicles >= 2:
            for i in range(num_vehicles):
                for j in range(i + 1, num_vehicles):
                    v1 = vehicle_boxes[i]["bbox"]
                    v2 = vehicle_boxes[j]["bbox"]
                    v_iou = calculate_iou(v1, v2)
                    if v_iou >= 0.22:
                        accident_box = [
                            min(v1[0], v2[0]),
                            min(v1[1], v2[1]),
                            max(v1[2], v2[2]),
                            max(v1[3], v2[3])
                        ]
                        acc_conf = min(0.98, 0.82 + (v_iou * 0.6))
                        raw_detections.append({
                            "event_type": "Accident",
                            "confidence": round(float(acc_conf), 2),
                            "bbox": accident_box,
                            "is_incident": True
                        })
                        candidate_incident_types.add("Accident")
                        is_accident = True
                        break
                if is_accident:
                    break

        # Check Vehicle-to-Pedestrian Collision (IoU >= 0.15)
        if not is_accident and vehicle_boxes and person_boxes:
            for v in vehicle_boxes:
                for p in person_boxes:
                    vp_iou = calculate_iou(v["bbox"], p["bbox"])
                    if vp_iou >= 0.15:
                        impact_box = [
                            min(v["bbox"][0], p["bbox"][0]),
                            min(v["bbox"][1], p["bbox"][1]),
                            max(v["bbox"][2], p["bbox"][2]),
                            max(v["bbox"][3], p["bbox"][3])
                        ]
                        raw_detections.append({
                            "event_type": "Accident",
                            "confidence": round(0.92, 2),
                            "bbox": impact_box,
                            "is_incident": True
                        })
                        candidate_incident_types.add("Accident")
                        is_accident = True
                        break
                if is_accident:
                    break

        # 5. Step 5: Strict Multi-Person Conflict Verification
        num_people = len(person_boxes)

        if num_people <= 1:
            for p in person_boxes:
                raw_detections.append({
                    "event_type": "Person",
                    "confidence": round(p["conf"], 2),
                    "bbox": p["bbox"],
                    "is_incident": False
                })
        else:
            is_fighting = False
            for i in range(num_people):
                for j in range(i + 1, num_people):
                    p1 = person_boxes[i]["bbox"]
                    p2 = person_boxes[j]["bbox"]
                    iou = calculate_iou(p1, p2)

                    combo_w = max(p1[2], p2[2]) - min(p1[0], p2[0])
                    combo_h = max(p1[3], p2[3]) - min(p1[1], p2[1])
                    combo_aspect = combo_h / float(combo_w) if combo_w > 0 else 1.0

                    if iou > 0.18 or (neural_fight_boxes and iou > 0.08) or (iou > 0.10 and combo_aspect < 1.20):
                        fight_box = [
                            min(p1[0], p2[0]),
                            min(p1[1], p2[1]),
                            max(p1[2], p2[2]),
                            max(p1[3], p2[3])
                        ]
                        fight_conf = min(0.98, 0.78 + (iou * 0.8))
                        raw_detections.append({
                            "event_type": "Fighting",
                            "confidence": round(float(fight_conf), 2),
                            "bbox": fight_box,
                            "is_incident": True
                        })
                        candidate_incident_types.add("Fighting")
                        is_fighting = True
                        break
                if is_fighting:
                    break

            if not is_fighting:
                for p in person_boxes:
                    raw_detections.append({
                        "event_type": "Person",
                        "confidence": round(p["conf"], 2),
                        "bbox": p["bbox"],
                        "is_incident": False
                    })

        # 6. Temporal Confirmation (>=3 Consecutive Frames)
        confirmed_types = self.temporal_tracker.update(camera_id, candidate_incident_types)
        newly_saved_events = []

        # 7. Draw Pedestrian & Threat Annotations on Frame
        for det in raw_detections:
            ev_type = det["event_type"]
            conf = det["confidence"]
            x1, y1, x2, y2 = det["bbox"]
            is_incident = det.get("is_incident", False)
            color = EVENT_COLORS.get(ev_type, EVENT_COLORS["Default"])

            if is_incident:
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 3)
                label = f"🚨 ALERT: {ev_type.upper()} ({conf*100:.0f}%)"
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(annotated_frame, (x1, max(0, y1 - 22)), (x1 + tw + 6, max(22, y1)), color, -1)
                cv2.putText(annotated_frame, label, (x1 + 3, max(17, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            elif ev_type == "Person":
                # High-visibility Cyan box & Badge for Pedestrians / Humans
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (254, 242, 0), 2)
                p_label = f"PERSON {conf*100:.0f}%"
                (pw, ph), _ = cv2.getTextSize(p_label, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
                cv2.rectangle(annotated_frame, (x1, max(0, y1 - 18)), (x1 + pw + 6, max(18, y1)), (254, 242, 0), -1)
                cv2.putText(annotated_frame, p_label, (x1 + 3, max(14, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (10, 10, 10), 1, cv2.LINE_AA)

        # 8. Save Confirmed Incidents to Database & Capture Evidence Snapshot
        for confirmed_type in confirmed_types:
            type_dets = [d for d in raw_detections if d["event_type"] == confirmed_type and d.get("is_incident", False)]
            if not type_dets:
                continue
            best_det = max(type_dets, key=lambda d: d["confidence"])

            db: Session = SessionLocal()
            try:
                recent_cutoff = datetime.datetime.now() - datetime.timedelta(seconds=30)
                existing_incident = db.query(Event).filter(
                    Event.camera_id == camera_id,
                    Event.event_type == confirmed_type,
                    Event.timestamp >= recent_cutoff
                ).order_by(Event.timestamp.desc()).first()

                if existing_incident:
                    existing_incident.confirmation_count = (existing_incident.confirmation_count or 1) + 1
                    existing_incident.confidence = max(existing_incident.confidence, best_det["confidence"])
                    db.commit()
                else:
                    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    snapshot_filename = f"incident_cam{camera_id}_{confirmed_type}_{timestamp_str}.jpg"
                    snapshot_full_path = os.path.join(SNAPSHOTS_DIR, snapshot_filename)
                    cv2.imwrite(snapshot_full_path, annotated_frame)

                    event_record = Event(
                        camera_id=camera_id,
                        event_type=confirmed_type,
                        confidence=best_det["confidence"],
                        bbox=json.dumps(best_det["bbox"]),
                        snapshot_path=f"/snapshots/{snapshot_filename}",
                        severity="Critical" if confirmed_type in ["Fighting", "Fire"] else "High",
                        status="Active",
                        confirmation_count=1
                    )
                    db.add(event_record)
                    db.commit()
                    db.refresh(event_record)
                    newly_saved_events.append({
                        "id": event_record.id,
                        "camera_id": camera_id,
                        "event_type": confirmed_type,
                        "confidence": event_record.confidence,
                        "timestamp": str(event_record.timestamp),
                        "snapshot_path": event_record.snapshot_path,
                        "severity": event_record.severity
                    })
                    logger.info(f"🚨 [NEW INVESTIGATIVE INCIDENT #{event_record.id}] Cam {camera_id} | {confirmed_type.upper()} | Conf: {best_det['confidence']:.2f}")
            except Exception as db_err:
                logger.error(f"Failed to persist incident to DB: {db_err}")
                db.rollback()
            finally:
                db.close()

        # Add HUD status header
        hud_text = f"VIGRAH AI | CAM #{camera_id} | ACTIVE"
        cv2.putText(annotated_frame, hud_text, (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 128), 2, cv2.LINE_AA)

        return annotated_frame, newly_saved_events
