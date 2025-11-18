"""Shared pytest fixtures for payment-service tests."""

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.local_payment_repo import PaymentRepository
from app.services.payment_service import PaymentService
from app.services.rabbitmq_publisher import RabbitMQPublisher


# Mock user_id for tests
TEST_USER_ID = uuid4()


def mock_get_current_user_id():
    """Mock function that returns a test user ID without checking JWT"""
    return TEST_USER_ID


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create an event loop for the test session.

    This fixture ensures all async tests share the same event loop.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_rabbitmq_publisher() -> Mock:
    """
    Create a mock RabbitMQ publisher.

    Returns:
        Mock publisher with mocked methods
    """
    publisher = Mock(spec=RabbitMQPublisher)
    publisher.connection = Mock()
    publisher.channel = Mock()
    publisher.publish_payment_success = AsyncMock()
    publisher.connect = AsyncMock()
    publisher.close = AsyncMock()
    return publisher


@pytest.fixture
def payment_repository() -> PaymentRepository:
    """
    Create a fresh payment repository for each test.

    Returns:
        PaymentRepository instance with empty storage
    """
    repo = PaymentRepository()
    # Clear any existing data
    repo.payments_storage = []
    return repo


@pytest.fixture
def payment_service(payment_repository: PaymentRepository) -> PaymentService:
    """
    Create a payment service with a clean repository.

    Args:
        payment_repository: Clean payment repository

    Returns:
        PaymentService instance
    """
    service = PaymentService()
    service.repository = payment_repository
    return service


@pytest.fixture
def sample_order_data() -> dict:
    """
    Sample order data for testing.

    Returns:
        Dictionary with order information
    """
    return {
        "user_id": "test-user-id-123",
        "amount": 2500.00
    }


@pytest.fixture
def sample_payment_data() -> dict:
    """
    Sample payment data for testing.

    Returns:
        Dictionary with payment information
    """
    return {
        "payment_id": "pay_test1234",
        "order_id": "ord_test123",
        "status": "pending",
        "amount": 2500.00,
        "currency": "RUB",
        "confirmation_url": "https://payment.gateway/confirm?token=pay_test1234",
        "payment_method": "card",
        "user_id": "test-user-id-123",
        "paid_at": None
    }


@pytest.fixture
def sample_payment_request() -> dict:
    """
    Sample payment request payload for API testing.

    Returns:
        Dictionary with request data
    """
    return {
        "order_id": "ord_test123",
        "payment_method": "card"
    }


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client with mocked JWT auth.

    Returns:
        TestClient for making HTTP requests to the API
    """
    from app.auth import get_current_user_id
    
    # Override JWT auth dependency with mock
    app.dependency_overrides[get_current_user_id] = mock_get_current_user_id
    
    client = TestClient(app)
    yield client
    
    # Clean up dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def reset_singletons():
    """
    Reset singleton instances before each test.

    This fixture automatically runs before each test to ensure
    clean state for repository and services.
    """
    # Import singletons
    from app.repositories import payment_repository
    from app.services import payment_service

    # Clear repository storage
    payment_repository.payments_storage = []

    # Reset service repository reference
    payment_service.repository = payment_repository

    yield

    # Cleanup after test
    payment_repository.payments_storage = []


@pytest.fixture
def mock_aio_pika_connection():
    """
    Create mock aio_pika connection and channel.

    Returns:
        Mock connection with channel
    """
    mock_connection = AsyncMock()
    mock_channel = AsyncMock()
    mock_queue = AsyncMock()

    mock_connection.channel = AsyncMock(return_value=mock_channel)
    mock_channel.declare_queue = AsyncMock(return_value=mock_queue)
    mock_channel.default_exchange = Mock()
    mock_channel.default_exchange.publish = AsyncMock()

    return mock_connection, mock_channel
