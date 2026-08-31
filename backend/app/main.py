import os
import time
import logging
import cv2
import numpy as np
from contextlib import asynccontextmanager
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .database import get_db, BASE_DIR, IS_POSTGRES, SessionLocal
from .models import Camera, Event, PersonVideoTrack, PersonVideoSighting, VideoEvidence
from .schemas import (
    CameraCreate, CameraResponse, EventResponse, 
    StartDetectionRequest, DetectionStatusResponse, VehicleFlagRequest
)
from .seed_data import init_db_and_seed
from . import vehicle_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vigrah_backend")

# Lazy Global instances
detection_engine = None
stream_manager = None
reid_engine = None

def get_detection_engine():
    """Lazy loader for YOLO and PyTorch incident detection models."""
    global detection_engine
    if detection_engine is None:
        logger.info("Lazy-loading YOLO detection models on demand...")
        from .model_downloader import load_models
        from .detection import DetectionEngine
        models_dict = load_models()
        detection_engine = DetectionEngine(models_dict)
    return detection_engine

def get_stream_manager():
    """Lazy loader for camera stream workers."""
    global stream_manager
    if stream_manager is None:
        engine = get_detection_engine()
        from .stream_manager import StreamManager
        stream_manager = StreamManager(engine)
    return stream_manager

def get_reid_engine():
    """Lazy loader for Person ReID engine."""
    global reid_engine
    if reid_engine is None:
        from .reid_engine import ReIDEngine
        reid_engine = ReIDEngine()
    return reid_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing VIGRAH AI Backend (Fast Startup Mode)...")
    init_start = time.perf_counter()

    # 1. Initialize SQLite Database Schema & Seed default records
    init_db_and_seed()
    
    # 2. Auto-index video evidence sources if empty
    from .video_person_engine import video_person_engine
    try:
        video_person_engine.auto_index_sample_videos_if_empty()
    except Exception as e:
        logger.warning(f"Video person auto-index warning: {e}")

    elapsed_ms = round((time.perf_counter() - init_start) * 1000, 2)
    logger.info(f"VIGRAH AI API Ready (Startup completed in {elapsed_ms}ms).")

    yield

    logger.info("Shutting down VIGRAH AI backend workers...")
    global stream_manager
    if stream_manager:
        for cam_id in list(stream_manager.workers.keys()):
            stream_manager.stop_camera(cam_id)


