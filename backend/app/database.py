import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger("database")

# 1. Load Environment Variables from .env file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

# 2. Database Connection URL
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

# Canonical absolute database path for single source of truth across all processes
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, "vigrah.db"))

if not DATABASE_URL or DATABASE_URL.startswith("sqlite"):
    DATABASE_URL = f"sqlite:///{DB_PATH}"

# Fix SQLAlchemy postgres dialect compatibility (postgres:// -> postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

IS_POSTGRES = DATABASE_URL.startswith("postgresql")

# 3. Create Engine with appropriate configuration
if not IS_POSTGRES:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    logger.info("Using SQLite database for local development fallback.")
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_recycle=300,
        pool_pre_ping=True
    )
    logger.info("Using PostgreSQL database with pgvector support.")
    # Attempt to enable pgvector extension automatically
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            logger.info("✓ PostgreSQL pgvector extension enabled.")
    except Exception as e:
        logger.warning(f"Could not initialize pgvector extension: {e}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency to retrieve database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
