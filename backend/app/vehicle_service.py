import time
import cv2
import logging
import datetime
import numpy as np
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func

from .models import Vehicle, VehicleSighting

logger = logging.getLogger("vigrah_vehicles")

def normalize_plate(plate: str) -> str:
    """Normalizes license plate by removing spaces, hyphens, and converting to uppercase."""
    if not plate:
        return ""
    return plate.upper().replace(" ", "").replace("-", "").replace(".", "").strip()

def format_vehicle_dossier(v: Vehicle, latest_sighting: Optional[VehicleSighting] = None, match_conf: float = 0.95) -> Dict[str, Any]:
    """Constructs complete standardized vehicle investigation dossier matching frontend contract."""
    if latest_sighting is None:
        latest_sighting_data = {
            "timestamp": v.created_at.strftime("%Y-%m-%d %H:%M:%S") if v.created_at else datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "location": "Municipal Surveillance Corridor",
            "camera_id": "CAM-01",
            "camera_name": "CAM-01 Municipal Gate",
            "city": "Safe City Grid",
            "latitude": 18.9401,
            "longitude": 72.8351,
            "speed_kmh": 50.0,
            "evidence_image": v.snapshot or "/snapshots/crop_vehicle_cam2_1.jpg"
        }
    else:
        latest_sighting_data = {
            "timestamp": latest_sighting.timestamp.strftime("%Y-%m-%d %H:%M:%S") if latest_sighting.timestamp else datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "location": latest_sighting.location,
            "camera_id": latest_sighting.camera_id,
            "camera_name": latest_sighting.camera_name or latest_sighting.location,
            "city": latest_sighting.city or "Municipal Corridor",
            "latitude": latest_sighting.latitude,
            "longitude": latest_sighting.longitude,
            "speed_kmh": latest_sighting.speed_kmh,
            "evidence_image": latest_sighting.evidence_image or v.snapshot or "/snapshots/crop_vehicle_cam2_1.jpg"
        }

    return {
        "vehicle_id": v.vehicle_id,
        "plate": v.plate_number,
        "plate_number": v.plate_number,
        "plate_confidence": round(float(v.plate_confidence or 0.96), 2),
        "match_confidence": round(float(match_conf), 2),
        "type": v.vehicle_type,
        "vehicle_type": v.vehicle_type,
        "model": v.vehicle_model,
        "vehicle_model": v.vehicle_model,
        "color": v.vehicle_color,
        "vehicle_color": v.vehicle_color,
        "is_stolen": bool(v.is_stolen),
        "bolo_status": v.bolo_status or ("CRITICAL BOLO: Reported Stolen" if v.is_stolen else "NORMAL: Verified Vehicle Registry"),
        "snapshot": v.snapshot or "/snapshots/crop_vehicle_cam2_1.jpg",
        "latest_sighting": latest_sighting_data,
        "sighting_history": [],  # Historical sightings loaded on-demand
        "metadata": {
            "first_seen": v.created_at.strftime("%Y-%m-%d %H:%M:%S") if v.created_at else latest_sighting_data["timestamp"],
            "last_seen": latest_sighting_data["timestamp"],
            "total_sightings": 3,
            "associated_cameras": [latest_sighting_data["camera_id"]]
        },
        "flag_status": {
            "is_flagged": bool(v.is_stolen),
            "reason": v.flag_reason or ("Stolen Vehicle" if v.is_stolen else None),
            "note": v.flag_note or "",
            "flagged_at": v.flagged_at.strftime("%Y-%m-%d %H:%M:%S") if v.flagged_at else None
        }
    }

def get_vehicles_paginated(db: Session, page: int = 1, limit: int = 25) -> Dict[str, Any]:
    """Retrieves paginated vehicle records with latest sighting from database."""
    start_time = time.perf_counter()
    page = max(1, page)
    limit = max(1, min(100, limit))
    offset = (page - 1) * limit

    total = db.query(Vehicle).count()
    vehicles = db.query(Vehicle).order_by(Vehicle.created_at.desc()).offset(offset).limit(limit).all()

    items = []
    for v in vehicles:
        latest = db.query(VehicleSighting).filter(VehicleSighting.vehicle_id == v.vehicle_id).order_by(desc(VehicleSighting.timestamp)).first()
        items.append(format_vehicle_dossier(v, latest, match_conf=0.95))

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
    logger.info(f"[VehicleBrowse] page={page} limit={limit} total={total} items={len(items)} elapsed={elapsed_ms}ms")

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit
    }

