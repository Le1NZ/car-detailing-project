"""
Integration tests for API endpoints
Tests the complete HTTP request/response flow
"""
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check_returns_200(self, test_client):
        """Test that health check returns 200 OK"""
        response = test_client.get("/health")

        assert response.status_code == 200

    def test_health_check_response_structure(self, test_client):
        """Test health check response contains correct fields"""
        response = test_client.get("/health")
        data = response.json()

        assert "status" in data
        assert "service" in data
        assert "port" in data

    def test_health_check_status_is_healthy(self, test_client):
        """Test that health check returns healthy status"""
        response = test_client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "fines-service"
        assert data["port"] == 8007


class TestRootEndpoint:
    """Test root endpoint"""

    def test_root_returns_200(self, test_client):
        """Test that root endpoint returns 200 OK"""
        response = test_client.get("/")

        assert response.status_code == 200

    def test_root_response_structure(self, test_client):
        """Test root endpoint response contains service info"""
        response = test_client.get("/")
        data = response.json()

        assert "service" in data
        assert "version" in data
        assert "endpoints" in data

    def test_root_endpoints_documentation(self, test_client):
        """Test that root endpoint documents available endpoints"""
        response = test_client.get("/")
        data = response.json()

        endpoints = data["endpoints"]
        assert "health" in endpoints
        assert "check_fines" in endpoints
        assert "pay_fine" in endpoints


class TestCheckFinesEndpoint:
    """Test GET /api/fines/check endpoint"""

    def test_check_fines_with_existing_plate(self, test_client):
        """Test checking fines for existing license plate"""
        response = test_client.get("/api/fines/check?license_plate=А123БВ799")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_check_fines_response_structure(self, test_client):
        """Test that response contains correct fine fields"""
        response = test_client.get("/api/fines/check?license_plate=А123БВ799")
        data = response.json()

        fine = data[0]
        assert "fine_id" in fine
        assert "amount" in fine
        assert "description" in fine
        assert "date" in fine
        # Should NOT include 'paid' field
        assert "paid" not in fine

    def test_check_fines_returns_correct_amount(self, test_client):
        """Test that correct fine amount is returned"""
        response = test_client.get("/api/fines/check?license_plate=А123БВ799")
        data = response.json()

        fine = data[0]
        assert fine["amount"] == 500.00

    def test_check_fines_returns_correct_description(self, test_client):
        """Test that correct fine description is returned"""
        response = test_client.get("/api/fines/check?license_plate=А123БВ799")
        data = response.json()

        fine = data[0]
        assert "Превышение скорости" in fine["description"]

    def test_check_fines_with_nonexistent_plate(self, test_client):
        """Test checking fines for non-existent license plate"""
        response = test_client.get("/api/fines/check?license_plate=NONEXISTENT")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_check_fines_without_license_plate_parameter(self, test_client):
        """Test checking fines without license_plate parameter"""
        response = test_client.get("/api/fines/check")

        # Should return 422 Unprocessable Entity (missing required parameter)
        assert response.status_code == 422

    def test_check_fines_with_empty_license_plate(self, test_client):
        """Test checking fines with empty license plate"""
        response = test_client.get("/api/fines/check?license_plate=")

        # Empty string should still work, just return empty list
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_check_fines_for_second_test_plate(self, test_client):
        """Test checking fines for second test license plate"""
        response = test_client.get("/api/fines/check?license_plate=М456КЛ177")

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        fine = data[0]
        assert fine["amount"] == 1000.00

    def test_check_fines_returns_only_unpaid(self, test_client):
        """Test that only unpaid fines are returned"""
        # First, get a fine and pay it
        response1 = test_client.get("/api/fines/check?license_plate=А123БВ799")
        fines_before = response1.json()

        if len(fines_before) > 0:
            fine_id = fines_before[0]["fine_id"]

            # Pay the fine
            pay_response = test_client.post(
                f"/api/fines/{fine_id}/pay",
                json={"payment_method_id": "card_123"}
            )
            assert pay_response.status_code == 200

            # Check fines again - paid fine should not appear
            response2 = test_client.get("/api/fines/check?license_plate=А123БВ799")
            fines_after = response2.json()

            # The paid fine should not be in the list
            fine_ids_after = [f["fine_id"] for f in fines_after]
            assert fine_id not in fine_ids_after


