from datetime import datetime
from typing import Any, Dict

from sqlalchemy import text

from app.db import SessionLocal


def severity_label(severity: int) -> str:
    if severity <= 2:
        return "low"
    elif severity == 3:
        return "medium"
    else:
        return "high"


def get_event_output(event_id: str) -> Dict[str, Any]:
    """
    Fetches event from public.events and returns the standardized Layer 4 event output payload.
    """
    db = SessionLocal()

    try:
        query = text(
            """
            SELECT
                event_id,
                event_type,
                timestamp,
                severity,
                source,
                confidence,
                ST_Y(geom::geometry) AS latitude,
                ST_X(geom::geometry) AS longitude
            FROM public.events
            WHERE event_id = :event_id
            """
        )
        row = db.execute(query, {"event_id": event_id}).fetchone()

        if row is None:
            raise ValueError(f"Event not found: {event_id}")

        data = dict(row._mapping)

        if isinstance(data.get("timestamp"), datetime):
            timestamp_str = data["timestamp"].isoformat()
        else:
            timestamp_str = str(data.get("timestamp")) if data.get("timestamp") else None

        sev_numeric = int(data["severity"]) if data.get("severity") is not None else 0
        sev_str = severity_label(sev_numeric)

        return {
            "event_id": str(data["event_id"]),
            "timestamp": timestamp_str,
            "latitude": float(data["latitude"]) if data.get("latitude") is not None else None,
            "longitude": float(data["longitude"]) if data.get("longitude") is not None else None,
            "event_type": data.get("event_type"),
            "severity": sev_str,
            "source": data.get("source"),
            "confidence": float(data["confidence"]) if data.get("confidence") is not None else None,
        }

    finally:
        db.close()
