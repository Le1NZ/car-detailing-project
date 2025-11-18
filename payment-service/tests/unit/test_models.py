"""Unit tests for Pydantic models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.payment import (
    InitiatePaymentRequest,
    PaymentCreateRequest,
    PaymentCreateResponse,
    PaymentResponse,
    PaymentStatusResponse,
)


class TestInitiatePaymentRequest:
    """Tests for InitiatePaymentRequest model."""

    def test_valid_request(self):
        """Test creating valid payment request."""
        # Arrange & Act
        request = InitiatePaymentRequest(
            order_id="ord_test123",
            payment_method="card"
        )

        # Assert
        assert request.order_id == "ord_test123"
        assert request.payment_method == "card"

    def test_valid_request_with_sbp_method(self):
        """Test creating request with SBP payment method."""
        # Arrange & Act
        request = InitiatePaymentRequest(
            order_id="ord_test456",
            payment_method="sbp"
        )

        # Assert
        assert request.order_id == "ord_test456"
        assert request.payment_method == "sbp"

    def test_missing_order_id_raises_error(self):
        """Test missing order_id raises ValidationError."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            InitiatePaymentRequest(payment_method="card")

        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any(error["loc"] == ("order_id",) for error in errors)

    def test_missing_payment_method_raises_error(self):
        """Test missing payment_method raises ValidationError."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            InitiatePaymentRequest(order_id="ord_test123")

        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any(error["loc"] == ("payment_method",) for error in errors)

    def test_empty_string_order_id(self):
        """Test empty string order_id is accepted."""
        # Arrange & Act
        request = InitiatePaymentRequest(
            order_id="",
            payment_method="card"
        )

        # Assert
        assert request.order_id == ""

    def test_model_to_dict(self):
        """Test converting model to dictionary."""
        # Arrange
        request = InitiatePaymentRequest(
            order_id="ord_test123",
            payment_method="card"
        )

        # Act
        data = request.model_dump()

        # Assert
        assert data == {
            "order_id": "ord_test123",
            "payment_method": "card"
        }

    def test_model_from_dict(self):
        """Test creating model from dictionary."""
        # Arrange
        data = {
            "order_id": "ord_test123",
            "payment_method": "card"
        }

        # Act
        request = InitiatePaymentRequest(**data)

        # Assert
        assert request.order_id == "ord_test123"
        assert request.payment_method == "card"


class TestPaymentResponse:
    """Tests for PaymentResponse model."""

    def test_valid_response(self):
        """Test creating valid payment response."""
        # Arrange & Act
        response = PaymentResponse(
            payment_id="pay_test123",
            order_id="ord_test123",
            status="pending",
            amount=2500.00,
            currency="RUB",
            confirmation_url="https://payment.gateway/confirm?token=pay_test123"
        )

        # Assert
        assert response.payment_id == "pay_test123"
        assert response.order_id == "ord_test123"
        assert response.status == "pending"
        assert response.amount == 2500.00
        assert response.currency == "RUB"
        assert response.confirmation_url == "https://payment.gateway/confirm?token=pay_test123"

    def test_response_with_default_currency(self):
        """Test response uses default currency if not provided."""
        # Arrange & Act
        response = PaymentResponse(
            payment_id="pay_test123",
            order_id="ord_test123",
            status="pending",
            amount=1000.00,
            confirmation_url="https://example.com"
        )

        # Assert
        assert response.currency == "RUB"

    def test_response_with_succeeded_status(self):
        """Test creating response with succeeded status."""
        # Arrange & Act
        response = PaymentResponse(
            payment_id="pay_test123",
            order_id="ord_test123",
            status="succeeded",
            amount=5000.00,
            confirmation_url="https://example.com"
        )

        # Assert
        assert response.status == "succeeded"

    def test_missing_required_fields_raises_error(self):
        """Test missing required fields raises ValidationError."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PaymentResponse(
                payment_id="pay_test123",
                # Missing other required fields
            )

        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_response_with_float_amount(self):
        """Test response handles float amounts correctly."""
        # Arrange & Act
        response = PaymentResponse(
            payment_id="pay_test123",
            order_id="ord_test123",
            status="pending",
            amount=1234.56,
            confirmation_url="https://example.com"
        )

        # Assert
        assert response.amount == 1234.56
        assert isinstance(response.amount, float)

    def test_response_with_integer_amount(self):
        """Test response converts integer amount to float."""
        # Arrange & Act
        response = PaymentResponse(
            payment_id="pay_test123",
            order_id="ord_test123",
            status="pending",
            amount=1000,
            confirmation_url="https://example.com"
        )

        # Assert
        assert response.amount == 1000.0

    def test_response_to_dict(self):
        """Test converting response to dictionary."""
        # Arrange
        response = PaymentResponse(
            payment_id="pay_test123",
            order_id="ord_test123",
            status="pending",
            amount=2500.00,
            currency="RUB",
            confirmation_url="https://example.com"
        )

        # Act
        data = response.model_dump()

        # Assert
        assert data["payment_id"] == "pay_test123"
        assert data["order_id"] == "ord_test123"
        assert data["status"] == "pending"
        assert data["amount"] == 2500.00
        assert data["currency"] == "RUB"

    def test_response_to_json(self):
        """Test converting response to JSON."""
        # Arrange
        response = PaymentResponse(
            payment_id="pay_test123",
            order_id="ord_test123",
            status="pending",
            amount=2500.00,
            confirmation_url="https://example.com"
        )

        # Act
        json_str = response.model_dump_json()

        # Assert
        assert "pay_test123" in json_str
        assert "ord_test123" in json_str
        assert "pending" in json_str


