import logging
from typing import Dict, Any
from app.integrations.layer3_client import Layer3Client
from app.integrations.layer4_client import Layer4Client
from app.services.llm_service import ExtractedIntent

logger = logging.getLogger(__name__)

class ValidationError(ValueError):
    """Raised when intent validation checks fail."""
    pass

class QueryExecutor:
    def __init__(self):
        self.layer3_client = Layer3Client()
        self.layer4_client = Layer4Client()

    async def execute(self, intent: ExtractedIntent, correlation_id: str) -> Dict[str, Any]:
        """
        Validates parameter formats and constraints, and retrieves real data via the integration clients.
        Returns a dict of the verified data.
        """
        op = intent.operation
        params = intent.parameters or {}

        logger.info(f"Validating and executing operation: {op} with params: {params}")

        if op == "GET_ENTITY_HISTORY":
            entity_id = params.get("entity_id")
            if not entity_id or not isinstance(entity_id, str):
                raise ValidationError("GET_ENTITY_HISTORY requires a string 'entity_id'.")
            
            result = await self.layer3_client.get_entity_history(
                entity_id=entity_id, 
                correlation_id=correlation_id
            )
            return result.model_dump(mode="json")

        elif op == "GET_EVENT_TIMELINE":
            event_id = params.get("event_id")
            if not event_id or not isinstance(event_id, str):
                raise ValidationError("GET_EVENT_TIMELINE requires a string 'event_id'.")
            
            result = await self.layer3_client.get_event_timeline(
                event_id=event_id, 
                correlation_id=correlation_id
            )
            return result.model_dump(mode="json")

        elif op == "GET_EVENT_ENTITIES":
            event_id = params.get("event_id")
            if not event_id or not isinstance(event_id, str):
                raise ValidationError("GET_EVENT_ENTITIES requires a string 'event_id'.")
            
            result = await self.layer3_client.get_event_entities(
                event_id=event_id, 
                correlation_id=correlation_id
            )
            return result.model_dump(mode="json")

        elif op == "GET_CAMERA_HISTORY":
            camera_id = params.get("camera_id")
            if not camera_id or not isinstance(camera_id, str):
                raise ValidationError("GET_CAMERA_HISTORY requires a string 'camera_id'.")
            
            result = await self.layer3_client.get_camera_history(
                camera_id=camera_id, 
                correlation_id=correlation_id
            )
            return result.model_dump(mode="json")

        elif op == "GET_NEARBY_INCIDENTS":
            try:
                lat = float(params.get("latitude"))
                lon = float(params.get("longitude"))
                # Default radius to 500 meters if not provided
                radius = float(params.get("radius_meters", 500.0))
            except (TypeError, ValueError):
                raise ValidationError("GET_NEARBY_INCIDENTS requires numeric 'latitude', 'longitude', and 'radius_meters'.")

            self._validate_coordinates(lat, lon)
            if radius <= 0:
                raise ValidationError("radius_meters must be a positive number.")

            result = await self.layer4_client.get_nearby_incidents(
                latitude=lat, 
                longitude=lon, 
                radius_meters=radius, 
                correlation_id=correlation_id
            )
            return result.model_dump(mode="json")

        elif op == "GET_HISTORICAL_PATTERN":
            try:
                lat = float(params.get("latitude"))
                lon = float(params.get("longitude"))
            except (TypeError, ValueError):
                raise ValidationError("GET_HISTORICAL_PATTERN requires numeric 'latitude' and 'longitude'.")

            self._validate_coordinates(lat, lon)

            result = await self.layer4_client.get_historical_pattern(
                latitude=lat, 
                longitude=lon, 
                correlation_id=correlation_id
            )
            return result.model_dump(mode="json")

        elif op == "GET_LOCATION_CONTEXT":
            try:
                lat = float(params.get("latitude"))
                lon = float(params.get("longitude"))
            except (TypeError, ValueError):
                raise ValidationError("GET_LOCATION_CONTEXT requires numeric 'latitude' and 'longitude'.")

            self._validate_coordinates(lat, lon)

            result = await self.layer4_client.get_location_context(
                latitude=lat, 
                longitude=lon, 
                correlation_id=correlation_id
            )
            return result.model_dump(mode="json")

        else:
            raise ValidationError(f"Operation '{op}' is not supported or recognized.")

    def _validate_coordinates(self, lat: float, lon: float) -> None:
        """Helper to assert standard geographic coordinate boundaries."""
        if not (-90.0 <= lat <= 90.0):
            raise ValidationError(f"latitude must be between -90 and 90. Received: {lat}")
        if not (-180.0 <= lon <= 180.0):
            raise ValidationError(f"longitude must be between -180 and 180. Received: {lon}")
