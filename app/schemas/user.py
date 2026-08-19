from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class UserResponse(BaseModel):
    id: str
    username: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)

class UserUpdate(BaseModel):
    is_active: Optional[bool] = None
