"""
Unit tests for Pydantic models in app.models.car.

Tests cover:
- Model validation (happy path)
- Field validators (VIN, license_plate)
- Invalid data scenarios
- Edge cases
- Field constraints
"""

import pytest
from uuid import UUID
from pydantic import ValidationError

from app.models.car import (
    AddCarRequest,
    CarResponse,
    AddDocumentRequest,
    DocumentResponse
)


@pytest.mark.unit
class TestAddCarRequest:
    """Test suite for AddCarRequest Pydantic model."""

    def test_valid_car_request(self, sample_owner_id: UUID):
        """Test creating AddCarRequest with all valid fields."""
        # Arrange & Act
        request = AddCarRequest(
            owner_id=sample_owner_id,
            license_plate="A123BC799",
            vin="XTA210930V0123456",
            make="Lada",
            model="Vesta",
            year=2021
        )

        # Assert
        assert request.owner_id == sample_owner_id
        assert request.license_plate == "A123BC799"
        assert request.vin == "XTA210930V0123456"
        assert request.make == "Lada"
        assert request.model == "Vesta"
        assert request.year == 2021

    def test_vin_uppercase_conversion(self, sample_owner_id: UUID):
        """Test that VIN is automatically converted to uppercase."""
        # Arrange & Act
        request = AddCarRequest(
            owner_id=sample_owner_id,
            license_plate="TEST123",
            vin="lowercase12345678",  # Exactly 17 chars, lowercase
            make="TestMake",
            model="TestModel",
            year=2020
        )

        # Assert
        assert request.vin == "LOWERCASE12345678"
        assert request.vin.isupper()

    def test_license_plate_uppercase_and_strip(self, sample_owner_id: UUID):
        """Test that license plate is stripped and converted to uppercase."""
        # Arrange & Act
        request = AddCarRequest(
            owner_id=sample_owner_id,
            license_plate="  a999bc777  ",  # spaces and lowercase
            vin="12345678901234567",
            make="Test",
            model="Car",
            year=2020
        )

        # Assert
        assert request.license_plate == "A999BC777"
        assert request.license_plate.isupper()
        assert " " not in request.license_plate

    def test_vin_must_be_alphanumeric(self, sample_owner_id: UUID):
        """Test that VIN validation rejects non-alphanumeric characters."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AddCarRequest(
                owner_id=sample_owner_id,
                license_plate="TEST",
                vin="VIN-WITH-DASHES--",  # Exactly 17 chars with dashes
                make="Test",
                model="Car",
                year=2020
            )

        # Verify error message
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("vin",) and
            "alphanumeric" in error["msg"].lower()
            for error in errors
        )

    def test_vin_length_exactly_17_chars(self, sample_owner_id: UUID):
        """Test that VIN must be exactly 17 characters."""
        # Test too short
        with pytest.raises(ValidationError) as exc_info:
            AddCarRequest(
                owner_id=sample_owner_id,
                license_plate="TEST",
                vin="SHORT",
                make="Test",
                model="Car",
                year=2020
            )
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("vin",) for error in errors)

        # Test too long
        with pytest.raises(ValidationError) as exc_info:
            AddCarRequest(
                owner_id=sample_owner_id,
                license_plate="TEST",
                vin="TOOLONGVIN12345678901234567",
                make="Test",
                model="Car",
                year=2020
            )
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("vin",) for error in errors)

    def test_year_minimum_boundary(self, sample_owner_id: UUID):
        """Test year minimum boundary (1900)."""
        # Valid: exactly 1900
        request = AddCarRequest(
            owner_id=sample_owner_id,
            license_plate="OLD",
            vin="12345678901234567",
            make="Ford",
            model="Model T",
            year=1900
        )
        assert request.year == 1900

        # Invalid: 1899
        with pytest.raises(ValidationError) as exc_info:
            AddCarRequest(
                owner_id=sample_owner_id,
                license_plate="TOOLLD",
                vin="12345678901234567",
                make="Ancient",
                model="Car",
                year=1899
            )
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("year",) and
            error["type"] == "greater_than_equal"
            for error in errors
        )

    def test_year_maximum_boundary(self, sample_owner_id: UUID):
        """Test year maximum boundary (2025)."""
        # Valid: exactly 2025
        request = AddCarRequest(
            owner_id=sample_owner_id,
            license_plate="NEW",
            vin="98765432109876543",
            make="Tesla",
            model="Model Y",
            year=2025
        )
        assert request.year == 2025

        # Invalid: 2026
        with pytest.raises(ValidationError) as exc_info:
            AddCarRequest(
                owner_id=sample_owner_id,
                license_plate="FUTURE",
                vin="98765432109876543",
                make="Future",
                model="Car",
                year=2026
            )
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("year",) and
            error["type"] == "less_than_equal"
            for error in errors
        )

    def test_license_plate_length_constraints(self, sample_owner_id: UUID):
        """Test license plate length constraints (1-20 chars)."""
        # Valid: 1 character
        request = AddCarRequest(
            owner_id=sample_owner_id,
            license_plate="A",
            vin="12345678901234567",
            make="Test",
            model="Car",
            year=2020
        )
        assert request.license_plate == "A"

        # Valid: 20 characters
        request = AddCarRequest(
            owner_id=sample_owner_id,
            license_plate="12345678901234567890",
            vin="12345678901234568",
            make="Test",
            model="Car",
            year=2020
        )
        assert len(request.license_plate) == 20

        # Invalid: empty string
        with pytest.raises(ValidationError) as exc_info:
            AddCarRequest(
                owner_id=sample_owner_id,
                license_plate="",
                vin="12345678901234567",
                make="Test",
                model="Car",
                year=2020
            )
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("license_plate",) for error in errors)

    def test_make_and_model_length_constraints(self, sample_owner_id: UUID):
        """Test make and model length constraints (1-50 chars)."""
        # Valid: 1 character make and model
        request = AddCarRequest(
            owner_id=sample_owner_id,
            license_plate="SHORT",
            vin="12345678901234567",
            make="A",
            model="B",
            year=2020
        )
        assert request.make == "A"
        assert request.model == "B"

        # Valid: 50 character make and model
        long_string = "A" * 50
        request = AddCarRequest(
            owner_id=sample_owner_id,
            license_plate="LONG",
            vin="12345678901234568",
            make=long_string,
            model=long_string,
            year=2020
        )
        assert len(request.make) == 50
        assert len(request.model) == 50

        # Invalid: empty make
        with pytest.raises(ValidationError) as exc_info:
            AddCarRequest(
                owner_id=sample_owner_id,
                license_plate="TEST",
                vin="12345678901234567",
                make="",
                model="Model",
                year=2020
            )
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("make",) for error in errors)

    def test_missing_required_fields(self):
        """Test that all required fields must be provided."""
        with pytest.raises(ValidationError) as exc_info:
            AddCarRequest()

        errors = exc_info.value.errors()
        required_fields = {"owner_id", "license_plate", "vin", "make", "model", "year"}
        error_fields = {error["loc"][0] for error in errors}
        assert required_fields == error_fields


@pytest.mark.unit
class TestCarResponse:
    """Test suite for CarResponse Pydantic model."""

    def test_valid_car_response(self, sample_car_id: UUID):
        """Test creating CarResponse with all valid fields."""
        # Arrange & Act
        response = CarResponse(
            car_id=sample_car_id,
            license_plate="A123BC799",
            vin="XTA210930V0123456",
            make="Lada",
            model="Vesta",
            year=2021
        )

        # Assert
        assert response.car_id == sample_car_id
        assert response.license_plate == "A123BC799"
        assert response.vin == "XTA210930V0123456"
        assert response.make == "Lada"
        assert response.model == "Vesta"
        assert response.year == 2021

    def test_car_response_serialization(self, sample_car_id: UUID):
        """Test that CarResponse can be serialized to dict/JSON."""
        # Arrange
        response = CarResponse(
            car_id=sample_car_id,
            license_plate="TEST123",
            vin="12345678901234567",
            make="Test",
            model="Car",
            year=2020
        )

        # Act
        response_dict = response.model_dump()
        response_json = response.model_dump_json()

        # Assert
        assert isinstance(response_dict, dict)
        assert response_dict["car_id"] == sample_car_id
        assert isinstance(response_json, str)
        assert str(sample_car_id) in response_json


@pytest.mark.unit
class TestAddDocumentRequest:
    """Test suite for AddDocumentRequest Pydantic model."""

    def test_valid_document_request_with_file(self):
        """Test creating AddDocumentRequest with file."""
        # Arrange & Act
        request = AddDocumentRequest(
            document_type="Insurance",
            file="insurance.pdf"
        )

        # Assert
        assert request.document_type == "Insurance"
        assert request.file == "insurance.pdf"

    def test_valid_document_request_without_file(self):
        """Test creating AddDocumentRequest without file (optional)."""
        # Arrange & Act
        request = AddDocumentRequest(
            document_type="Registration"
        )

        # Assert
        assert request.document_type == "Registration"
        assert request.file is None

    def test_document_type_length_constraint(self):
        """Test document_type length constraint (min 1 char)."""
        # Valid: 1 character
        request = AddDocumentRequest(document_type="A")
        assert request.document_type == "A"

        # Valid: 100 characters
        long_type = "A" * 100
        request = AddDocumentRequest(document_type=long_type)
        assert len(request.document_type) == 100

        # Invalid: empty string
        with pytest.raises(ValidationError) as exc_info:
            AddDocumentRequest(document_type="")

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("document_type",) for error in errors)

    def test_missing_required_document_type(self):
        """Test that document_type is required."""
        with pytest.raises(ValidationError) as exc_info:
            AddDocumentRequest(file="test.pdf")

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("document_type",) for error in errors)


@pytest.mark.unit
class TestDocumentResponse:
    """Test suite for DocumentResponse Pydantic model."""

    def test_valid_document_response(
        self,
        sample_car_id: UUID,
        sample_document_id: UUID
    ):
        """Test creating DocumentResponse with all valid fields."""
        # Arrange & Act
        response = DocumentResponse(
            car_id=sample_car_id,
            document_id=sample_document_id,
            document_type="Insurance",
            status="pending"
        )

        # Assert
        assert response.car_id == sample_car_id
        assert response.document_id == sample_document_id
        assert response.document_type == "Insurance"
        assert response.status == "pending"

    def test_document_response_serialization(
        self,
        sample_car_id: UUID,
        sample_document_id: UUID
    ):
        """Test that DocumentResponse can be serialized to dict/JSON."""
        # Arrange
        response = DocumentResponse(
            car_id=sample_car_id,
            document_id=sample_document_id,
            document_type="Test",
            status="approved"
        )

        # Act
        response_dict = response.model_dump()
        response_json = response.model_dump_json()

        # Assert
        assert isinstance(response_dict, dict)
        assert response_dict["car_id"] == sample_car_id
        assert response_dict["document_id"] == sample_document_id
        assert isinstance(response_json, str)
        assert str(sample_car_id) in response_json

    def test_all_fields_required(self):
        """Test that all fields in DocumentResponse are required."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentResponse()

        errors = exc_info.value.errors()
        required_fields = {"car_id", "document_id", "document_type", "status"}
        error_fields = {error["loc"][0] for error in errors}
        assert required_fields == error_fields


