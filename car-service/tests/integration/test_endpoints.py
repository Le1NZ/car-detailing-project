"""
Integration tests for FastAPI endpoints in app.endpoints.cars.

Tests cover:
- POST /api/cars (create car) - success and error scenarios
- GET /api/cars/{car_id} (get car) - success and not found
- POST /api/cars/{car_id}/documents (add document) - success and errors
- HTTP status codes validation
- Response format validation
- End-to-end API flows
- Critical endpoint for order-service integration
"""

import pytest
from uuid import UUID, uuid4
from typing import Dict

from fastapi.testclient import TestClient


@pytest.mark.integration
class TestHealthEndpoints:
    """Test suite for health and root endpoints."""

    def test_health_check_endpoint(self, test_client: TestClient):
        """Test GET /health endpoint returns healthy status."""
        # Act
        response = test_client.get("/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "car-service"
        assert "version" in data

    def test_root_endpoint(self, test_client: TestClient):
        """Test GET / endpoint returns service information."""
        # Act
        response = test_client.get("/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "car-service"
        assert data["api_prefix"] == "/api"
        assert "version" in data
        assert "docs" in data


@pytest.mark.integration
class TestCreateCarEndpoint:
    """Test suite for POST /api/cars endpoint."""

    def test_create_car_success(
        self,
        test_client: TestClient,
        valid_car_data: Dict
    ):
        """Test successfully creating a car via POST /api/cars."""
        # Arrange
        request_data = {
            **valid_car_data,
            "owner_id": str(valid_car_data["owner_id"])
        }

        # Act
        response = test_client.post("/api/cars", json=request_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "car_id" in data
        assert UUID(data["car_id"])  # Validate UUID format
        assert data["license_plate"] == valid_car_data["license_plate"]
        assert data["vin"] == valid_car_data["vin"]
        assert data["make"] == valid_car_data["make"]
        assert data["model"] == valid_car_data["model"]
        assert data["year"] == valid_car_data["year"]

    def test_create_car_returns_valid_json_schema(
        self,
        test_client: TestClient,
        valid_car_data: Dict
    ):
        """Test that response matches expected CarResponse schema."""
        # Arrange
        request_data = {
            **valid_car_data,
            "owner_id": str(valid_car_data["owner_id"])
        }

        # Act
        response = test_client.post("/api/cars", json=request_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        required_fields = {"car_id", "license_plate", "vin", "make", "model", "year"}
        assert set(data.keys()) == required_fields

    def test_create_car_duplicate_vin_returns_409(
        self,
        test_client: TestClient,
        valid_car_data: Dict
    ):
        """Test that creating car with duplicate VIN returns 409 Conflict."""
        # Arrange
        request_data = {
            **valid_car_data,
            "owner_id": str(valid_car_data["owner_id"])
        }
        test_client.post("/api/cars", json=request_data)  # Create first car

        # Modify plate but keep same VIN
        duplicate_vin_data = {**request_data, "license_plate": "DIFFERENT123"}

        # Act
        response = test_client.post("/api/cars", json=duplicate_vin_data)

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
        assert "VIN" in data["detail"]
        assert "already exists" in data["detail"]

    def test_create_car_duplicate_license_plate_returns_409(
        self,
        test_client: TestClient,
        valid_car_data: Dict
    ):
        """Test that creating car with duplicate license plate returns 409 Conflict."""
        # Arrange
        request_data = {
            **valid_car_data,
            "owner_id": str(valid_car_data["owner_id"])
        }
        test_client.post("/api/cars", json=request_data)  # Create first car

        # Modify VIN but keep same plate
        duplicate_plate_data = {**request_data, "vin": "DIFFERENTVIN12345"}

        # Act
        response = test_client.post("/api/cars", json=duplicate_plate_data)

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
        assert "license plate" in data["detail"].lower()
        assert "already exists" in data["detail"]

    def test_create_car_invalid_vin_length_returns_422(
        self,
        test_client: TestClient,
        valid_car_data: Dict
    ):
        """Test that invalid VIN length returns 422 Unprocessable Entity."""
        # Arrange - VIN too short
        invalid_data = {
            **valid_car_data,
            "owner_id": str(valid_car_data["owner_id"]),
            "vin": "SHORT"
        }

        # Act
        response = test_client.post("/api/cars", json=invalid_data)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_create_car_invalid_vin_characters_returns_422(
        self,
        test_client: TestClient,
        valid_car_data: Dict
    ):
        """Test that VIN with invalid characters returns 422."""
        # Arrange - VIN with dashes
        invalid_data = {
            **valid_car_data,
            "owner_id": str(valid_car_data["owner_id"]),
            "vin": "VIN-WITH-DASHES!"
        }

        # Act
        response = test_client.post("/api/cars", json=invalid_data)

        # Assert
        assert response.status_code == 422

    def test_create_car_invalid_year_too_old_returns_422(
        self,
        test_client: TestClient,
        valid_car_data: Dict
    ):
        """Test that year < 1900 returns 422."""
        # Arrange
        invalid_data = {
            **valid_car_data,
            "owner_id": str(valid_car_data["owner_id"]),
            "year": 1899
        }

        # Act
        response = test_client.post("/api/cars", json=invalid_data)

        # Assert
        assert response.status_code == 422

    def test_create_car_invalid_year_too_new_returns_422(
        self,
        test_client: TestClient,
        valid_car_data: Dict
    ):
        """Test that year > 2025 returns 422."""
        # Arrange
        invalid_data = {
            **valid_car_data,
            "owner_id": str(valid_car_data["owner_id"]),
            "year": 2026
        }

        # Act
        response = test_client.post("/api/cars", json=invalid_data)

        # Assert
        assert response.status_code == 422

    def test_create_car_missing_required_field_returns_422(
        self,
        test_client: TestClient
    ):
        """Test that missing required fields returns 422."""
        # Arrange - missing 'make' field
        invalid_data = {
            "owner_id": str(uuid4()),
            "license_plate": "TEST",
            "vin": "12345678901234567",
            # "make": "Missing",  # Intentionally omitted
            "model": "Car",
            "year": 2020
        }

        # Act
        response = test_client.post("/api/cars", json=invalid_data)

        # Assert
        assert response.status_code == 422

    def test_create_car_invalid_owner_id_format_returns_422(
        self,
        test_client: TestClient,
        valid_car_data: Dict
    ):
        """Test that invalid UUID format for owner_id returns 422."""
        # Arrange
        invalid_data = {
            **valid_car_data,
            "owner_id": "not-a-valid-uuid"
        }

        # Act
        response = test_client.post("/api/cars", json=invalid_data)

        # Assert
        assert response.status_code == 422

    def test_create_car_vin_uppercase_conversion(
        self,
        test_client: TestClient,
        valid_car_data: Dict
    ):
        """Test that VIN is converted to uppercase."""
        # Arrange
        request_data = {
            **valid_car_data,
            "owner_id": str(valid_car_data["owner_id"]),
            "vin": "lowercase12345678"  # Exactly 17 chars, lowercase
        }

        # Act
        response = test_client.post("/api/cars", json=request_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["vin"] == "LOWERCASE12345678"

    def test_create_car_license_plate_normalization(
        self,
        test_client: TestClient,
        valid_car_data: Dict
    ):
        """Test that license plate is trimmed and uppercased."""
        # Arrange
        request_data = {
            **valid_car_data,
            "owner_id": str(valid_car_data["owner_id"]),
            "license_plate": "  lowercase123  "
        }

        # Act
        response = test_client.post("/api/cars", json=request_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["license_plate"] == "LOWERCASE123"

    def test_create_multiple_unique_cars(
        self,
        test_client: TestClient,
        sample_owner_id: UUID
    ):
        """Test creating multiple cars with unique identifiers."""
        # Arrange
        cars_data = [
            {
                "owner_id": str(sample_owner_id),
                "license_plate": "CAR001",
                "vin": "11111111111111111",
                "make": "Toyota",
                "model": "Camry",
                "year": 2020
            },
            {
                "owner_id": str(sample_owner_id),
                "license_plate": "CAR002",
                "vin": "22222222222222222",
                "make": "Honda",
                "model": "Accord",
                "year": 2021
            },
            {
                "owner_id": str(sample_owner_id),
                "license_plate": "CAR003",
                "vin": "33333333333333333",
                "make": "Ford",
                "model": "Focus",
                "year": 2019
            }
        ]

        # Act
        responses = [test_client.post("/api/cars", json=data) for data in cars_data]

        # Assert
        assert all(r.status_code == 201 for r in responses)
        car_ids = [r.json()["car_id"] for r in responses]
        assert len(set(car_ids)) == 3  # All IDs are unique


@pytest.mark.integration
class TestGetCarEndpoint:
    """Test suite for GET /api/cars/{car_id} endpoint - CRITICAL for order-service."""

    def test_get_car_success(
        self,
        test_client_with_car: tuple[TestClient, Dict]
    ):
        """Test successfully retrieving a car by ID."""
        # Arrange
        client, car = test_client_with_car
        car_id = car["car_id"]

        # Act
        response = client.get(f"/api/cars/{car_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["car_id"] == car_id
        assert data["license_plate"] == car["license_plate"]
        assert data["vin"] == car["vin"]
        assert data["make"] == car["make"]
        assert data["model"] == car["model"]
        assert data["year"] == car["year"]

    def test_get_car_not_found_returns_404(self, test_client: TestClient):
        """Test that getting non-existent car returns 404 Not Found."""
        # Arrange
        non_existent_id = uuid4()

        # Act
        response = test_client.get(f"/api/cars/{non_existent_id}")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert str(non_existent_id) in data["detail"]
        assert "not found" in data["detail"].lower()

    def test_get_car_invalid_uuid_format_returns_422(self, test_client: TestClient):
        """Test that invalid UUID format returns 422."""
        # Act
        response = test_client.get("/api/cars/not-a-valid-uuid")

        # Assert
        assert response.status_code == 422

    def test_get_car_returns_valid_json_schema(
        self,
        test_client_with_car: tuple[TestClient, Dict]
    ):
        """Test that response matches expected CarResponse schema."""
        # Arrange
        client, car = test_client_with_car

        # Act
        response = client.get(f"/api/cars/{car['car_id']}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        required_fields = {"car_id", "license_plate", "vin", "make", "model", "year"}
        assert set(data.keys()) == required_fields

    def test_get_car_critical_for_order_service_integration(
        self,
        test_client: TestClient,
        valid_car_data: Dict
    ):
        """
        CRITICAL TEST: Verify endpoint works for order-service integration.

        This endpoint is used by order-service to verify car existence
        when creating orders.
        """
        # Arrange - Create a car
        create_response = test_client.post("/api/cars", json={
            **valid_car_data,
            "owner_id": str(valid_car_data["owner_id"])
        })
        assert create_response.status_code == 201
        car_id = create_response.json()["car_id"]

        # Act - Simulate order-service checking if car exists
        response = test_client.get(f"/api/cars/{car_id}")

        # Assert - Must return 200 for order-service to proceed
        assert response.status_code == 200
        data = response.json()
        assert "car_id" in data
        assert data["car_id"] == car_id

    def test_get_car_after_creation_consistency(
        self,
        test_client: TestClient,
        valid_car_data: Dict
    ):
        """Test data consistency between create and get operations."""
        # Arrange - Create a car
        create_response = test_client.post("/api/cars", json={
            **valid_car_data,
            "owner_id": str(valid_car_data["owner_id"])
        })
        created_car = create_response.json()

        # Act - Retrieve the same car
        get_response = test_client.get(f"/api/cars/{created_car['car_id']}")

        # Assert - Data should match exactly
        retrieved_car = get_response.json()
        assert created_car == retrieved_car

    def test_get_specific_car_from_multiple(
        self,
        test_client: TestClient,
        sample_owner_id: UUID
    ):
        """Test retrieving specific car when multiple exist."""
        # Arrange - Create multiple cars
        car1_data = {
            "owner_id": str(sample_owner_id),
            "license_plate": "CAR1",
            "vin": "11111111111111111",
            "make": "Make1",
            "model": "Model1",
            "year": 2020
        }
        car2_data = {
            "owner_id": str(sample_owner_id),
            "license_plate": "CAR2",
            "vin": "22222222222222222",
            "make": "Make2",
            "model": "Model2",
            "year": 2021
        }

        response1 = test_client.post("/api/cars", json=car1_data)
        response2 = test_client.post("/api/cars", json=car2_data)
        car2_id = response2.json()["car_id"]

        # Act - Get car2
        response = test_client.get(f"/api/cars/{car2_id}")

        # Assert - Should return car2, not car1
        data = response.json()
        assert data["car_id"] == car2_id
        assert data["vin"] == "22222222222222222"
        assert data["make"] == "Make2"


@pytest.mark.integration
class TestAddDocumentEndpoint:
    """Test suite for POST /api/cars/{car_id}/documents endpoint."""

    def test_add_document_success(
        self,
        test_client_with_car: tuple[TestClient, Dict],
        valid_document_request: Dict
    ):
        """Test successfully adding a document to a car."""
        # Arrange
        client, car = test_client_with_car
        car_id = car["car_id"]
        doc_data = {
            "document_type": valid_document_request.document_type,
            "file": valid_document_request.file
        }

        # Act
        response = client.post(f"/api/cars/{car_id}/documents", json=doc_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "document_id" in data
        assert UUID(data["document_id"])  # Validate UUID format
        assert data["car_id"] == car_id
        assert data["document_type"] == doc_data["document_type"]
        assert data["status"] == "pending"

    def test_add_document_returns_valid_json_schema(
        self,
        test_client_with_car: tuple[TestClient, Dict]
    ):
        """Test that response matches expected DocumentResponse schema."""
        # Arrange
        client, car = test_client_with_car
        doc_data = {"document_type": "Test", "file": "test.pdf"}

        # Act
        response = client.post(f"/api/cars/{car['car_id']}/documents", json=doc_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        required_fields = {"car_id", "document_id", "document_type", "status"}
        assert set(data.keys()) == required_fields

    def test_add_document_without_file(
        self,
        test_client_with_car: tuple[TestClient, Dict]
    ):
        """Test adding document without file field (optional)."""
        # Arrange
        client, car = test_client_with_car
        doc_data = {"document_type": "Registration"}

        # Act
        response = client.post(f"/api/cars/{car['car_id']}/documents", json=doc_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["document_type"] == "Registration"
        assert data["status"] == "pending"

    def test_add_document_car_not_found_returns_404(
        self,
        test_client: TestClient
    ):
        """Test that adding document to non-existent car returns 404."""
        # Arrange
        non_existent_car_id = uuid4()
        doc_data = {"document_type": "Test", "file": "test.pdf"}

        # Act
        response = test_client.post(
            f"/api/cars/{non_existent_car_id}/documents",
            json=doc_data
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_add_document_invalid_car_id_format_returns_422(
        self,
        test_client: TestClient
    ):
        """Test that invalid UUID format returns 422."""
        # Arrange
        doc_data = {"document_type": "Test"}

        # Act
        response = test_client.post(
            "/api/cars/not-a-valid-uuid/documents",
            json=doc_data
        )

        # Assert
        assert response.status_code == 422

    def test_add_document_missing_document_type_returns_422(
        self,
        test_client_with_car: tuple[TestClient, Dict]
    ):
        """Test that missing document_type returns 422."""
        # Arrange
        client, car = test_client_with_car
        doc_data = {"file": "test.pdf"}  # Missing document_type

        # Act
        response = client.post(f"/api/cars/{car['car_id']}/documents", json=doc_data)

        # Assert
        assert response.status_code == 422

    def test_add_document_empty_document_type_returns_422(
        self,
        test_client_with_car: tuple[TestClient, Dict]
    ):
        """Test that empty document_type returns 422."""
        # Arrange
        client, car = test_client_with_car
        doc_data = {"document_type": ""}  # Empty string

        # Act
        response = client.post(f"/api/cars/{car['car_id']}/documents", json=doc_data)

        # Assert
        assert response.status_code == 422

    def test_add_multiple_documents_to_same_car(
        self,
        test_client_with_car: tuple[TestClient, Dict]
    ):
        """Test adding multiple documents to a single car."""
        # Arrange
        client, car = test_client_with_car
        car_id = car["car_id"]
        documents = [
            {"document_type": "Registration", "file": "reg.pdf"},
            {"document_type": "Insurance", "file": "ins.pdf"},
            {"document_type": "Inspection", "file": "insp.pdf"}
        ]

        # Act
        responses = [
            client.post(f"/api/cars/{car_id}/documents", json=doc)
            for doc in documents
        ]

        # Assert
        assert all(r.status_code == 200 for r in responses)
        doc_ids = [r.json()["document_id"] for r in responses]
        assert len(set(doc_ids)) == 3  # All document IDs are unique
        assert all(r.json()["car_id"] == car_id for r in responses)

    def test_add_document_status_always_pending(
        self,
        test_client_with_car: tuple[TestClient, Dict]
    ):
        """Test that all new documents have status 'pending'."""
        # Arrange
        client, car = test_client_with_car
        doc_data = {"document_type": "Test"}

        # Act
        response = client.post(f"/api/cars/{car['car_id']}/documents", json=doc_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"


@pytest.mark.integration
class TestEndToEndFlows:
    """Test suite for complete end-to-end API flows."""

    def test_complete_car_lifecycle(
        self,
        test_client: TestClient,
        valid_car_data: Dict
    ):
        """Test complete car lifecycle: create -> get -> add documents."""
        # Step 1: Create car
        create_response = test_client.post("/api/cars", json={
            **valid_car_data,
            "owner_id": str(valid_car_data["owner_id"])
        })
        assert create_response.status_code == 201
        car = create_response.json()
        car_id = car["car_id"]

        # Step 2: Retrieve car
        get_response = test_client.get(f"/api/cars/{car_id}")
        assert get_response.status_code == 200
        retrieved_car = get_response.json()
        assert retrieved_car["car_id"] == car_id

        # Step 3: Add document
        doc_data = {"document_type": "Registration", "file": "reg.pdf"}
        doc_response = test_client.post(
            f"/api/cars/{car_id}/documents",
            json=doc_data
        )
        assert doc_response.status_code == 200
        document = doc_response.json()
        assert document["car_id"] == car_id

    def test_order_service_integration_flow(
        self,
        test_client: TestClient,
        valid_car_data: Dict
    ):
        """
        Test the exact flow that order-service uses.

        Flow:
        1. User registers car in car-service
        2. order-service checks if car exists before creating order
        """
        # Step 1: User creates car in car-service
        create_response = test_client.post("/api/cars", json={
            **valid_car_data,
            "owner_id": str(valid_car_data["owner_id"])
        })
        assert create_response.status_code == 201
        car_id = create_response.json()["car_id"]

        # Step 2: order-service verifies car exists (CRITICAL)
        verify_response = test_client.get(f"/api/cars/{car_id}")
        assert verify_response.status_code == 200

        # Step 3: order-service can proceed with order creation
        car_data = verify_response.json()
        assert "car_id" in car_data
        assert "vin" in car_data

    def test_duplicate_prevention_flow(
        self,
        test_client: TestClient,
        valid_car_data: Dict
    ):
        """Test that duplicate prevention works across requests."""
        # Arrange
        request_data = {
            **valid_car_data,
            "owner_id": str(valid_car_data["owner_id"])
        }

        # Step 1: Create car successfully
        response1 = test_client.post("/api/cars", json=request_data)
        assert response1.status_code == 201

        # Step 2: Attempt to create same car again
        response2 = test_client.post("/api/cars", json=request_data)
        assert response2.status_code == 409

        # Step 3: Modify VIN, attempt again
        modified_data = {**request_data, "vin": "DIFFERENT12345678"}
        response3 = test_client.post("/api/cars", json=modified_data)
        assert response3.status_code == 409  # Still fails due to duplicate plate

    def test_multiple_cars_and_documents_flow(
        self,
        test_client: TestClient,
        sample_owner_id: UUID
    ):
        """Test managing multiple cars with their documents."""
        # Create car 1
        car1_data = {
            "owner_id": str(sample_owner_id),
            "license_plate": "CAR1",
            "vin": "11111111111111111",
            "make": "Toyota",
            "model": "Camry",
            "year": 2020
        }
        car1_response = test_client.post("/api/cars", json=car1_data)
        car1_id = car1_response.json()["car_id"]

        # Create car 2
        car2_data = {
            "owner_id": str(sample_owner_id),
            "license_plate": "CAR2",
            "vin": "22222222222222222",
            "make": "Honda",
            "model": "Accord",
            "year": 2021
        }
        car2_response = test_client.post("/api/cars", json=car2_data)
        car2_id = car2_response.json()["car_id"]

        # Add documents to car1
        doc1_response = test_client.post(
            f"/api/cars/{car1_id}/documents",
            json={"document_type": "Car1Doc"}
        )
        assert doc1_response.status_code == 200

        # Add documents to car2
        doc2_response = test_client.post(
            f"/api/cars/{car2_id}/documents",
            json={"document_type": "Car2Doc"}
        )
        assert doc2_response.status_code == 200

        # Verify both cars exist
        assert test_client.get(f"/api/cars/{car1_id}").status_code == 200
        assert test_client.get(f"/api/cars/{car2_id}").status_code == 200


@pytest.mark.integration
class TestAPIErrorHandling:
    """Test suite for API error handling and edge cases."""

    def test_invalid_json_body_returns_422(self, test_client: TestClient):
        """Test that invalid JSON returns 422."""
        # Act
        response = test_client.post(
            "/api/cars",
            data="invalid json{{{",
            headers={"Content-Type": "application/json"}
        )

        # Assert
        assert response.status_code == 422

    def test_content_type_validation(
        self,
        test_client: TestClient,
        valid_car_data: Dict
    ):
        """Test that requests require proper Content-Type."""
        # Act - Send as form data instead of JSON
        response = test_client.post(
            "/api/cars",
            data=valid_car_data  # Not JSON
        )

        # Assert - Should fail validation
        assert response.status_code == 422

    def test_get_endpoint_with_malformed_uuid(self, test_client: TestClient):
        """Test various malformed UUID formats."""
        malformed_uuids = [
            "12345",
            "not-a-uuid",
            "550e8400-e29b-41d4-a716",  # Too short
            "550e8400-e29b-41d4-a716-446655440000-extra",  # Too long
        ]

        for bad_uuid in malformed_uuids:
            response = test_client.get(f"/api/cars/{bad_uuid}")
            assert response.status_code == 422, f"Failed for UUID: {bad_uuid}"

    def test_endpoint_paths_case_sensitive(self, test_client: TestClient):
        """Test that endpoint paths are case-sensitive."""
        # Arrange
        non_existent_id = uuid4()

        # Act - Try uppercase
        response = test_client.get(f"/API/CARS/{non_existent_id}")

        # Assert - Should not match route
        assert response.status_code == 404  # Route not found, not car not found
