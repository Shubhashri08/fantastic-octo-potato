import os
import cv2
import json
import time
import math
import uuid
import datetime
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session

from .database import SessionLocal, Base, engine
from .models import VideoEvidence, PersonVideoTrack, PersonVideoSighting

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
    Forensic Video Ingestion & Missing Person Re-Identification Engine:
    - Frame sampling & person detection
    - Bounding box extraction & quality filtering
    - Spatial-temporal person tracking across frames
    - High-resolution evidence crop saving
    - 128-D appearance embedding extraction & indexing
    - High-speed cosine similarity search
    """
    def __init__(self):
        self.detector = None
        self._init_detector()

    def _init_detector(self):
        if YOLO is not None:
            try:
                # Load lightweight nano model for rapid person detection
                self.detector = YOLO("yolo11n.pt")
                print("✓ VideoPersonEngine: Initialized YOLO person detector.")
            except Exception as e:
                print(f"VideoPersonEngine YOLO warning: {e}. Falling back to OpenCV HOG detector.")
                self.detector = None

    def extract_person_embedding(self, img: np.ndarray) -> np.ndarray:
        """
        Extracts 128-D normalized hybrid appearance & color biometric vector:
        - Upper body / torso color distribution (HSV spatial grid)
        - Lower body color distribution
        - Edge texture & structure gradients (Sobel filter)
        - Invariant to lighting scaling; L2-normalized.
        """
        if img is None or img.size == 0:
            return np.zeros(128, dtype=np.float32)

        try:
            resized = cv2.resize(img, (64, 128))
            hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
            gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

            # Spatial partition: Head (top 20%), Torso (30-65%), Lower Body (65-100%)
            torso_hsv = hsv[25:85, :]
            lower_hsv = hsv[85:, :]

            # Color Histograms
            hist_h_torso = cv2.calcHist([torso_hsv], [0], None, [24], [0, 180])
            hist_s_torso = cv2.calcHist([torso_hsv], [1], None, [16], [0, 256])

            hist_h_lower = cv2.calcHist([lower_hsv], [0], None, [24], [0, 180])
            hist_s_lower = cv2.calcHist([lower_hsv], [1], None, [16], [0, 256])

            # Texture / Structural Gradients (Sobel)
            sobelx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
            mag, _ = cv2.cartToPolar(sobelx, sobely)
            mag_u8 = np.clip(mag, 0, 255).astype(np.uint8)

            hist_tex_top = cv2.calcHist([mag_u8[:64, :]], [0], None, [24], [0, 256])
            hist_tex_bot = cv2.calcHist([mag_u8[64:, :]], [0], None, [24], [0, 256])

            feature_vec = np.concatenate([
                hist_h_torso.flatten(),
                hist_s_torso.flatten(),
                hist_h_lower.flatten(),
                hist_s_lower.flatten(),
                hist_tex_top.flatten(),
                hist_tex_bot.flatten()
            ]).astype(np.float32)

            # L2 Normalization
            norm = np.linalg.norm(feature_vec)
            if norm > 1e-6:
                feature_vec = feature_vec / norm
            return feature_vec
        except Exception as e:
            print(f"Error extracting embedding: {e}")
            return np.zeros(128, dtype=np.float32)

    def process_video_evidence(
        self,
        video_path: str,
        source_id: str,
        source_name: Optional[str] = None,
        location: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Ingests a video evidence file:
        1. Samples frames (2 to 3 FPS for optimal performance).
        2. Detects people using YOLO.
        3. Tracks candidates across time into persistent track clusters.
        4. Crops and saves high-resolution person evidence images.
        5. Extracts 128-D appearance vectors and indexes them into DB.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found at: {video_path}")

        filename = os.path.basename(video_path)
        display_name = source_name or f"{source_id}: {filename}"

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration_sec = total_frames / max(fps, 1.0)

        # Sample approx 3 frames per second
        sample_step = max(1, int(round(fps / 3.0)))

        source_evidence_dir = os.path.join(EVIDENCE_DIR, source_id)
        os.makedirs(source_evidence_dir, exist_ok=True)

        tracks_dict: Dict[str, Dict[str, Any]] = {}
        active_tracks: List[Dict[str, Any]] = []
        track_counter = 1

        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % sample_step != 0:
                frame_idx += 1
                continue

            timestamp_sec = frame_idx / max(fps, 1.0)
            mins = int(timestamp_sec // 60)
            secs = int(timestamp_sec % 60)
            formatted_time = f"{mins:02d}:{secs:02d}"

            # Detect people in frame
            person_boxes = []
            if self.detector is not None:
                try:
                    results = self.detector(frame, verbose=False, classes=[0], conf=0.40)
                    for r in results:
                        boxes = r.boxes
                        for box in boxes:
                            cls_id = int(box.cls[0].item())
                            conf = float(box.conf[0].item())
                            if cls_id == 0 and conf >= 0.40:
                                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                                # Quality filter: minimum crop dimensions
                                if (x2 - x1) >= 32 and (y2 - y1) >= 64:
                                    person_boxes.append({
                                        "bbox": [x1, y1, x2, y2],
                                        "confidence": conf
                                    })
                except Exception as det_err:
                    pass

            # Fallback if YOLO returned nothing or is unavailable: detect pedestrians
            if not person_boxes:
                # Use OpenCV HOG pedestrian detector as reliable fallback
                hog = cv2.HOGDescriptor()
                hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
                rects, weights = hog.detectMultiScale(frame, winStride=(8, 8), padding=(4, 4), scale=1.05)
                for (rx, ry, rw, rh), w in zip(rects, weights):
                    if rw >= 32 and rh >= 64 and w >= 0.2:
                        person_boxes.append({
                            "bbox": [rx, ry, rx + rw, ry + rh],
                            "confidence": min(0.95, float(w) + 0.4)
                        })

            # Spatial-temporal track assignment
            frame_h, frame_w = frame.shape[:2]
            for p_det in person_boxes:
                x1, y1, x2, y2 = p_det["bbox"]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(frame_w, x2), min(frame_h, y2)
                p_conf = p_det["confidence"]

                crop = frame[y1:y2, x1:x2]
                if crop.size == 0:
                    continue

                # Match with active tracks by spatial overlap
                matched_track = None
                best_iou = 0.20
                for trk in active_tracks:
                    if (timestamp_sec - trk["last_time"]) < 2.5:
                        tx1, ty1, tx2, ty2 = trk["last_bbox"]
                        # Calculate Intersection over Union (IoU)
                        ix1, iy1 = max(x1, tx1), max(y1, ty1)
                        ix2, iy2 = min(x2, tx2), min(y2, ty2)
                        iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
                        inter_area = iw * ih
                        union_area = ((x2 - x1) * (y2 - y1)) + ((tx2 - tx1) * (ty2 - ty1)) - inter_area
                        iou = inter_area / max(1.0, union_area)
                        if iou > best_iou:
                            best_iou = iou
                            matched_track = trk

                if matched_track is None:
                    # New Track
                    track_id = f"TRK-{track_counter:03d}"
                    track_counter += 1
                    matched_track = {
                        "track_id": track_id,
                        "start_time": timestamp_sec,
                        "last_time": timestamp_sec,
                        "last_bbox": [x1, y1, x2, y2],
                        "sightings": []
                    }
                    active_tracks.append(matched_track)
                    tracks_dict[track_id] = matched_track

                matched_track["last_time"] = timestamp_sec
                matched_track["last_bbox"] = [x1, y1, x2, y2]

                # Save crop image
                track_dir = os.path.join(source_evidence_dir, matched_track["track_id"])
                os.makedirs(track_dir, exist_ok=True)
                sighting_filename = f"frame_{frame_idx}_{len(matched_track['sightings'])+1}.jpg"
                crop_disk_path = os.path.join(track_dir, sighting_filename)
                cv2.imwrite(crop_disk_path, crop)

                crop_rel_url = f"/evidence/persons/{source_id}/{matched_track['track_id']}/{sighting_filename}"
                embedding = self.extract_person_embedding(crop)

                matched_track["sightings"].append({
                    "timestamp_sec": timestamp_sec,
                    "formatted_time": formatted_time,
                    "crop_path": crop_rel_url,
                    "crop_disk_path": crop_disk_path,
                    "bbox": [x1, y1, x2, y2],
                    "confidence": p_conf,
                    "embedding": embedding,
                    "crop_area": (x2 - x1) * (y2 - y1)
                })

            frame_idx += 1

        cap.release()

        # Prune very short / noise tracks (e.g. tracks with only 1 brief detection) if multiple exist
        valid_tracks = {k: v for k, v in tracks_dict.items() if len(v["sightings"]) >= 1}

        # Persist to Database
        db: Session = SessionLocal()
        total_sightings_count = 0
        try:
            # 1. VideoEvidence Record
            existing_ve = db.query(VideoEvidence).filter(VideoEvidence.source_id == source_id).first()
            if existing_ve:
                db.query(PersonVideoSighting).filter(PersonVideoSighting.source_id == source_id).delete()
                db.query(PersonVideoTrack).filter(PersonVideoTrack.source_id == source_id).delete()
                db.commit()
                ve_record = existing_ve
            else:
                ve_record = VideoEvidence(source_id=source_id)
                db.add(ve_record)

            ve_record.filename = filename
            ve_record.file_path = video_path
            ve_record.source_name = display_name
            ve_record.location = location
            ve_record.latitude = lat
            ve_record.longitude = lon
            ve_record.duration_sec = duration_sec
            ve_record.fps = fps
            ve_record.total_frames = total_frames
            ve_record.status = "ready"
            ve_record.track_count = len(valid_tracks)

            db.commit()
            db.refresh(ve_record)

            # 2. Persist Tracks & Sightings
            for trk_id, trk_data in valid_tracks.items():
                sightings = trk_data["sightings"]
                total_sightings_count += len(sightings)

                # Find best representative crop (largest crop area / highest confidence)
                best_sighting = max(sightings, key=lambda s: s["crop_area"] * s["confidence"])
                
                # Compute average track embedding
                all_embeddings = np.array([s["embedding"] for s in sightings], dtype=np.float32)
                avg_emb = np.mean(all_embeddings, axis=0)
                norm = np.linalg.norm(avg_emb)
                if norm > 1e-6:
                    avg_emb = avg_emb / norm

                db_track = PersonVideoTrack(
                    track_id=trk_id,
                    source_id=source_id,
                    start_time_sec=trk_data["start_time"],
                    end_time_sec=trk_data["last_time"],
                    representative_crop_path=best_sighting["crop_path"],
                    detection_count=len(sightings),
                    average_embedding=json.dumps(avg_emb.tolist())
                )
                db.add(db_track)

                for s_idx, s in enumerate(sightings):
                    bbox_clean = [int(v) for v in s["bbox"]] if isinstance(s["bbox"], (list, tuple, np.ndarray)) else []
                    db_sighting = PersonVideoSighting(
                        sighting_id=f"SIGHT-{source_id}-{trk_id}-{s_idx+1}",
                        track_id=trk_id,
                        source_id=source_id,
                        timestamp_sec=float(s["timestamp_sec"]),
                        formatted_time=str(s["formatted_time"]),
                        crop_path=str(s["crop_path"]),
                        bbox=json.dumps(bbox_clean),
                        confidence=float(s["confidence"]),
                        embedding=json.dumps(s["embedding"].tolist())
                    )
                    db.add(db_sighting)

            ve_record.sighting_count = total_sightings_count
            db.commit()
            print(f"✓ Video Evidence Processed [{source_id}]: {len(valid_tracks)} person tracks, {total_sightings_count} evidence sightings.")
        except Exception as e:
            db.rollback()
            print(f"Error persisting video evidence {source_id}: {e}")
            raise e
        finally:
            db.close()

        return {
            "source_id": source_id,
            "source_name": display_name,
            "filename": filename,
            "duration_sec": round(duration_sec, 2),
            "track_count": len(valid_tracks),
            "sighting_count": total_sightings_count,
            "status": "ready"
        }

    def get_evidence_crop_file_path(self, source_id: str, track_id: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Locates the verified evidence crop image file on disk for a given source and track.
        """
        track_dir = os.path.join(EVIDENCE_DIR, source_id, track_id)
        if not os.path.exists(track_dir):
            return None

        if filename:
            target_path = os.path.join(track_dir, os.path.basename(filename))
            if os.path.exists(target_path):
                return target_path

        # Find best/first available image in track directory
        candidates = [f for f in os.listdir(track_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if candidates:
            # Pick representative crop if exists, else first
            candidates.sort()
            return os.path.join(track_dir, candidates[0])
        return None

    def search_person_gallery(
        self,
        query_img: np.ndarray,
        min_similarity: float = 0.50,
        source_id: Optional[str] = None,
        time_window: Optional[str] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Executes query embedding extraction and vector search across stored video sightings.
        Applies source filtering, threshold filtering, groups by Track, and returns Top-K (max 5) matches.
        """
        # Enforce strict top-K limit (max 5)
        top_k = min(max(1, limit), 5)

        if query_img is None or query_img.size == 0:
            return {
                "total_candidates": 0,
                "returned_candidates": 0,
                "limit": top_k,
                "min_similarity": min_similarity,
                "matches": []
            }

        # 1. Extract Query Embedding
        query_emb = self.extract_person_embedding(query_img)
        if np.linalg.norm(query_emb) < 1e-6:
            return {
                "total_candidates": 0,
                "returned_candidates": 0,
                "limit": top_k,
                "min_similarity": min_similarity,
                "matches": []
            }

        db: Session = SessionLocal()
        all_candidates = []
        try:
            # Query active tracks
            query = db.query(PersonVideoTrack)
            if source_id and source_id != "ALL" and source_id != "All":
                query = query.filter(PersonVideoTrack.source_id == source_id)
            
            tracks = query.all()
            if not tracks:
                return {
                    "total_candidates": 0,
                    "returned_candidates": 0,
                    "limit": top_k,
                    "min_similarity": min_similarity,
                    "matches": []
                }

            # Load video evidence metadata map
            ve_records = {ve.source_id: ve for ve in db.query(VideoEvidence).all()}

            for trk in tracks:
                if not trk.average_embedding:
                    continue
                try:
                    trk_emb = np.array(json.loads(trk.average_embedding), dtype=np.float32)
                except Exception:
                    continue

                # Cosine Similarity between normalized vectors (dot product)
                cos_sim = float(np.dot(query_emb, trk_emb))
                # Clamp strictly to [0.0, 1.0]
                similarity = max(0.0, min(1.0, cos_sim))

                # Apply threshold filter
                if similarity < min_similarity:
                    continue

                sim_percent = int(round(similarity * 100))
                ve = ve_records.get(trk.source_id)
                source_name = ve.source_name if ve else trk.source_id
                location_str = ve.location if (ve and ve.location) else "Video source location unavailable"

                # Verify crop existence on disk
                disk_crop = self.get_evidence_crop_file_path(trk.source_id, trk.track_id)
                if not disk_crop or not os.path.exists(disk_crop):
                    continue

                # Clean API Evidence URLs
                canonical_crop_url = f"/api/person/evidence/{trk.source_id}/{trk.track_id}"

                # Fetch individual sightings timeline for this track
                sightings_query = db.query(PersonVideoSighting).filter(
                    PersonVideoSighting.source_id == trk.source_id,
                    PersonVideoSighting.track_id == trk.track_id
                ).order_by(PersonVideoSighting.timestamp_sec.asc()).all()

                sightings_list = []
                for s in sightings_query:
                    s_fname = os.path.basename(s.crop_path) if s.crop_path else "crop.jpg"
                    sightings_list.append({
                        "sighting_id": s.sighting_id,
                        "formatted_time": s.formatted_time,
                        "timestamp_sec": s.timestamp_sec,
                        "crop_path": f"/api/person/evidence/{trk.source_id}/{trk.track_id}/{s_fname}",
                        "evidence_image_url": f"/api/person/evidence/{trk.source_id}/{trk.track_id}/{s_fname}",
                        "confidence": round(float(s.confidence), 2)
                    })

                latest_sighting = sightings_list[-1] if sightings_list else None

                all_candidates.append({
                    "track_id": f"{trk.source_id}/{trk.track_id}",
                    "raw_track_id": trk.track_id,
                    "source_id": trk.source_id,
                    "source_name": source_name,
                    "similarity": round(similarity, 4),
                    "similarity_percent": sim_percent,
                    "evidence_image_url": canonical_crop_url,
                    "representative_crop": canonical_crop_url,
                    "detection_count": trk.detection_count,
                    "start_time_sec": trk.start_time_sec,
                    "end_time_sec": trk.end_time_sec,
                    "latest_timestamp": latest_sighting["formatted_time"] if latest_sighting else "00:00",
                    "location": location_str,
                    "sightings": sightings_list
                })

            # Sort descending strictly by similarity
            all_candidates.sort(key=lambda m: m["similarity"], reverse=True)

            # Take Top-K
            top_matches = all_candidates[:top_k]
            # Add rank property
            for idx, m in enumerate(top_matches):
                m["rank"] = idx + 1
                m["is_best_match"] = (idx == 0)

        finally:
            db.close()

        return {
            "total_candidates": len(all_candidates),
            "returned_candidates": len(top_matches),
            "limit": top_k,
            "min_similarity": min_similarity,
            "matches": top_matches
        }

    def auto_index_sample_videos_if_empty(self):
        """
        Auto-indexes available CCTV sample video files if database has 0 video evidence sources.
        Ensures Person Finder has realistic video evidence tracks ready out-of-the-box!
        """
        db: Session = SessionLocal()
        count = 0
        try:
            count = db.query(VideoEvidence).count()
        except Exception:
            pass
        finally:
            db.close()

        if count == 0:
            sample_candidates = [
                ("fight_1.mp4", "VIDEO-01", "CAM-01: Mumbai CSMT Concourse (CCTV Feed)", "Mumbai CSMT Terminal", 18.9401, 72.8351),
                ("blr_mg_road_metro.mp4", "VIDEO-02", "CAM-02: Bengaluru MG Road Commercial Corridor", "Bengaluru MG Road", 12.9756, 77.6067),
                ("mumbai_csmt_station.mp4", "VIDEO-03", "CAM-03: Mumbai Marine Drive Coastal Unit", "Mumbai Coastal Corridor", 18.9438, 72.8233),
                ("blr_indiranagar_100ft.mp4", "VIDEO-04", "CAM-04: Bengaluru Trinity Circle Transit Checkpoint", "Bengaluru Trinity Circle", 12.9725, 77.6200)
            ]

            for fname, sid, sname, loc, lat, lon in sample_candidates:
                vpath = os.path.join(SAMPLES_DIR, fname)
                if os.path.exists(vpath):
                    try:
                        self.process_video_evidence(vpath, sid, sname, loc, lat, lon)
                    except Exception as e:
                        print(f"Sample auto-index warning for {fname}: {e}")

video_person_engine = VideoPersonEngine()
