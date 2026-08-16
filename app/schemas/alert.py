from datetime import datetime
from typing import List, Dict, Any, Optional, Literal, Tuple
from pydantic import BaseModel, Field, UUID4

class GeoJsonPointSchema(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: Tuple[float, float] = Field(
        ...,
        description="Point coordinates in [longitude, latitude] order."
    )

class Layer3EventSchema(BaseModel):
    event_id: UUID4 = Field(..., description="Unique event identifier from Layer 3")
    camera_id: str = Field(..., description="Unique source camera identifier")
    event_type: str = Field(..., description="Event type")
    timestamp: datetime = Field(..., description="Event generation timestamp")
    geom: GeoJsonPointSchema = Field(..., description="Point coordinates in [longitude, latitude] order")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detections confidence score")
    severity: str = Field(..., description="Severity rating: HIGH, MEDIUM, LOW")
    bbox: Optional[List[float]] = Field(default=None, description="Optional bounding box coordinates")
    is_verified: bool = Field(default=False, description="Verification status of the event")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Relational or extra event context")

class Layer4ContextSchema(BaseModel):
    geom: GeoJsonPointSchema = Field(..., description="Coordinates lookup location in [longitude, latitude] order")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Upstream risk score")
    hotspot: bool = Field(..., description="Indicates if location is a known high-incident area")
    historical_incident_count: int = Field(..., ge=0, description="Count of historical incidents in this region")
    dominant_incident_type: str = Field(..., description="Primary incident type recorded in this hotspot")
    peak_time: str = Field(..., description="Historical peak hours window (e.g. '18:00-22:00')")
    gis_context: Optional[Dict[str, Any]] = Field(default=None, description="General GIS/boundary details")

class AlertEvaluationRequest(BaseModel):
    event: Layer3EventSchema
    context: Layer4ContextSchema

class AlertResponse(BaseModel):
    id: str
    event_id: str
    camera_id: str
    event_type: str
    timestamp: datetime
    latitude: float
    longitude: float
    confidence: float
    severity: str
    bbox: Optional[List[float]] = None
    is_verified: bool
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
