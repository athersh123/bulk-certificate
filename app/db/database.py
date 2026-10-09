import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# 1. Prepare SQLite-specific connection arguments
# In SQLite + FastAPI, multiple threads can interact with the DB across requests.
# 'check_same_thread': False allows FastAPI to share connections across threads safely.
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False,
        "timeout": 30,  # 30-second busy timeout to prevent 'database is locked' errors under concurrency
    }

# 2. Create the SQLAlchemy Engine
# The engine is the central connection source to our database.
engine = create_engine(
    settings.DATABASE_URL.replace("+aiosqlite", ""),  # Ensure standard sqlite:// connection string
    connect_args=connect_args,
    echo=settings.DEBUG,  # Log SQL queries to console during development
)

# 3. Create SessionLocal factory
# Each instance of SessionLocal represents a dedicated database transaction session.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# 4. Create Declarative Base
# All ORM models will inherit from this Base class.
Base = declarative_base()


# 5. Dependency injection generator for FastAPI endpoints
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session per request
    and guarantees proper cleanup (closing session) after request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
