from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.schemas.alert import GeoJsonPointSchema

# Layer 3 / 2 - Entity Tracking History
class EntityHistoryPoint(BaseModel):
    timestamp: datetime
    geom: GeoJsonPointSchema = Field(..., description="Sighting location coordinates in [longitude, latitude] order")
    camera_id: str

class EntityHistoryResponse(BaseModel):
    entity_id: str
    entity_type: str
    history: List[EntityHistoryPoint] = Field(default_factory=list)

# Layer 3 - Event Timeline
class TimelineEventPoint(BaseModel):
    timestamp: datetime
    description: str
    status: str

class EventTimelineResponse(BaseModel):
    event_id: str
    timeline: List[TimelineEventPoint] = Field(default_factory=list)

# Layer 3 - Event Entities Mapping
class AssociatedEntity(BaseModel):
    track_id: str = Field(..., description="Unique tracking entity identifier")
    association_type: str = Field(..., description="E.g., primary_subject, background_object")
    proximity_meters: float = Field(..., description="Distance tolerance in meters")

class EventEntitiesResponse(BaseModel):
    event_id: str
    entities: List[AssociatedEntity] = Field(default_factory=list)

# Layer 3 - Camera History
class SightingPoint(BaseModel):
    timestamp: datetime
    detected_entity_id: str
    confidence: float

class CameraHistoryResponse(BaseModel):
    camera_id: str
    observations: List[SightingPoint] = Field(default_factory=list)


# Layer 4 - Nearby Incidents
class NearbyIncidentPoint(BaseModel):
    event_id: str
    event_type: str
    timestamp: datetime
    geom: GeoJsonPointSchema = Field(..., description="Event location coordinates in [longitude, latitude] order")
    severity: str
    distance_meters: float

class NearbyIncidentsResponse(BaseModel):
    geom: GeoJsonPointSchema = Field(..., description="Coordinates lookup location in [longitude, latitude] order")
    radius_meters: float
    incidents: List[NearbyIncidentPoint] = Field(default_factory=list)

# Layer 4 - Historical Patterns
class HistoricalPatternPoint(BaseModel):
    hour_of_day: int
    incident_count: int
    avg_risk_score: float

class HistoricalPatternResponse(BaseModel):
    geom: GeoJsonPointSchema = Field(..., description="Coordinates lookup location in [longitude, latitude] order")
    dominant_incident_type: str
    peak_hours: str
    patterns: List[HistoricalPatternPoint] = Field(default_factory=list)

# Layer 4 - GIS / Location Context
class GISLocationContextResponse(BaseModel):
    geom: GeoJsonPointSchema = Field(..., description="Coordinates lookup location in [longitude, latitude] order")
    risk_score: float = Field(..., ge=0.0, le=1.0)
    hotspot: bool
    historical_incident_count: int
    dominant_incident_type: str
    peak_time: str
    gis_region_name: str
    boundary_coordinates: Optional[List[GeoJsonPointSchema]] = None
