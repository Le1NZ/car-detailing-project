"""
Shared pytest fixtures for fines-service tests
"""
import pytest
from datetime import date
from uuid import UUID, uuid4
from unittest.mock import Mock
from fastapi.testclient import TestClient
from app.models.fine import Fine
from app.repositories.local_fine_repo import LocalFineRepository
from app.services.fine_service import FineService
from app.main import app


# Mock user_id for tests
TEST_USER_ID = uuid4()


def mock_get_current_user_id() -> UUID:
    """Mock function that returns a test user ID without checking JWT"""
    return TEST_USER_ID


@pytest.fixture
def sample_fine_id() -> UUID:
    """Generate a sample fine ID"""
    return UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def sample_fine(sample_fine_id) -> Fine:
    """Create a sample unpaid fine"""
    return Fine(
        fine_id=sample_fine_id,
        license_plate="А123БВ799",
        amount=500.00,
        description="Превышение скорости на 20-40 км/ч",
        date=date(2024, 5, 15),
        paid=False
    )


@pytest.fixture
def sample_paid_fine() -> Fine:
    """Create a sample paid fine"""
    return Fine(
        fine_id=uuid4(),
        license_plate="М456КЛ177",
        amount=1000.00,
        description="Проезд на красный свет",
        date=date(2024, 6, 1),
        paid=True
    )


@pytest.fixture
def mock_repository():
    """Create a mock repository for testing"""
    return Mock(spec=LocalFineRepository)


@pytest.fixture
def real_repository():
    """Create a real repository instance for unit testing"""
    return LocalFineRepository()


@pytest.fixture
def fine_service(mock_repository):
    """Create a fine service with mocked repository"""
    return FineService(mock_repository)


@pytest.fixture
def real_fine_service(real_repository):
    """Create a fine service with real repository"""
    return FineService(real_repository)


@pytest.fixture
def test_client():
    """Create a test client for integration testing with mocked JWT auth"""
    from app.auth import get_current_user_id
    
    # Override JWT auth dependency with mock
    app.dependency_overrides[get_current_user_id] = mock_get_current_user_id
    
    client = TestClient(app)
    yield client
    
    # Clean up dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture
def empty_repository():
    """Create an empty repository without test data"""
    repo = Mock(spec=LocalFineRepository)
    repo._fines = {}
    repo._fines_by_id = {}
    return repo
