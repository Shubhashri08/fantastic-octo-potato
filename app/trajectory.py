from sqlalchemy import text

from app.db import SessionLocal


def get_trajectory(track_id: str) -> list[dict]:
    db = SessionLocal()

    try:
        query = text(
            """
            SELECT
                es.sighting_id,
                es.track_id,
                es.camera_id,
                c.camera_name,
                es.timestamp,
                ST_Y(es.geom::geometry) AS latitude,
                ST_X(es.geom::geometry) AS longitude
            FROM public.entity_sightings es
            LEFT JOIN public.cameras c
                ON c.camera_id = es.camera_id
            WHERE es.track_id = :track_id
            ORDER BY es.timestamp ASC
            """
        )

        result = db.execute(
            query,
            {"track_id": track_id},
        )

        return [dict(row._mapping) for row in result]

    finally:
        db.close()


def get_trajectory_with_movement(track_id: str) -> list[dict]:
    db = SessionLocal()

    try:
        query = text(
            """
            WITH trajectory AS (
                SELECT
                    es.sighting_id,
                    es.track_id,
                    es.camera_id,
                    c.camera_name,
                    es.timestamp,
                    es.geom,

                    LAG(es.geom) OVER (
                        PARTITION BY es.track_id
                        ORDER BY es.timestamp
                    ) AS previous_geom,

                    LAG(es.timestamp) OVER (
                        PARTITION BY es.track_id
                        ORDER BY es.timestamp
                    ) AS previous_timestamp

                FROM public.entity_sightings es

                LEFT JOIN public.cameras c
                    ON c.camera_id = es.camera_id

                WHERE es.track_id = :track_id
            )

            SELECT
                sighting_id,
                track_id,
                camera_id,
                camera_name,
                timestamp,

                ST_Y(geom::geometry) AS latitude,
                ST_X(geom::geometry) AS longitude,

                CASE
                    WHEN previous_geom IS NULL
                    THEN NULL
                    ELSE ST_Distance(
                        geom,
                        previous_geom
                    )
                END AS distance_from_previous_meters,

                CASE
                    WHEN previous_timestamp IS NULL
                    THEN NULL
                    ELSE EXTRACT(
                        EPOCH FROM (
                            timestamp - previous_timestamp
                        )
                    )
                END AS time_from_previous_seconds

            FROM trajectory

            ORDER BY timestamp ASC
            """
        )

        result = db.execute(
            query,
            {"track_id": track_id},
        )

        return [dict(row._mapping) for row in result]

    finally:
        db.close()