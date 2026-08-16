from typing import Optional, List, Dict, Any
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.investigation import InvestigationQuery

async def create_investigation_query(
    db: AsyncSession,
    user_id: str,
    user_question: str,
    validation_status: str,
    llm_intent: Optional[Dict[str, Any]] = None,
    query_executed: Optional[str] = None,
    verified_data: Optional[Dict[str, Any]] = None,
    llm_response: Optional[str] = None
) -> InvestigationQuery:
    """
    Creates and logs a new investigation trace, including the immutable verified data snapshot.
    """
    db_query = InvestigationQuery(
        user_id=user_id,
        user_question=user_question,
        llm_intent=llm_intent,
        validation_status=validation_status,
        query_executed=query_executed,
        verified_data=verified_data,
        llm_response=llm_response
    )
    db.add(db_query)
    await db.commit()
    await db.refresh(db_query)
    return db_query

async def get_investigation_query_by_id(
    db: AsyncSession, 
    query_id: str
) -> Optional[InvestigationQuery]:
    result = await db.execute(select(InvestigationQuery).filter(InvestigationQuery.id == query_id))
    return result.scalars().first()

async def get_investigation_queries(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100
) -> List[InvestigationQuery]:
    result = await db.execute(
        select(InvestigationQuery)
        .order_by(InvestigationQuery.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())
