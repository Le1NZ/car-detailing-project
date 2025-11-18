"""Unit tests for PaymentRepository."""

from datetime import datetime

import pytest

from app.repositories.local_payment_repo import PaymentRepository


class TestPaymentRepositoryCreate:
    """Tests for creating payments in the repository."""

    def test_create_payment_success(self, payment_repository: PaymentRepository):
        """Test successfully creating a payment."""
        # Arrange
        payment_data = {
            "payment_id": "pay_abc123",
            "order_id": "ord_test123",
            "status": "pending",
            "amount": 1000.00,
            "currency": "RUB"
        }

        # Act
        result = payment_repository.create_payment(payment_data)

        # Assert
        assert result == payment_data
        assert len(payment_repository.payments_storage) == 1
        assert payment_repository.payments_storage[0] == payment_data

    def test_create_multiple_payments(self, payment_repository: PaymentRepository):
        """Test creating multiple payments stores all of them."""
        # Arrange
        payment1 = {"payment_id": "pay_001", "order_id": "ord_001", "status": "pending"}
        payment2 = {"payment_id": "pay_002", "order_id": "ord_002", "status": "pending"}

        # Act
        payment_repository.create_payment(payment1)
        payment_repository.create_payment(payment2)

        # Assert
        assert len(payment_repository.payments_storage) == 2
        assert payment_repository.payments_storage[0] == payment1
        assert payment_repository.payments_storage[1] == payment2


class TestPaymentRepositoryRetrieve:
    """Tests for retrieving payments from the repository."""

    def test_get_payment_by_id_success(self, payment_repository: PaymentRepository):
        """Test successfully retrieving a payment by ID."""
        # Arrange
        payment_data = {
            "payment_id": "pay_xyz789",
            "order_id": "ord_test123",
            "status": "succeeded"
        }
        payment_repository.create_payment(payment_data)

        # Act
        result = payment_repository.get_payment_by_id("pay_xyz789")

        # Assert
        assert result is not None
        assert result["payment_id"] == "pay_xyz789"
        assert result["order_id"] == "ord_test123"
        assert result["status"] == "succeeded"

    def test_get_payment_by_id_not_found(self, payment_repository: PaymentRepository):
        """Test retrieving non-existent payment returns None."""
        # Act
        result = payment_repository.get_payment_by_id("pay_nonexistent")

        # Assert
        assert result is None

    def test_get_payment_by_id_from_multiple(self, payment_repository: PaymentRepository):
        """Test retrieving specific payment from multiple payments."""
        # Arrange
        payment1 = {"payment_id": "pay_001", "status": "pending"}
        payment2 = {"payment_id": "pay_002", "status": "succeeded"}
        payment3 = {"payment_id": "pay_003", "status": "failed"}
        payment_repository.create_payment(payment1)
        payment_repository.create_payment(payment2)
        payment_repository.create_payment(payment3)

        # Act
        result = payment_repository.get_payment_by_id("pay_002")

        # Assert
        assert result is not None
        assert result["payment_id"] == "pay_002"
        assert result["status"] == "succeeded"


class TestPaymentRepositoryUpdate:
    """Tests for updating payment status."""

    def test_update_payment_status_success(self, payment_repository: PaymentRepository):
        """Test successfully updating payment status."""
        # Arrange
        payment_data = {
            "payment_id": "pay_update1",
            "status": "pending"
        }
        payment_repository.create_payment(payment_data)

        # Act
        result = payment_repository.update_payment_status("pay_update1", "succeeded")

        # Assert
        assert result is True
        updated_payment = payment_repository.get_payment_by_id("pay_update1")
        assert updated_payment["status"] == "succeeded"

    def test_update_payment_status_with_paid_at(self, payment_repository: PaymentRepository):
        """Test updating payment status with paid_at timestamp."""
        # Arrange
        payment_data = {
            "payment_id": "pay_update2",
            "status": "pending",
            "paid_at": None
        }
        payment_repository.create_payment(payment_data)
        paid_at = datetime(2024, 6, 11, 14, 30, 0)

        # Act
        result = payment_repository.update_payment_status(
            "pay_update2",
            "succeeded",
            paid_at=paid_at
        )

        # Assert
        assert result is True
        updated_payment = payment_repository.get_payment_by_id("pay_update2")
        assert updated_payment["status"] == "succeeded"
        assert updated_payment["paid_at"] == paid_at

    def test_update_payment_status_not_found(self, payment_repository: PaymentRepository):
        """Test updating non-existent payment returns False."""
        # Act
        result = payment_repository.update_payment_status("pay_nonexistent", "succeeded")

        # Assert
        assert result is False

    def test_update_payment_status_to_failed(self, payment_repository: PaymentRepository):
        """Test updating payment status to failed."""
        # Arrange
        payment_data = {
            "payment_id": "pay_fail1",
            "status": "pending"
        }
        payment_repository.create_payment(payment_data)

        # Act
        result = payment_repository.update_payment_status("pay_fail1", "failed")

        # Assert
        assert result is True
        updated_payment = payment_repository.get_payment_by_id("pay_fail1")
        assert updated_payment["status"] == "failed"


