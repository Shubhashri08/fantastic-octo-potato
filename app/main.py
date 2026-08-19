import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base, async_session_maker
from app.crud.user import seed_admin
from app.routers import auth, alerts, investigation, users

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Startup: Initialize tables and seed DB
    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Seeding bootstrap administrator...")
    async with async_session_maker() as session:
        await seed_admin(session)
    
    logger.info("Layer 5 Backend initialization complete.")
    yield
    # Shutdown logic (if any)
    logger.info("Shutting down Layer 5 Backend.")

app = FastAPI(
    title="VIGRAH AI - Layer 5: RESPOND / Decision Support Backend",
    description="Implements alert evaluation priority rules, evidence-based investigation assist, JWT RBAC control, and centralized audit trails.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Policy configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(alerts.router)
app.include_router(investigation.router)
app.include_router(users.router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "VIGRAH AI - Layer 5 (RESPOND / Decision Support)",
        "documentation": "/docs"
    }
