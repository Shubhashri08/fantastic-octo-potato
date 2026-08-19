import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Load Environment Variables from .env file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

# 2. Database Connection URL
# Supports Neon DB (postgresql://...) or local SQLite (sqlite:///...)
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if not DATABASE_URL:
    DB_PATH = os.path.join(BASE_DIR, "vigrah.db")
    DATABASE_URL = f"sqlite:///{DB_PATH}"

# Fix SQLAlchemy postgres dialect compatibility (postgres:// -> postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 3. Create Engine with appropriate pooling
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL / Neon DB Serverless Configuration
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_recycle=300,
        pool_pre_ping=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency to retrieve database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
