from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.crud.user import (
    get_user_by_id, 
    get_user_by_username, 
    get_users, 
    create_user, 
    update_user
)
from app.crud.audit import create_audit_log
from app.auth.dependencies import get_current_user
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.models.user import User

router = APIRouter(prefix="/users", tags=["User Management"])

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Creates a new system user. Requires authentication.
    Logs action in audit log.
    """
    existing_user = await get_user_by_username(db, payload.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered."
        )

    user = await create_user(db, payload)

    # Log action
    await create_audit_log(
        db=db,
        action="USER_CREATE",
        user_id=current_user.id,
        details={
            "created_username": user.username
        }
    )

    return user

@router.get("", response_model=List[UserResponse])
async def list_system_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lists system users. Requires authentication.
    """
    users = await get_users(db, skip=skip, limit=limit)
    return users

@router.patch("/{id}", response_model=UserResponse)
async def update_system_user(
    id: str,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Updates user settings (status). Requires authentication.
    Logs action in audit log.
    """
    user = await get_user_by_id(db, id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {id} not found."
        )

    # Prevent deactivating or modifying own user
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot edit or deactivate their own profiles."
        )

    updated_user = await update_user(db, user, payload)

    # Log action
    await create_audit_log(
        db=db,
        action="USER_UPDATE",
        user_id=current_user.id,
        details={
            "updated_username": user.username,
            "updated_fields": {k: v for k, v in payload.model_dump().items() if v is not None}
        }
    )

    return updated_user
