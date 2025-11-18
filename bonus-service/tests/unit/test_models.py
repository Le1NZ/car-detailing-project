"""Unit tests for Pydantic models in bonus service"""
import pytest
from uuid import UUID
from pydantic import ValidationError

from app.models.bonus import (
    ApplyPromocodeRequest,
    PromocodeResponse,
    SpendBonusesRequest,
    SpendBonusesResponse,
    HealthResponse
)


@pytest.mark.unit
class TestApplyPromocodeRequest:
    """Test ApplyPromocodeRequest model validation"""

    def test_valid_request(self, test_order_id: UUID, valid_promocode: str):
        """Test creating request with valid data"""
        # Arrange & Act
        request = ApplyPromocodeRequest(
            order_id=test_order_id,
            promocode=valid_promocode
        )

        # Assert
        assert request.order_id == test_order_id
        assert request.promocode == valid_promocode

    def test_valid_request_from_dict(self):
        """Test creating request from dictionary"""
        # Arrange
        data = {
            "order_id": "123e4567-e89b-12d3-a456-426614174000",
            "promocode": "SUMMER24"
        }

        # Act
        request = ApplyPromocodeRequest(**data)

        # Assert
        assert isinstance(request.order_id, UUID)
        assert request.promocode == "SUMMER24"

    def test_empty_promocode_rejected(self, test_order_id: UUID):
        """Test that empty promocode is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ApplyPromocodeRequest(
                order_id=test_order_id,
                promocode=""
            )

        # Verify validation error mentions the field
        assert "promocode" in str(exc_info.value)

    def test_invalid_order_id_rejected(self):
        """Test that invalid UUID format is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ApplyPromocodeRequest(
                order_id="not-a-uuid",
                promocode="SUMMER24"
            )

        # Verify validation error mentions UUID
        assert "order_id" in str(exc_info.value)

    def test_missing_fields_rejected(self):
        """Test that missing required fields are rejected"""
        # Test missing order_id
        with pytest.raises(ValidationError):
            ApplyPromocodeRequest(promocode="SUMMER24")

        # Test missing promocode
        with pytest.raises(ValidationError):
            ApplyPromocodeRequest(order_id="123e4567-e89b-12d3-a456-426614174000")


@pytest.mark.unit
class TestPromocodeResponse:
    """Test PromocodeResponse model"""

    def test_valid_response(self, test_order_id: UUID):
        """Test creating response with valid data"""
        # Arrange & Act
        response = PromocodeResponse(
            order_id=test_order_id,
            promocode="SUMMER24",
            status="applied",
            discount_amount=500.0
        )

        # Assert
        assert response.order_id == test_order_id
        assert response.promocode == "SUMMER24"
        assert response.status == "applied"
        assert response.discount_amount == 500.0

    def test_response_serialization(self, test_order_id: UUID):
        """Test response can be serialized to JSON"""
        # Arrange
        response = PromocodeResponse(
            order_id=test_order_id,
            promocode="SUMMER24",
            status="applied",
            discount_amount=500.0
        )

        # Act
        json_data = response.model_dump()

        # Assert
        assert json_data["order_id"] == test_order_id
        assert json_data["promocode"] == "SUMMER24"
        assert json_data["status"] == "applied"
        assert json_data["discount_amount"] == 500.0

    def test_negative_discount_amount_allowed(self, test_order_id: UUID):
        """Test that negative discount amounts are allowed (for flexibility)"""
        # Arrange & Act
        response = PromocodeResponse(
            order_id=test_order_id,
            promocode="TEST",
            status="applied",
            discount_amount=-100.0
        )

        # Assert
        assert response.discount_amount == -100.0


