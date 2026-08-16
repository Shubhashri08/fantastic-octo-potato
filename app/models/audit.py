import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=True) # Nullable for unauthenticated login attempts
    action = Column(String(100), nullable=False, index=True)
    details = Column(JSON, nullable=True) # Will store metadata/results as JSONB
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
