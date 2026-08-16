from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    id: str
    user_id: str
    user_question: str
    llm_intent: Optional[Dict[str, Any]] = None
    validation_status: str
    query_executed: Optional[str] = None
    verified_data: Optional[Dict[str, Any]] = None
    llm_response: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
