"""
Unit tests for Pydantic models
"""
import pytest
from datetime import date
from uuid import UUID, uuid4
from pydantic import ValidationError
from app.models.fine import Fine, FineResponse, PayFineRequest, PaymentResponse


class TestFineModel:
    """Test the Fine model"""

    def test_create_fine_with_valid_data(self):
        """Test creating a Fine instance with valid data"""
        fine_id = uuid4()
        fine = Fine(
            fine_id=fine_id,
            license_plate="А123БВ799",
            amount=500.00,
            description="Превышение скорости",
            date=date(2024, 5, 15),
            paid=False
        )

        assert fine.fine_id == fine_id
        assert fine.license_plate == "А123БВ799"
        assert fine.amount == 500.00
        assert fine.description == "Превышение скорости"
        assert fine.date == date(2024, 5, 15)
        assert fine.paid is False

    def test_fine_default_paid_is_false(self):
        """Test that paid defaults to False"""
        fine = Fine(
            fine_id=uuid4(),
            license_plate="А123БВ799",
            amount=500.00,
            description="Превышение скорости",
            date=date(2024, 5, 15)
        )

        assert fine.paid is False

    def test_fine_with_paid_true(self):
        """Test creating a Fine with paid=True"""
        fine = Fine(
            fine_id=uuid4(),
            license_plate="А123БВ799",
            amount=500.00,
            description="Превышение скорости",
            date=date(2024, 5, 15),
            paid=True
        )

        assert fine.paid is True

    def test_fine_amount_can_be_float(self):
        """Test that amount accepts float values"""
        fine = Fine(
            fine_id=uuid4(),
            license_plate="А123БВ799",
            amount=1234.56,
            description="Превышение скорости",
            date=date(2024, 5, 15)
        )

        assert fine.amount == 1234.56

    def test_fine_amount_can_be_int(self):
        """Test that amount accepts integer values"""
        fine = Fine(
            fine_id=uuid4(),
            license_plate="А123БВ799",
            amount=500,
            description="Превышение скорости",
            date=date(2024, 5, 15)
        )

        assert fine.amount == 500.0

    def test_fine_invalid_uuid_raises_error(self):
        """Test that invalid UUID raises ValidationError"""
        with pytest.raises(ValidationError):
            Fine(
                fine_id="not-a-uuid",
                license_plate="А123БВ799",
                amount=500.00,
                description="Превышение скорости",
                date=date(2024, 5, 15)
            )

    def test_fine_invalid_date_raises_error(self):
        """Test that invalid date raises ValidationError"""
        with pytest.raises(ValidationError):
            Fine(
                fine_id=uuid4(),
                license_plate="А123БВ799",
                amount=500.00,
                description="Превышение скорости",
                date="not-a-date"
            )

    def test_fine_missing_required_field_raises_error(self):
        """Test that missing required fields raise ValidationError"""
        with pytest.raises(ValidationError):
            Fine(
                fine_id=uuid4(),
                license_plate="А123БВ799",
                amount=500.00,
                date=date(2024, 5, 15)
                # Missing description
            )


class TestFineResponseModel:
    """Test the FineResponse model"""

    def test_create_fine_response_with_valid_data(self):
        """Test creating a FineResponse instance with valid data"""
        fine_id = uuid4()
        response = FineResponse(
            fine_id=fine_id,
            amount=500.00,
            description="Превышение скорости",
            date=date(2024, 5, 15)
        )

        assert response.fine_id == fine_id
        assert response.amount == 500.00
        assert response.description == "Превышение скорости"
        assert response.date == date(2024, 5, 15)

    def test_fine_response_no_paid_field(self):
        """Test that FineResponse does not have paid field"""
        response = FineResponse(
            fine_id=uuid4(),
            amount=500.00,
            description="Превышение скорости",
            date=date(2024, 5, 15)
        )

        assert not hasattr(response, 'paid')

    def test_fine_response_invalid_uuid_raises_error(self):
        """Test that invalid UUID raises ValidationError"""
        with pytest.raises(ValidationError):
            FineResponse(
                fine_id="not-a-uuid",
                amount=500.00,
                description="Превышение скорости",
                date=date(2024, 5, 15)
            )


