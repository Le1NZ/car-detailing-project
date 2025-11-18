"""Pytest configuration and shared fixtures for all tests."""
import pytest
from uuid import uuid4, UUID
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.local_ticket_repo import LocalTicketRepository, ticket_repository
from app.models.ticket import Ticket, Message


# Mock user_id for tests
TEST_USER_ID = uuid4()


def mock_get_current_user_id() -> UUID:
    """Mock function that returns a test user ID without checking JWT"""
    return TEST_USER_ID


@pytest.fixture
def sample_user_id():
    """Provide a sample user UUID for testing."""
    return TEST_USER_ID


@pytest.fixture
def sample_ticket_id():
    """Provide a sample ticket UUID for testing."""
    return uuid4()


@pytest.fixture
def sample_order_id():
    """Provide a sample order UUID for testing."""
    return uuid4()


@pytest.fixture
def sample_ticket(sample_user_id, sample_ticket_id, sample_order_id):
    """Provide a sample Ticket object for testing."""
    return Ticket(
        ticket_id=sample_ticket_id,
        user_id=sample_user_id,
        subject="Sample Ticket Subject",
        message="Sample ticket message content",
        order_id=sample_order_id,
        status="open",
        created_at=datetime.utcnow()
    )


@pytest.fixture
def sample_message(sample_ticket_id):
    """Provide a sample Message object for testing."""
    return Message(
        message_id=uuid4(),
        ticket_id=sample_ticket_id,
        author_id="support_agent_01",
        message="Sample message content",
        created_at=datetime.utcnow()
    )


@pytest.fixture
def clean_repository():
    """Provide a clean repository instance for testing."""
    repo = LocalTicketRepository()
    yield repo
    # Cleanup after test
    repo.tickets.clear()
    repo.messages.clear()


@pytest.fixture(autouse=True)
def reset_singleton_repository():
    """Automatically reset the singleton repository before each test."""
    ticket_repository.tickets.clear()
    ticket_repository.messages.clear()
    yield
    # Cleanup after test
    ticket_repository.tickets.clear()
    ticket_repository.messages.clear()


@pytest.fixture
def client():
    """Provide a TestClient for FastAPI application testing with mocked JWT auth."""
    from app.auth import get_current_user_id
    
    # Override JWT auth dependency with mock
    app.dependency_overrides[get_current_user_id] = mock_get_current_user_id
    
    test_client = TestClient(app)
    yield test_client
    
    # Clean up dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture
def sample_create_ticket_payload(sample_order_id):
    """Provide a sample CreateTicketRequest payload."""
    return {
        "subject": "Test Support Ticket",
        "message": "This is a test support ticket message",
        "order_id": str(sample_order_id)
    }


@pytest.fixture
def sample_add_message_payload():
    """Provide a sample AddMessageRequest payload."""
    return {
        "message": "This is a test message reply"
    }


# Markers for test organization
def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
