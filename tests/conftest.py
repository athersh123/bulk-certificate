import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.db.database import Base, get_db
from app.core.config import settings
from app.services import job_processor

# In-memory SQLite engine with StaticPool so all connections share the same memory DB
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Sets up a temporary storage directory for tests and cleans it up afterward."""
    temp_dir = tempfile.mkdtemp(prefix="test_certs_")
    original_storage = settings.STORAGE_DIR
    settings.STORAGE_DIR = temp_dir

    yield temp_dir

    # Cleanup temporary storage directory
    settings.STORAGE_DIR = original_storage
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def db_session(monkeypatch):
    """Creates fresh database tables for each test and yields an isolated DB session."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # Patch background processor to use the isolated test session factory
    monkeypatch.setattr(job_processor, "SessionLocal", TestingSessionLocal)

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Provides a FastAPI TestClient with database dependency overridden for tests."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()
