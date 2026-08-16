import logging
from pydantic import ValidationError
from app.config import settings
from app.integrations.base_client import BaseClient, UpstreamResponseValidationError
from app.schemas.integration import (
    NearbyIncidentsResponse,
    HistoricalPatternResponse,
    GISLocationContextResponse
)

logger = logging.getLogger(__name__)

class Layer4Client(BaseClient):
    """
    Client for interacting with upstream Layer 4 (UNDERSTAND) service.
    Note: All API paths documented here are PROPOSED contracts pending final upstream integration.
    """

    def __init__(self):
        super().__init__(
            base_url=settings.LAYER4_BASE_URL,
            token=settings.LAYER4_CLIENT_TOKEN
        )

    async def get_nearby_incidents(
        self, 
        latitude: float, 
        longitude: float, 
        radius_meters: float, 
        correlation_id: str
    ) -> NearbyIncidentsResponse:
        """
        [PROPOSED API CONTRACT]: GET /api/v1/gis/nearby
        Fetches incident data within a bounding radius.
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "radius_meters": radius_meters
        }
        response = await self._request(
            method="GET",
            path="/api/v1/gis/nearby",
            correlation_id=correlation_id,
            params=params
        )
        try:
            return NearbyIncidentsResponse.model_validate(response.json())
        except ValidationError as e:
            logger.error(f"Layer 4 get_nearby_incidents schema validation error: {str(e)}")
            raise UpstreamResponseValidationError(f"Invalid response format from Layer 4 get_nearby_incidents: {str(e)}")

    async def get_historical_pattern(
        self, 
        latitude: float, 
        longitude: float, 
        correlation_id: str
    ) -> HistoricalPatternResponse:
        """
        [PROPOSED API CONTRACT]: GET /api/v1/historical/patterns
        Fetches risk pattern metrics (e.g. peak hours, counts).
        """
        params = {
            "latitude": latitude,
            "longitude": longitude
        }
        response = await self._request(
            method="GET",
            path="/api/v1/historical/patterns",
            correlation_id=correlation_id,
            params=params
        )
        try:
            return HistoricalPatternResponse.model_validate(response.json())
        except ValidationError as e:
            logger.error(f"Layer 4 get_historical_pattern schema validation error: {str(e)}")
            raise UpstreamResponseValidationError(f"Invalid response format from Layer 4 get_historical_pattern: {str(e)}")

    async def get_location_context(
        self, 
        latitude: float, 
        longitude: float, 
        correlation_id: str
    ) -> GISLocationContextResponse:
        """
        [PROPOSED API CONTRACT]: GET /api/v1/gis/context
        Fetches location contextual data like risk score and region attributes.
        """
        params = {
            "latitude": latitude,
            "longitude": longitude
        }
        response = await self._request(
            method="GET",
            path="/api/v1/gis/context",
            correlation_id=correlation_id,
            params=params
        )
        try:
            return GISLocationContextResponse.model_validate(response.json())
        except ValidationError as e:
            logger.error(f"Layer 4 get_location_context schema validation error: {str(e)}")
            raise UpstreamResponseValidationError(f"Invalid response format from Layer 4 get_location_context: {str(e)}")
class_name = "Layer4Client"
