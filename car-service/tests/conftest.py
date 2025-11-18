"""Shared pytest fixtures for car-service tests."""

import pytest
from uuid import uuid4, UUID
from typing import Dict, Generator
from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.main import app
from app.models.car import AddCarRequest, AddDocumentRequest
from app.repositories.local_car_repo import LocalCarRepository, get_repository
from app.services.car_service import CarService
from app.endpoints.cars import get_car_service


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_owner_id() -> UUID:
    """Generate a sample owner UUID for testing."""
    return UUID("550e8400-e29b-41d4-a716-446655440000")


@pytest.fixture
def sample_car_id() -> UUID:
    """Generate a sample car UUID for testing."""
    return UUID("a8b9c1d2-e3f4-5678-9abc-def012345678")


@pytest.fixture
def sample_document_id() -> UUID:
    """Generate a sample document UUID for testing."""
    return UUID("11111111-2222-3333-4444-555555555555")


@pytest.fixture
def valid_car_data(sample_owner_id: UUID) -> Dict:
    """Valid car data dictionary for testing."""
    return {
        "owner_id": sample_owner_id,
        "license_plate": "A123BC799",
        "vin": "XTA210930V0123456",
        "make": "Lada",
        "model": "Vesta",
        "year": 2021
    }


@pytest.fixture
def valid_car_request(sample_owner_id: UUID) -> AddCarRequest:
    """Valid AddCarRequest for testing."""
    return AddCarRequest(
        owner_id=sample_owner_id,
        license_plate="A123BC799",
        vin="XTA210930V0123456",
        make="Lada",
        model="Vesta",
        year=2021
    )


@pytest.fixture
def another_valid_car_request(sample_owner_id: UUID) -> AddCarRequest:
    """Another valid AddCarRequest with different VIN and plate."""
    return AddCarRequest(
        owner_id=sample_owner_id,
        license_plate="X999YZ777",
        vin="1HGBH41JXMN109186",
        make="Toyota",
        model="Camry",
        year=2022
    )


@pytest.fixture
def valid_document_request() -> AddDocumentRequest:
    """Valid AddDocumentRequest for testing."""
    return AddDocumentRequest(
        document_type="СТС",
        file="scan_sts.pdf"
    )


@pytest.fixture
def valid_document_data() -> Dict:
    """Valid document data dictionary for testing."""
    return {
        "document_type": "Insurance",
        "file": "insurance.pdf"
    }


# ============================================================================
# Repository Fixtures
# ============================================================================

@pytest.fixture
def clean_repository() -> Generator[LocalCarRepository, None, None]:
    """
    Provide a clean LocalCarRepository instance for each test.

    This fixture ensures complete isolation between tests by:
    1. Creating a fresh repository instance
    2. Clearing all data after the test
    """
    repo = LocalCarRepository()
    yield repo
    repo.clear()


@pytest.fixture
def repository_with_car(
    clean_repository: LocalCarRepository,
    valid_car_data: Dict
) -> tuple[LocalCarRepository, Dict]:
    """
    Provide a repository with one car already added.

    Returns:
        Tuple of (repository, created_car_dict)
    """
    car = clean_repository.add_car(valid_car_data)
    return clean_repository, car


# ============================================================================
# Service Layer Fixtures
# ============================================================================

@pytest.fixture
def car_service(clean_repository: LocalCarRepository) -> CarService:
    """Provide a CarService instance with a clean repository."""
    return CarService(clean_repository)


@pytest.fixture
def car_service_with_car(
    repository_with_car: tuple[LocalCarRepository, Dict]
) -> tuple[CarService, Dict]:
    """
    Provide a CarService with one car already created.

    Returns:
        Tuple of (car_service, created_car_dict)
    """
    repository, car = repository_with_car
    service = CarService(repository)
    return service, car


