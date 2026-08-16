from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.crud.alert import (
    get_alert_by_id, 
    get_alerts, 
    create_alert, 
    update_alert_status,
    get_alert_by_event_id
)
from app.crud.audit import create_audit_log
from app.services.alert_engine import AlertEngine, AlertConsistencyError
from app.auth.dependencies import get_current_user, require_permission
from app.schemas.alert import AlertEvaluationRequest, AlertResponse, AlertStatusUpdate
from app.models.user import User

router = APIRouter(prefix="/alerts", tags=["Alert Engine"])

@router.post("/evaluate", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def evaluate_alert(
    payload: AlertEvaluationRequest,
    response: Response,
    req: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Ingests connected event (Layer 3) and geo-context (Layer 4) to evaluate priority,
    creates the Alert record, and registers an audit log entry.
    Enforces validation consistency and idempotency (returning existing alert if event_id matches).
    """
    import uuid

    # 1. Validate data consistency between Layer 3 and Layer 4 inputs
    try:
        AlertEngine.validate_consistency(payload)
    except AlertConsistencyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Extract correlation ID from transport headers
    correlation_id = req.headers.get("X-Correlation-ID", f"CORR_L5_{uuid.uuid4().hex[:12]}")

    # Idempotency Check: return existing alert if already ingested
    existing = await get_alert_by_event_id(db, str(payload.event.event_id))
    if existing:
        response.status_code = status.HTTP_200_OK
        return existing

    # 2. Evaluate alert priority level
    priority = AlertEngine.evaluate_priority(payload)

    # 3. Persist alert atomically (idempotent creation)
    alert = await create_alert(db=db, request=payload, priority=priority, correlation_id=correlation_id)

    # 4. Record audit log
    await create_audit_log(
        db=db,
        action="ALERT_EVALUATE",
        details={
            "event_id": alert.event_id,
            "correlation_id": alert.correlation_id,
            "priority": alert.priority,
            "status": alert.status
        }
    )

    return alert

@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("VIEW_ALERTS"))
):
    """
    Lists system alerts. Supports filtering by priority and status.
    Requires VIEW_ALERTS permission.
    """
    alerts = await get_alerts(db, skip=skip, limit=limit, status=status, priority=priority)
    return alerts

@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("VIEW_ALERTS"))
):
    """
    Retrieves individual alert details.
    Requires VIEW_ALERTS permission.
    """
    alert = await get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found."
        )
    return alert

@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    payload: AlertStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Updates individual alert status (NEW -> ACKNOWLEDGED -> RESOLVED).
    Enforces authorization check:
    - User must hold the ACKNOWLEDGE_ALERTS permission to acknowledge or resolve an alert.
    Logs actions in the audit trail.
    """
    alert = await get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found."
        )

    requested_status = payload.status.upper()
    if requested_status not in ["NEW", "ACKNOWLEDGED", "RESOLVED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status value. Must be 'NEW', 'ACKNOWLEDGED', or 'RESOLVED'."
        )

    # Validate permissions dynamically based on status transition
    user_permissions = {p.name.upper() for p in current_user.role.permissions}
    is_admin = current_user.role.name.upper() == "ADMIN"
    
    if not is_admin and "ACKNOWLEDGE_ALERTS" not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to acknowledge or resolve alerts"
        )

    updated_alert = await update_alert_status(
        db=db,
        alert=alert,
        new_status=requested_status,
        user_id=current_user.id
    )

    # Log action to audit logs
    await create_audit_log(
        db=db,
        action="ALERT_STATUS_UPDATE",
        user_id=current_user.id,
        details={
            "alert_id": alert_id,
            "old_status": alert.status,
            "new_status": requested_status
        }
    )

    return updated_alert
