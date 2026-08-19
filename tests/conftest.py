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
from app.crud.user import seed_admin, create_user
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
    """Initializes tables and seeds the admin once for the test session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        await seed_admin(session)
        
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
    """Creates standard test users and returns their access tokens."""
    # Register user profiles directly as standard users
    user = await create_user(
        db_session, 
        UserCreate(username="test_user", password="password123")
    )
    user_2 = await create_user(
        db_session, 
        UserCreate(username="test_user_2", password="password123")
    )
    user_3 = await create_user(
        db_session, 
        UserCreate(username="test_user_3", password="password123")
    )
    user_4 = await create_user(
        db_session, 
        UserCreate(username="test_user_4", password="password123")
    )
    
    return {
        "user": {"username": "test_user", "token": create_access_token("test_user")},
        "user_2": {"username": "test_user_2", "token": create_access_token("test_user_2")},
        "user_3": {"username": "test_user_3", "token": create_access_token("test_user_3")},
        "user_4": {"username": "test_user_4", "token": create_access_token("test_user_4")}
    }
