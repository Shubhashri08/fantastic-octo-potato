from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class LocationSchema(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)

class Layer3EventSchema(BaseModel):
    event_id: str = Field(..., description="Unique event identifier from Layer 3")
    event_type: str = Field(..., description="Event type")
    timestamp: datetime = Field(..., description="Event generation timestamp")
    location: LocationSchema = Field(..., description="Geospatial coordinates of event occurrence")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detections confidence score")
    severity: str = Field(..., description="Severity rating: HIGH, MEDIUM, LOW")
    entities: List[str] = Field(default_factory=list, description="IDs of involved entities")
    cameras: List[str] = Field(default_factory=list, description="IDs of source cameras")
    correlation_id: str = Field(..., description="Tracing cross-layer correlation ID")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Relational or extra event context")

class Layer4ContextSchema(BaseModel):
    location: LocationSchema = Field(..., description="Coordinates lookup location")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Upstream risk score")
    hotspot: bool = Field(..., description="Indicates if location is a known high-incident area")
    historical_incident_count: int = Field(..., ge=0, description="Count of historical incidents in this region")
    dominant_incident_type: str = Field(..., description="Primary incident type recorded in this hotspot")
    peak_time: str = Field(..., description="Historical peak hours window (e.g. '18:00-22:00')")
    gis_context: Optional[Dict[str, Any]] = Field(default=None, description="General GIS/boundary details")
    correlation_id: str = Field(..., description="Tracing cross-layer correlation ID")

class AlertEvaluationRequest(BaseModel):
    event: Layer3EventSchema
    context: Layer4ContextSchema

class AlertResponse(BaseModel):
    id: str
    event_id: str
    event_type: str
    timestamp: datetime
    latitude: float
    longitude: float
    confidence: float
    severity: str
    entities: List[str]
    cameras: List[str]
    risk_score: float
    hotspot: bool
    historical_incident_count: int
    dominant_incident_type: str
    peak_time: str
    priority: str
    status: str
    correlation_id: str
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AlertStatusUpdate(BaseModel):
    status: str = Field(..., description="New status value: NEW, ACKNOWLEDGED, RESOLVED")
