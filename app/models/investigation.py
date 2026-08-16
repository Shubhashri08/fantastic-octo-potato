import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class InvestigationQuery(Base):
    __tablename__ = "investigation_queries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    user_question = Column(Text, nullable=False)
    
    # Store LLM intent extraction details (e.g., {"operation": "GET_ENTITY_HISTORY", "parameters": {"entity_id": "vehicle_V17"}})
    llm_intent = Column(JSON, nullable=True)
    validation_status = Column(String(50), nullable=False) # VALIDATED, REJECTED
    query_executed = Column(String(255), nullable=True) # Description of what query was sent to client
    
    # Real data snapshot retrieved from integration clients
    verified_data = Column(JSON, nullable=True)
    
    # Generated markdown report
    llm_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