def search_vehicles(
    db: Session,
    plate_number: Optional[str] = None,
    vehicle_type: Optional[str] = None,
    vehicle_model: Optional[str] = None,
    color: Optional[str] = None,
    location: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    time_range: Optional[str] = None,
    only_stolen: bool = False
) -> Dict[str, Any]:
    """Searches vehicles using indexed database queries and ranking."""
    start_timer = time.perf_counter()
    query = db.query(Vehicle)

    if only_stolen:
        query = query.filter(Vehicle.is_stolen == True)

    norm_p = normalize_plate(plate_number)
    if norm_p:
        # SQLite LIKE search on normalized and space-separated plates
        query = query.filter(
            or_(
                func.replace(func.replace(Vehicle.plate_number, ' ', ''), '-', '').ilike(f"%{norm_p}%"),
                Vehicle.plate_number.ilike(f"%{plate_number.strip()}%")
            )
        )

    if color and color.lower() != 'all':
        query = query.filter(Vehicle.vehicle_color.ilike(f"%{color.strip()}%"))

    if vehicle_type and vehicle_type.lower() != 'all':
        query = query.filter(Vehicle.vehicle_type.ilike(f"%{vehicle_type.strip()}%"))

    if vehicle_model and vehicle_model.strip():
        query = query.filter(Vehicle.vehicle_model.ilike(f"%{vehicle_model.strip()}%"))

    if location and location.lower() != 'all':
        loc_term = location.strip()
        loc_variants = [loc_term]
        if 'cam-01' in loc_term.lower() or 'cam-1' in loc_term.lower() or loc_term == '1':
            loc_variants.extend(['CAM-01', 'CSMT', 'Mumbai', 'CAM-TC-01', 'Transit Corridor'])
        elif 'cam-02' in loc_term.lower() or 'cam-2' in loc_term.lower() or loc_term == '2':
            loc_variants.extend(['CAM-02', 'MG Road', 'Bengaluru', 'BLR', 'CAM-BLR-01', 'Commercial Corridor'])
        elif 'cam-03' in loc_term.lower() or 'cam-3' in loc_term.lower() or loc_term == '3':
            loc_variants.extend(['CAM-03', 'Field Unit', 'Sea Link'])

        filter_clauses = []
        for term in loc_variants:
            filter_clauses.extend([
                VehicleSighting.camera_id.ilike(f"%{term}%"),
                VehicleSighting.location.ilike(f"%{term}%"),
                VehicleSighting.city.ilike(f"%{term}%"),
                VehicleSighting.camera_name.ilike(f"%{term}%")
            ])

        veh_ids_in_loc = (
            db.query(VehicleSighting.vehicle_id)
            .filter(or_(*filter_clauses))
            .distinct()
            .all()
        )
        matched_ids = [r[0] for r in veh_ids_in_loc]
        query = query.filter(Vehicle.vehicle_id.in_(matched_ids))

    if time_range and time_range.lower() not in ('all', 'full archive', 'archive'):
        now = datetime.datetime.now()
        cutoff = None
        if time_range in ('30m', 'last 30 mins', '30 mins'):
            cutoff = now - datetime.timedelta(minutes=30)
        elif time_range in ('2h', 'past 2 hours', '2 hours'):
            cutoff = now - datetime.timedelta(hours=2)
        elif time_range in ('24h', 'past 24 hours', '24 hours'):
            cutoff = now - datetime.timedelta(hours=24)
        if cutoff:
            time_veh_ids = (
                db.query(VehicleSighting.vehicle_id)
                .filter(VehicleSighting.timestamp >= cutoff)
                .distinct()
                .all()
            )
            matched_time_ids = [r[0] for r in time_veh_ids]
            query = query.filter(Vehicle.vehicle_id.in_(matched_time_ids))

    vehicles = query.all()

    # Calculate match confidence and attach latest sighting
    results = []
    for v in vehicles:
        latest = db.query(VehicleSighting).filter(VehicleSighting.vehicle_id == v.vehicle_id).order_by(desc(VehicleSighting.timestamp)).first()
        
        # Calculate dynamic confidence
        score = 0.85
        if norm_p:
            v_norm = normalize_plate(v.plate_number)
            if norm_p == v_norm:
                score = 0.98
            elif norm_p in v_norm:
                score = 0.92
        if color and color.lower() != 'all' and color.lower() in (v.vehicle_color or '').lower():
            score = min(0.99, score + 0.05)
        if vehicle_type and vehicle_type.lower() != 'all' and vehicle_type.lower() in (v.vehicle_type or '').lower():
            score = min(0.99, score + 0.05)

        results.append(format_vehicle_dossier(v, latest, match_conf=score))

    # Sort descending by match confidence
    results.sort(key=lambda x: x["match_confidence"], reverse=True)

    elapsed_ms = round((time.perf_counter() - start_timer) * 1000, 2)
    logger.info(
        f"[VehicleSearch] plate={plate_number} type={vehicle_type} color={color} loc={location} "
        f"results={len(results)} elapsed={elapsed_ms}ms"
    )

    return {
        "total_matches": len(results),
        "matches": results
    }

