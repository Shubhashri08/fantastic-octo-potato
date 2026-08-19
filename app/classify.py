def classify_entity(
    event_type: str,
    severity: int,
    entity_type: str,
    proximity_meters: float,
    minutes_offset: float,
) -> str:
    """
    Conservative, explainable entity classification.

    Proximity alone is not enough to classify an entity
    as a suspect or victim, so the default is WITNESS.
    """

    # Current Layer 3 policy:
    # nearby entities are treated as witnesses unless
    # stronger evidence is available.
    return "WITNESS"
