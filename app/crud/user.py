from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, Role, Permission
from app.schemas.user import UserCreate, UserUpdate
from app.auth.jwt import hash_password
from app.config import settings

async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    result = await db.execute(
        select(User)
        .filter(User.id == user_id)
        .options(selectinload(User.role))
    )
    return result.scalars().first()

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    result = await db.execute(
        select(User)
        .filter(User.username == username)
        .options(selectinload(User.role).selectinload(Role.permissions))
    )
    return result.scalars().first()

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    result = await db.execute(
        select(User)
        .options(selectinload(User.role))
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    hashed_pwd = hash_password(user_in.password)
    db_user = User(
        username=user_in.username,
        hashed_password=hashed_pwd,
        role_id=user_in.role_id,
        is_active=True
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_user(db: AsyncSession, db_user: User, user_update: UserUpdate) -> User:
    if user_update.role_id is not None:
        db_user.role_id = user_update.role_id
    if user_update.is_active is not None:
        db_user.is_active = user_update.is_active
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def seed_rbac(db: AsyncSession) -> None:
    """
    Seeds permissions, roles, and default bootstrap admin user if not present.
    """
    # 1. Define Permissions
    permission_data = {
        # Operator
        "VIEW_ALERTS": "Permission to view security alerts",
        "ACKNOWLEDGE_ALERTS": "Permission to acknowledge alerts",
        "VIEW_INCIDENTS": "Permission to view incident metadata",
        # Investigator
        "SEARCH_ENTITIES": "Permission to search/track entities",
        "ASK_QUESTIONS": "Permission to query investigation assistant",
        "VIEW_RECONSTRUCTION": "Permission to view reconstructed timelines",
        # Analyst
        "VIEW_GIS": "Permission to query GIS context maps",
        "VIEW_HISTORICAL": "Permission to view aggregation data",
        "VIEW_RISK": "Permission to view regional risk metrics",
        # Admin
        "MANAGE_USERS": "Permission to manage users",
        "MANAGE_ROLES": "Permission to manage role mappings",
        "VIEW_SYSTEM_LOGS": "Permission to view audit trails"
    }

    db_permissions = {}
    for name, desc in permission_data.items():
        result = await db.execute(select(Permission).filter(Permission.name == name))
        perm = result.scalars().first()
        if not perm:
            perm = Permission(name=name, description=desc)
            db.add(perm)
        db_permissions[name] = perm
    await db.commit()

    # Refresh permissions to get primary keys
    for name in db_permissions.keys():
        result = await db.execute(select(Permission).filter(Permission.name == name))
        db_permissions[name] = result.scalars().first()

    # 2. Define Roles and assign permissions
    roles_data = {
        "ADMIN": list(permission_data.keys()),
        "OPERATOR": ["VIEW_ALERTS", "ACKNOWLEDGE_ALERTS", "VIEW_INCIDENTS"],
        "INVESTIGATOR": ["VIEW_ALERTS", "SEARCH_ENTITIES", "ASK_QUESTIONS", "VIEW_RECONSTRUCTION"],
        "ANALYST": ["VIEW_GIS", "VIEW_HISTORICAL", "VIEW_RISK"]
    }

    db_roles = {}
    for role_name, perm_names in roles_data.items():
        result = await db.execute(
            select(Role)
            .filter(Role.name == role_name)
            .options(selectinload(Role.permissions))
        )
        role = result.scalars().first()
        if not role:
            role = Role(name=role_name, description=f"Default {role_name.capitalize()} role")
            db.add(role)
        
        # Link permissions
        role.permissions = [db_permissions[p] for p in perm_names]
        db_roles[role_name] = role
    await db.commit()

    # Refresh roles to get IDs
    for name in db_roles.keys():
        result = await db.execute(select(Role).filter(Role.name == name))
        db_roles[name] = result.scalars().first()

    # 3. Bootstrap Admin User
    admin_username = settings.BOOTSTRAP_ADMIN_USER
    result = await db.execute(select(User).filter(User.username == admin_username))
    admin_user = result.scalars().first()
    
    if not admin_user:
        hashed_pwd = hash_password(settings.BOOTSTRAP_ADMIN_PASSWORD)
        admin_user = User(
            username=admin_username,
            hashed_password=hashed_pwd,
            role_id=db_roles["ADMIN"].id,
            is_active=True
        )
        db.add(admin_user)
        await db.commit()
