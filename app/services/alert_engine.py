import logging
from app.config import settings
from app.schemas.alert import AlertEvaluationRequest

logger = logging.getLogger(__name__)

class AlertConsistencyError(ValueError):
    """Raised when Layer 3 event and Layer 4 context do not correspond."""
    pass

class AlertEngine:
    @staticmethod
    def validate_consistency(request: AlertEvaluationRequest) -> None:
        """
        Validates that the Layer 4 context corresponds to the Layer 3 event.
        Checks:
        - geographic coordinates tolerance
        """
        event = request.event
        context = request.context

        # Extract coordinates [longitude, latitude]
        event_lon = event.geom.coordinates[0]
        event_lat = event.geom.coordinates[1]

        context_lon = context.geom.coordinates[0]
        context_lat = context.geom.coordinates[1]

        # Verify geographic coordinates are within acceptable tolerance
        lat_diff = abs(event_lat - context_lat)
        lon_diff = abs(event_lon - context_lon)
        
        if lat_diff > settings.GEOGRAPHIC_TOLERANCE or lon_diff > settings.GEOGRAPHIC_TOLERANCE:
            logger.error(
                f"Location discrepancy too high: Event=({event_lat}, {event_lon}), "
                f"Context=({context_lat}, {context_lon}), Tolerance={settings.GEOGRAPHIC_TOLERANCE}"
            )
            raise AlertConsistencyError(
                f"Location tolerance exceeded. Distance difference (lat: {lat_diff:.6f}, "
                f"lon: {lon_diff:.6f}) exceeds limit of {settings.GEOGRAPHIC_TOLERANCE}"
            )

    @staticmethod
    def evaluate_priority(request: AlertEvaluationRequest) -> str:
        """
        Evaluates the alert priority using initial deterministic rules:
        - confidence >= 0.85 AND severity = HIGH -> HIGH
        - confidence >= 0.70 -> MEDIUM
        - otherwise -> LOW
        """
        event = request.event

        if event.confidence >= 0.85 and event.severity.upper() == "HIGH":
            return "HIGH"
        elif event.confidence >= 0.70:
            return "MEDIUM"
        else:
            return "LOW"
