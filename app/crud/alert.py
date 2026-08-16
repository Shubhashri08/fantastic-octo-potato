from datetime import datetime
from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.models.alert import Alert
from app.schemas.alert import AlertEvaluationRequest

async def get_alert_by_id(db: AsyncSession, alert_id: str) -> Optional[Alert]:
    result = await db.execute(select(Alert).filter(Alert.id == alert_id))
    return result.scalars().first()

async def get_alert_by_event_id(db: AsyncSession, event_id: str) -> Optional[Alert]:
    result = await db.execute(select(Alert).filter(Alert.event_id == event_id))
    return result.scalars().first()

async def get_alerts(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    priority: Optional[str] = None
) -> List[Alert]:
    query = select(Alert)
    if status:
        query = query.filter(Alert.status == status.upper())
    if priority:
        query = query.filter(Alert.priority == priority.upper())
    
    query = query.order_by(Alert.timestamp.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())

async def create_alert(
    db: AsyncSession,
    request: AlertEvaluationRequest,
    priority: str
) -> Alert:
    """
    Creates a new Alert.
    Handles unique key violations on event_id atomically to guarantee idempotency.
    """
    event = request.event
    context = request.context

    # 1. Double check existence to save transaction rollback overhead in non-race scenarios
    existing = await get_alert_by_event_id(db, event.event_id)
    if existing:
        return existing

    # 2. Prepare new alert record
    db_alert = Alert(
        event_id=event.event_id,
        event_type=event.event_type,
        timestamp=event.timestamp.replace(tzinfo=None), # Remove tzinfo for database compatibility
        latitude=event.location.latitude,
        longitude=event.location.longitude,
        confidence=event.confidence,
        severity=event.severity.upper(),
        entities=event.entities,
        cameras=event.cameras,
        
        risk_score=context.risk_score,
        hotspot=context.hotspot,
        historical_incident_count=context.historical_incident_count,
        dominant_incident_type=context.dominant_incident_type,
        peak_time=context.peak_time,
        
        priority=priority.upper(),
        status="NEW",
        correlation_id=event.correlation_id
    )

    db.add(db_alert)
    try:
        await db.commit()
        await db.refresh(db_alert)
        return db_alert
    except IntegrityError:
        # Atomic lock triggered: duplicate insert occurred concurrently. Rollback and fetch original.
        await db.rollback()
        existing = await get_alert_by_event_id(db, event.event_id)
        if existing:
            return existing
        raise

async def update_alert_status(
    db: AsyncSession,
    alert: Alert,
    new_status: str,
    user_id: str
) -> Alert:
    """
    Updates the alert status and logs the modifying user ID and timestamp.
    """
    status_upper = new_status.upper()
    alert.status = status_upper

    if status_upper == "ACKNOWLEDGED":
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.utcnow()
    elif status_upper == "RESOLVED":
        alert.resolved_by = user_id
        alert.resolved_at = datetime.utcnow()

    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert
