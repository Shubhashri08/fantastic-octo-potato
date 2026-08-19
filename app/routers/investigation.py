import uuid
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.crud.investigation import (
    create_investigation_query,
    get_investigation_query_by_id,
    get_investigation_queries
)
from app.crud.audit import create_audit_log
from app.services.llm_service import LlmService, ExtractedIntent
from app.services.query_executor import QueryExecutor, ValidationError
from app.integrations.base_client import (
    UpstreamTimeoutError,
    UpstreamConnectionError,
    UpstreamResponseValidationError,
    UpstreamResponseError
)
from app.auth.dependencies import get_current_user
from app.schemas.investigation import QueryRequest, QueryResponse
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/investigation", tags=["Investigation Assistant"])

# Instantiate services
llm_service = LlmService()
query_executor = QueryExecutor()

@router.post("/query", response_model=QueryResponse)
async def ask_question(
    payload: QueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submits user query to the AI Assistant.
    Flow:
    1. Extracts intent structure using Gemini.
    2. Validates operation parameters.
    3. Fetches live data snapshot from the appropriate Layer 3 or Layer 4 client (verified evidence).
    4. Passes the snapshot to Gemini to write the markdown response.
    5. Saves full execution traces and audit logs.
    """
    correlation_id = f"INV_CORR_{uuid.uuid4().hex[:12]}"
    user_question = payload.question

    # 1. Intent Extraction
    try:
        intent = await llm_service.extract_intent(user_question)
    except Exception as e:
        logger.error(f"Intent extraction failed: {str(e)}")
        # Log failure
        await create_investigation_query(
            db=db,
            user_id=current_user.id,
            user_question=user_question,
            validation_status="REJECTED",
            llm_response="Could not extract query intent."
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to parse question intent structure."
        )

    # 2. Validation & Execution of Upstream Client Request
    verified_data = None
    query_executed = f"Operation: {intent.operation}"
    try:
        verified_data = await query_executor.execute(intent, correlation_id)
        validation_status = "VALIDATED"
    except ValidationError as e:
        logger.warning(f"Intent validation check failed: {str(e)}")
        # Log parameter failure
        await create_investigation_query(
            db=db,
            user_id=current_user.id,
            user_question=user_question,
            validation_status="REJECTED",
            llm_intent=intent.model_dump(),
            llm_response=f"Validation failed: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parameters validation failed: {str(e)}"
        )
    except UpstreamTimeoutError as e:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(e))
    except (UpstreamConnectionError, UpstreamResponseValidationError) as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except UpstreamResponseError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

    # 3. LLM synthesis of answer using verified snapshot only
    try:
        llm_response = await llm_service.generate_answer(user_question, verified_data)
    except Exception as e:
        logger.error(f"Gemini answer generation failed: {str(e)}")
        llm_response = "Could not synthesize response from database evidence."

    # 4. Save Query Trace to Database (including verified_data snapshot)
    query_record = await create_investigation_query(
        db=db,
        user_id=current_user.id,
        user_question=user_question,
        validation_status=validation_status,
        llm_intent=intent.model_dump(),
        query_executed=query_executed,
        verified_data=verified_data,
        llm_response=llm_response
    )

    # 5. Log action in Audit log
    await create_audit_log(
        db=db,
        action="INVESTIGATION_QUERY",
        user_id=current_user.id,
        details={
            "query_id": query_record.id,
            "operation": intent.operation,
            "correlation_id": correlation_id
        }
    )

    return query_record

@router.get("/history", response_model=List[QueryResponse])
async def list_queries(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns investigation question histories.
    Requires authentication.
    """
    queries = await get_investigation_queries(db, skip=skip, limit=limit)
    return queries

@router.get("/{query_id}", response_model=QueryResponse)
async def get_query(
    query_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves individual query execution trace and snapshots.
    Requires authentication.
    """
    query_record = await get_investigation_query_by_id(db, query_id)
    if not query_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query log with ID {query_id} not found."
        )
    return query_record
