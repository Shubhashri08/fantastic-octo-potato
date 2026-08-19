"""
VIGRAH Reconstruction Module.
Assembles event details, correlated entities, and entity trajectories into a reconstructed timeline JSON structure.
"""

import json
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import text

from app.db import SessionLocal
from app.trajectory import get_trajectory_with_movement


def reconstruct_event(event_id: str) -> Dict[str, Any]:
    """
    Constructs a structured reconstructed timeline for an event.

    1. Fetches event from public.events
    2. Fetches correlated entities from public.event_entity_mapping joined with public.entities
    3. Fetches trajectory for each correlated entity via get_trajectory_with_movement(track_id)
    4. Builds structured timeline dictionary
    5. Saves timeline as JSONB to public.events.reconstructed_timeline
    6. Returns the timeline dictionary
    """
    db = SessionLocal()

    try:
        # 1. Fetch Event Details
        event_query = text(
            """
            SELECT
                event_id,
                event_type,
                timestamp,
                severity
            FROM public.events
            WHERE event_id = :event_id
            """
        )
        event_row = db.execute(event_query, {"event_id": event_id}).fetchone()

        if event_row is None:
            raise ValueError(f"Event not found: {event_id}")

        event_data = dict(event_row._mapping)

        if isinstance(event_data.get("timestamp"), datetime):
            event_timestamp_str = event_data["timestamp"].isoformat()
        else:
            event_timestamp_str = str(event_data.get("timestamp")) if event_data.get("timestamp") else None

        event_obj = {
            "event_id": str(event_data["event_id"]),
            "event_type": event_data.get("event_type"),
            "timestamp": event_timestamp_str,
            "severity": event_data.get("severity"),
        }

        # 2. Fetch Correlated Entities
        correlated_query = text(
            """
            SELECT
                eem.track_id,
                e.entity_type,
                eem.association_type,
                eem.proximity_meters
            FROM public.event_entity_mapping eem
            JOIN public.entities e
                ON eem.track_id = e.track_id
            WHERE eem.event_id = :event_id
            """
        )
        entity_rows = db.execute(correlated_query, {"event_id": event_id}).fetchall()

        entities_list: List[Dict[str, Any]] = []

        for entity_row in entity_rows:
            entity_dict = dict(entity_row._mapping)
            track_id = entity_dict["track_id"]

            # 3. Fetch Trajectory for each entity
            raw_trajectory = get_trajectory_with_movement(track_id)

            trajectory_list: List[Dict[str, Any]] = []
            for sighting in raw_trajectory:
                s_dict = dict(sighting)

                if isinstance(s_dict.get("timestamp"), datetime):
                    ts_str = s_dict["timestamp"].isoformat()
                else:
                    ts_str = str(s_dict.get("timestamp")) if s_dict.get("timestamp") is not None else None

                point = {
                    "timestamp": ts_str,
                    "camera_name": s_dict.get("camera_name") or s_dict.get("camera_id"),
                    "latitude": float(s_dict["latitude"]) if s_dict.get("latitude") is not None else None,
                    "longitude": float(s_dict["longitude"]) if s_dict.get("longitude") is not None else None,
                    "distance_from_previous_meters": float(s_dict["distance_from_previous_meters"]) if s_dict.get("distance_from_previous_meters") is not None else None,
                    "time_from_previous_seconds": float(s_dict["time_from_previous_seconds"]) if s_dict.get("time_from_previous_seconds") is not None else None,
                }

                trajectory_list.append(point)

            entity_obj = {
                "track_id": str(track_id),
                "entity_type": entity_dict.get("entity_type"),
                "association_type": entity_dict.get("association_type"),
                "proximity_meters": float(entity_dict["proximity_meters"]) if entity_dict.get("proximity_meters") is not None else None,
                "trajectory": trajectory_list,
            }
            entities_list.append(entity_obj)

        # 4. Construct Reconstruction Document
        timeline_payload: Dict[str, Any] = {
            "event": event_obj,
            "entities": entities_list,
        }

        # 5. Persist JSONB to DB
        update_query = text(
            """
            UPDATE public.events
            SET reconstructed_timeline = :reconstructed_timeline
            WHERE event_id = :event_id
            """
        )
        db.execute(
            update_query,
            {
                "reconstructed_timeline": json.dumps(timeline_payload),
                "event_id": event_id,
            },
        )
        db.commit()

        return timeline_payload

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def build_reconstructed_timeline(event_id: str, save_to_db: bool = True) -> Dict[str, Any]:
    """Alias for reconstruct_event."""
    return reconstruct_event(event_id)