class TestPayFineEndpoint:
    """Test POST /api/fines/{fine_id}/pay endpoint"""

    def test_pay_fine_success(self, test_client):
        """Test successful fine payment"""
        # First get a fine to pay
        response = test_client.get("/api/fines/check?license_plate=М456КЛ177")
        fines = response.json()

        if len(fines) > 0:
            fine_id = fines[0]["fine_id"]

            # Pay the fine
            pay_response = test_client.post(
                f"/api/fines/{fine_id}/pay",
                json={"payment_method_id": "card_123"}
            )

            assert pay_response.status_code == 200

    def test_pay_fine_response_structure(self, test_client):
        """Test payment response contains correct fields"""
        # Get a fine to pay (using fresh test client to ensure unpaid fine exists)
        from app.main import app
        from fastapi.testclient import TestClient
        fresh_client = TestClient(app)

        response = fresh_client.get("/api/fines/check?license_plate=А123БВ799")
        fines = response.json()

        if len(fines) > 0:
            fine_id = fines[0]["fine_id"]

            pay_response = fresh_client.post(
                f"/api/fines/{fine_id}/pay",
                json={"payment_method_id": "card_123"}
            )

            data = pay_response.json()
            assert "payment_id" in data
            assert "fine_id" in data
            assert "status" in data

    def test_pay_fine_returns_paid_status(self, test_client):
        """Test that payment response has status 'paid'"""
        from app.main import app
        from fastapi.testclient import TestClient
        fresh_client = TestClient(app)

        response = fresh_client.get("/api/fines/check?license_plate=М456КЛ177")
        fines = response.json()

        if len(fines) > 0:
            fine_id = fines[0]["fine_id"]

            pay_response = fresh_client.post(
                f"/api/fines/{fine_id}/pay",
                json={"payment_method_id": "card_123"}
            )

            data = pay_response.json()
            assert data["status"] == "paid"
            assert data["fine_id"] == fine_id

    def test_pay_nonexistent_fine_returns_404(self, test_client):
        """Test paying non-existent fine returns 404"""
        nonexistent_id = str(uuid4())

        response = test_client.post(
            f"/api/fines/{nonexistent_id}/pay",
            json={"payment_method_id": "card_123"}
        )

        assert response.status_code == 404

    def test_pay_fine_twice_returns_409(self, test_client):
        """Test paying the same fine twice returns 409 Conflict"""
        from app.main import app
        from fastapi.testclient import TestClient
        fresh_client = TestClient(app)

        # Get a fine
        response = fresh_client.get("/api/fines/check?license_plate=А123БВ799")
        fines = response.json()

        if len(fines) > 0:
            fine_id = fines[0]["fine_id"]

            # Pay the fine first time
            pay_response1 = fresh_client.post(
                f"/api/fines/{fine_id}/pay",
                json={"payment_method_id": "card_123"}
            )
            assert pay_response1.status_code == 200

            # Try to pay again
            pay_response2 = fresh_client.post(
                f"/api/fines/{fine_id}/pay",
                json={"payment_method_id": "card_123"}
            )
            assert pay_response2.status_code == 409

    def test_pay_fine_without_payment_method_returns_422(self, test_client):
        """Test paying fine without payment_method_id returns 422"""
        from app.main import app
        from fastapi.testclient import TestClient
        fresh_client = TestClient(app)

        response = fresh_client.get("/api/fines/check?license_plate=А123БВ799")
        fines = response.json()

        if len(fines) > 0:
            fine_id = fines[0]["fine_id"]

            # Try to pay without payment_method_id
            pay_response = fresh_client.post(
                f"/api/fines/{fine_id}/pay",
                json={}
            )

            assert pay_response.status_code == 422

    def test_pay_fine_with_invalid_uuid_returns_422(self, test_client):
        """Test paying fine with invalid UUID format returns 422"""
        response = test_client.post(
            "/api/fines/not-a-uuid/pay",
            json={"payment_method_id": "card_123"}
        )

        assert response.status_code == 422

    def test_pay_fine_generates_payment_id(self, test_client):
        """Test that payment response includes unique payment_id"""
        from app.main import app
        from fastapi.testclient import TestClient
        fresh_client = TestClient(app)

        response = fresh_client.get("/api/fines/check?license_plate=М456КЛ177")
        fines = response.json()

        if len(fines) > 0:
            fine_id = fines[0]["fine_id"]

            pay_response = fresh_client.post(
                f"/api/fines/{fine_id}/pay",
                json={"payment_method_id": "card_123"}
            )

            data = pay_response.json()
            assert "payment_id" in data
            # Verify it's a valid UUID format
            payment_id = data["payment_id"]
            assert len(payment_id) == 36  # UUID string length with dashes

    def test_pay_fine_error_response_includes_detail(self, test_client):
        """Test that error responses include detail message"""
        nonexistent_id = str(uuid4())

        response = test_client.post(
            f"/api/fines/{nonexistent_id}/pay",
            json={"payment_method_id": "card_123"}
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows"""

    def test_complete_payment_workflow(self, test_client):
        """Test complete workflow: check fines -> pay -> verify"""
        from app.main import app
        from fastapi.testclient import TestClient
        fresh_client = TestClient(app)

        license_plate = "А123БВ799"

        # Step 1: Check fines
        check_response = fresh_client.get(f"/api/fines/check?license_plate={license_plate}")
        assert check_response.status_code == 200
        fines_before = check_response.json()
        initial_count = len(fines_before)

        if initial_count > 0:
            fine_to_pay = fines_before[0]
            fine_id = fine_to_pay["fine_id"]

            # Step 2: Pay the fine
            pay_response = fresh_client.post(
                f"/api/fines/{fine_id}/pay",
                json={"payment_method_id": "card_123"}
            )
            assert pay_response.status_code == 200
            payment_data = pay_response.json()
            assert payment_data["status"] == "paid"

            # Step 3: Verify fine is no longer in unpaid list
            check_response2 = fresh_client.get(f"/api/fines/check?license_plate={license_plate}")
            fines_after = check_response2.json()

            # Should have one less fine now
            assert len(fines_after) == initial_count - 1

            # The paid fine should not be in the list
            fine_ids_after = [f["fine_id"] for f in fines_after]
            assert fine_id not in fine_ids_after

    def test_multiple_fines_workflow(self, test_client):
        """Test workflow with multiple fines"""
        from app.main import app
        from fastapi.testclient import TestClient
        from app.repositories.local_fine_repo import fine_repository

        # Reset repository to ensure test data is fresh
        fine_repository._initialize_test_data()

        fresh_client = TestClient(app)

        # Check first license plate
        response1 = fresh_client.get("/api/fines/check?license_plate=А123БВ799")
        assert response1.status_code == 200
        fines1 = response1.json()

        # Check second license plate
        response2 = fresh_client.get("/api/fines/check?license_plate=М456КЛ177")
        assert response2.status_code == 200
        fines2 = response2.json()

        # Both should have fines initially
        assert len(fines1) > 0
        assert len(fines2) > 0

        # Fines should be different
        fine_id_1 = fines1[0]["fine_id"]
        fine_id_2 = fines2[0]["fine_id"]
        assert fine_id_1 != fine_id_2


class TestAPIValidation:
    """Test API validation and error handling"""

    def test_check_fines_validates_required_parameter(self, test_client):
        """Test that license_plate parameter is required"""
        response = test_client.get("/api/fines/check")

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_pay_fine_validates_request_body(self, test_client):
        """Test that request body is validated"""
        fine_id = str(uuid4())

        # Send invalid JSON
        response = test_client.post(
            f"/api/fines/{fine_id}/pay",
            json={"invalid_field": "value"}
        )

        assert response.status_code == 422

    def test_pay_fine_validates_uuid_format(self, test_client):
        """Test that UUID format is validated"""
        response = test_client.post(
            "/api/fines/invalid-uuid-format/pay",
            json={"payment_method_id": "card_123"}
        )

        assert response.status_code == 422

    def test_endpoints_return_json(self, test_client):
        """Test that all endpoints return JSON"""
        # Health check
        response1 = test_client.get("/health")
        assert response1.headers["content-type"] == "application/json"

        # Check fines
        response2 = test_client.get("/api/fines/check?license_plate=TEST")
        assert response2.headers["content-type"] == "application/json"


class TestAPIDocumentation:
    """Test that API documentation endpoints are available"""

    def test_openapi_json_available(self, test_client):
        """Test that OpenAPI JSON schema is available"""
        response = test_client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_docs_endpoint_available(self, test_client):
        """Test that Swagger UI docs are available"""
        response = test_client.get("/docs")

        assert response.status_code == 200

    def test_redoc_endpoint_available(self, test_client):
        """Test that ReDoc docs are available"""
        response = test_client.get("/redoc")

        assert response.status_code == 200
