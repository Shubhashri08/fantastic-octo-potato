from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth.jwt import decode_access_token
from app.models.user import User, Role, Permission

# Setup OAuth2 token scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    FastAPI dependency that extracts the current user from the JWT bearer token.
    Loads user relationships (role and permissions) eagerly.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    username = decode_access_token(token)
    if username is None:
        raise credentials_exception

    # Query the user and eagerly load their role and permissions
    result = await db.execute(
        select(User)
        .filter(User.username == username)
        .options(selectinload(User.role).selectinload(Role.permissions))
    )
    user = result.scalars().first()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user account")
        
    return user

class PermissionChecker:
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """
        Validates if the current user possesses the required permission.
        """
        # Admin is treated as a superuser who has access to everything
        if current_user.role.name.upper() == "ADMIN":
            return current_user

        # Extract permission names
        user_permissions = {p.name.upper() for p in current_user.role.permissions}
        
        if self.required_permission.upper() not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource"
            )
            
        return current_user

# Convenience check functions
def require_permission(permission: str):
    return PermissionChecker(permission)