class TestPayFineRequestModel:
    """Test the PayFineRequest model"""

    def test_create_pay_fine_request_with_valid_data(self):
        """Test creating a PayFineRequest instance with valid data"""
        request = PayFineRequest(payment_method_id="card_123")

        assert request.payment_method_id == "card_123"

    def test_pay_fine_request_accepts_various_formats(self):
        """Test that payment_method_id accepts various string formats"""
        test_values = [
            "card_123",
            "bank_account_456",
            "wallet_789",
            "1234567890"
        ]

        for value in test_values:
            request = PayFineRequest(payment_method_id=value)
            assert request.payment_method_id == value

    def test_pay_fine_request_missing_field_raises_error(self):
        """Test that missing payment_method_id raises ValidationError"""
        with pytest.raises(ValidationError):
            PayFineRequest()

    def test_pay_fine_request_empty_string_is_valid(self):
        """Test that empty string is technically valid"""
        request = PayFineRequest(payment_method_id="")
        assert request.payment_method_id == ""


class TestPaymentResponseModel:
    """Test the PaymentResponse model"""

    def test_create_payment_response_with_valid_data(self):
        """Test creating a PaymentResponse instance with valid data"""
        payment_id = uuid4()
        fine_id = uuid4()

        response = PaymentResponse(
            payment_id=payment_id,
            fine_id=fine_id,
            status="paid"
        )

        assert response.payment_id == payment_id
        assert response.fine_id == fine_id
        assert response.status == "paid"

    def test_payment_response_accepts_various_statuses(self):
        """Test that status accepts various string values"""
        test_statuses = ["paid", "pending", "failed", "processing"]

        for status in test_statuses:
            response = PaymentResponse(
                payment_id=uuid4(),
                fine_id=uuid4(),
                status=status
            )
            assert response.status == status

    def test_payment_response_invalid_uuid_raises_error(self):
        """Test that invalid UUID raises ValidationError"""
        with pytest.raises(ValidationError):
            PaymentResponse(
                payment_id="not-a-uuid",
                fine_id=uuid4(),
                status="paid"
            )

    def test_payment_response_missing_required_field_raises_error(self):
        """Test that missing required fields raise ValidationError"""
        with pytest.raises(ValidationError):
            PaymentResponse(
                payment_id=uuid4(),
                fine_id=uuid4()
                # Missing status
            )


class TestModelSerialization:
    """Test model serialization and deserialization"""

    def test_fine_to_dict(self):
        """Test converting Fine to dictionary"""
        fine_id = uuid4()
        fine = Fine(
            fine_id=fine_id,
            license_plate="А123БВ799",
            amount=500.00,
            description="Превышение скорости",
            date=date(2024, 5, 15),
            paid=False
        )

        fine_dict = fine.model_dump()

        assert fine_dict["fine_id"] == fine_id
        assert fine_dict["license_plate"] == "А123БВ799"
        assert fine_dict["amount"] == 500.00
        assert fine_dict["paid"] is False

    def test_fine_response_to_json(self):
        """Test converting FineResponse to JSON"""
        response = FineResponse(
            fine_id=uuid4(),
            amount=500.00,
            description="Превышение скорости",
            date=date(2024, 5, 15)
        )

        json_str = response.model_dump_json()
        assert isinstance(json_str, str)
        assert "fine_id" in json_str
        assert "amount" in json_str

    def test_payment_response_to_dict(self):
        """Test converting PaymentResponse to dictionary"""
        payment_id = uuid4()
        fine_id = uuid4()

        response = PaymentResponse(
            payment_id=payment_id,
            fine_id=fine_id,
            status="paid"
        )

        response_dict = response.model_dump()

        assert response_dict["payment_id"] == payment_id
        assert response_dict["fine_id"] == fine_id
        assert response_dict["status"] == "paid"