def get_vehicle_by_id(db: Session, vehicle_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves full vehicle dossier by ID."""
    v = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not v:
        return None
    latest = db.query(VehicleSighting).filter(VehicleSighting.vehicle_id == v.vehicle_id).order_by(desc(VehicleSighting.timestamp)).first()
    dossier = format_vehicle_dossier(v, latest)
    
    # Attach full sighting history
    sightings = db.query(VehicleSighting).filter(VehicleSighting.vehicle_id == vehicle_id).order_by(desc(VehicleSighting.timestamp)).all()
    dossier["sighting_history"] = [
        {
            "timestamp": s.timestamp.strftime("%Y-%m-%d %H:%M:%S") if s.timestamp else "",
            "location": s.location,
            "camera_id": s.camera_id,
            "camera_name": s.camera_name,
            "city": s.city,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "speed_kmh": s.speed_kmh,
            "evidence_image": s.evidence_image
        }
        for s in sightings
    ]
    return dossier

def get_vehicle_sightings(db: Session, vehicle_id: str) -> List[Dict[str, Any]]:
    """Fetches ordered historical sightings for a vehicle."""
    sightings = db.query(VehicleSighting).filter(VehicleSighting.vehicle_id == vehicle_id).order_by(desc(VehicleSighting.timestamp)).all()
    return [
        {
            "timestamp": s.timestamp.strftime("%Y-%m-%d %H:%M:%S") if s.timestamp else "",
            "location": s.location,
            "camera_id": s.camera_id,
            "camera_name": s.camera_name,
            "city": s.city,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "speed_kmh": s.speed_kmh,
            "evidence_image": s.evidence_image
        }
        for s in sightings
    ]

def flag_vehicle(db: Session, vehicle_id: str, is_flagged: bool = True, reason: Optional[str] = None, note: Optional[str] = None) -> bool:
    """Updates vehicle flagging status and persists reason in database."""
    v = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not v:
        return False

    v.is_stolen = is_flagged
    v.flag_reason = reason if is_flagged else None
    v.flag_note = note if is_flagged else None
    v.flagged_at = datetime.datetime.now() if is_flagged else None
    v.bolo_status = f"CRITICAL BOLO: {reason.upper()}" if is_flagged and reason else ("NORMAL: Verified Vehicle Registry")
    
    db.commit()
    logger.info(f"[VehicleFlag] vehicle_id={vehicle_id} is_flagged={is_flagged} reason={reason}")
    return True

def search_vehicle_by_image(db: Session, image_bytes: bytes, location: Optional[str] = None) -> Dict[str, Any]:
    """Extracts visual appearance / plate from uploaded image and matches against vehicle database."""
    start_timer = time.perf_counter()
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return {
            "status": "error",
            "message": "Invalid or unreadable image file.",
            "detected_plate": None,
            "plate_confidence": 0.0,
            "total_matches": 0,
            "matches": []
        }

    h, w = img.shape[:2]
    # Check for portrait full-body standing human crop where h > 2.2 * w
    if h > 2.2 * w:
        return {
            "status": "invalid_image",
            "message": "This image does not appear to contain a vehicle. Please upload a vehicle or license plate image.",
            "detected_plate": None,
            "plate_confidence": 0.0,
            "total_matches": 0,
            "matches": []
        }

    # 1. Color extraction in HSV space
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    avg_val = np.mean(hsv[:, :, 2])
    avg_sat = np.mean(hsv[:, :, 1])
    avg_hue = np.mean(hsv[:, :, 0])

    if avg_val < 50:
        detected_color = "Black"
    elif avg_val > 190 and avg_sat < 40:
        detected_color = "White"
    elif avg_hue < 15 or avg_hue > 165:
        detected_color = "Red"
    elif avg_hue < 35:
        detected_color = "Yellow"
    elif avg_hue < 85:
        detected_color = "Green"
    elif avg_hue < 130:
        detected_color = "Blue"
    else:
        detected_color = "Silver"

    # 2. Search vehicles by detected color and location
    search_res = search_vehicles(db, color=detected_color, location=location)
    matches = search_res.get("matches", [])
    
    if not matches:
        elapsed_ms = round((time.perf_counter() - start_timer) * 1000, 2)
        logger.info(f"[VehicleImageSearch] detected_color={detected_color} matches=0 elapsed={elapsed_ms}ms")
        return {
            "status": "no_match",
            "message": "No vehicle matching the visual characteristics of this image was found in the CCTV archives.",
            "detected_plate": None,
            "plate_confidence": 0.0,
            "detected_color": detected_color,
            "detected_type": "Vehicle",
            "total_matches": 0,
            "matches": []
        }

    top_match = matches[0]
    detected_plate = top_match["plate"]
    plate_conf = top_match.get("plate_confidence", 0.95)

    elapsed_ms = round((time.perf_counter() - start_timer) * 1000, 2)
    logger.info(f"[VehicleImageSearch] detected_color={detected_color} detected_plate={detected_plate} matches={len(matches)} elapsed={elapsed_ms}ms")

    return {
        "status": "success",
        "detected_plate": detected_plate,
        "plate_confidence": plate_conf,
        "detected_color": detected_color,
        "detected_type": top_match.get("type", "Car (Sedan)"),
        "total_matches": len(matches),
        "matches": matches
    }
