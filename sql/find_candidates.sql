SELECT
    es.sighting_id,
    es.track_id,
    es.camera_id,
    es.timestamp,

    ST_Distance(
        es.geom,
        e.geom
    ) AS proximity_meters,

    EXTRACT(
        EPOCH FROM (es.timestamp - e.timestamp)
    ) / 60.0 AS minutes_offset

FROM entity_sightings es
JOIN events e
    ON e.event_id = :event_id

WHERE es.timestamp
    BETWEEN e.timestamp
        - (:time_window_minutes || ' minutes')::interval
        AND e.timestamp
        + (:time_window_minutes || ' minutes')::interval

AND ST_DWithin(
    es.geom,
    e.geom,
    :radius_meters
)

ORDER BY proximity_meters ASC;