app = FastAPI(
    title="VIGRAH AI - Visual Intelligence & Geospatial Response Hub",
    description="Real-time multi-model video analytics & incident detection engine.",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware for React Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Mount static asset directories
snapshots_path = os.path.join(BASE_DIR, "snapshots")
os.makedirs(snapshots_path, exist_ok=True)
app.mount("/snapshots", StaticFiles(directory=snapshots_path), name="snapshots")

recordings_path = os.path.join(BASE_DIR, "recordings")
os.makedirs(recordings_path, exist_ok=True)
app.mount("/recordings", StaticFiles(directory=recordings_path), name="recordings")

samples_path = os.path.join(BASE_DIR, "samples")
os.makedirs(samples_path, exist_ok=True)
app.mount("/samples", StaticFiles(directory=samples_path), name="samples")

evidence_path = os.path.join(BASE_DIR, "evidence")
os.makedirs(evidence_path, exist_ok=True)
app.mount("/evidence", StaticFiles(directory=evidence_path), name="evidence")

uploads_path = os.path.join(BASE_DIR, "uploads")
os.makedirs(uploads_path, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")


# ================= CAMERA ENDPOINTS =================

@app.get("/api/cameras", response_model=List[CameraResponse])
def get_cameras(db: Session = Depends(get_db)):
    """Fetch all registered CCTV/video cameras."""
    return db.query(Camera).all()

@app.post("/api/cameras", response_model=CameraResponse)
def create_camera(cam: CameraCreate, db: Session = Depends(get_db)):
    """Register a new camera feed."""
    new_cam = Camera(**cam.model_dump())
    db.add(new_cam)
    db.commit()
    db.refresh(new_cam)
    if new_cam.is_active:
        sm = get_stream_manager()
        sm.start_camera(new_cam.id, new_cam.source, new_cam.source_type)
    return new_cam

@app.put("/api/cameras/{camera_id}", response_model=CameraResponse)
def update_camera(camera_id: int, cam_data: CameraCreate, db: Session = Depends(get_db)):
    """Update an existing camera's source or properties."""
    cam = db.query(Camera).filter(Camera.id == camera_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    for key, value in cam_data.model_dump().items():
        setattr(cam, key, value)
    
    db.commit()
    db.refresh(cam)
    
    sm = get_stream_manager()
    if cam.is_active:
        sm.start_camera(cam.id, cam.source, cam.source_type)
    else:
        sm.stop_camera(cam.id)
            
    return cam


# ================= EVENT ENDPOINTS =================

@app.get("/api/events", response_model=List[EventResponse])
def get_events(
    limit: int = 50,
    offset: int = 0,
    event_type: Optional[str] = Query(None),
    camera_id: Optional[int] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Fetch detected investigative incidents with filtering and pagination."""
    query = db.query(Event)
    if event_type and event_type != "ALL":
        query = query.filter(Event.event_type.ilike(f"%{event_type}%"))
    if camera_id and camera_id != "ALL":
        try:
            cid = int(str(camera_id).replace("CAM-0", "").replace("CAM-", ""))
            query = query.filter(Event.camera_id == cid)
        except Exception:
            pass
    if severity and severity != "ALL":
        query = query.filter(Event.severity.ilike(severity))
    if status and status != "ALL":
        query = query.filter(Event.status == status)
    return query.order_by(Event.timestamp.desc()).offset(offset).limit(limit).all()

@app.post("/api/system/reset-demo")
def reset_demo_endpoint(db: Session = Depends(get_db)):
    """Reset demonstration dataset to verified distributed CCTV state."""
    from .seed_data import init_db_and_seed
    init_db_and_seed(force_reset_events=True)
    return {"status": "success", "message": "Demo investigative incidents reset successfully."}

from .reconstruction_engine import analyze_event_reconstruction
from pydantic import BaseModel

class ReconstructionRequest(BaseModel):
    event_id: int

@app.post("/api/reconstruction/analyze")
@app.get("/api/reconstruction/analyze")
def analyze_reconstruction_endpoint(
    event_id: Optional[int] = Query(None),
    payload: Optional[ReconstructionRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Geospatial Event Reconstruction & Trajectory Prediction API:
    Builds observed pre-incident movement, predicts 3-5 candidate future routes along road network,
    ranks them with transparent likelihood scores, and calculates next CCTV intercept checkpoints.
    """
    target_event_id = (payload.event_id if payload else None) or event_id
    if not target_event_id:
        # Fallback to the latest high/critical event
        latest_ev = db.query(Event).order_by(Event.timestamp.desc()).first()
        if not latest_ev:
            raise HTTPException(status_code=404, detail="No recorded incidents available for reconstruction.")
        target_event_id = latest_ev.id

    try:
        return analyze_event_reconstruction(db, target_event_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reconstruction analysis error: {str(e)}")

@app.get("/api/events/{event_id}/reconstruction")
def get_event_reconstruction(event_id: int, db: Session = Depends(get_db)):
    """
    Forensic Incident Reconstruction API (Alias for Event Detail).
    """
    try:
        return analyze_event_reconstruction(db, event_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reconstruction analysis error: {str(e)}")


# ================= VIDEO EVIDENCE & MISSING PERSON RE-ID ENDPOINTS =================

from .video_person_engine import video_person_engine
from .models import VideoEvidence
import cv2

@app.get("/api/person/videos")
def get_person_videos_endpoint(db: Session = Depends(get_db)):
    """
    Returns list of indexed CCTV/Video Evidence sources with real-time status and track counts.
    """
    videos = db.query(VideoEvidence).order_by(VideoEvidence.created_at.desc()).all()
    return [
        {
            "source_id": v.source_id,
            "source_name": v.source_name,
            "camera_id": v.camera_id or "CAM-01",
            "filename": v.filename,
            "location": v.location or "Video source location unavailable",
            "duration_sec": round(v.duration_sec, 2),
            "fps": round(v.fps, 1),
            "total_frames": v.total_frames,
            "status": v.status,  # queued, processing, ready, failed
            "error_message": v.error_message,
            "track_count": v.track_count,
            "sighting_count": v.sighting_count,
            "created_at": str(v.created_at)
        }
        for v in videos
    ]

@app.post("/api/person/videos/upload")
async def upload_person_video_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source_name: Optional[str] = Query(None),
    camera_id: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Asynchronously uploads and processes CCTV / Video Evidence:
    Extracts frames at configured FPS, detects people via YOLO11, tracks via ByteTrack,
    filters crops by quality, generates TransReID embeddings, and indexes into vector store.
    """
    if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
        raise HTTPException(status_code=400, detail="Unsupported video format. Please upload MP4, AVI, MOV, MKV, or WEBM.")

    count = db.query(VideoEvidence).count()
    source_id = f"VIDEO-{(count + 1):02d}"

    uploads_dir = os.path.join(BASE_DIR, "uploads", "videos")
    os.makedirs(uploads_dir, exist_ok=True)
    saved_filename = f"{source_id}_{file.filename}"
    saved_path = os.path.join(uploads_dir, saved_filename)

    contents = await file.read()
    with open(saved_path, "wb") as f:
        f.write(contents)

    source_hash = video_person_engine.compute_file_sha256(saved_path)

    # Check for existing video with same hash (Idempotency)
    existing_video = db.query(VideoEvidence).filter(VideoEvidence.source_hash == source_hash).first()
    if existing_video and existing_video.status == "ready":
        return {
            "status": "ready",
            "message": f"Identical video evidence already indexed as [{existing_video.source_id}].",
            "video": {
                "source_id": existing_video.source_id,
                "source_name": existing_video.source_name,
                "camera_id": existing_video.camera_id,
                "filename": existing_video.filename,
                "duration_sec": round(existing_video.duration_sec, 2),
                "track_count": existing_video.track_count,
                "sighting_count": existing_video.sighting_count,
                "status": existing_video.status
            }
        }

    # Register in 'queued' status
    ve = VideoEvidence(
        source_id=source_id,
        source_hash=source_hash,
        filename=file.filename,
        file_path=saved_path,
        source_name=source_name or f"{source_id}: {file.filename}",
        camera_id=camera_id or "CAM-01",
        location=location or "Surveillance Sector",
        status="queued"
    )
    db.add(ve)
    db.commit()
    db.refresh(ve)

    # Launch processing in background task
    background_tasks.add_task(
        video_person_engine.process_video_evidence,
        video_path=saved_path,
        source_id=source_id,
        source_name=source_name or f"{source_id}: {file.filename}",
        camera_id=camera_id or "CAM-01",
        location=location or "Surveillance Sector"
    )

    return {
        "status": "queued",
        "message": f"Video evidence [{source_id}] accepted and queued for background indexing.",
        "video": {
            "source_id": source_id,
            "source_name": ve.source_name,
            "camera_id": ve.camera_id,
            "filename": ve.filename,
            "status": "queued"
        }
    }

@app.delete("/api/person/videos/{source_id}")
def delete_person_video_endpoint(source_id: str, db: Session = Depends(get_db)):
    """Deletes a video evidence source and all associated tracks/sightings."""
    from .models import PersonVideoTrack, PersonVideoSighting
    ve = db.query(VideoEvidence).filter(VideoEvidence.source_id == source_id).first()
    if not ve:
        raise HTTPException(status_code=404, detail=f"Video source {source_id} not found.")

    db.query(PersonVideoSighting).filter(PersonVideoSighting.source_id == source_id).delete()
    db.query(PersonVideoTrack).filter(PersonVideoTrack.source_id == source_id).delete()
    db.delete(ve)
    db.commit()
    return {"status": "success", "message": f"Removed video evidence source {source_id}."}

@app.get("/api/person/evidence/{source_id}/{track_id}")
def get_person_evidence_representative_crop(source_id: str, track_id: str):
    """
    Direct endpoint serving the representative evidence crop image with correct MIME type.
    """
    file_path = video_person_engine.get_evidence_crop_file_path(source_id, track_id)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Evidence crop for {source_id}/{track_id} not found.")
    return FileResponse(file_path, media_type="image/jpeg")

@app.get("/api/person/evidence/{source_id}/{track_id}/{filename}")
def get_person_evidence_sighting_crop(source_id: str, track_id: str, filename: str):
    """
    Direct endpoint serving a specific sighting frame evidence image with correct MIME type.
    """
    file_path = video_person_engine.get_evidence_crop_file_path(source_id, track_id, filename)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Evidence crop {filename} for {source_id}/{track_id} not found.")
    return FileResponse(file_path, media_type="image/jpeg")

@app.post("/api/person/search")
async def search_person(
    file: UploadFile = File(...),
    min_similarity: float = Query(0.50, ge=0.0, le=1.0),
    camera_id: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    time_window: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Missing Person Video Re-Identification API:
    Accepts reference photo, validates single-person detection, evaluates crop quality,
    extracts TransReID embedding, and returns ranked visual similarity candidates from CCTV gallery.
    """
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    query_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if query_img is None:
        raise HTTPException(status_code=400, detail="Invalid image file format. Could not decode image.")

    cam_filter = camera_id or location
    search_result = video_person_engine.search_person_gallery(
        query_img=query_img,
        min_similarity=min_similarity,
        camera_id=cam_filter,
        limit=limit
    )

    if search_result.get("status") == "error":
        return {
            "status": "error",
            "error_code": search_result.get("error_code"),
            "message": search_result.get("message"),
            "query_filename": file.filename,
            "matches": []
        }

    return {
        "status": "success",
        "query_filename": file.filename,
        "query": search_result.get("query", {}),
        "source_filter": cam_filter or "All Cameras",
        "min_similarity": min_similarity,
        "limit": search_result.get("limit", limit),
        "total_candidates": search_result.get("total_candidates", 0),
        "returned_candidates": search_result.get("returned_candidates", 0),
        "matches": search_result.get("matches", [])
    }


# ================= VEHICLE IDENTIFICATION & RE-ID ENDPOINTS =================

@app.get("/api/vehicles")
def get_vehicles_endpoint(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Browse Logged Vehicles API:
    Retrieves paginated vehicle records with latest CCTV sighting and metadata.
    """
    return vehicle_service.get_vehicles_paginated(db, page=page, limit=limit)

@app.get("/api/vehicles/search")
@app.get("/api/vehicle/search")
def search_vehicles_endpoint(
    plate: Optional[str] = Query(None),
    plate_number: Optional[str] = Query(None),
    vehicle_type: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    vehicle_model: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    color: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    time_range: Optional[str] = Query(None),
    only_stolen: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    Vehicle Finder Search API:
    Searches logged vehicles by plate number or visual appearance attributes (model, color, location).
    """
    p = plate_number or plate
    t = vehicle_type or type
    m = vehicle_model or model

    return vehicle_service.search_vehicles(
        db,
        plate_number=p,
        vehicle_type=t,
        vehicle_model=m,
        color=color,
        location=location,
        start_time=start_time,
        end_time=end_time,
        time_range=time_range,
        only_stolen=only_stolen
    )

@app.post("/api/vehicles/search/image")
@app.post("/api/vehicle/search-image")
async def search_vehicle_by_image_endpoint(
    file: UploadFile = File(...),
    location: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Vehicle Re-ID by Uploaded Photo / Plate Crop:
    Extracts plate & visual characteristics from photograph and matches against vehicle database.
    """
    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        return vehicle_service.search_vehicle_by_image(db, contents, location=location)
    except Exception as e:
        logger.error(f"Error processing vehicle image search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Image processing error: {str(e)}")

@app.get("/api/vehicles/{vehicle_id}")
def get_single_vehicle(vehicle_id: str, db: Session = Depends(get_db)):
    """Retrieves full investigation dossier for a specific vehicle."""
    dossier = vehicle_service.get_vehicle_by_id(db, vehicle_id)
    if not dossier:
        raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found in database.")
    return dossier

@app.get("/api/vehicles/{vehicle_id}/sightings")
def get_vehicle_sightings_endpoint(vehicle_id: str, db: Session = Depends(get_db)):
    """Retrieves historical sighting timeline for a specific vehicle."""
    return vehicle_service.get_vehicle_sightings(db, vehicle_id)

@app.post("/api/vehicles/{vehicle_id}/flag")
@app.post("/api/vehicle/flag")
def flag_vehicle_endpoint(
    req: VehicleFlagRequest,
    vehicle_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Investigator Action: Flag or unflag a vehicle in the surveillance database.
    """
    v_id = vehicle_id or req.vehicle_id
    if not v_id:
        raise HTTPException(status_code=400, detail="vehicle_id is required.")

    is_flagged = req.is_flagged if req.is_flagged is not None else (req.is_stolen if req.is_stolen is not None else True)
    reason = req.reason or "Stolen Vehicle"
    note = req.note or ""

    success = vehicle_service.flag_vehicle(db, v_id, is_flagged=is_flagged, reason=reason, note=note)
    if not success:
        raise HTTPException(status_code=404, detail=f"Vehicle {v_id} not found.")

    return {
        "status": "success",
        "vehicle_id": v_id,
        "is_flagged": is_flagged,
        "reason": reason,
        "note": note,
        "message": f"Vehicle {v_id} {'flagged in grid watchlist' if is_flagged else 'unflagged and restored to normal'}"
    }


# ================= MULTI-CITY GIS NODES =================

@app.get("/api/cities")
def get_cities():
    """Retrieve list of available multi-city CCTV mesh networks."""
    engine = get_reid_engine()
    cities_summary = []
    for city_key, data in engine.city_networks.items():
        cities_summary.append({
            "key": city_key,
            "name": data.get("city"),
            "state": data.get("state"),
            "center": data.get("center"),
            "zoom": data.get("zoom", 12),
            "total_nodes": data.get("total_nodes", 0),
            "source": data.get("source")
        })
    return {"cities": cities_summary}

@app.get("/api/cities/{city_name}/nodes")
def get_city_nodes(city_name: str, limit: int = 200):
    """Retrieve camera nodes for a specific city mesh."""
    engine = get_reid_engine()
    if city_name not in engine.city_networks:
        raise HTTPException(status_code=404, detail="City mesh not found")
    
    city_data = engine.city_networks[city_name]
    nodes = city_data.get("nodes", [])[:limit]
    return {
        "city": city_name,
        "center": city_data.get("center"),
        "zoom": city_data.get("zoom", 12),
        "total_nodes": len(city_data.get("nodes", [])),
        "nodes": nodes
    }


# ================= STREAMING & DETECTION CONTROLS =================

@app.get("/stream/{camera_id}")
def video_feed(camera_id: int):
    """MJPEG Video streaming endpoint for real-time live feed playback."""
    sm = get_stream_manager()
    worker = sm.get_worker(camera_id)
    if not worker or not worker.is_running:
        from .database import SessionLocal
        db = SessionLocal()
        cam = db.query(Camera).filter(Camera.id == camera_id).first()
        db.close()
        if cam:
            sm.start_camera(cam.id, cam.source, cam.source_type)

    return StreamingResponse(
        sm.generate_mjpeg_frames(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/stream/video/{filename}")
def stream_video_file(filename: str):
    """Stream any unique CCTV sample file as continuous real-time MJPEG (100% browser-compatible)."""
    import cv2
    sample_file = os.path.join(BASE_DIR, "samples", filename)
    if not os.path.exists(sample_file):
        sample_file = os.path.join(BASE_DIR, "samples", "fight_1.mp4")

    def frame_generator():
        cap = cv2.VideoCapture(sample_file)
        while True:
            if not cap.isOpened():
                time.sleep(0.1)
                cap = cv2.VideoCapture(sample_file)
                continue

            ret, frame = cap.read()
            if not ret or frame is None:
                cap.release()
                cap = cv2.VideoCapture(sample_file)
                ret, frame = cap.read()
                if not ret or frame is None:
                    time.sleep(0.05)
                    continue

            ret, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            time.sleep(0.035)

    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.post("/api/start_detection")
def start_detection(req: StartDetectionRequest, db: Session = Depends(get_db)):
    """Start or restart detection on a specific camera with custom source."""
    cam = db.query(Camera).filter(Camera.id == req.camera_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")

    if req.source:
        cam.source = req.source
    if req.source_type:
        cam.source_type = req.source_type
    cam.is_active = True
    db.commit()

    sm = get_stream_manager()
    sm.start_camera(cam.id, cam.source, cam.source_type)

    return {"status": "started", "camera_id": cam.id, "source": cam.source, "source_type": cam.source_type}

@app.post("/api/stop_detection")
def stop_detection(camera_id: int, db: Session = Depends(get_db)):
    """Stop detection stream worker for a camera."""
    cam = db.query(Camera).filter(Camera.id == camera_id).first()
    if cam:
        cam.is_active = False
        db.commit()
    sm = get_stream_manager()
    sm.stop_camera(camera_id)
    return {"status": "stopped", "camera_id": camera_id}


# ================= SYSTEM STATUS =================

@app.get("/api/status")
def system_status(db: Session = Depends(get_db)):
    """Retrieve runtime GPU, active cameras, and model telemetry."""
    device_name = "cpu"
    gpu_name = "CPU (Fallback)"
    try:
        import torch
        if torch.cuda.is_available():
            device_name = "cuda"
            gpu_name = torch.cuda.get_device_name(0)
        elif torch.backends.mps.is_available():
            device_name = "mps"
            gpu_name = "Apple Silicon GPU (MPS)"
    except Exception:
        pass

    active_workers = len(stream_manager.workers) if stream_manager else 0
    active_models = list(detection_engine.models.keys()) if detection_engine else []

    # Get Person Re-ID Runtime state
    reid_backend = video_person_engine.reid_backend
    indexed_tracks_count = db.query(PersonVideoTrack).count()
    indexed_videos_count = db.query(VideoEvidence).count()

    return {
        "status": "online",
        "device": device_name,
        "gpu_name": gpu_name,
        "active_models": active_models,
        "active_camera_workers": active_workers,
        "person_reid": {
            "enabled": True,
            "model": reid_backend.model_name,
            "model_version": reid_backend.model_version,
            "checkpoint_loaded": reid_backend.model is not None,
            "embedding_dimension": reid_backend.embedding_dim,
            "device": reid_backend.device,
            "vector_database": "postgresql_pgvector" if IS_POSTGRES else "sqlite_numpy_fallback",
            "indexed_videos": indexed_videos_count,
            "indexed_tracks": indexed_tracks_count
        },
        "phase_2_modules": ["Person Finder (ReID)", "Vehicle Finder (Plate & Appearance)", "Multi-City GIS Grid"]
    }
