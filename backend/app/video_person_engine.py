import os
import cv2
import json
import time
import math
import uuid
import datetime
import hashlib
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

from .database import SessionLocal, Base, engine, IS_POSTGRES
from .models import VideoEvidence, PersonVideoTrack, PersonVideoSighting
from .person_reid.factory import get_person_reid_backend
from .person_reid.base import PersonReIDBackend
from .tracking.byte_tracker import BYTETracker, STrack
from .tracking.quality_filter import compute_person_crop_quality, QualityFilterConfig

logger = logging.getLogger("video_person_engine")

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE_DIR = os.path.join(BASE_DIR, "evidence", "persons")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads", "videos")
SAMPLES_DIR = os.path.join(BASE_DIR, "samples")

os.makedirs(EVIDENCE_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(SAMPLES_DIR, exist_ok=True)


class VideoPersonEngine:
    """
    Production Video Person Ingestion & Cross-Camera Re-Identification Engine.
    - Official TransReID Transformer Model (768-D dynamically validated embeddings)
    - YOLO11 Person Detection (Class 0)
    - Official ByteTrack Multi-Object Tracker (Kalman filter, 2-stage association)
    - Deterministic Quality Filtering (Resolution, Blur, Contrast, Illumination)
    - PostgreSQL + pgvector Vector Search (with NumPy SQLite fallback)
    - Track-Level Quality-Weighted Mean Embeddings
    """
    def __init__(self):
        self.detector = None
        self._init_detector()
        self.reid_backend: PersonReIDBackend = get_person_reid_backend()
        self.quality_config = QualityFilterConfig()

    def _init_detector(self):
        if YOLO is not None:
            yolo_candidates = [
                os.path.join(BASE_DIR, "yolo11n.pt"),
                os.path.join(BASE_DIR, "weights", "yolo11n.pt"),
                os.path.join(os.path.dirname(BASE_DIR), "backend", "yolo11n.pt"),
                "yolo11n.pt"
            ]
            for yp in yolo_candidates:
                if os.path.exists(yp):
                    try:
                        self.detector = YOLO(yp)
                        logger.info(f"✓ VideoPersonEngine: Initialized YOLO11n person detector from {yp}.")
                        return
                    except Exception as e:
                        logger.warning(f"Failed to load YOLO from {yp}: {e}")
            try:
                self.detector = YOLO("yolo11n.pt")
                logger.info("✓ VideoPersonEngine: Initialized YOLO11n person detector.")
            except Exception as e:
                logger.warning(f"VideoPersonEngine YOLO initialization warning: {e}")
                self.detector = None

    def compute_file_sha256(self, file_path: str) -> str:
        """Computes SHA-256 checksum of a video file for idempotency."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def detect_query_person(self, img: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[List[int]], float, str]:
        """
        Validates query image:
        Requires strictly ONE person.
        Returns: (cropped_img, bbox, confidence, status_code)
        Status codes:
            - 'OK'
            - 'NO_PERSON_DETECTED'
            - 'MULTIPLE_PERSONS_DETECTED'
            - 'QUERY_QUALITY_TOO_LOW'
        """
        if img is None or img.size == 0:
            return None, None, 0.0, "NO_PERSON_DETECTED"

        h, w = img.shape[:2]
        if w < 15 or h < 25:
            return None, None, 0.0, "NO_PERSON_DETECTED"

        # 1. Run YOLO person detection at sensitive threshold
        person_boxes = []
        if self.detector is not None:
            try:
                results = self.detector(img, verbose=False, classes=[0], conf=0.15)
                for r in results:
                    for box in r.boxes:
                        if int(box.cls[0].item()) == 0:
                            conf = float(box.conf[0].item())
                            xyxy = [int(v) for v in box.xyxy[0].tolist()]
                            bw = xyxy[2] - xyxy[0]
                            bh = xyxy[3] - xyxy[1]
                            if bw >= 15 and bh >= 25:
                                person_boxes.append((xyxy, conf, bw * bh))
            except Exception as e:
                logger.warning(f"Query YOLO detection warning: {e}")

        # Check for multiple persons detected
        if len(person_boxes) > 1:
            return None, None, 0.0, "MULTIPLE_PERSONS_DETECTED"

        # If 1 person detected via YOLO
        if len(person_boxes) == 1:
            best_box, best_conf, _ = person_boxes[0]
            x1 = max(0, best_box[0])
            y1 = max(0, best_box[1])
            x2 = min(w, best_box[2])
            y2 = min(h, best_box[3])
            crop = img[y1:y2, x1:x2]

            quality_score, is_acceptable, reason = compute_person_crop_quality(
                crop, (x1, y1, x2, y2), (h, w), self.quality_config
            )
            if not is_acceptable and quality_score < 0.15:
                return None, None, 0.0, "QUERY_QUALITY_TOO_LOW"

            return crop, [x1, y1, x2, y2], best_conf, "OK"

        # If YOLO found no person, check if image is a pre-cropped vertical person portrait
        if h >= 1.20 * w and w >= 20 and h >= 40:
            person_crop = img
            quality_score, is_acceptable, reason = compute_person_crop_quality(
                person_crop, (0, 0, w, h), (h, w), self.quality_config
            )
            if not is_acceptable and quality_score < 0.15:
                return None, None, 0.0, "QUERY_QUALITY_TOO_LOW"
            return person_crop, [0, 0, w, h], 0.90, "OK"

        return None, None, 0.0, "NO_PERSON_DETECTED"

    def process_video_evidence(
        self,
        video_path: str,
        source_id: str,
        source_name: Optional[str] = None,
        camera_id: Optional[str] = "CAM-01",
        location: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        target_fps: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Asynchronous Video Indexing Pipeline:
        1. Checks SHA-256 idempotency.
        2. Sets status = 'processing'.
        3. Decodes video at configured PERSON_INDEX_FPS (default 3.0 FPS).
        4. Detects persons via YOLO11 (class 0).
        5. Tracks candidate identities via official ByteTrack.
        6. Assesses deterministic crop quality.
        7. Extracts TransReID embeddings for valid observations.
        8. Aggregates sightings per track into Quality-Weighted Mean L2-Normalized Embeddings.
        9. Persists to PostgreSQL+pgvector / SQLite.
        10. Sets status = 'ready'.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found at: {video_path}")

        source_hash = self.compute_file_sha256(video_path)
        filename = os.path.basename(video_path)
        display_name = source_name or f"{source_id}: {filename}"
        cam_code = camera_id or "CAM-01"

        db: Session = SessionLocal()
        try:
            # 1. Update/Create VideoEvidence Record in 'processing' status
            ve_record = db.query(VideoEvidence).filter(VideoEvidence.source_id == source_id).first()
            if not ve_record:
                ve_record = VideoEvidence(source_id=source_id)
                db.add(ve_record)

            ve_record.filename = filename
            ve_record.file_path = video_path
            ve_record.source_name = display_name
            ve_record.source_hash = source_hash
            ve_record.camera_id = cam_code
            ve_record.location = location or "Surveillance Sector"
            ve_record.latitude = lat
            ve_record.longitude = lon
            ve_record.status = "processing"
            ve_record.error_message = None
            db.commit()
        finally:
            db.close()

        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Could not open video stream for file: {video_path}")

            video_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            duration_sec = total_frames / max(video_fps, 1.0)

            # Sampling rate from environment or argument
            sampling_fps = target_fps or float(os.getenv("PERSON_INDEX_FPS", "3.0"))
            sample_step = max(1, int(round(video_fps / max(0.5, sampling_fps))))

            source_evidence_dir = os.path.join(EVIDENCE_DIR, source_id)
            os.makedirs(source_evidence_dir, exist_ok=True)

            # Initialize ByteTrack for this video stream
            track_thresh = float(os.getenv("BYTE_TRACK_THRESH", "0.50"))
            match_thresh = float(os.getenv("BYTE_MATCH_THRESH", "0.70"))
            track_buffer = int(os.getenv("BYTE_TRACK_BUFFER", "30"))
            tracker = BYTETracker(
                track_thresh=track_thresh,
                match_thresh=match_thresh,
                track_buffer=track_buffer,
                frame_rate=int(video_fps)
            )

            # Track collector: track_id -> dict of sightings & attributes
            tracks_map: Dict[str, Dict[str, Any]] = {}
            frame_idx = 0

            while True:
                ret, frame = cap.read()
                if not ret or frame is None:
                    break

                if frame_idx % sample_step != 0:
                    frame_idx += 1
                    continue

                timestamp_sec = frame_idx / max(video_fps, 1.0)
                mins = int(timestamp_sec // 60)
                secs = int(timestamp_sec % 60)
                formatted_time = f"{mins:02d}:{secs:02d}"

                frame_h, frame_w = frame.shape[:2]

                # YOLO Detection (Class 0: Person)
                detections_list = []
                if self.detector is not None:
                    try:
                        results = self.detector(frame, verbose=False, classes=[0], conf=0.30)
                        for r in results:
                            for box in r.boxes:
                                cls_id = int(box.cls[0].item())
                                conf = float(box.conf[0].item())
                                if cls_id == 0:
                                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                                    detections_list.append([x1, y1, x2, y2, conf, 0])
                    except Exception as e:
                        logger.warning(f"Detection error at frame {frame_idx}: {e}")

                detections_arr = np.array(detections_list, dtype=np.float32) if detections_list else np.empty((0, 6), dtype=np.float32)

                # ByteTrack Update
                online_targets = tracker.update(detections_arr)

                # Process tracked objects
                for t in online_targets:
                    tlbr = t.tlbr
                    x1 = max(0, int(tlbr[0]))
                    y1 = max(0, int(tlbr[1]))
                    x2 = min(frame_w, int(tlbr[2]))
                    y2 = min(frame_h, int(tlbr[3]))
                    track_num = t.track_id
                    track_str = f"TRK-{track_num:03d}"

                    crop = frame[y1:y2, x1:x2]
                    if crop.size == 0 or crop.shape[0] < 10 or crop.shape[1] < 10:
                        continue

                    # Compute Quality Score
                    quality_score, is_acceptable, reason = compute_person_crop_quality(
                        crop, (x1, y1, x2, y2), (frame_h, frame_w), self.quality_config
                    )

                    # Extract TransReID Feature Vector
                    embedding = self.reid_backend.extract_embedding(crop)

                    # Save crop to disk
                    track_dir = os.path.join(source_evidence_dir, track_str)
                    os.makedirs(track_dir, exist_ok=True)
                    sighting_num = len(tracks_map.get(track_str, {}).get("sightings", [])) + 1
                    sighting_fname = f"frame_{frame_idx}_{sighting_num}.jpg"
                    sighting_disk_path = os.path.join(track_dir, sighting_fname)
                    cv2.imwrite(sighting_disk_path, crop)

                    sighting_rel_url = f"/evidence/persons/{source_id}/{track_str}/{sighting_fname}"

                    if track_str not in tracks_map:
                        tracks_map[track_str] = {
                            "track_id": track_str,
                            "source_id": source_id,
                            "camera_id": cam_code,
                            "camera_name": display_name,
                            "location": location or "Surveillance Sector",
                            "start_time_sec": timestamp_sec,
                            "first_seen_formatted": formatted_time,
                            "last_time_sec": timestamp_sec,
                            "last_seen_formatted": formatted_time,
                            "sightings": []
                        }

                    tracks_map[track_str]["last_time_sec"] = timestamp_sec
                    tracks_map[track_str]["last_seen_formatted"] = formatted_time
                    tracks_map[track_str]["sightings"].append({
                        "sighting_id": f"SIGHT-{source_id}-{track_str}-{sighting_num}",
                        "timestamp_sec": timestamp_sec,
                        "frame_number": frame_idx,
                        "formatted_time": formatted_time,
                        "crop_path": sighting_rel_url,
                        "crop_disk_path": sighting_disk_path,
                        "bbox": [x1, y1, x2, y2],
                        "confidence": float(t.score),
                        "quality_score": float(quality_score),
                        "detection_confidence": float(t.score),
                        "embedding": embedding,
                        "crop_area": (x2 - x1) * (y2 - y1)
                    })

                frame_idx += 1

            cap.release()

            # Filter valid tracks with at least 1 sighting
            valid_tracks = {k: v for k, v in tracks_map.items() if len(v["sightings"]) >= 1}

            # Persist to Database
            db = SessionLocal()
            total_sightings_count = 0
            try:
                # Clear existing tracks for this source if re-indexing
                db.query(PersonVideoSighting).filter(PersonVideoSighting.source_id == source_id).delete()
                db.query(PersonVideoTrack).filter(PersonVideoTrack.source_id == source_id).delete()
                db.commit()

                ve = db.query(VideoEvidence).filter(VideoEvidence.source_id == source_id).first()
                if not ve:
                    ve = VideoEvidence(source_id=source_id)
                    db.add(ve)

                ve.filename = filename
                ve.file_path = video_path
                ve.source_name = display_name
                ve.source_hash = source_hash
                ve.camera_id = cam_code
                ve.location = location or "Surveillance Sector"
                ve.latitude = lat
                ve.longitude = lon
                ve.duration_sec = duration_sec
                ve.fps = video_fps
                ve.total_frames = total_frames
                ve.status = "ready"
                ve.track_count = len(valid_tracks)

                # Persist tracks and sightings
                now_dt = datetime.datetime.now(datetime.timezone.utc)
                model_name = self.reid_backend.model_name
                model_ver = self.reid_backend.model_version
                emb_dim = self.reid_backend.embedding_dim

                for trk_id, trk_data in valid_tracks.items():
                    sightings = trk_data["sightings"]
                    total_sightings_count += len(sightings)

                    # Pick highest quality sighting crop as representative
                    best_sighting = max(sightings, key=lambda s: s["quality_score"] * s["confidence"] * math.sqrt(s["crop_area"]))
                    mean_quality = float(np.mean([s["quality_score"] for s in sightings]))

                    # Quality-weighted Mean Track Embedding
                    weights = np.array([max(0.1, s["quality_score"]) for s in sightings], dtype=np.float32)
                    all_embs = np.array([s["embedding"] for s in sightings], dtype=np.float32)
                    weighted_mean = np.average(all_embs, axis=0, weights=weights)
                    norm = np.linalg.norm(weighted_mean)
                    if norm > 1e-6:
                        weighted_mean = weighted_mean / norm
                    else:
                        weighted_mean = np.zeros(emb_dim, dtype=np.float32)

                    db_track = PersonVideoTrack(
                        track_id=trk_id,
                        source_id=source_id,
                        camera_id=cam_code,
                        camera_name=display_name,
                        location=location or "Surveillance Sector",
                        start_time_sec=trk_data["start_time_sec"],
                        end_time_sec=trk_data["last_time_sec"],
                        first_seen_formatted=trk_data["first_seen_formatted"],
                        last_seen_formatted=trk_data["last_seen_formatted"],
                        detection_count=len(sightings),
                        quality_score=round(mean_quality, 4),
                        representative_crop_path=best_sighting["crop_path"],
                        average_embedding=json.dumps(weighted_mean.tolist()),
                        reid_model=model_name,
                        reid_model_version=model_ver,
                        embedding_dim=emb_dim,
                        index_version="v1.0",
                        embedding_created_at=now_dt
                    )
                    db.add(db_track)

                    for s in sightings:
                        db_sighting = PersonVideoSighting(
                            sighting_id=s["sighting_id"],
                            track_id=trk_id,
                            source_id=source_id,
                            camera_id=cam_code,
                            timestamp_sec=float(s["timestamp_sec"]),
                            frame_number=int(s["frame_number"]),
                            formatted_time=str(s["formatted_time"]),
                            crop_path=str(s["crop_path"]),
                            bbox=json.dumps(s["bbox"]),
                            confidence=float(s["confidence"]),
                            quality_score=float(s["quality_score"]),
                            detection_confidence=float(s["detection_confidence"]),
                            embedding=json.dumps(s["embedding"].tolist()),
                            reid_model=model_name,
                            reid_model_version=model_ver,
                            embedding_dim=emb_dim,
                            index_version="v1.0",
                            embedding_created_at=now_dt
                        )
                        db.add(db_sighting)

                ve.sighting_count = total_sightings_count
                db.commit()
                logger.info(
                    f"✓ Video Evidence [{source_id}] Successfully Indexed ({model_name} {emb_dim}-D): "
                    f"{len(valid_tracks)} tracks, {total_sightings_count} sightings."
                )
            except Exception as e:
                db.rollback()
                logger.error(f"Error persisting video tracks for {source_id}: {e}")
                raise e
            finally:
                db.close()

            return {
                "source_id": source_id,
                "source_name": display_name,
                "camera_id": cam_code,
                "filename": filename,
                "duration_sec": round(duration_sec, 2),
                "track_count": len(valid_tracks),
                "sighting_count": total_sightings_count,
                "status": "ready"
            }

        except Exception as e:
            logger.error(f"Failed to process video {source_id}: {e}", exc_info=True)
            db = SessionLocal()
            try:
                ve_rec = db.query(VideoEvidence).filter(VideoEvidence.source_id == source_id).first()
                if ve_rec:
                    ve_rec.status = "failed"
                    ve_rec.error_message = str(e)
                    db.commit()
            finally:
                db.close()
            raise e

    def get_evidence_crop_file_path(self, source_id: str, track_id: str, filename: Optional[str] = None) -> Optional[str]:
        """Locates verified evidence crop on disk."""
        track_dir = os.path.join(EVIDENCE_DIR, source_id, track_id)
        if not os.path.exists(track_dir):
            return None

        if filename:
            target = os.path.join(track_dir, os.path.basename(filename))
            if os.path.exists(target):
                return target

        files = [f for f in os.listdir(track_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if files:
            files.sort()
            return os.path.join(track_dir, files[0])
        return None

    def search_person_gallery(
        self,
        query_img: np.ndarray,
        min_similarity: float = 0.50,
        camera_id: Optional[str] = None,
        location: Optional[str] = None,
        time_start: Optional[float] = None,
        time_end: Optional[float] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Executes genuine Person Re-ID search against indexed CCTV gallery:
        1. Checks query image for strictly one valid person crop.
        2. Evaluates query crop quality.
        3. Extracts TransReID embedding.
        4. Queries vector gallery (pgvector / optimized NumPy).
        5. Groups sightings into candidate tracks.
        6. Returns structured visual similarity candidates.
        """
        top_k = min(max(1, limit), 50)

        # 1. Query Person Detection & Quality Validation
        crop, bbox, det_conf, status_code = self.detect_query_person(query_img)
        if status_code != "OK":
            error_messages = {
                "NO_PERSON_DETECTED": "No person detected in the uploaded photograph. Please upload a clear photo containing a person.",
                "MULTIPLE_PERSONS_DETECTED": "Multiple people detected in the uploaded image. Please upload a photo containing exactly one person.",
                "QUERY_QUALITY_TOO_LOW": "The uploaded image is not suitable for reliable person search. Image quality is too low (excessive blur, severe underexposure, or low resolution)."
            }
            return {
                "status": "error",
                "error_code": status_code,
                "message": error_messages.get(status_code, "Invalid query photograph."),
                "total_candidates": 0,
                "matches": []
            }

        # 2. Compute query crop quality
        q_quality, _, _ = compute_person_crop_quality(crop)

        # 3. Extract TransReID Query Embedding
        query_emb = self.reid_backend.extract_embedding(crop)
        q_norm = np.linalg.norm(query_emb)
        if q_norm < 1e-6:
            return {
                "status": "error",
                "error_code": "EMBEDDING_FAILED",
                "message": "Could not generate neural feature embedding for the query image.",
                "total_candidates": 0,
                "matches": []
            }

        query_hash = hashlib.md5(query_emb.tobytes()).hexdigest()[:8]

        # 4. Search Database Gallery
        db: Session = SessionLocal()
        all_matches = []
        try:
            tracks_query = db.query(PersonVideoTrack)

            # Optional Camera / Source Filter
            if camera_id and camera_id not in ("ALL", "All", ""):
                tracks_query = tracks_query.filter(
                    (PersonVideoTrack.camera_id == camera_id) | (PersonVideoTrack.source_id == camera_id)
                )
            if location and location not in ("ALL", "All", ""):
                tracks_query = tracks_query.filter(PersonVideoTrack.location.ilike(f"%{location}%"))

            tracks = tracks_query.all()
            if not tracks:
                return {
                    "status": "success",
                    "query": {
                        "model": self.reid_backend.model_name,
                        "embedding_dimension": self.reid_backend.embedding_dim,
                        "quality": q_quality,
                        "query_hash": query_hash
                    },
                    "total_candidates": 0,
                    "returned_candidates": 0,
                    "matches": []
                }

            ve_map = {ve.source_id: ve for ve in db.query(VideoEvidence).all()}

            for trk in tracks:
                if not trk.average_embedding:
                    continue
                try:
                    trk_emb = np.array(json.loads(trk.average_embedding), dtype=np.float32)
                except Exception:
                    continue

                if trk_emb.shape[0] != self.reid_backend.embedding_dim:
                    # Model dimension mismatch -> skip (requires re-indexing with current model)
                    continue

                # Cosine Similarity
                cos_sim = PersonReIDBackend.compare(query_emb, trk_emb)

                # Filter by minimum similarity threshold
                if cos_sim < min_similarity:
                    continue

                # Time Window Filter
                if time_start is not None and trk.end_time_sec < time_start:
                    continue
                if time_end is not None and trk.start_time_sec > time_end:
                    continue

                ve = ve_map.get(trk.source_id)
                loc_str = trk.location or (ve.location if ve else "Surveillance Sector")
                cam_code = trk.camera_id or (ve.camera_id if ve else "CAM-01")
                cam_name = trk.camera_name or (ve.source_name if ve else cam_code)

                # Sighting timeline for this candidate
                sightings_records = db.query(PersonVideoSighting).filter(
                    PersonVideoSighting.source_id == trk.source_id,
                    PersonVideoSighting.track_id == trk.track_id
                ).order_by(PersonVideoSighting.timestamp_sec.asc()).all()

                sightings_list = []
                for s in sightings_records:
                    s_fname = os.path.basename(s.crop_path) if s.crop_path else "crop.jpg"
                    sightings_list.append({
                        "sighting_id": s.sighting_id,
                        "formatted_time": s.formatted_time,
                        "timestamp_sec": round(s.timestamp_sec, 2),
                        "crop_url": f"/api/person/evidence/{trk.source_id}/{trk.track_id}/{s_fname}",
                        "bbox": json.loads(s.bbox) if s.bbox else [],
                        "confidence": round(float(s.confidence), 2),
                        "quality_score": round(float(s.quality_score), 2)
                    })

                all_matches.append({
                    "track_id": trk.track_id,
                    "source_id": trk.source_id,
                    "camera_id": cam_code,
                    "camera_name": cam_name,
                    "location": loc_str,
                    "first_seen": trk.first_seen_formatted or f"{int(trk.start_time_sec//60):02d}:{int(trk.start_time_sec%60):02d}",
                    "last_seen": trk.last_seen_formatted or f"{int(trk.end_time_sec//60):02d}:{int(trk.end_time_sec%60):02d}",
                    "start_time_sec": round(trk.start_time_sec, 2),
                    "end_time_sec": round(trk.end_time_sec, 2),
                    "similarity": round(float(cos_sim), 4),
                    "similarity_percent": int(round(cos_sim * 100)),
                    "quality_score": round(float(trk.quality_score or 1.0), 2),
                    "sighting_count": trk.detection_count,
                    "representative_crop_url": f"/api/person/evidence/{trk.source_id}/{trk.track_id}",
                    "sightings": sightings_list
                })

            # Sort descending by similarity
            all_matches.sort(key=lambda m: m["similarity"], reverse=True)
            top_matches = all_matches[:top_k]

            for idx, m in enumerate(top_matches):
                m["rank"] = idx + 1
                m["is_best_match"] = (idx == 0)

            logger.info(
                f"[PersonSearch] QueryHash={query_hash} Gallery={len(tracks)} "
                f"MatchedThreshold={len(all_matches)} ReturnedTopK={len(top_matches)}"
            )

        finally:
            db.close()

        return {
            "status": "success",
            "query": {
                "model": self.reid_backend.model_name,
                "embedding_dimension": self.reid_backend.embedding_dim,
                "quality": q_quality,
                "query_hash": query_hash
            },
            "total_candidates": len(all_matches),
            "returned_candidates": len(top_matches),
            "limit": top_k,
            "min_similarity": min_similarity,
            "matches": top_matches
        }

    def reindex_all_video_evidence(self):
        """
        Re-indexes all existing video footage in uploads/samples with the active Re-ID model.
        """
        logger.info(f"Re-indexing video footage with active model [{self.reid_backend.model_name}]...")
        db: Session = SessionLocal()
        try:
            videos = db.query(VideoEvidence).all()
        finally:
            db.close()

        for v in videos:
            if os.path.exists(v.file_path):
                try:
                    self.process_video_evidence(
                        video_path=v.file_path,
                        source_id=v.source_id,
                        source_name=v.source_name,
                        camera_id=v.camera_id,
                        location=v.location,
                        lat=v.latitude,
                        lon=v.longitude
                    )
                except Exception as e:
                    logger.error(f"Re-indexing failed for {v.source_id}: {e}")


video_person_engine = VideoPersonEngine()
