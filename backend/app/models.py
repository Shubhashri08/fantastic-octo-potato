import os
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.sql import func
from .database import Base, IS_POSTGRES

# Optional pgvector support for PostgreSQL
try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    source = Column(String(255), nullable=False, default="0")  # '0', video file path, or rtsp url
    source_type = Column(String(20), nullable=False, default="webcam")  # webcam, video, rtsp
    lat = Column(Float, nullable=False, default=18.9401)
    lon = Column(Float, nullable=False, default=72.8351)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # Fire, Smoke, Accident, Fighting, Person, Vehicle
    confidence = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    bbox = Column(Text, nullable=True)
    snapshot_path = Column(String(255), nullable=True)
    video_clip_path = Column(String(255), nullable=True)
    severity = Column(String(20), default="Medium", index=True)
    status = Column(String(20), default="Active", index=True)
    is_demo = Column(Boolean, default=False)
    confirmation_count = Column(Integer, default=1)
    event_id = Column(String(50), nullable=True)
    source = Column(String(50), nullable=True)


class Entity(Base):
    __tablename__ = "entities"

    track_id = Column(String(100), primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False)  # PERSON, VEHICLE
    first_seen = Column(DateTime(timezone=True))
    last_seen = Column(DateTime(timezone=True))
    meta_info = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EntitySighting(Base):
    __tablename__ = "entity_sightings"

    sighting_id = Column(String(100), primary_key=True, index=True)
    track_id = Column(String(100), ForeignKey("entities.track_id"), nullable=False)
    camera_id = Column(String(50), nullable=False)
    timestamp = Column(DateTime(timezone=True))
    confidence = Column(Float, default=0.90)
    bbox = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EventEntityMapping(Base):
    __tablename__ = "event_entity_mapping"

    event_id = Column(String(100), primary_key=True)
    track_id = Column(String(100), primary_key=True)
    association_type = Column(String(50), default="WITNESS")
    proximity_meters = Column(Float, default=50.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(100), primary_key=True, index=True)
    event_id = Column(String(100), nullable=True)
    camera_id = Column(String(100), nullable=False)
    event_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    confidence = Column(Float, default=0.85)
    severity = Column(String(20), default="high")
    risk_score = Column(Float, default=50.0)
    priority = Column(String(20), default="CRITICAL")
    status = Column(String(50), default="ACTION_REQUIRED")
    correlation_id = Column(String(100), nullable=True)


class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id = Column(String(50), primary_key=True, index=True)
    plate_number = Column(String(50), index=True, nullable=False)
    plate_confidence = Column(Float, default=0.95)
    vehicle_type = Column(String(50), index=True, default="Car (Sedan)")
    vehicle_model = Column(String(100), index=True, default="Toyota Corolla Sedan")
    vehicle_color = Column(String(50), index=True, default="Silver")
    is_stolen = Column(Boolean, default=False, index=True)
    bolo_status = Column(String(100), default="NORMAL: Verified Vehicle Registry")
    flag_reason = Column(String(100), nullable=True)
    flag_note = Column(Text, nullable=True)
    flagged_at = Column(DateTime(timezone=True), nullable=True)
    snapshot = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class VehicleSighting(Base):
    __tablename__ = "vehicle_sightings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    vehicle_id = Column(String(50), ForeignKey("vehicles.vehicle_id"), index=True, nullable=False)
    camera_id = Column(String(50), index=True, nullable=False)
    camera_name = Column(String(100), nullable=True)
    location = Column(String(150), index=True, nullable=False)
    city = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed_kmh = Column(Float, default=50.0)
    timestamp = Column(DateTime(timezone=True), index=True, server_default=func.now())
    evidence_image = Column(String(255), nullable=True)


# =========================================================================
# Production Person Video Evidence, Tracks & Sightings Schema
# =========================================================================

class VideoEvidence(Base):
    __tablename__ = "video_evidence"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String(50), unique=True, index=True, nullable=False)
    source_hash = Column(String(64), index=True, nullable=True)  # SHA-256 idempotency hash
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    source_name = Column(String(255), nullable=False)
    camera_id = Column(String(50), nullable=True, default="CAM-01")
    location = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    duration_sec = Column(Float, default=0.0)
    fps = Column(Float, default=30.0)
    total_frames = Column(Integer, default=0)
    status = Column(String(20), default="queued", index=True)  # queued, processing, ready, failed
    error_message = Column(Text, nullable=True)
    track_count = Column(Integer, default=0)
    sighting_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PersonVideoTrack(Base):
    __tablename__ = "person_video_tracks"

    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(String(100), index=True, nullable=False)
    source_id = Column(String(50), index=True, nullable=False)
    camera_id = Column(String(50), index=True, nullable=True, default="CAM-01")
    camera_name = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    start_time_sec = Column(Float, default=0.0)
    end_time_sec = Column(Float, default=0.0)
    first_seen_formatted = Column(String(50), nullable=True)
    last_seen_formatted = Column(String(50), nullable=True)
    detection_count = Column(Integer, default=1)
    quality_score = Column(Float, default=1.0)
    representative_crop_path = Column(String(500), nullable=False)
    average_embedding = Column(Text, nullable=True)  # JSON-serialized vector or vector reference
    
    # Model Versioning & Provenance
    reid_model = Column(String(50), default="transreid")
    reid_model_version = Column(String(100), default="transreid-damo-market1501-v1")
    embedding_dim = Column(Integer, default=768)
    index_version = Column(String(20), default="v1.0")
    embedding_created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Cross-camera Trajectory Stitching Fields
    appearance_cluster_id = Column(String(100), index=True, nullable=True)
    cluster_confidence = Column(Float, nullable=True)
    linked_track_ids = Column(JSON, nullable=True)

    clothing_desc = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PersonVideoSighting(Base):
    __tablename__ = "person_video_sightings"

    id = Column(Integer, primary_key=True, index=True)
    sighting_id = Column(String(100), unique=True, index=True, nullable=False)
    track_id = Column(String(100), index=True, nullable=False)
    source_id = Column(String(50), index=True, nullable=False)
    camera_id = Column(String(50), index=True, nullable=True, default="CAM-01")
    timestamp_sec = Column(Float, default=0.0)
    frame_number = Column(Integer, default=0)
    formatted_time = Column(String(50), nullable=False)
    crop_path = Column(String(500), nullable=False)
    bbox = Column(String(100), nullable=True)
    confidence = Column(Float, default=0.90)
    quality_score = Column(Float, default=1.0)
    detection_confidence = Column(Float, default=0.90)
    embedding = Column(Text, nullable=True)

    # Model Versioning
    reid_model = Column(String(50), default="transreid")
    reid_model_version = Column(String(100), default="transreid-damo-market1501-v1")
    embedding_dim = Column(Integer, default=768)
    index_version = Column(String(20), default="v1.0")
    embedding_created_at = Column(DateTime(timezone=True), server_default=func.now())

    created_at = Column(DateTime(timezone=True), server_default=func.now())
