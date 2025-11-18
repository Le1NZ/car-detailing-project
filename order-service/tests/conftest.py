"""Shared test fixtures and configuration for pytest"""
import pytest
from datetime import datetime
from uuid import UUID, uuid4
from unittest.mock import Mock, AsyncMock

from app.models.order import Order, Review
from app.repositories.local_order_repo import LocalOrderRepository


# Test data constants
TEST_CAR_ID = UUID("123e4567-e89b-12d3-a456-426614174000")
TEST_ORDER_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
TEST_REVIEW_ID = UUID("660e8400-e29b-41d4-a716-446655440001")
TEST_DATETIME = datetime(2025, 11, 20, 10, 0, 0)


@pytest.fixture
def test_car_id() -> UUID:
    """Fixture providing a test car UUID"""
    return TEST_CAR_ID


@pytest.fixture
def test_order_id() -> UUID:
    """Fixture providing a test order UUID"""
    return TEST_ORDER_ID


@pytest.fixture
def test_review_id() -> UUID:
    """Fixture providing a test review UUID"""
    return TEST_REVIEW_ID


@pytest.fixture
def test_datetime() -> datetime:
    """Fixture providing a test datetime"""
    return TEST_DATETIME


@pytest.fixture
def sample_order_data() -> dict:
    """Fixture providing sample order data"""
    return {
        "car_id": TEST_CAR_ID,
        "desired_time": TEST_DATETIME,
        "description": "Engine oil change and filter replacement"
    }


@pytest.fixture
def sample_review_data() -> dict:
    """Fixture providing sample review data"""
    return {
        "rating": 5,
        "comment": "Excellent service, very professional staff"
    }


@pytest.fixture
def sample_order() -> Order:
    """Fixture providing a sample Order instance"""
    return Order(
        order_id=TEST_ORDER_ID,
        car_id=TEST_CAR_ID,
        status="created",
        appointment_time=TEST_DATETIME,
        description="Engine oil change and filter replacement",
        created_at=datetime(2025, 11, 15, 14, 30, 0)
    )


@pytest.fixture
def sample_review() -> Review:
    """Fixture providing a sample Review instance"""
    return Review(
        review_id=TEST_REVIEW_ID,
        order_id=TEST_ORDER_ID,
        status="published",
        rating=5,
        comment="Excellent service, very professional staff",
        created_at=datetime(2025, 11, 20, 15, 0, 0)
    )


@pytest.fixture
def mock_repository():
    """Fixture providing a mock repository"""
    repo = Mock(spec=LocalOrderRepository)

    # Configure async methods
    repo.create_order = AsyncMock()
    repo.get_order_by_id = AsyncMock()
    repo.update_order_status = AsyncMock()
    repo.create_review = AsyncMock()
    repo.has_review = AsyncMock()
    repo.get_review_by_order_id = AsyncMock()

    return repo


@pytest.fixture
def mock_car_client():
    """Fixture providing a mock car service client"""
    client = Mock()
    client.verify_car_exists = AsyncMock()
    client.get_car_details = AsyncMock()
    return client


@pytest.fixture
def fresh_repository():
    """Fixture providing a fresh repository instance for each test"""
    return LocalOrderRepository()
