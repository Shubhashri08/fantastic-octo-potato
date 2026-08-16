import logging
from datetime import datetime
from typing import Optional
from pydantic import ValidationError
from app.config import settings
from app.integrations.base_client import BaseClient, UpstreamResponseValidationError
from app.schemas.integration import (
    EntityHistoryResponse,
    EventTimelineResponse,
    EventEntitiesResponse,
    CameraHistoryResponse
)

logger = logging.getLogger(__name__)

class Layer3Client(BaseClient):
    """
    Client for interacting with upstream Layer 3 (CONNECT / IDENTIFY) service.
    Note: All API paths documented here are PROPOSED contracts pending final upstream integration.
    """

    def __init__(self):
        super().__init__(
            base_url=settings.LAYER3_BASE_URL,
            token=settings.LAYER3_CLIENT_TOKEN
        )

    async def get_entity_history(
        self, 
        entity_id: str, 
        correlation_id: str, 
        start_time: Optional[datetime] = None, 
        end_time: Optional[datetime] = None
    ) -> EntityHistoryResponse:
        """
        [PROPOSED API CONTRACT]: GET /api/v1/entities/{entity_id}/history
        Fetches tracking history points for an entity.
        """
        params = {}
        if start_time:
            params["start_time"] = start_time.isoformat()
        if end_time:
            params["end_time"] = end_time.isoformat()

        response = await self._request(
            method="GET",
            path=f"/api/v1/entities/{entity_id}/history",
            correlation_id=correlation_id,
            params=params
        )
        try:
            return EntityHistoryResponse.model_validate(response.json())
        except ValidationError as e:
            logger.error(f"Layer 3 get_entity_history schema validation error: {str(e)}")
            raise UpstreamResponseValidationError(f"Invalid response format from Layer 3 get_entity_history: {str(e)}")

    async def get_event_timeline(self, event_id: str, correlation_id: str) -> EventTimelineResponse:
        """
        [PROPOSED API CONTRACT]: GET /api/v1/events/{event_id}/timeline
        Fetches chronological milestones of an event.
        """
        response = await self._request(
            method="GET",
            path=f"/api/v1/events/{event_id}/timeline",
            correlation_id=correlation_id
        )
        try:
            return EventTimelineResponse.model_validate(response.json())
        except ValidationError as e:
            logger.error(f"Layer 3 get_event_timeline schema validation error: {str(e)}")
            raise UpstreamResponseValidationError(f"Invalid response format from Layer 3 get_event_timeline: {str(e)}")

    async def get_event_entities(self, event_id: str, correlation_id: str) -> EventEntitiesResponse:
        """
        [PROPOSED API CONTRACT]: GET /api/v1/events/{event_id}/entities
        Fetches tracking entities connected to the event.
        """
        response = await self._request(
            method="GET",
            path=f"/api/v1/events/{event_id}/entities",
            correlation_id=correlation_id
        )
        try:
            return EventEntitiesResponse.model_validate(response.json())
        except ValidationError as e:
            logger.error(f"Layer 3 get_event_entities schema validation error: {str(e)}")
            raise UpstreamResponseValidationError(f"Invalid response format from Layer 3 get_event_entities: {str(e)}")

    async def get_camera_history(
        self, 
        camera_id: str, 
        correlation_id: str, 
        start_time: Optional[datetime] = None, 
        end_time: Optional[datetime] = None
    ) -> CameraHistoryResponse:
        """
        [PROPOSED API CONTRACT]: GET /api/v1/cameras/{camera_id}/history
        Fetches historical records of objects captured by camera.
        """
        params = {}
        if start_time:
            params["start_time"] = start_time.isoformat()
        if end_time:
            params["end_time"] = end_time.isoformat()

        response = await self._request(
            method="GET",
            path=f"/api/v1/cameras/{camera_id}/history",
            correlation_id=correlation_id,
            params=params
        )
        try:
            return CameraHistoryResponse.model_validate(response.json())
        except ValidationError as e:
            logger.error(f"Layer 3 get_camera_history schema validation error: {str(e)}")
            raise UpstreamResponseValidationError(f"Invalid response format from Layer 3 get_camera_history: {str(e)}")