@pytest.mark.unit
class TestModelEdgeCases:
    """Test suite for edge cases and boundary conditions across all models."""

    def test_uuid_string_conversion(self, sample_owner_id: UUID):
        """Test that UUID fields accept both UUID objects and valid UUID strings."""
        # Using UUID object
        request1 = AddCarRequest(
            owner_id=sample_owner_id,
            license_plate="TEST1",
            vin="12345678901234567",
            make="Test",
            model="Car",
            year=2020
        )
        assert isinstance(request1.owner_id, UUID)

        # Using UUID string
        request2 = AddCarRequest(
            owner_id="550e8400-e29b-41d4-a716-446655440000",
            license_plate="TEST2",
            vin="12345678901234568",
            make="Test",
            model="Car",
            year=2020
        )
        assert isinstance(request2.owner_id, UUID)
        assert request2.owner_id == sample_owner_id

    def test_invalid_uuid_format(self):
        """Test that invalid UUID strings are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            AddCarRequest(
                owner_id="not-a-valid-uuid",
                license_plate="TEST",
                vin="12345678901234567",
                make="Test",
                model="Car",
                year=2020
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("owner_id",) for error in errors)

    def test_special_characters_in_license_plate(self, sample_owner_id: UUID):
        """Test license plates with special characters (allowed after strip/uppercase)."""
        # Cyrillic characters
        request = AddCarRequest(
            owner_id=sample_owner_id,
            license_plate="А123БВ",
            vin="12345678901234567",
            make="Test",
            model="Car",
            year=2020
        )
        assert request.license_plate == "А123БВ"

    def test_numeric_only_vin(self, sample_owner_id: UUID):
        """Test VIN with only numeric characters."""
        request = AddCarRequest(
            owner_id=sample_owner_id,
            license_plate="NUM",
            vin="12345678901234567",
            make="Test",
            model="Car",
            year=2020
        )
        assert request.vin == "12345678901234567"
        assert request.vin.isdigit()

    def test_alpha_only_vin(self, sample_owner_id: UUID):
        """Test VIN with only alphabetic characters."""
        request = AddCarRequest(
            owner_id=sample_owner_id,
            license_plate="ALPHA",
            vin="ABCDEFGHIJKLMNOPQ",
            make="Test",
            model="Car",
            year=2020
        )
        assert request.vin == "ABCDEFGHIJKLMNOPQ"
        assert request.vin.isalpha()
