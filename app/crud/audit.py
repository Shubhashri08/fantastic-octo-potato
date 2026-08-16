from typing import Optional, List, Dict, Any
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog

async def create_audit_log(
    db: AsyncSession,
    action: str,
    user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
) -> AuditLog:
    """
    Creates and records a new audit trace in the database.
    """
    db_log = AuditLog(
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip_address
    )
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log

async def get_audit_logs(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100
) -> List[AuditLog]:
    """
    Retrieves chronological audit logs.
    """
    result = await db.execute(
        select(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())
