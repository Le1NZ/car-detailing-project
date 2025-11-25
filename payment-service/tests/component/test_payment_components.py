"""Component tests for payment service.

Component tests verify the interaction between INTERNAL components:
- API endpoint + Service + Repository work TOGETHER (without mocks)
- Only EXTERNAL dependencies are mocked (RabbitMQ publisher)

These tests validate end-to-end flows within the service boundary.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


class TestCreatePaymentFlow:
    """Component test: Payment creation flow through API -> Service -> Repository."""

    def test_create_payment_flow(self, test_client: TestClient):
        """
        Test complete payment creation flow across internal components.

        Flow:
        1. API POST /api/payments receives request
        2. Service generates payment_id and saves to Repository
        3. Service launches background processing task
        4. API returns payment with status "pending"

        Components involved (NO MOCKS):
        - API endpoint (payments.py)
        - PaymentService (payment_service.py)
        - PaymentRepository (local_payment_repo.py)

        External mocks:
        - RabbitMQPublisher (external dependency)
        """
        # Arrange
        order_id = "ORDER1"
        payload = {
            "order_id": order_id,
            "payment_method": "card"
        }

        # Mock ONLY external RabbitMQ publisher
        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            # Act - Make API request (endpoint -> service -> repository)
            response = test_client.post("/api/payments", json=payload)

            # Assert - API response
            assert response.status_code == 201
            response_data = response.json()
            assert response_data["order_id"] == order_id
            assert response_data["status"] == "pending"
            assert response_data["amount"] == 5000.00
            assert response_data["currency"] == "RUB"
            assert response_data["payment_id"].startswith("pay_")
            assert "confirmation_url" in response_data
            assert "payment.gateway/confirm" in response_data["confirmation_url"]

            payment_id = response_data["payment_id"]

            # Assert - Service saved to Repository (verify internal component interaction)
            from app.repositories import payment_repository
            stored_payment = payment_repository.get_payment_by_id(payment_id)
            assert stored_payment is not None
            assert stored_payment["payment_id"] == payment_id
            assert stored_payment["order_id"] == order_id
            assert stored_payment["status"] == "pending"
            assert stored_payment["payment_method"] == "card"
            assert stored_payment["paid_at"] is None
            assert stored_payment["amount"] == 5000.00


class TestPaymentStatusRetrievalFlow:
    """Component test: Payment status retrieval flow through API -> Service -> Repository."""

    def test_payment_status_retrieval_flow(self, test_client: TestClient):
        """
        Test complete payment status retrieval flow across internal components.

        Flow:
        1. Create payment through API (saved to Repository)
        2. Service stores payment in Repository
        3. GET /api/payments/{payment_id} reads from Repository via Service
        4. API returns correct status

        Components involved (NO MOCKS):
        - API endpoint (payments.py)
        - PaymentService (payment_service.py)
        - PaymentRepository (local_payment_repo.py)

        External mocks:
        - RabbitMQPublisher (external dependency)
        """
        # Arrange - Create payment first
        order_id = "ORDER2"
        create_payload = {
            "order_id": order_id,
            "payment_method": "card"
        }

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            # Act 1 - Create payment via API
            create_response = test_client.post("/api/payments", json=create_payload)
            assert create_response.status_code == 201
            payment_id = create_response.json()["payment_id"]

            # Act 2 - Retrieve payment status via API (endpoint -> service -> repository)
            status_response = test_client.get(f"/api/payments/{payment_id}")

            # Assert - Status endpoint returns correct data
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert status_data["payment_id"] == payment_id
            assert status_data["status"] == "pending"
            assert status_data["paid_at"] is None

            # Assert - Repository has correct data (verify internal consistency)
            from app.repositories import payment_repository
            stored_payment = payment_repository.get_payment_by_id(payment_id)
            assert stored_payment is not None
            assert stored_payment["status"] == "pending"
            assert stored_payment["order_id"] == order_id


class TestAsyncPaymentProcessingFlow:
    """Component test: Asynchronous payment processing flow."""

    @pytest.mark.asyncio
    async def test_async_payment_processing_flow(self):
        """
        Test asynchronous payment processing flow across internal components.

        Flow:
        1. Create payment through Service directly (status: pending)
        2. Wait 6 seconds for background task processing
        3. Service updates status in Repository to "succeeded"
        4. Verify Repository shows status "succeeded"

        Components involved (NO MOCKS):
        - PaymentService (payment_service.py)
        - PaymentService._process_payment_async() (background task)
        - PaymentRepository (local_payment_repo.py)

        External mocks:
        - RabbitMQPublisher (external dependency)

        Note: TestClient doesn't support background tasks, so we call Service directly.
        """
        # Arrange
        from app.repositories import payment_repository
        from app.services import payment_service
        from tests.conftest import TEST_USER_ID

        order_id = "ORDER3"
        user_id = str(TEST_USER_ID)

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            # Act 1 - Create payment through Service (which stores in Repository)
            payment = await payment_service.initiate_payment(
                order_id=order_id,
                payment_method="card",
                user_id=user_id,
                amount=5000.0
            )
            payment_id = payment["payment_id"]

            # Assert - Initial status is pending
            initial_payment = payment_repository.get_payment_by_id(payment_id)
            assert initial_payment["status"] == "pending"
            assert initial_payment["paid_at"] is None

            # Act 2 - Wait for background async processing (5s + 1s buffer)
            await asyncio.sleep(6)

            # Assert - Service updated status in Repository to succeeded
            updated_payment = payment_repository.get_payment_by_id(payment_id)
            assert updated_payment is not None
            assert updated_payment["status"] == "succeeded"
            assert updated_payment["paid_at"] is not None


class TestDuplicatePaymentPrevention:
    """Component test: Duplicate payment prevention flow."""

    def test_duplicate_payment_prevention(self, test_client: TestClient):
        """
        Test duplicate payment prevention across internal components.

        Flow:
        1. Create payment for order_id="ORDER1" through API
        2. Service saves to Repository
        3. Manually update status to "succeeded" in Repository
        4. Attempt to create second payment for order_id="ORDER1"
        5. Service checks Repository and finds existing succeeded payment
        6. Service returns error
        7. API returns 409 Conflict

        Components involved (NO MOCKS):
        - API endpoint (payments.py)
        - PaymentService (payment_service.py)
        - PaymentRepository.check_order_paid() (business logic)
        - PaymentRepository (local_payment_repo.py)

        External mocks:
        - RabbitMQPublisher (external dependency)
        """
        # Arrange
        order_id = "ORDER1"
        payload = {
            "order_id": order_id,
            "payment_method": "card"
        }

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            # Act 1 - Create first payment via API
            first_response = test_client.post("/api/payments", json=payload)
            assert first_response.status_code == 201
            payment_id = first_response.json()["payment_id"]

            # Act 2 - Manually update payment status to succeeded in Repository
            from datetime import datetime
            from app.repositories import payment_repository
            success = payment_repository.update_payment_status(
                payment_id=payment_id,
                new_status="succeeded",
                paid_at=datetime.utcnow()
            )
            assert success is True

            # Verify Repository has succeeded payment
            payment = payment_repository.get_payment_by_id(payment_id)
            assert payment["status"] == "succeeded"
            assert payment_repository.check_order_paid(order_id) is True

            # Act 3 - Attempt to create duplicate payment for same order
            duplicate_response = test_client.post("/api/payments", json=payload)

            # Assert - API returns 409 Conflict
            assert duplicate_response.status_code == 409
            error_data = duplicate_response.json()
            assert "detail" in error_data
            assert "already paid" in error_data["detail"].lower()
            assert order_id in error_data["detail"]


class TestRabbitMQEventPublishingIntegration:
    """Component test: RabbitMQ event publishing integration."""

    @pytest.mark.asyncio
    async def test_rabbitmq_event_publishing_integration(self):
        """
        Test RabbitMQ event publishing after payment processing.

        Flow:
        1. Create payment through Service
        2. Mock RabbitMQ publisher (external dependency)
        3. Wait for async payment processing (6 seconds)
        4. Service updates Repository to "succeeded"
        5. Service calls publisher.publish_payment_success()
        6. Verify publisher was called with correct data

        Components involved (NO MOCKS):
        - PaymentService (payment_service.py)
        - PaymentService._process_payment_async() (background task)
        - PaymentRepository (local_payment_repo.py)

        External mocks:
        - RabbitMQPublisher (external dependency - THIS IS MOCKED)

        Note: TestClient doesn't support background tasks, so we call Service directly.
        """
        # Arrange
        from app.repositories import payment_repository
        from app.services import payment_service
        from tests.conftest import TEST_USER_ID

        order_id = "ORDER5"
        user_id = str(TEST_USER_ID)
        amount = 5000.0

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            # Act 1 - Create payment through Service (which stores in Repository)
            payment = await payment_service.initiate_payment(
                order_id=order_id,
                payment_method="card",
                user_id=user_id,
                amount=amount
            )
            payment_id = payment["payment_id"]

            # Act 2 - Wait for async payment processing
            await asyncio.sleep(6)

            # Assert - Repository status updated to succeeded
            updated_payment = payment_repository.get_payment_by_id(payment_id)
            assert updated_payment is not None
            assert updated_payment["status"] == "succeeded"
            assert updated_payment["paid_at"] is not None

            # Assert - RabbitMQ publisher was called with correct data
            mock_publisher.publish_payment_success.assert_called_once_with(
                order_id=order_id,
                user_id=user_id,
                amount=amount
            )
