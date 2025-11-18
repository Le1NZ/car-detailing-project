"""
Shared pytest fixtures for user-service tests.

This module provides fixtures for mocking database sessions, repositories,
and other dependencies used across unit and integration tests.
"""

import pytest
from unittest.mock import AsyncMock, Mock, MagicMock
from datetime import datetime
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.database import Base, get_db
from app.main import app
from app.schemas.user import User
from app.config import settings


# Test database URL (SQLite in-memory for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    mock_config = Mock()
    mock_config.POSTGRES_URL = TEST_DATABASE_URL
    mock_config.JWT_SECRET_KEY = "test-secret-key-for-testing-only"
    mock_config.JWT_ALGORITHM = "HS256"
    mock_config.JWT_ACCESS_TOKEN_EXPIRE_SECONDS = 3600
    mock_config.APP_NAME = "User Service Test"
    mock_config.APP_VERSION = "1.0.0-test"
    mock_config.DEBUG = True
    return mock_config


@pytest.fixture
async def async_db_engine():
    """
    Create an async in-memory SQLite database engine for testing.

    This engine is used for integration tests that require actual database operations.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def async_db_session(async_db_engine):
    """
    Create an async database session for testing.

    This session is connected to the in-memory test database.
    """
    async_session = async_sessionmaker(
        async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def mock_db_session():
    """
    Mock database session for unit tests.

    Returns an AsyncMock that simulates database operations without
    actually connecting to a database.
    """
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.add = Mock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.close = AsyncMock()
    return mock_session


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "strongpassword123",
        "full_name": "Test User",
        "phone_number": "+79991234567"
    }


@pytest.fixture
def sample_user():
    """
    Sample User database model instance for testing.

    Returns a User object with predefined test data.
    """
    user = User(
        id=uuid4(),
        email="test@example.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqZjKzpHy6",  # hashed "password123"
        full_name="Test User",
        phone_number="+79991234567",
        created_at=datetime(2024, 1, 1, 12, 0, 0)
    )
    return user


@pytest.fixture
def sample_user_2():
    """
    Another sample User for testing uniqueness constraints.
    """
    user = User(
        id=uuid4(),
        email="another@example.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqZjKzpHy6",
        full_name="Another User",
        phone_number="+79991234568",
        created_at=datetime(2024, 1, 2, 12, 0, 0)
    )
    return user


@pytest.fixture
def mock_user_repository():
    """
    Mock UserRepository for unit testing services.

    Returns a Mock object with AsyncMock methods for all repository operations.
    """
    mock_repo = Mock()
    mock_repo.create_user = AsyncMock()
    mock_repo.get_user_by_email = AsyncMock()
    mock_repo.check_email_exists = AsyncMock()
    mock_repo.check_phone_exists = AsyncMock()
    return mock_repo


@pytest.fixture
async def test_client(async_db_session):
    """
    FastAPI TestClient with overridden database dependency.

    This client is used for integration testing API endpoints with
    a real (in-memory) database.
    """
    async def override_get_db():
        yield async_db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def test_client_sync():
    """
    Synchronous TestClient for simple endpoint tests.

    Use this when async operations are not required.
    """
    return TestClient(app)
