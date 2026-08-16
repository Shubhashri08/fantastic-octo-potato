from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class LocationSchema(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)

# Layer 3 / 2 - Entity Tracking History
class EntityHistoryPoint(BaseModel):
    timestamp: datetime
    latitude: float
    longitude: float
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

# Layer 3 - Event Entities
class AssociatedEntity(BaseModel):
    entity_id: str
    entity_type: str
    confidence: float

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
    latitude: float
    longitude: float
    severity: str
    distance_meters: float

class NearbyIncidentsResponse(BaseModel):
    latitude: float
    longitude: float
    radius_meters: float
    incidents: List[NearbyIncidentPoint] = Field(default_factory=list)

# Layer 4 - Historical Patterns
class HistoricalPatternPoint(BaseModel):
    hour_of_day: int
    incident_count: int
    avg_risk_score: float

class HistoricalPatternResponse(BaseModel):
    location: LocationSchema
    dominant_incident_type: str
    peak_hours: str
    patterns: List[HistoricalPatternPoint] = Field(default_factory=list)

# Layer 4 - GIS / Location Context
class GISLocationContextResponse(BaseModel):
    location: LocationSchema
    risk_score: float = Field(..., ge=0.0, le=1.0)
    hotspot: bool
    historical_incident_count: int
    dominant_incident_type: str
    peak_time: str
    gis_region_name: str
    boundary_coordinates: Optional[List[LocationSchema]] = None
