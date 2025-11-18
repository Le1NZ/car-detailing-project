"""Integration tests for payment API endpoints."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app


class TestHealthEndpoint:
    """Integration tests for health check endpoint."""

    def test_health_endpoint_success(self, test_client: TestClient):
        """Test health endpoint returns 200 OK."""
        # Act
        response = test_client.get("/health")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "payment-service"
        assert "rabbitmq_connected" in data

    def test_health_endpoint_structure(self, test_client: TestClient):
        """Test health endpoint returns correct structure."""
        # Act
        response = test_client.get("/health")

        # Assert
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "rabbitmq_connected" in data
        assert isinstance(data["rabbitmq_connected"], bool)


class TestCreatePaymentEndpoint:
    """Integration tests for POST /api/payments endpoint."""

    def test_create_payment_success(self, test_client: TestClient):
        """Test successfully creating a payment."""
        # Arrange
        payload = {
            "order_id": "ord_test123",
            "payment_method": "card"
        }

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            # Act
            response = test_client.post("/api/payments", json=payload)

            # Assert
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["order_id"] == "ord_test123"
            assert data["status"] == "pending"
            assert data["amount"] == 5000.00  # Updated to reflect default amount
            assert data["currency"] == "RUB"
            assert "payment_id" in data
            assert data["payment_id"].startswith("pay_")
            assert "confirmation_url" in data

    def test_create_payment_order_not_found(self, test_client: TestClient):
        """Test creating payment for non-existent order (decoupled microservice approach)."""
        # Note: After refactoring, payment-service no longer checks order existence
        # This test now verifies that payment can be created without order validation
        # Arrange
        payload = {
            "order_id": "ord_nonexistent",
            "payment_method": "card"
        }

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            # Act
            response = test_client.post("/api/payments", json=payload)

            # Assert - Should succeed as we no longer validate order existence
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["order_id"] == "ord_nonexistent"
            assert data["status"] == "pending"

    def test_create_payment_already_paid(self, test_client: TestClient):
        """Test creating payment for already paid order returns 409."""
        # Arrange
        payload = {
            "order_id": "ord_test123",
            "payment_method": "card"
        }

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            # Create first payment
            response1 = test_client.post("/api/payments", json=payload)
            assert response1.status_code == status.HTTP_201_CREATED
            payment_id = response1.json()["payment_id"]

            # Manually update payment to succeeded status
            from app.repositories import payment_repository
            from datetime import datetime
            payment_repository.update_payment_status(
                payment_id, "succeeded", datetime.utcnow()
            )

            # Act - Try to create second payment
            response2 = test_client.post("/api/payments", json=payload)

            # Assert
            assert response2.status_code == status.HTTP_409_CONFLICT
            data = response2.json()
            assert "already paid" in data["detail"].lower()
            assert "ord_test123" in data["detail"]

    def test_create_payment_missing_order_id(self, test_client: TestClient):
        """Test creating payment without order_id returns 422."""
        # Arrange
        payload = {
            "payment_method": "card"
        }

        # Act
        response = test_client.post("/api/payments", json=payload)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_payment_missing_payment_method(self, test_client: TestClient):
        """Test creating payment without payment_method returns 422."""
        # Arrange
        payload = {
            "order_id": "ord_test123"
        }

        # Act
        response = test_client.post("/api/payments", json=payload)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_payment_with_sbp_method(self, test_client: TestClient):
        """Test creating payment with SBP payment method."""
        # Arrange
        payload = {
            "order_id": "ord_test123",
            "payment_method": "sbp"
        }

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            # Act
            response = test_client.post("/api/payments", json=payload)

            # Assert
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["order_id"] == "ord_test123"

    def test_create_payment_with_alternative_order(self, test_client: TestClient):
        """Test creating payment with alternative test order."""
        # Arrange
        payload = {
            "order_id": "ord_a1b2c3d4",
            "payment_method": "card"
        }

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            # Act
            response = test_client.post("/api/payments", json=payload)

            # Assert
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["order_id"] == "ord_a1b2c3d4"
            assert data["amount"] == 5000.00  # Updated to reflect default amount

    def test_create_payment_empty_body(self, test_client: TestClient):
        """Test creating payment with empty body returns 422."""
        # Act
        response = test_client.post("/api/payments", json={})

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_payment_invalid_json(self, test_client: TestClient):
        """Test creating payment with invalid JSON returns 422."""
        # Act
        response = test_client.post(
            "/api/payments",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_payment_response_structure(self, test_client: TestClient):
        """Test payment response has correct structure."""
        # Arrange
        payload = {
            "order_id": "ord_test123",
            "payment_method": "card"
        }

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            # Act
            response = test_client.post("/api/payments", json=payload)

            # Assert
            data = response.json()
            assert "payment_id" in data
            assert "order_id" in data
            assert "status" in data
            assert "amount" in data
            assert "currency" in data
            assert "confirmation_url" in data


class TestGetPaymentStatusEndpoint:
    """Integration tests for GET /api/payments/{payment_id} endpoint."""

    def test_get_payment_status_pending(self, test_client: TestClient):
        """Test getting status of pending payment."""
        # Arrange - Create a payment first
        create_payload = {
            "order_id": "ord_test123",
            "payment_method": "card"
        }

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            create_response = test_client.post("/api/payments", json=create_payload)
            payment_id = create_response.json()["payment_id"]

            # Act
            response = test_client.get(f"/api/payments/{payment_id}")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["payment_id"] == payment_id
            assert data["status"] == "pending"
            assert data["paid_at"] is None

    def test_get_payment_status_succeeded(self, test_client: TestClient):
        """Test getting status of succeeded payment."""
        # Arrange - Create payment and update to succeeded
        create_payload = {
            "order_id": "ord_test123",
            "payment_method": "card"
        }

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            create_response = test_client.post("/api/payments", json=create_payload)
            payment_id = create_response.json()["payment_id"]

            # Update to succeeded
            from app.repositories import payment_repository
            from datetime import datetime
            paid_at = datetime.utcnow()
            payment_repository.update_payment_status(payment_id, "succeeded", paid_at)

            # Act
            response = test_client.get(f"/api/payments/{payment_id}")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["payment_id"] == payment_id
            assert data["status"] == "succeeded"
            assert data["paid_at"] is not None

    def test_get_payment_status_not_found(self, test_client: TestClient):
        """Test getting status of non-existent payment returns 404."""
        # Act
        response = test_client.get("/api/payments/pay_nonexistent")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["detail"].lower()
        assert "pay_nonexistent" in data["detail"]

    def test_get_payment_status_response_structure(self, test_client: TestClient):
        """Test payment status response has correct structure."""
        # Arrange
        create_payload = {
            "order_id": "ord_test123",
            "payment_method": "card"
        }

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            create_response = test_client.post("/api/payments", json=create_payload)
            payment_id = create_response.json()["payment_id"]

            # Act
            response = test_client.get(f"/api/payments/{payment_id}")

            # Assert
            data = response.json()
            assert "payment_id" in data
            assert "status" in data
            assert "paid_at" in data


class TestPaymentWorkflow:
    """Integration tests for complete payment workflow."""

    def test_complete_payment_workflow(self, test_client: TestClient):
        """Test complete workflow from creation to success."""
        # Arrange
        payload = {
            "order_id": "ord_test123",
            "payment_method": "card"
        }

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            # Act 1 - Create payment
            create_response = test_client.post("/api/payments", json=payload)
            assert create_response.status_code == status.HTTP_201_CREATED
            payment_id = create_response.json()["payment_id"]

            # Act 2 - Check initial status
            status_response_1 = test_client.get(f"/api/payments/{payment_id}")
            assert status_response_1.status_code == status.HTTP_200_OK
            assert status_response_1.json()["status"] == "pending"

            # Simulate payment processing
            from app.repositories import payment_repository
            from datetime import datetime
            payment_repository.update_payment_status(
                payment_id, "succeeded", datetime.utcnow()
            )

            # Act 3 - Check final status
            status_response_2 = test_client.get(f"/api/payments/{payment_id}")
            assert status_response_2.status_code == status.HTTP_200_OK
            final_data = status_response_2.json()

            # Assert
            assert final_data["status"] == "succeeded"
            assert final_data["paid_at"] is not None

    def test_multiple_payments_for_different_orders(self, test_client: TestClient):
        """Test creating multiple payments for different orders."""
        # Arrange
        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            # Act - Create multiple payments
            response1 = test_client.post("/api/payments", json={
                "order_id": "ord_test123",
                "payment_method": "card"
            })

            # Clear repository to allow second payment
            from app.repositories import payment_repository
            payment_repository.payments_storage = []

            response2 = test_client.post("/api/payments", json={
                "order_id": "ord_a1b2c3d4",
                "payment_method": "sbp"
            })

            # Assert
            assert response1.status_code == status.HTTP_201_CREATED
            assert response2.status_code == status.HTTP_201_CREATED

            data1 = response1.json()
            data2 = response2.json()

            assert data1["order_id"] == "ord_test123"
            assert data2["order_id"] == "ord_a1b2c3d4"
            assert data1["payment_id"] != data2["payment_id"]


class TestAPIErrorHandling:
    """Integration tests for API error handling."""

    def test_invalid_http_method_on_payments(self, test_client: TestClient):
        """Test invalid HTTP method returns 405."""
        # Act
        response = test_client.put("/api/payments")

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_invalid_http_method_on_payment_status(self, test_client: TestClient):
        """Test invalid HTTP method on status endpoint returns 405."""
        # Act
        response = test_client.post("/api/payments/pay_test123")

        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_content_type_validation(self, test_client: TestClient):
        """Test endpoint requires JSON content type."""
        # Act
        response = test_client.post(
            "/api/payments",
            data="order_id=test&payment_method=card",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAPICORS:
    """Integration tests for CORS configuration."""

    def test_cors_headers_present(self, test_client: TestClient):
        """Test CORS headers are present in response."""
        # Act
        response = test_client.options(
            "/api/payments",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )

        # Assert
        assert "access-control-allow-origin" in response.headers


class TestAPIDocumentation:
    """Integration tests for API documentation endpoints."""

    def test_openapi_docs_available(self, test_client: TestClient):
        """Test OpenAPI documentation is available."""
        # Act
        response = test_client.get("/docs")

        # Assert
        assert response.status_code == status.HTTP_200_OK

    def test_redoc_available(self, test_client: TestClient):
        """Test ReDoc documentation is available."""
        # Act
        response = test_client.get("/redoc")

        # Assert
        assert response.status_code == status.HTTP_200_OK

    def test_openapi_json_available(self, test_client: TestClient):
        """Test OpenAPI JSON schema is available."""
        # Act
        response = test_client.get("/openapi.json")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data


class TestAPIEdgeCases:
    """Integration tests for edge cases."""

    def test_create_payment_with_extra_fields(self, test_client: TestClient):
        """Test creating payment with extra fields ignores them."""
        # Arrange
        payload = {
            "order_id": "ord_test123",
            "payment_method": "card",
            "extra_field": "should_be_ignored"
        }

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            # Act
            response = test_client.post("/api/payments", json=payload)

            # Assert
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert "extra_field" not in data

    def test_get_payment_with_special_characters_in_id(self, test_client: TestClient):
        """Test getting payment with special characters returns 404."""
        # Act
        response = test_client.get("/api/payments/pay_test@#$")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_concurrent_payment_creation_different_orders(self, test_client: TestClient):
        """Test concurrent payment creation for different orders."""
        # This is a simplified concurrency test
        # Arrange
        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            # Act - Create payments in sequence (simulating concurrent requests)
            response1 = test_client.post("/api/payments", json={
                "order_id": "ord_test123",
                "payment_method": "card"
            })

            # Clear for second payment
            from app.repositories import payment_repository
            payment_id_1 = response1.json()["payment_id"]
            # Keep first payment but allow second order
            payment_repository.payments_storage = [
                p for p in payment_repository.payments_storage
                if p["payment_id"] == payment_id_1 and p["status"] != "succeeded"
            ]

            response2 = test_client.post("/api/payments", json={
                "order_id": "ord_a1b2c3d4",
                "payment_method": "card"
            })

            # Assert
            assert response1.status_code == status.HTTP_201_CREATED
            assert response2.status_code == status.HTTP_201_CREATED
            assert response1.json()["payment_id"] != response2.json()["payment_id"]
