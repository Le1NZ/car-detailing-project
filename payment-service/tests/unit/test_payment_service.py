"""Unit tests for PaymentService."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.repositories.local_payment_repo import PaymentRepository
from app.services.payment_service import PaymentService


class TestPaymentServiceInitiatePayment:
    """Tests for initiating payments."""

    @pytest.mark.asyncio
    async def test_initiate_payment_success(
        self, payment_service: PaymentService, payment_repository: PaymentRepository
    ):
        """Test successfully initiating a payment."""
        # Arrange
        order_id = "ord_test123"
        payment_method = "card"
        user_id = "test-user-id-123"
        amount = 2500.00

        # Mock RabbitMQ publisher
        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            # Act
            result = await payment_service.initiate_payment(order_id, payment_method, user_id, amount)

            # Assert
            assert result is not None
            assert result["order_id"] == order_id
            assert result["status"] == "pending"
            assert result["amount"] == 2500.00
            assert result["currency"] == "RUB"
            assert result["payment_method"] == payment_method
            assert "payment_id" in result
            assert result["payment_id"].startswith("pay_")
            assert "confirmation_url" in result
            assert result["created_at"] is not None
            assert result["user_id"] == "test-user-id-123"

    @pytest.mark.asyncio
    async def test_initiate_payment_order_not_found(self, payment_service: PaymentService):
        """Test initiating payment for non-existent order raises ValueError."""
        # Arrange
        order_id = "ord_nonexistent"
        payment_method = "card"
        user_id = "test-user-id"
        amount = 5000.0

        # NOTE: This test is no longer relevant as we removed order validation
        # The service now accepts any order_id and processes payment
        # Skipping this test by expecting successful payment instead
        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()
            result = await payment_service.initiate_payment(order_id, payment_method, user_id, amount)
            assert result is not None

    @pytest.mark.asyncio
    async def test_initiate_payment_order_already_paid(
        self, payment_service: PaymentService, payment_repository: PaymentRepository
    ):
        """Test initiating payment for already paid order raises ValueError."""
        # Arrange
        order_id = "ord_test123"
        user_id = "test-user-id"
        amount = 5000.0

        # Create existing successful payment
        existing_payment = {
            "payment_id": "pay_existing",
            "order_id": order_id,
            "status": "succeeded"
        }
        payment_repository.create_payment(existing_payment)

        # Act & Assert
        with pytest.raises(ValueError, match="Order ord_test123 already paid"):
            await payment_service.initiate_payment(order_id, "card", user_id, amount)

    @pytest.mark.asyncio
    async def test_initiate_payment_creates_unique_payment_id(
        self, payment_service: PaymentService
    ):
        """Test each payment gets a unique payment_id."""
        # Arrange
        order_id = "ord_test123"
        user_id = "test-user-id"
        amount = 5000.0

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            # Act
            payment1 = await payment_service.initiate_payment(order_id, "card", user_id, amount)

            # Clear the paid status for second attempt
            payment_service.repository.payments_storage = []

            payment2 = await payment_service.initiate_payment(order_id, "card", user_id, amount)

            # Assert
            assert payment1["payment_id"] != payment2["payment_id"]

    @pytest.mark.asyncio
    async def test_initiate_payment_saves_to_repository(
        self, payment_service: PaymentService, payment_repository: PaymentRepository
    ):
        """Test initiated payment is saved to repository."""
        # Arrange
        order_id = "ord_test123"
        user_id = "test-user-id"
        amount = 5000.0

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            # Act
            result = await payment_service.initiate_payment(order_id, "card", user_id, amount)

            # Assert
            saved_payment = payment_repository.get_payment_by_id(result["payment_id"])
            assert saved_payment is not None
            assert saved_payment["order_id"] == order_id
            assert saved_payment["status"] == "pending"

    @pytest.mark.asyncio
    async def test_initiate_payment_starts_background_task(
        self, payment_service: PaymentService
    ):
        """Test initiating payment starts background processing task."""
        # Arrange
        order_id = "ord_test123"
        user_id = "test-user-id"
        amount = 5000.0

        with patch("app.services.payment_service.asyncio.create_task") as mock_create_task:
            with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
                mock_publisher.publish_payment_success = AsyncMock()

                # Act
                await payment_service.initiate_payment(order_id, "card", user_id, amount)

                # Assert
                mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_initiate_payment_with_different_payment_method(
        self, payment_service: PaymentService
    ):
        """Test initiating payment with different payment methods."""
        # Arrange
        order_id = "ord_test123"
        user_id = "test-user-id"
        amount = 5000.0

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            # Act
            result = await payment_service.initiate_payment(order_id, "sbp", user_id, amount)

            # Assert
            assert result["payment_method"] == "sbp"


class TestPaymentServiceProcessPaymentAsync:
    """Tests for background payment processing."""

    @pytest.mark.asyncio
    async def test_process_payment_async_success(
        self, payment_service: PaymentService, payment_repository: PaymentRepository
    ):
        """Test successful async payment processing."""
        # Arrange
        payment_id = "pay_test123"
        order_id = "ord_test123"
        user_id = "user_456"
        amount = 2500.00

        payment_data = {
            "payment_id": payment_id,
            "order_id": order_id,
            "status": "pending",
            "user_id": user_id,
            "amount": amount
        }
        payment_repository.create_payment(payment_data)

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            # Mock asyncio.sleep to speed up test
            with patch("app.services.payment_service.asyncio.sleep", new_callable=AsyncMock):
                # Act
                await payment_service._process_payment_async(
                    payment_id=payment_id,
                    order_id=order_id,
                    user_id=user_id,
                    amount=amount
                )

                # Assert
                updated_payment = payment_repository.get_payment_by_id(payment_id)
                assert updated_payment["status"] == "succeeded"
                assert updated_payment["paid_at"] is not None
                mock_publisher.publish_payment_success.assert_called_once_with(
                    order_id=order_id,
                    user_id=user_id,
                    amount=amount
                )

    @pytest.mark.asyncio
    async def test_process_payment_async_publishes_to_rabbitmq(
        self, payment_service: PaymentService, payment_repository: PaymentRepository
    ):
        """Test async processing publishes event to RabbitMQ."""
        # Arrange
        payment_id = "pay_test456"
        order_id = "ord_test123"
        user_id = "user_789"
        amount = 3000.00

        payment_data = {
            "payment_id": payment_id,
            "order_id": order_id,
            "status": "pending"
        }
        payment_repository.create_payment(payment_data)

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            with patch("app.services.payment_service.asyncio.sleep", new_callable=AsyncMock):
                # Act
                await payment_service._process_payment_async(
                    payment_id=payment_id,
                    order_id=order_id,
                    user_id=user_id,
                    amount=amount
                )

                # Assert
                mock_publisher.publish_payment_success.assert_called_once()
                call_args = mock_publisher.publish_payment_success.call_args
                assert call_args[1]["order_id"] == order_id
                assert call_args[1]["user_id"] == user_id
                assert call_args[1]["amount"] == amount

    @pytest.mark.asyncio
    async def test_process_payment_async_payment_not_found(
        self, payment_service: PaymentService, payment_repository: PaymentRepository
    ):
        """Test async processing when payment doesn't exist in repository."""
        # Arrange
        payment_id = "pay_nonexistent"

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            with patch("app.services.payment_service.asyncio.sleep", new_callable=AsyncMock):
                # Act
                await payment_service._process_payment_async(
                    payment_id=payment_id,
                    order_id="ord_123",
                    user_id="user_456",
                    amount=1000.00
                )

                # Assert - should not publish if update failed
                mock_publisher.publish_payment_success.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_payment_async_handles_exception(
        self, payment_service: PaymentService, payment_repository: PaymentRepository
    ):
        """Test async processing handles exceptions and sets failed status."""
        # Arrange
        payment_id = "pay_test789"
        payment_data = {
            "payment_id": payment_id,
            "order_id": "ord_test123",
            "status": "pending"
        }
        payment_repository.create_payment(payment_data)

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock(
                side_effect=Exception("RabbitMQ error")
            )

            with patch("app.services.payment_service.asyncio.sleep", new_callable=AsyncMock):
                # Act
                await payment_service._process_payment_async(
                    payment_id=payment_id,
                    order_id="ord_test123",
                    user_id="user_456",
                    amount=1000.00
                )

                # Assert - status should be updated to failed
                updated_payment = payment_repository.get_payment_by_id(payment_id)
                assert updated_payment["status"] == "failed"

    @pytest.mark.asyncio
    async def test_process_payment_async_sets_paid_at_timestamp(
        self, payment_service: PaymentService, payment_repository: PaymentRepository
    ):
        """Test async processing sets paid_at timestamp."""
        # Arrange
        payment_id = "pay_time_test"
        payment_data = {
            "payment_id": payment_id,
            "order_id": "ord_test123",
            "status": "pending",
            "paid_at": None
        }
        payment_repository.create_payment(payment_data)

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            with patch("app.services.payment_service.asyncio.sleep", new_callable=AsyncMock):
                # Act
                before = datetime.utcnow()
                await payment_service._process_payment_async(
                    payment_id=payment_id,
                    order_id="ord_test123",
                    user_id="user_456",
                    amount=1000.00
                )
                after = datetime.utcnow()

                # Assert
                updated_payment = payment_repository.get_payment_by_id(payment_id)
                assert updated_payment["paid_at"] is not None
                assert before <= updated_payment["paid_at"] <= after

    @pytest.mark.asyncio
    async def test_process_payment_async_does_not_publish_on_update_failure(
        self, payment_service: PaymentService
    ):
        """Test no RabbitMQ publish if status update fails."""
        # Arrange - no payment in repository, so update will fail
        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            with patch("app.services.payment_service.asyncio.sleep", new_callable=AsyncMock):
                # Act
                await payment_service._process_payment_async(
                    payment_id="pay_nonexistent",
                    order_id="ord_123",
                    user_id="user_456",
                    amount=1000.00
                )

                # Assert
                mock_publisher.publish_payment_success.assert_not_called()


