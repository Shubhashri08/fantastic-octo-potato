import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Ingested Layer 3 Event details
    event_id = Column(String(100), unique=True, nullable=False, index=True) # Unique constraint ensures idempotency
    camera_id = Column(String(50), nullable=False)
    event_type = Column(String(100), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    severity = Column(String(50), nullable=False)
    bbox = Column(JSON, nullable=True) # Optional bounding box coordinates
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Ingested Layer 4 Context details
    risk_score = Column(Float, nullable=False)
    hotspot = Column(Boolean, nullable=False)
    historical_incident_count = Column(Integer, nullable=False)
    dominant_incident_type = Column(String(100), nullable=False)
    peak_time = Column(String(50), nullable=False)
    
    # Layer 5 Derived Decision details
    priority = Column(String(50), nullable=False) # HIGH, MEDIUM, LOW
    status = Column(String(50), default="NEW", nullable=False) # NEW, ACKNOWLEDGED, RESOLVED
    correlation_id = Column(String(100), nullable=False, index=True)
    
    # Acknowledge / Resolve logging
    acknowledged_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    ack_user = relationship("User", foreign_keys=[acknowledged_by])
    res_user = relationship("User", foreign_keys=[resolved_by])