@pytest.mark.unit
class TestSpendBonusesRequest:
    """Test SpendBonusesRequest model validation"""

    def test_valid_request(self, test_order_id: UUID):
        """Test creating request with valid data"""
        # Arrange & Act
        request = SpendBonusesRequest(
            order_id=test_order_id,
            amount=100
        )

        # Assert
        assert request.order_id == test_order_id
        assert request.amount == 100

    def test_zero_amount_rejected(self, test_order_id: UUID):
        """Test that zero amount is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            SpendBonusesRequest(
                order_id=test_order_id,
                amount=0
            )

        # Verify validation error is about amount
        assert "amount" in str(exc_info.value)

    def test_negative_amount_rejected(self, test_order_id: UUID):
        """Test that negative amount is rejected"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            SpendBonusesRequest(
                order_id=test_order_id,
                amount=-100
            )

    def test_large_amount_accepted(self, test_order_id: UUID):
        """Test that large amounts are accepted"""
        # Arrange & Act
        request = SpendBonusesRequest(
            order_id=test_order_id,
            amount=1000000
        )

        # Assert
        assert request.amount == 1000000

    def test_float_amount_converted_to_int(self, test_order_id: UUID):
        """Test that float amounts are converted to int"""
        # Arrange & Act
        request = SpendBonusesRequest(
            order_id=test_order_id,
            amount=100.5
        )

        # Assert
        assert isinstance(request.amount, int)
        assert request.amount == 100


@pytest.mark.unit
class TestSpendBonusesResponse:
    """Test SpendBonusesResponse model"""

    def test_valid_response(self, test_order_id: UUID):
        """Test creating response with valid data"""
        # Arrange & Act
        response = SpendBonusesResponse(
            order_id=test_order_id,
            bonuses_spent=100,
            new_balance=900.0
        )

        # Assert
        assert response.order_id == test_order_id
        assert response.bonuses_spent == 100
        assert response.new_balance == 900.0

    def test_zero_new_balance(self, test_order_id: UUID):
        """Test response with zero new balance"""
        # Arrange & Act
        response = SpendBonusesResponse(
            order_id=test_order_id,
            bonuses_spent=1000,
            new_balance=0.0
        )

        # Assert
        assert response.new_balance == 0.0

    def test_response_to_json(self, test_order_id: UUID):
        """Test response serialization to JSON"""
        # Arrange
        response = SpendBonusesResponse(
            order_id=test_order_id,
            bonuses_spent=100,
            new_balance=900.0
        )

        # Act
        json_str = response.model_dump_json()

        # Assert
        assert "order_id" in json_str
        assert "bonuses_spent" in json_str
        assert "new_balance" in json_str


@pytest.mark.unit
class TestHealthResponse:
    """Test HealthResponse model"""

    def test_valid_health_response(self):
        """Test creating health response"""
        # Arrange & Act
        response = HealthResponse(
            status="healthy",
            service="bonus-service"
        )

        # Assert
        assert response.status == "healthy"
        assert response.service == "bonus-service"

    def test_unhealthy_status(self):
        """Test health response with unhealthy status"""
        # Arrange & Act
        response = HealthResponse(
            status="unhealthy",
            service="bonus-service"
        )

        # Assert
        assert response.status == "unhealthy"

    def test_missing_fields_rejected(self):
        """Test that missing fields are rejected"""
        # Test missing status
        with pytest.raises(ValidationError):
            HealthResponse(service="bonus-service")

        # Test missing service
        with pytest.raises(ValidationError):
            HealthResponse(status="healthy")


@pytest.mark.unit
class TestModelIntegration:
    """Test model integration scenarios"""

    def test_request_response_cycle(self, test_order_id: UUID):
        """Test complete request-response cycle for promocode"""
        # Arrange
        request = ApplyPromocodeRequest(
            order_id=test_order_id,
            promocode="SUMMER24"
        )

        # Act - simulate service processing
        response = PromocodeResponse(
            order_id=request.order_id,
            promocode=request.promocode,
            status="applied",
            discount_amount=500.0
        )

        # Assert
        assert response.order_id == request.order_id
        assert response.promocode == request.promocode

    def test_spend_bonuses_cycle(self, test_order_id: UUID):
        """Test complete request-response cycle for spending bonuses"""
        # Arrange
        request = SpendBonusesRequest(
            order_id=test_order_id,
            amount=100
        )

        # Act - simulate service processing
        response = SpendBonusesResponse(
            order_id=request.order_id,
            bonuses_spent=request.amount,
            new_balance=900.0
        )

        # Assert
        assert response.order_id == request.order_id
        assert response.bonuses_spent == request.amount
