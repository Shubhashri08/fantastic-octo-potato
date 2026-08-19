from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.sql import func
from .database import Base

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
    camera_id = Column(Integer, nullable=False)
    event_type = Column(String(50), nullable=False)  # Fire, Smoke, Accident, Fighting, Person, Vehicle
    confidence = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    bbox = Column(Text, nullable=True)
    snapshot_path = Column(String(255), nullable=True)
    video_clip_path = Column(String(255), nullable=True)
    severity = Column(String(20), default="Medium")
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
    association_type = Column(String(50), default="WITNESS")  # SUSPECT, WITNESS, VEHICLE_ESCAPE
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
