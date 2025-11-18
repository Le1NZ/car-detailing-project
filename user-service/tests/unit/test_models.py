"""
Unit tests for Pydantic models.

Tests validation logic for request and response models:
- RegisterRequest validation
- LoginRequest validation
- Response model serialization
"""

import pytest
from datetime import datetime
from uuid import uuid4
from pydantic import ValidationError

from app.models.user import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse
)


class TestRegisterRequestValidation:
    """Test RegisterRequest model validation."""

    def test_register_request_valid_data(self, sample_user_data):
        """Test RegisterRequest with valid data."""
        # Arrange & Act
        request = RegisterRequest(**sample_user_data)

        # Assert
        assert request.email == sample_user_data["email"]
        assert request.password == sample_user_data["password"]
        assert request.full_name == sample_user_data["full_name"]
        assert request.phone_number == sample_user_data["phone_number"]

    def test_register_request_password_minimum_length(self):
        """Test that password must be at least 8 characters."""
        # Arrange
        data = {
            "email": "test@example.com",
            "password": "1234567",  # Only 7 characters
            "full_name": "Test User",
            "phone_number": "+79991234567"
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(**data)

        # Verify the error is about password length
        errors = exc_info.value.errors()
        assert any("password" in str(error) for error in errors)

    def test_register_request_password_exactly_8_characters(self):
        """Test that password with exactly 8 characters is valid."""
        # Arrange
        data = {
            "email": "test@example.com",
            "password": "12345678",  # Exactly 8 characters
            "full_name": "Test User",
            "phone_number": "+79991234567"
        }

        # Act
        request = RegisterRequest(**data)

        # Assert
        assert request.password == "12345678"

    def test_register_request_invalid_email(self):
        """Test that invalid email raises ValidationError."""
        # Arrange
        data = {
            "email": "not-an-email",
            "password": "password123",
            "full_name": "Test User",
            "phone_number": "+79991234567"
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(**data)

        # Verify the error is about email
        errors = exc_info.value.errors()
        assert any("email" in error["loc"] for error in errors)

    def test_register_request_missing_email(self):
        """Test that missing email raises ValidationError."""
        # Arrange
        data = {
            "password": "password123",
            "full_name": "Test User",
            "phone_number": "+79991234567"
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(**data)

        errors = exc_info.value.errors()
        assert any("email" in error["loc"] for error in errors)

    def test_register_request_missing_password(self):
        """Test that missing password raises ValidationError."""
        # Arrange
        data = {
            "email": "test@example.com",
            "full_name": "Test User",
            "phone_number": "+79991234567"
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(**data)

        errors = exc_info.value.errors()
        assert any("password" in error["loc"] for error in errors)

    def test_register_request_missing_full_name(self):
        """Test that missing full_name raises ValidationError."""
        # Arrange
        data = {
            "email": "test@example.com",
            "password": "password123",
            "phone_number": "+79991234567"
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(**data)

        errors = exc_info.value.errors()
        assert any("full_name" in error["loc"] for error in errors)

    def test_register_request_missing_phone_number(self):
        """Test that missing phone_number raises ValidationError."""
        # Arrange
        data = {
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(**data)

        errors = exc_info.value.errors()
        assert any("phone_number" in error["loc"] for error in errors)

    def test_register_request_empty_full_name(self):
        """Test that empty full_name raises ValidationError."""
        # Arrange
        data = {
            "email": "test@example.com",
            "password": "password123",
            "full_name": "",
            "phone_number": "+79991234567"
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(**data)

        errors = exc_info.value.errors()
        assert any("full_name" in error["loc"] for error in errors)

    def test_register_request_special_characters_in_password(self):
        """Test that password with special characters is valid."""
        # Arrange
        data = {
            "email": "test@example.com",
            "password": "p@$$w0rd!#%",
            "full_name": "Test User",
            "phone_number": "+79991234567"
        }

        # Act
        request = RegisterRequest(**data)

        # Assert
        assert request.password == "p@$$w0rd!#%"

    def test_register_request_unicode_in_full_name(self):
        """Test that Unicode characters in full_name are valid."""
        # Arrange
        data = {
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Иванов Петр Сергеевич",
            "phone_number": "+79991234567"
        }

        # Act
        request = RegisterRequest(**data)

        # Assert
        assert request.full_name == "Иванов Петр Сергеевич"


class TestLoginRequestValidation:
    """Test LoginRequest model validation."""

    def test_login_request_valid_data(self):
        """Test LoginRequest with valid data."""
        # Arrange
        data = {
            "email": "test@example.com",
            "password": "password123"
        }

        # Act
        request = LoginRequest(**data)

        # Assert
        assert request.email == "test@example.com"
        assert request.password == "password123"

    def test_login_request_invalid_email(self):
        """Test that invalid email raises ValidationError."""
        # Arrange
        data = {
            "email": "not-an-email",
            "password": "password123"
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(**data)

        errors = exc_info.value.errors()
        assert any("email" in error["loc"] for error in errors)

    def test_login_request_missing_email(self):
        """Test that missing email raises ValidationError."""
        # Arrange
        data = {
            "password": "password123"
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(**data)

        errors = exc_info.value.errors()
        assert any("email" in error["loc"] for error in errors)

    def test_login_request_missing_password(self):
        """Test that missing password raises ValidationError."""
        # Arrange
        data = {
            "email": "test@example.com"
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(**data)

        errors = exc_info.value.errors()
        assert any("password" in error["loc"] for error in errors)

    def test_login_request_empty_password(self):
        """Test that empty password is still accepted by model (service validates)."""
        # Arrange
        data = {
            "email": "test@example.com",
            "password": ""
        }

        # Act
        request = LoginRequest(**data)

        # Assert - model accepts it, service layer will validate
        assert request.password == ""


class TestRegisterResponseModel:
    """Test RegisterResponse model."""

    def test_register_response_creation(self):
        """Test creating RegisterResponse with valid data."""
        # Arrange
        user_id = uuid4()
        created_at = datetime.now()

        # Act
        response = RegisterResponse(
            user_id=user_id,
            email="test@example.com",
            full_name="Test User",
            created_at=created_at
        )

        # Assert
        assert response.user_id == user_id
        assert response.email == "test@example.com"
        assert response.full_name == "Test User"
        assert response.created_at == created_at

    def test_register_response_from_attributes(self, sample_user):
        """Test creating RegisterResponse from ORM model."""
        # Act
        response = RegisterResponse.model_validate(sample_user)

        # Assert
        assert response.user_id == sample_user.id
        assert response.email == sample_user.email
        assert response.full_name == sample_user.full_name
        assert response.created_at == sample_user.created_at

    def test_register_response_serialization(self):
        """Test that RegisterResponse can be serialized to dict."""
        # Arrange
        user_id = uuid4()
        created_at = datetime.now()
        response = RegisterResponse(
            user_id=user_id,
            email="test@example.com",
            full_name="Test User",
            created_at=created_at
        )

        # Act
        response_dict = response.model_dump()

        # Assert
        assert "user_id" in response_dict
        assert "email" in response_dict
        assert "full_name" in response_dict
        assert "created_at" in response_dict
        assert response_dict["email"] == "test@example.com"


class TestLoginResponseModel:
    """Test LoginResponse model."""

    def test_login_response_creation(self):
        """Test creating LoginResponse with valid data."""
        # Arrange & Act
        response = LoginResponse(
            access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            token_type="bearer",
            expires_in=3600
        )

        # Assert
        assert response.access_token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        assert response.token_type == "bearer"
        assert response.expires_in == 3600

    def test_login_response_default_token_type(self):
        """Test that token_type defaults to 'bearer'."""
        # Arrange & Act
        response = LoginResponse(
            access_token="token123",
            expires_in=3600
        )

        # Assert
        assert response.token_type == "bearer"

    def test_login_response_serialization(self):
        """Test that LoginResponse can be serialized to dict."""
        # Arrange
        response = LoginResponse(
            access_token="token123",
            token_type="bearer",
            expires_in=3600
        )

        # Act
        response_dict = response.model_dump()

        # Assert
        assert "access_token" in response_dict
        assert "token_type" in response_dict
        assert "expires_in" in response_dict
        assert response_dict["access_token"] == "token123"
        assert response_dict["expires_in"] == 3600

    def test_login_response_missing_access_token(self):
        """Test that missing access_token raises ValidationError."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            LoginResponse(expires_in=3600)

        errors = exc_info.value.errors()
        assert any("access_token" in error["loc"] for error in errors)

    def test_login_response_missing_expires_in(self):
        """Test that missing expires_in raises ValidationError."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            LoginResponse(access_token="token123")

        errors = exc_info.value.errors()
        assert any("expires_in" in error["loc"] for error in errors)