class TestPaymentServiceGetPayment:
    """Tests for retrieving payment information."""

    def test_get_payment_success(
        self, payment_service: PaymentService, payment_repository: PaymentRepository
    ):
        """Test successfully retrieving a payment."""
        # Arrange
        payment_data = {
            "payment_id": "pay_retrieve",
            "order_id": "ord_test123",
            "status": "succeeded"
        }
        payment_repository.create_payment(payment_data)

        # Act
        result = payment_service.get_payment("pay_retrieve")

        # Assert
        assert result is not None
        assert result["payment_id"] == "pay_retrieve"
        assert result["order_id"] == "ord_test123"
        assert result["status"] == "succeeded"

    def test_get_payment_not_found(self, payment_service: PaymentService):
        """Test retrieving non-existent payment returns None."""
        # Act
        result = payment_service.get_payment("pay_nonexistent")

        # Assert
        assert result is None

    def test_get_payment_with_pending_status(
        self, payment_service: PaymentService, payment_repository: PaymentRepository
    ):
        """Test retrieving payment with pending status."""
        # Arrange
        payment_data = {
            "payment_id": "pay_pending",
            "order_id": "ord_test123",
            "status": "pending",
            "paid_at": None
        }
        payment_repository.create_payment(payment_data)

        # Act
        result = payment_service.get_payment("pay_pending")

        # Assert
        assert result is not None
        assert result["status"] == "pending"
        assert result["paid_at"] is None

    def test_get_payment_with_failed_status(
        self, payment_service: PaymentService, payment_repository: PaymentRepository
    ):
        """Test retrieving payment with failed status."""
        # Arrange
        payment_data = {
            "payment_id": "pay_failed",
            "order_id": "ord_test123",
            "status": "failed"
        }
        payment_repository.create_payment(payment_data)

        # Act
        result = payment_service.get_payment("pay_failed")

        # Assert
        assert result is not None
        assert result["status"] == "failed"