@pytest.fixture
def mock_repository() -> Mock:
    """
    Provide a mocked LocalCarRepository for isolated service testing.

    This mock can be configured in tests to simulate various scenarios
    without touching the actual repository implementation.
    """
    return Mock(spec=LocalCarRepository)


# ============================================================================
# Integration Test Fixtures
# ============================================================================

@pytest.fixture
def test_client(clean_repository: LocalCarRepository) -> Generator[TestClient, None, None]:
    """
    Provide a TestClient for integration testing with clean repository.

    This fixture:
    1. Overrides the repository dependency with a clean instance
    2. Provides a TestClient for making HTTP requests
    3. Ensures test isolation
    """
    # Override the repository dependency
    def override_get_repository():
        return clean_repository

    # Override the service dependency
    def override_get_car_service():
        return CarService(clean_repository)

    app.dependency_overrides[get_repository] = override_get_repository
    app.dependency_overrides[get_car_service] = override_get_car_service

    with TestClient(app) as client:
        yield client

    # Clean up overrides
    app.dependency_overrides.clear()
    clean_repository.clear()


@pytest.fixture
def test_client_with_car(
    test_client: TestClient,
    valid_car_data: Dict
) -> tuple[TestClient, Dict]:
    """
    Provide a TestClient with one car already in the system.

    Returns:
        Tuple of (test_client, car_data_with_id)
    """
    # Create a car via the API
    response = test_client.post("/api/cars", json={
        **valid_car_data,
        "owner_id": str(valid_car_data["owner_id"])
    })
    assert response.status_code == 201
    car = response.json()
    return test_client, car


# ============================================================================
# Validation Test Data Fixtures
# ============================================================================

@pytest.fixture
def invalid_vin_cars(sample_owner_id: UUID) -> list[Dict]:
    """List of car data with invalid VINs for validation testing."""
    return [
        {
            "owner_id": str(sample_owner_id),
            "license_plate": "A123BC",
            "vin": "SHORT",  # Too short
            "make": "Test",
            "model": "Car",
            "year": 2020
        },
        {
            "owner_id": str(sample_owner_id),
            "license_plate": "A123BC",
            "vin": "TOOLONGVIN1234567890",  # Too long
            "make": "Test",
            "model": "Car",
            "year": 2020
        },
        {
            "owner_id": str(sample_owner_id),
            "license_plate": "A123BC",
            "vin": "VIN-WITH-DASHES!",  # Invalid characters
            "make": "Test",
            "model": "Car",
            "year": 2020
        }
    ]


@pytest.fixture
def invalid_year_cars(sample_owner_id: UUID) -> list[Dict]:
    """List of car data with invalid years for validation testing."""
    return [
        {
            "owner_id": str(sample_owner_id),
            "license_plate": "A123BC",
            "vin": "12345678901234567",
            "make": "Test",
            "model": "Car",
            "year": 1899  # Too old
        },
        {
            "owner_id": str(sample_owner_id),
            "license_plate": "A123BC",
            "vin": "12345678901234567",
            "make": "Test",
            "model": "Car",
            "year": 2026  # Too new
        }
    ]


# ============================================================================
# Edge Case Fixtures
# ============================================================================

@pytest.fixture
def edge_case_valid_cars(sample_owner_id: UUID) -> list[Dict]:
    """List of edge case but valid car data."""
    return [
        {
            # Minimum year
            "owner_id": str(sample_owner_id),
            "license_plate": "MINYR",
            "vin": "12345678901234567",
            "make": "Ford",
            "model": "Model T",
            "year": 1900
        },
        {
            # Maximum year
            "owner_id": str(sample_owner_id),
            "license_plate": "MAXYR",
            "vin": "98765432109876543",
            "make": "Tesla",
            "model": "Model Y",
            "year": 2025
        },
        {
            # Single character make/model
            "owner_id": str(sample_owner_id),
            "license_plate": "SHORT",
            "vin": "11111111111111111",
            "make": "A",
            "model": "B",
            "year": 2020
        }
    ]
