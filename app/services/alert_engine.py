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
        - correlation_id match
        - geographic coordinates tolerance
        """
        event = request.event
        context = request.context

        # 1. Verify Correlation ID matches
        if event.correlation_id != context.correlation_id:
            logger.error(
                f"Correlation ID mismatch: Event correlation_id={event.correlation_id}, "
                f"Context correlation_id={context.correlation_id}"
            )
            raise AlertConsistencyError(
                f"Correlation ID mismatch. Event ({event.correlation_id}) "
                f"does not match Context ({context.correlation_id})"
            )

        # 2. Verify geographic coordinates are within acceptable tolerance
        lat_diff = abs(event.location.latitude - context.location.latitude)
        lon_diff = abs(event.location.longitude - context.location.longitude)
        
        if lat_diff > settings.GEOGRAPHIC_TOLERANCE or lon_diff > settings.GEOGRAPHIC_TOLERANCE:
            logger.error(
                f"Location discrepancy too high: Event={event.location}, Context={context.location}, "
                f"Tolerance={settings.GEOGRAPHIC_TOLERANCE}"
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