class TestPaymentRepositoryOrderChecks:
    """Tests for order-related checks in the repository."""

    def test_check_order_paid_true(self, payment_repository: PaymentRepository):
        """Test checking if order is paid returns True for succeeded payment."""
        # Arrange
        payment_data = {
            "payment_id": "pay_check1",
            "order_id": "ord_paid",
            "status": "succeeded"
        }
        payment_repository.create_payment(payment_data)

        # Act
        result = payment_repository.check_order_paid("ord_paid")

        # Assert
        assert result is True

    def test_check_order_paid_false_pending(self, payment_repository: PaymentRepository):
        """Test checking if order is paid returns False for pending payment."""
        # Arrange
        payment_data = {
            "payment_id": "pay_check2",
            "order_id": "ord_pending",
            "status": "pending"
        }
        payment_repository.create_payment(payment_data)

        # Act
        result = payment_repository.check_order_paid("ord_pending")

        # Assert
        assert result is False

    def test_check_order_paid_false_not_found(self, payment_repository: PaymentRepository):
        """Test checking if order is paid returns False for non-existent order."""
        # Act
        result = payment_repository.check_order_paid("ord_nonexistent")

        # Assert
        assert result is False

    def test_check_order_paid_false_failed(self, payment_repository: PaymentRepository):
        """Test checking if order is paid returns False for failed payment."""
        # Arrange
        payment_data = {
            "payment_id": "pay_check3",
            "order_id": "ord_failed",
            "status": "failed"
        }
        payment_repository.create_payment(payment_data)

        # Act
        result = payment_repository.check_order_paid("ord_failed")

        # Assert
        assert result is False

    def test_check_order_paid_multiple_payments_one_succeeded(
        self, payment_repository: PaymentRepository
    ):
        """Test order is considered paid if any payment succeeded."""
        # Arrange
        payment1 = {
            "payment_id": "pay_multi1",
            "order_id": "ord_multi",
            "status": "failed"
        }
        payment2 = {
            "payment_id": "pay_multi2",
            "order_id": "ord_multi",
            "status": "succeeded"
        }
        payment_repository.create_payment(payment1)
        payment_repository.create_payment(payment2)

        # Act
        result = payment_repository.check_order_paid("ord_multi")

        # Assert
        assert result is True


class TestPaymentRepositoryOrderData:
    """Tests for retrieving order data from mock storage."""

    def test_get_order_data_existing_order(self, payment_repository: PaymentRepository):
        """Test retrieving existing order data."""
        # Act
        result = payment_repository.get_order_data("ord_a1b2c3d4")

        # Assert
        assert result is not None
        assert result["user_id"] == "c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d"
        assert result["amount"] == 4500.00

    def test_get_order_data_test_order(self, payment_repository: PaymentRepository):
        """Test retrieving test order data."""
        # Act
        result = payment_repository.get_order_data("ord_test123")

        # Assert
        assert result is not None
        assert result["user_id"] == "test-user-id-123"
        assert result["amount"] == 2500.00

    def test_get_order_data_not_found(self, payment_repository: PaymentRepository):
        """Test retrieving non-existent order returns None."""
        # Act
        result = payment_repository.get_order_data("ord_nonexistent")

        # Assert
        assert result is None


class TestPaymentRepositoryEdgeCases:
    """Tests for edge cases and error scenarios."""

    def test_empty_repository_get_payment(self, payment_repository: PaymentRepository):
        """Test getting payment from empty repository."""
        # Act
        result = payment_repository.get_payment_by_id("any_id")

        # Assert
        assert result is None
        assert len(payment_repository.payments_storage) == 0

    def test_empty_repository_check_order_paid(self, payment_repository: PaymentRepository):
        """Test checking order paid on empty repository."""
        # Act
        result = payment_repository.check_order_paid("any_order")

        # Assert
        assert result is False

    def test_create_payment_with_same_id(self, payment_repository: PaymentRepository):
        """Test creating multiple payments with same ID are all stored."""
        # Note: The repository doesn't enforce uniqueness
        # Arrange
        payment1 = {"payment_id": "pay_same", "order_id": "ord_001"}
        payment2 = {"payment_id": "pay_same", "order_id": "ord_002"}

        # Act
        payment_repository.create_payment(payment1)
        payment_repository.create_payment(payment2)

        # Assert
        assert len(payment_repository.payments_storage) == 2
        # get_payment_by_id returns the first match
        result = payment_repository.get_payment_by_id("pay_same")
        assert result["order_id"] == "ord_001"

    def test_update_payment_without_paid_at(self, payment_repository: PaymentRepository):
        """Test updating status without providing paid_at keeps it None."""
        # Arrange
        payment_data = {
            "payment_id": "pay_no_time",
            "status": "pending",
            "paid_at": None
        }
        payment_repository.create_payment(payment_data)

        # Act
        payment_repository.update_payment_status("pay_no_time", "succeeded")

        # Assert
        updated_payment = payment_repository.get_payment_by_id("pay_no_time")
        assert updated_payment["status"] == "succeeded"
        # paid_at should remain None if not provided
        assert updated_payment.get("paid_at") is None
