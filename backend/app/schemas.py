from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CameraBase(BaseModel):
    name: str
    source: str
    source_type: str = "webcam"
    lat: float = 28.6139
    lon: float = 77.2090
    is_active: bool = True

class CameraCreate(CameraBase):
    pass

class CameraResponse(CameraBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class EventBase(BaseModel):
    camera_id: int
    event_type: str
    confidence: float
    bbox: Optional[str] = None
    snapshot_path: Optional[str] = None
    video_clip_path: Optional[str] = None
    severity: str = "Medium"

class EventCreate(EventBase):
    pass

class EventResponse(EventBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class StartDetectionRequest(BaseModel):
    camera_id: int
    source: Optional[str] = None
    source_type: Optional[str] = None

class DetectionStatusResponse(BaseModel):
    camera_id: int
    running: bool
    source: str
    fps: float
    active_models: List[str]
