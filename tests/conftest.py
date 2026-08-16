import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from app.config import settings

# Override database URL to use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
settings.DATABASE_URL = TEST_DATABASE_URL

from app.main import app
from app.database import Base, get_db
from app.crud.user import seed_rbac, create_user
from app.schemas.user import UserCreate
from app.auth.jwt import create_access_token

# Setup test async database engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Creates a session-wide event loop for test run execution."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_db() -> AsyncGenerator[None, None]:
    """Initializes tables and seeds roles/permissions once for the test session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        await seed_rbac(session)
        
    yield
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yields a transaction-isolated session, rolled back after test completion."""
    async with test_engine.connect() as connection:
        transaction = await connection.begin()
        async with TestingSessionLocal(bind=connection) as session:
            yield session
            await session.close()
        await transaction.rollback()

@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provides an AsyncClient bound to the FastAPI app with db overrides."""
    async def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_test_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def test_users(db_session: AsyncSession) -> dict:
    """Creates a user for each role and returns their access tokens."""
    # Find role IDs
    from app.models.user import Role
    from sqlalchemy.future import select
    
    roles_result = await db_session.execute(select(Role))
    roles = {r.name: r.id for r in roles_result.scalars().all()}
    
    # Register user profiles
    admin = await create_user(
        db_session, 
        UserCreate(username="test_admin", password="password123", role_id=roles["ADMIN"])
    )
    operator = await create_user(
        db_session, 
        UserCreate(username="test_operator", password="password123", role_id=roles["OPERATOR"])
    )
    investigator = await create_user(
        db_session, 
        UserCreate(username="test_investigator", password="password123", role_id=roles["INVESTIGATOR"])
    )
    analyst = await create_user(
        db_session, 
        UserCreate(username="test_analyst", password="password123", role_id=roles["ANALYST"])
    )
    
    return {
        "admin": {"username": "test_admin", "token": create_access_token("test_admin")},
        "operator": {"username": "test_operator", "token": create_access_token("test_operator")},
        "investigator": {"username": "test_investigator", "token": create_access_token("test_investigator")},
        "analyst": {"username": "test_analyst", "token": create_access_token("test_analyst")}
    }
