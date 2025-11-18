"""
Pytest configuration and shared fixtures for Cart Service tests
"""
import pytest
from uuid import UUID, uuid4
from typing import Generator
from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.models.cart import CartItem, AddItemRequest
from app.repositories.local_cart_repo import LocalCartRepo
from app.services.cart_service import CartService
from app.config import MOCK_USER_ID


# Test constants
TEST_USER_ID = MOCK_USER_ID
ALTERNATIVE_USER_ID = UUID("87654321-4321-8765-4321-876543218765")


# Mock function for JWT authorization in tests
def mock_get_current_user_id():
    """Mock function that returns a test user ID without checking JWT"""
    return TEST_USER_ID


# ============================================================================
# Model Fixtures
# ============================================================================

@pytest.fixture
def sample_cart_item() -> CartItem:
    """Create a sample cart item for testing"""
    return CartItem(
        item_id="svc_oil_change",
        type="service",
        name="Замена масла",
        quantity=1,
        price=2500.00
    )


@pytest.fixture
def sample_cart_item_product() -> CartItem:
    """Create a sample product cart item for testing"""
    return CartItem(
        item_id="prod_oil_filter",
        type="product",
        name="Масляный фильтр",
        quantity=2,
        price=1000.00
    )


@pytest.fixture
def sample_add_item_request() -> AddItemRequest:
    """Create a sample add item request for testing"""
    return AddItemRequest(
        item_id="svc_oil_change",
        type="service",
        quantity=1
    )


@pytest.fixture
def sample_add_item_request_product() -> AddItemRequest:
    """Create a sample add item request for product"""
    return AddItemRequest(
        item_id="prod_oil_filter",
        type="product",
        quantity=2
    )


# ============================================================================
# Repository Fixtures
# ============================================================================

@pytest.fixture
def clean_cart_repo() -> LocalCartRepo:
    """Create a fresh cart repository instance for each test"""
    return LocalCartRepo()


@pytest.fixture
def populated_cart_repo(clean_cart_repo: LocalCartRepo, sample_cart_item: CartItem) -> LocalCartRepo:
    """Create a cart repository with sample data"""
    clean_cart_repo.add_item(TEST_USER_ID, sample_cart_item)
    return clean_cart_repo


# ============================================================================
# Service Fixtures
# ============================================================================

@pytest.fixture
def cart_service(clean_cart_repo: LocalCartRepo) -> CartService:
    """Create a cart service with a clean repository"""
    return CartService(clean_cart_repo)


@pytest.fixture
def cart_service_with_data(populated_cart_repo: LocalCartRepo) -> CartService:
    """Create a cart service with pre-populated data"""
    return CartService(populated_cart_repo)


@pytest.fixture
def mock_cart_repo() -> Mock:
    """Create a mock cart repository for testing service layer"""
    mock_repo = Mock(spec=LocalCartRepo)
    mock_repo.get_cart.return_value = []
    mock_repo.add_item.return_value = []
    mock_repo.remove_item.return_value = True
    mock_repo.clear_cart.return_value = None
    return mock_repo


# ============================================================================
# API Test Client Fixtures
# ============================================================================

@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """
    Create a TestClient for integration testing
    Uses the actual FastAPI app with real dependencies

    Note: Clears the singleton repository before each test to ensure test isolation
    """
    from app.main import app
    from app.endpoints import cart
    from app.auth import get_current_user_id

    # Override JWT auth dependency with mock
    app.dependency_overrides[get_current_user_id] = mock_get_current_user_id

    # Clear the singleton repository state before each test
    cart.cart_repo._storage.clear()

    with TestClient(app) as client:
        yield client

    # Clear the singleton repository state after each test (cleanup)
    cart.cart_repo._storage.clear()
    
    # Clean up dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture
def test_client_with_mock_service(mock_cart_repo: Mock) -> Generator[TestClient, None, None]:
    """
    Create a TestClient with mocked service dependencies
    Useful for testing API endpoints in isolation
    """
    from app.main import app
    from app.endpoints import cart
    from app.auth import get_current_user_id

    # Override JWT auth dependency with mock
    app.dependency_overrides[get_current_user_id] = mock_get_current_user_id

    # Replace the singleton service with a mocked one
    original_service = cart.cart_service
    cart.cart_service = CartService(mock_cart_repo)

    with TestClient(app) as client:
        yield client

    # Restore original service after test
    cart.cart_service = original_service
    
    # Clean up dependency overrides
    app.dependency_overrides.clear()


# ============================================================================
# Utility Functions for Tests
# ============================================================================

def create_cart_item(
    item_id: str = "test_item",
    item_type: str = "service",
    name: str = "Test Item",
    quantity: int = 1,
    price: float = 100.0
) -> CartItem:
    """Helper function to create cart items with custom parameters"""
    return CartItem(
        item_id=item_id,
        type=item_type,
        name=name,
        quantity=quantity,
        price=price
    )


def create_add_request(
    item_id: str = "test_item",
    item_type: str = "service",
    quantity: int = 1
) -> AddItemRequest:
    """Helper function to create add item requests with custom parameters"""
    return AddItemRequest(
        item_id=item_id,
        type=item_type,
        quantity=quantity
    )
