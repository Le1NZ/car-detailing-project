"""Pytest configuration and shared fixtures for bonus-service tests"""
import pytest
from uuid import UUID, uuid4
from typing import AsyncGenerator
from unittest.mock import Mock, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import application components
from app.main import app
from app.repositories.local_bonus_repo import LocalBonusRepository, Promocode
from app.services.bonus_service import BonusService
from app.services.rabbitmq_consumer import RabbitMQConsumer


# ==================== Auth Mock ====================

# Mock user_id for tests
TEST_USER_ID = UUID("c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d")


def mock_get_current_user_id() -> UUID:
    """Mock function that returns a test user ID without checking JWT"""
    return TEST_USER_ID


# ==================== Test Data Fixtures ====================

@pytest.fixture
def test_user_id() -> UUID:
    """Standard test user ID"""
    return TEST_USER_ID


@pytest.fixture
def test_order_id() -> UUID:
    """Standard test order ID"""
    return UUID("123e4567-e89b-12d3-a456-426614174000")


@pytest.fixture
def different_user_id() -> UUID:
    """Different user ID for multi-user tests"""
    return UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


@pytest.fixture
def valid_promocode() -> str:
    """Valid promocode string"""
    return "SUMMER24"


@pytest.fixture
def invalid_promocode() -> str:
    """Invalid promocode string"""
    return "INVALID"


# ==================== Repository Fixtures ====================

@pytest.fixture
def mock_repository() -> AsyncMock:
    """Mock repository with predefined behavior"""
    repo = AsyncMock(spec=LocalBonusRepository)

    # Default mock behaviors
    repo.get_user_balance = AsyncMock(return_value=1000.0)
    repo.add_bonuses = AsyncMock(return_value=1100.0)
    repo.spend_bonuses = AsyncMock(return_value=900.0)

    # Mock promocode data
    mock_promo = Mock(spec=Promocode)
    mock_promo.code = "SUMMER24"
    mock_promo.discount_amount = 500.0
    mock_promo.active = True
    repo.find_promocode = AsyncMock(return_value=mock_promo)

    return repo


@pytest.fixture
def fresh_repository() -> LocalBonusRepository:
    """Create a fresh repository instance for each test"""
    return LocalBonusRepository()


# ==================== Service Fixtures ====================

@pytest.fixture
def mock_bonus_service() -> AsyncMock:
    """Mock bonus service for testing endpoints"""
    service = AsyncMock(spec=BonusService)

    # Default mock behaviors
    service.apply_promocode = AsyncMock(return_value=("applied", 500.0))
    service.spend_bonuses = AsyncMock(return_value=(100, 900.0))
    service.accrue_bonuses = AsyncMock(return_value=100.0)

    return service


@pytest.fixture
def bonus_service(mock_repository: AsyncMock) -> BonusService:
    """Create a bonus service instance with mock repository"""
    return BonusService(repository=mock_repository)


# ==================== RabbitMQ Fixtures ====================

@pytest.fixture
def mock_rabbitmq_connection() -> AsyncMock:
    """Mock aio_pika connection"""
    connection = AsyncMock()
    channel = AsyncMock()
    queue = AsyncMock()

    # Setup mock chain
    connection.channel = AsyncMock(return_value=channel)
    channel.set_qos = AsyncMock()
    channel.declare_queue = AsyncMock(return_value=queue)
    channel.close = AsyncMock()
    connection.close = AsyncMock()
    queue.consume = AsyncMock()

    return connection


@pytest.fixture
def mock_incoming_message() -> Mock:
    """Mock RabbitMQ incoming message"""
    message = Mock()
    message.body = b'{"order_id": "123e4567-e89b-12d3-a456-426614174000", "user_id": "c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d", "amount": 10000.0}'
    message.process = MagicMock()
    return message


# ==================== FastAPI Test Client Fixtures ====================

@pytest.fixture
def test_client() -> TestClient:
    """Synchronous test client for FastAPI app"""
    # Disable lifespan to avoid RabbitMQ connection during tests
    from fastapi import FastAPI
    from app.endpoints import bonuses
    from app.models.bonus import HealthResponse
    from app.config import settings
    from app.auth import get_current_user_id

    test_app = FastAPI(title="Test Bonus Service")
    
    # Override JWT auth dependency with mock
    test_app.dependency_overrides[get_current_user_id] = mock_get_current_user_id
    
    test_app.include_router(bonuses.router)

    @test_app.get("/health", response_model=HealthResponse)
    async def health_check():
        return HealthResponse(status="healthy", service=settings.SERVICE_NAME)

    @test_app.get("/")
    async def root():
        return {"service": settings.SERVICE_NAME, "version": "1.0.0", "status": "running"}

    return TestClient(test_app)


@pytest.fixture
async def async_test_client() -> AsyncGenerator[AsyncClient, None]:
    """Async test client for FastAPI app"""
    from fastapi import FastAPI
    from app.endpoints import bonuses
    from app.models.bonus import HealthResponse
    from app.config import settings
    from app.auth import get_current_user_id

    test_app = FastAPI(title="Test Bonus Service")
    
    # Override JWT auth dependency with mock
    test_app.dependency_overrides[get_current_user_id] = mock_get_current_user_id
    
    test_app.include_router(bonuses.router)

    @test_app.get("/health", response_model=HealthResponse)
    async def health_check():
        return HealthResponse(status="healthy", service=settings.SERVICE_NAME)

    @test_app.get("/")
    async def root():
        return {"service": settings.SERVICE_NAME, "version": "1.0.0", "status": "running"}

    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


# ==================== Pytest Configuration ====================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests that don't require external dependencies")
    config.addinivalue_line("markers", "integration: Integration tests that test full API endpoints")
    config.addinivalue_line("markers", "asyncio: Async tests requiring asyncio event loop")


# ==================== Helper Functions ====================

def create_mock_promocode(code: str = "TEST", discount: float = 100.0, active: bool = True) -> Mock:
    """Helper to create mock promocode objects"""
    promo = Mock(spec=Promocode)
    promo.code = code
    promo.discount_amount = discount
    promo.active = active
    return promo
