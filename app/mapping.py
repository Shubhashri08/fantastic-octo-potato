from sqlalchemy import text

from app.classify import classify_entity
from app.db import SessionLocal


def save_mapping(event_id: str, candidates: list[dict]) -> int:
    db = SessionLocal()

    try:
        event_query = text(
            """
            SELECT event_type, severity
            FROM public.events
            WHERE event_id = :event_id
            """
        )

        event = db.execute(event_query, {"event_id": event_id}).fetchone()

        if event is None:
            raise ValueError(f"Event not found: {event_id}")

        event_type, severity = event

        entity_query = text(
            """
            SELECT track_id, entity_type
            FROM public.entities
            WHERE track_id = :track_id
            """
        )

        insert_query = text(
            """
            INSERT INTO public.event_entity_mapping
            (
                event_id,
                track_id,
                association_type,
                proximity_meters
            )
            VALUES
            (
                :event_id,
                :track_id,
                :association_type,
                :proximity_meters
            )
            ON CONFLICT (event_id, track_id)
            DO UPDATE SET
                association_type = EXCLUDED.association_type,
                proximity_meters = EXCLUDED.proximity_meters
            """
        )

        saved = 0

        for candidate in candidates:
            entity = db.execute(
                entity_query,
                {"track_id": candidate["track_id"]},
            ).fetchone()

            if entity is None:
                continue

            track_id, entity_type = entity

            association_type = classify_entity(
                event_type=event_type,
                severity=severity,
                entity_type=entity_type,
                proximity_meters=float(candidate["proximity_meters"]),
                minutes_offset=float(candidate["minutes_offset"]),
            )

            db.execute(
                insert_query,
                {
                    "event_id": event_id,
                    "track_id": track_id,
                    "association_type": association_type,
                    "proximity_meters": candidate["proximity_meters"],
                },
            )

            saved += 1

        db.commit()

        return saved

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