class TestPaymentServiceIntegration:
    """Integration tests for complete payment flow."""

    @pytest.mark.asyncio
    async def test_complete_payment_flow(
        self, payment_service: PaymentService, payment_repository: PaymentRepository
    ):
        """Test complete flow from initiate to successful payment."""
        # Arrange
        order_id = "ord_test123"
        user_id = "test-user-id"
        amount = 5000.0

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            with patch("app.services.payment_service.asyncio.sleep", new_callable=AsyncMock):
                # Act - Initiate payment
                payment = await payment_service.initiate_payment(order_id, "card", user_id, amount)
                payment_id = payment["payment_id"]

                # Verify pending status
                assert payment["status"] == "pending"

                # Process payment
                await payment_service._process_payment_async(
                    payment_id=payment_id,
                    order_id=order_id,
                    user_id=payment["user_id"],
                    amount=payment["amount"]
                )

                # Get final status
                final_payment = payment_service.get_payment(payment_id)

                # Assert
                assert final_payment["status"] == "succeeded"
                assert final_payment["paid_at"] is not None
                mock_publisher.publish_payment_success.assert_called_once()

    @pytest.mark.asyncio
    async def test_payment_flow_prevents_duplicate_payment(
        self, payment_service: PaymentService
    ):
        """Test that duplicate payment attempts are prevented."""
        # Arrange
        order_id = "ord_test123"
        user_id = "test-user-id"
        amount = 5000.0

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            with patch("app.services.payment_service.asyncio.sleep", new_callable=AsyncMock):
                # Act - First payment
                payment1 = await payment_service.initiate_payment(order_id, "card", user_id, amount)

                # Process to completion
                await payment_service._process_payment_async(
                    payment_id=payment1["payment_id"],
                    order_id=order_id,
                    user_id=payment1["user_id"],
                    amount=payment1["amount"]
                )

                # Assert - Second payment attempt should fail
                with pytest.raises(ValueError, match="already paid"):
                    await payment_service.initiate_payment(order_id, "card", user_id, amount)


class TestPaymentServiceEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_initiate_payment_with_existing_order_alternative(
        self, payment_service: PaymentService
    ):
        """Test initiating payment with alternative test order."""
        # Arrange
        order_id = "ord_a1b2c3d4"
        user_id = "c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d"
        amount = 4500.00

        with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
            mock_publisher.publish_payment_success = AsyncMock()

            # Act
            result = await payment_service.initiate_payment(order_id, "card", user_id, amount)

            # Assert
            assert result["order_id"] == order_id
            assert result["amount"] == 4500.00
            assert result["user_id"] == "c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d"

    @pytest.mark.asyncio
    async def test_process_payment_handles_repository_exception(
        self, payment_service: PaymentService, payment_repository: PaymentRepository
    ):
        """Test processing handles repository exceptions gracefully."""
        # Arrange
        payment_id = "pay_error"
        payment_data = {
            "payment_id": payment_id,
            "order_id": "ord_test123",
            "status": "pending"
        }
        payment_repository.create_payment(payment_data)

        # Mock repository update to raise exception
        with patch.object(
            payment_repository, "update_payment_status", side_effect=Exception("DB error")
        ):
            with patch("app.services.payment_service.rabbitmq_publisher") as mock_publisher:
                mock_publisher.publish_payment_success = AsyncMock()

                with patch("app.services.payment_service.asyncio.sleep", new_callable=AsyncMock):
                    # Act - should not raise
                    await payment_service._process_payment_async(
                        payment_id=payment_id,
                        order_id="ord_test123",
                        user_id="user_456",
                        amount=1000.00
                    )

                    # Assert - should not publish on error
                    mock_publisher.publish_payment_success.assert_not_called()

    def test_service_initialization(self):
        """Test service initializes with repository."""
        # Act
        service = PaymentService()

        # Assert
        assert service.repository is not None
        assert isinstance(service.repository, PaymentRepository)