class TestPaymentStatusResponse:
    """Tests for PaymentStatusResponse model."""

    def test_valid_status_response_pending(self):
        """Test creating status response for pending payment."""
        # Arrange & Act
        response = PaymentStatusResponse(
            payment_id="pay_test123",
            status="pending",
            paid_at=None
        )

        # Assert
        assert response.payment_id == "pay_test123"
        assert response.status == "pending"
        assert response.paid_at is None

    def test_valid_status_response_succeeded(self):
        """Test creating status response for succeeded payment."""
        # Arrange
        paid_at = datetime(2024, 6, 11, 14, 30, 0)

        # Act
        response = PaymentStatusResponse(
            payment_id="pay_test123",
            status="succeeded",
            paid_at=paid_at
        )

        # Assert
        assert response.payment_id == "pay_test123"
        assert response.status == "succeeded"
        assert response.paid_at == paid_at

    def test_status_response_with_failed_status(self):
        """Test creating status response for failed payment."""
        # Arrange & Act
        response = PaymentStatusResponse(
            payment_id="pay_test123",
            status="failed",
            paid_at=None
        )

        # Assert
        assert response.status == "failed"
        assert response.paid_at is None

    def test_status_response_without_paid_at(self):
        """Test paid_at is optional and defaults to None."""
        # Arrange & Act
        response = PaymentStatusResponse(
            payment_id="pay_test123",
            status="pending"
        )

        # Assert
        assert response.paid_at is None

    def test_missing_payment_id_raises_error(self):
        """Test missing payment_id raises ValidationError."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PaymentStatusResponse(status="pending")

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("payment_id",) for error in errors)

    def test_missing_status_raises_error(self):
        """Test missing status raises ValidationError."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PaymentStatusResponse(payment_id="pay_test123")

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("status",) for error in errors)

    def test_status_response_to_dict(self):
        """Test converting status response to dictionary."""
        # Arrange
        paid_at = datetime(2024, 6, 11, 14, 30, 0)
        response = PaymentStatusResponse(
            payment_id="pay_test123",
            status="succeeded",
            paid_at=paid_at
        )

        # Act
        data = response.model_dump()

        # Assert
        assert data["payment_id"] == "pay_test123"
        assert data["status"] == "succeeded"
        assert data["paid_at"] == paid_at

    def test_status_response_with_datetime_string(self):
        """Test creating status response with datetime string."""
        # Arrange & Act
        response = PaymentStatusResponse(
            payment_id="pay_test123",
            status="succeeded",
            paid_at="2024-06-11T14:30:00"
        )

        # Assert
        assert response.paid_at is not None
        assert isinstance(response.paid_at, datetime)


