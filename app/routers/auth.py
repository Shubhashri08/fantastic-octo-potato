from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.crud.user import get_user_by_username
from app.crud.audit import create_audit_log
from app.auth.jwt import verify_password, create_access_token
from app.auth.dependencies import get_current_user
from app.schemas.auth import Token
from app.schemas.user import UserResponse
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    """
    OAuth2 compatible token login, yielding a JWT bearer token.
    Saves an audit log entry on success/failure.
    """
    user = await get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Log failed login attempt
        await create_audit_log(
            db=db,
            action="LOGIN_FAILURE",
            details={"attempted_username": form_data.username}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Log successful login
    await create_audit_log(
        db=db,
        action="LOGIN",
        user_id=user.id,
        details={"username": user.username}
    )

    access_token = create_access_token(subject=user.username)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the authenticated user's profile and active role mapping.
    """
    return current_user
