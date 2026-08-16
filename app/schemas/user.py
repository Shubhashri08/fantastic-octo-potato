from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: str
    username: str
    is_active: bool
    role_id: int
    role: Optional[RoleResponse] = None
    created_at: datetime

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)
    role_id: int

class UserUpdate(BaseModel):
    role_id: Optional[int] = None
    is_active: Optional[bool] = None