class TestModelAliases:
    """Tests for model aliases (backward compatibility)."""

    def test_payment_create_request_is_alias(self):
        """Test PaymentCreateRequest is alias of InitiatePaymentRequest."""
        # Arrange & Act
        request1 = PaymentCreateRequest(
            order_id="ord_test123",
            payment_method="card"
        )
        request2 = InitiatePaymentRequest(
            order_id="ord_test123",
            payment_method="card"
        )

        # Assert
        assert type(request1) == type(request2)
        assert request1.order_id == request2.order_id
        assert request1.payment_method == request2.payment_method

    def test_payment_create_response_is_alias(self):
        """Test PaymentCreateResponse is alias of PaymentResponse."""
        # Arrange & Act
        response1 = PaymentCreateResponse(
            payment_id="pay_test123",
            order_id="ord_test123",
            status="pending",
            amount=1000.00,
            confirmation_url="https://example.com"
        )
        response2 = PaymentResponse(
            payment_id="pay_test123",
            order_id="ord_test123",
            status="pending",
            amount=1000.00,
            confirmation_url="https://example.com"
        )

        # Assert
        assert type(response1) == type(response2)


class TestModelEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_response_with_zero_amount(self):
        """Test response with zero amount."""
        # Arrange & Act
        response = PaymentResponse(
            payment_id="pay_test123",
            order_id="ord_test123",
            status="pending",
            amount=0.0,
            confirmation_url="https://example.com"
        )

        # Assert
        assert response.amount == 0.0

    def test_response_with_negative_amount(self):
        """Test response with negative amount is accepted by model."""
        # Note: Business logic validation should happen in service layer
        # Arrange & Act
        response = PaymentResponse(
            payment_id="pay_test123",
            order_id="ord_test123",
            status="pending",
            amount=-100.0,
            confirmation_url="https://example.com"
        )

        # Assert
        assert response.amount == -100.0

    def test_response_with_very_large_amount(self):
        """Test response with very large amount."""
        # Arrange & Act
        response = PaymentResponse(
            payment_id="pay_test123",
            order_id="ord_test123",
            status="pending",
            amount=999999999.99,
            confirmation_url="https://example.com"
        )

        # Assert
        assert response.amount == 999999999.99

    def test_request_with_long_order_id(self):
        """Test request with very long order_id."""
        # Arrange
        long_order_id = "ord_" + "a" * 100

        # Act
        request = InitiatePaymentRequest(
            order_id=long_order_id,
            payment_method="card"
        )

        # Assert
        assert request.order_id == long_order_id

    def test_request_with_special_characters_in_order_id(self):
        """Test request with special characters in order_id."""
        # Arrange & Act
        request = InitiatePaymentRequest(
            order_id="ord-test_123.special",
            payment_method="card"
        )

        # Assert
        assert request.order_id == "ord-test_123.special"

    def test_response_with_empty_string_payment_id(self):
        """Test response with empty string payment_id."""
        # Arrange & Act
        response = PaymentResponse(
            payment_id="",
            order_id="ord_test123",
            status="pending",
            amount=1000.00,
            confirmation_url="https://example.com"
        )

        # Assert
        assert response.payment_id == ""

    def test_status_response_with_current_datetime(self):
        """Test status response with current datetime."""
        # Arrange
        now = datetime.utcnow()

        # Act
        response = PaymentStatusResponse(
            payment_id="pay_test123",
            status="succeeded",
            paid_at=now
        )

        # Assert
        assert response.paid_at == now

    def test_response_with_custom_currency(self):
        """Test response with custom currency."""
        # Arrange & Act
        response = PaymentResponse(
            payment_id="pay_test123",
            order_id="ord_test123",
            status="pending",
            amount=1000.00,
            currency="USD",
            confirmation_url="https://example.com"
        )

        # Assert
        assert response.currency == "USD"

    def test_model_immutability_not_enforced(self):
        """Test that models are mutable by default."""
        # Arrange
        request = InitiatePaymentRequest(
            order_id="ord_test123",
            payment_method="card"
        )

        # Act
        request.order_id = "ord_modified"

        # Assert
        assert request.order_id == "ord_modified"
