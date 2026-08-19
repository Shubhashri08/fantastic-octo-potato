from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.auth.jwt import hash_password
from app.config import settings

async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    result = await db.execute(
        select(User)
        .filter(User.id == user_id)
    )
    return result.scalars().first()

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    result = await db.execute(
        select(User)
        .filter(User.username == username)
    )
    return result.scalars().first()

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    result = await db.execute(
        select(User)
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    hashed_pwd = hash_password(user_in.password)
    db_user = User(
        username=user_in.username,
        hashed_password=hashed_pwd,
        is_active=True
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_user(db: AsyncSession, db_user: User, user_update: UserUpdate) -> User:
    if user_update.is_active is not None:
        db_user.is_active = user_update.is_active
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def seed_admin(db: AsyncSession) -> None:
    """
    Seeds the default bootstrap administrator account if not present.
    """
    admin_username = settings.BOOTSTRAP_ADMIN_USER
    result = await db.execute(select(User).filter(User.username == admin_username))
    admin_user = result.scalars().first()
    
    if not admin_user:
        hashed_pwd = hash_password(settings.BOOTSTRAP_ADMIN_PASSWORD)
        admin_user = User(
            username=admin_username,
            hashed_password=hashed_pwd,
            is_active=True
        )
        db.add(admin_user)
        await db.commit()
