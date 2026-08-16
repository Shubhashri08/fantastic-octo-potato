import pytest
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings
from app.database import Base
from app.models.alert import Alert
from app.crud.alert import create_alert, get_alert_by_event_id
from app.schemas.alert import AlertEvaluationRequest, Layer3EventSchema, Layer4ContextSchema, LocationSchema

import os
from dotenv import load_dotenv

# Load the real PostgreSQL environment variables
load_dotenv()
real_db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/vigrah_l5")

# Define engine using real PostgreSQL database url
engine = create_async_engine(real_db_url)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

@pytest.mark.asyncio
async def test_postgres_alert_ingest_and_spatial_query():
    """
    Verifies alert ingestion, database uniqueness constraint, and real PostGIS
    ST_DWithin spatial queries through the application's database layer.
    """
    # 1. Prepare Request Data
    event_id = "EVT_POSTGRES_TEST_123"
    correlation_id = "CORR_POSTGRES_TEST"
    lat, lon = 19.123, 72.456

    payload = AlertEvaluationRequest(
        event=Layer3EventSchema(
            event_id=event_id,
            event_type="accident",
            timestamp=datetime.utcnow(),
            location=LocationSchema(latitude=lat, longitude=lon),
            confidence=0.95,
            severity="HIGH",
            entities=["vehicle_V17"],
            cameras=["CAM_03"],
            correlation_id=correlation_id
        ),
        context=Layer4ContextSchema(
            location=LocationSchema(latitude=lat, longitude=lon),
            risk_score=0.8,
            hotspot=True,
            historical_incident_count=5,
            dominant_incident_type="accident",
            peak_time="18:00-22:00",
            correlation_id=correlation_id
        )
    )

    async with SessionLocal() as session:
        # Cleanup pre-existing test alert if any
        existing = await get_alert_by_event_id(session, event_id)
        if existing:
            await session.delete(existing)
            await session.commit()

        # 2. Ingest via create_alert
        alert = await create_alert(session, payload, "HIGH")
        assert alert.event_id == event_id
        assert alert.priority == "HIGH"
        assert alert.status == "NEW"

        # 3. Verify uniqueness constraint
        # Attempting to insert duplicate alert should trigger db unique constraint and raise IntegrityError
        # or be caught by create_alert to return the existing one. Let's verify create_alert returns existing (idempotency)
        duplicate_alert = await create_alert(session, payload, "HIGH")
        assert duplicate_alert.id == alert.id

        # 4. Perform a real PostGIS ST_DWithin query via SQLAlchemy session
        # Check if the alert location is within 100 meters (approx 0.0009 degrees)
        # Using PostGIS ST_DWithin geography query
        query = text("""
            SELECT id, event_id 
            FROM alerts 
            WHERE ST_DWithin(
                ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography, 
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 
                :radius_meters
            )
            AND event_id = :event_id
        """)
        res = await session.execute(query, {"lon": lon, "lat": lat, "radius_meters": 100.0, "event_id": event_id})
        rows = res.fetchall()
        assert len(rows) == 1
        assert rows[0][1] == event_id

        # Cleanup test alert
        await session.delete(alert)
        await session.commit()
