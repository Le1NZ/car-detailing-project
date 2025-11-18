"""
Unit tests for UserService.

Tests all business logic in the service layer with mocked dependencies.
Repository and database operations are mocked to ensure complete isolation.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.services.user_service import UserService
from app.models.user import RegisterRequest, LoginRequest
from app.repositories.db_user_repo import UserRepository


class TestUserServiceRegisterUser:
    """Test UserService.register_user method."""

    @pytest.mark.asyncio
    async def test_register_user_success(self, mock_db_session, sample_user_data, sample_user):
        """Test successful user registration."""
        # Arrange
        request = RegisterRequest(**sample_user_data)

        with patch.object(UserRepository, 'check_email_exists', return_value=False), \
             patch.object(UserRepository, 'check_phone_exists', return_value=False), \
             patch.object(UserRepository, 'create_user', return_value=sample_user):

            # Act
            response = await UserService.register_user(mock_db_session, request)

            # Assert
            assert response.user_id == sample_user.id
            assert response.email == sample_user.email
            assert response.full_name == sample_user.full_name
            assert response.created_at == sample_user.created_at

    @pytest.mark.asyncio
    async def test_register_user_hashes_password(self, mock_db_session, sample_user_data, sample_user):
        """Test that password is hashed before storing."""
        # Arrange
        request = RegisterRequest(**sample_user_data)
        plain_password = sample_user_data["password"]

        with patch.object(UserRepository, 'check_email_exists', return_value=False), \
             patch.object(UserRepository, 'check_phone_exists', return_value=False), \
             patch.object(UserRepository, 'create_user', return_value=sample_user) as mock_create:

            # Act
            await UserService.register_user(mock_db_session, request)

            # Assert
            # Verify create_user was called
            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args[1]

            # Verify password_hash is different from plain password
            assert 'password_hash' in call_kwargs
            assert call_kwargs['password_hash'] != plain_password
            assert len(call_kwargs['password_hash']) > 0

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email_raises_409(self, mock_db_session, sample_user_data):
        """Test that duplicate email raises HTTP 409 Conflict."""
        # Arrange
        request = RegisterRequest(**sample_user_data)

        with patch.object(UserRepository, 'check_email_exists', return_value=True):

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await UserService.register_user(mock_db_session, request)

            assert exc_info.value.status_code == 409
            assert "Email already registered" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_register_user_duplicate_phone_raises_409(self, mock_db_session, sample_user_data):
        """Test that duplicate phone number raises HTTP 409 Conflict."""
        # Arrange
        request = RegisterRequest(**sample_user_data)

        with patch.object(UserRepository, 'check_email_exists', return_value=False), \
             patch.object(UserRepository, 'check_phone_exists', return_value=True):

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await UserService.register_user(mock_db_session, request)

            assert exc_info.value.status_code == 409
            assert "Phone number already registered" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_register_user_integrity_error_raises_409(self, mock_db_session, sample_user_data):
        """Test that IntegrityError from database raises HTTP 409."""
        # Arrange
        request = RegisterRequest(**sample_user_data)

        with patch.object(UserRepository, 'check_email_exists', return_value=False), \
             patch.object(UserRepository, 'check_phone_exists', return_value=False), \
             patch.object(UserRepository, 'create_user', side_effect=IntegrityError(
                 "duplicate key", params={}, orig=Exception()
             )):

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await UserService.register_user(mock_db_session, request)

            assert exc_info.value.status_code == 409
            assert "Email or phone number already registered" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_register_user_checks_email_before_phone(self, mock_db_session, sample_user_data):
        """Test that email uniqueness is checked before phone."""
        # Arrange
        request = RegisterRequest(**sample_user_data)

        with patch.object(UserRepository, 'check_email_exists', return_value=True) as mock_email, \
             patch.object(UserRepository, 'check_phone_exists', return_value=False) as mock_phone:

            # Act & Assert
            with pytest.raises(HTTPException):
                await UserService.register_user(mock_db_session, request)

            # Verify email check was called but phone check was not
            mock_email.assert_called_once()
            mock_phone.assert_not_called()

    @pytest.mark.asyncio
    async def test_register_user_with_minimum_valid_password(self, mock_db_session, sample_user):
        """Test registration with minimum valid password length."""
        # Arrange
        user_data = {
            "email": "test@example.com",
            "password": "12345678",  # Minimum 8 characters
            "full_name": "Test User",
            "phone_number": "+79991234567"
        }
        request = RegisterRequest(**user_data)

        with patch.object(UserRepository, 'check_email_exists', return_value=False), \
             patch.object(UserRepository, 'check_phone_exists', return_value=False), \
             patch.object(UserRepository, 'create_user', return_value=sample_user):

            # Act
            response = await UserService.register_user(mock_db_session, request)

            # Assert
            assert response is not None
            assert response.user_id == sample_user.id


class TestUserServiceAuthenticateUser:
    """Test UserService.authenticate_user method."""

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, mock_db_session, sample_user):
        """Test successful user authentication."""
        # Arrange
        email = "test@example.com"
        password = "password123"

        # Mock password verification to return True
        with patch.object(UserRepository, 'get_user_by_email', return_value=sample_user), \
             patch('app.services.user_service._verify_password', return_value=True):

            # Act
            response = await UserService.authenticate_user(mock_db_session, email, password)

            # Assert
            assert response is not None
            assert response.access_token is not None
            assert response.token_type == "bearer"
            assert response.expires_in == 3600
            assert isinstance(response.access_token, str)
            assert len(response.access_token) > 0

    @pytest.mark.asyncio
    async def test_authenticate_user_generates_jwt_token(self, mock_db_session, sample_user):
        """Test that authentication generates a valid JWT token."""
        # Arrange
        email = "test@example.com"
        password = "password123"

        with patch.object(UserRepository, 'get_user_by_email', return_value=sample_user), \
             patch('app.services.user_service._verify_password', return_value=True):

            # Act
            response = await UserService.authenticate_user(mock_db_session, email, password)

            # Assert
            # JWT tokens have 3 parts separated by dots
            token_parts = response.access_token.split('.')
            assert len(token_parts) == 3

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_email_raises_401(self, mock_db_session):
        """Test that non-existent email raises HTTP 401 Unauthorized."""
        # Arrange
        email = "nonexistent@example.com"
        password = "password123"

        with patch.object(UserRepository, 'get_user_by_email', return_value=None):

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await UserService.authenticate_user(mock_db_session, email, password)

            assert exc_info.value.status_code == 401
            assert "Incorrect email or password" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password_raises_401(self, mock_db_session, sample_user):
        """Test that incorrect password raises HTTP 401 Unauthorized."""
        # Arrange
        email = "test@example.com"
        password = "wrongpassword"

        with patch.object(UserRepository, 'get_user_by_email', return_value=sample_user), \
             patch('app.services.user_service._verify_password', return_value=False):

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await UserService.authenticate_user(mock_db_session, email, password)

            assert exc_info.value.status_code == 401
            assert "Incorrect email or password" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_authenticate_user_missing_email_raises_422(self, mock_db_session):
        """Test that missing email raises HTTP 422 Unprocessable Entity."""
        # Arrange
        email = ""
        password = "password123"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await UserService.authenticate_user(mock_db_session, email, password)

        assert exc_info.value.status_code == 422
        assert "Email and password are required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_authenticate_user_missing_password_raises_422(self, mock_db_session):
        """Test that missing password raises HTTP 422 Unprocessable Entity."""
        # Arrange
        email = "test@example.com"
        password = ""

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await UserService.authenticate_user(mock_db_session, email, password)

        assert exc_info.value.status_code == 422
        assert "Email and password are required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_authenticate_user_none_email_raises_422(self, mock_db_session):
        """Test that None email raises HTTP 422."""
        # Arrange
        email = None
        password = "password123"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await UserService.authenticate_user(mock_db_session, email, password)

        assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_authenticate_user_none_password_raises_422(self, mock_db_session):
        """Test that None password raises HTTP 422."""
        # Arrange
        email = "test@example.com"
        password = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await UserService.authenticate_user(mock_db_session, email, password)

        assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_authenticate_user_calls_get_user_by_email(self, mock_db_session, sample_user):
        """Test that authenticate_user calls repository method correctly."""
        # Arrange
        email = "test@example.com"
        password = "password123"

        with patch.object(UserRepository, 'get_user_by_email', return_value=sample_user) as mock_get, \
             patch('app.services.user_service._verify_password', return_value=True):

            # Act
            await UserService.authenticate_user(mock_db_session, email, password)

            # Assert
            mock_get.assert_called_once_with(mock_db_session, email)

    @pytest.mark.asyncio
    async def test_authenticate_user_verifies_password(self, mock_db_session, sample_user):
        """Test that password verification is called with correct arguments."""
        # Arrange
        email = "test@example.com"
        password = "password123"

        with patch.object(UserRepository, 'get_user_by_email', return_value=sample_user), \
             patch('app.services.user_service._verify_password', return_value=True) as mock_verify:

            # Act
            await UserService.authenticate_user(mock_db_session, email, password)

            # Assert
            mock_verify.assert_called_once_with(password, sample_user.password_hash)

    @pytest.mark.asyncio
    async def test_authenticate_user_token_contains_user_id(self, mock_db_session, sample_user):
        """Test that generated token contains user ID in payload."""
        # Arrange
        from jose import jwt
        from app.config import settings

        email = "test@example.com"
        password = "password123"

        with patch.object(UserRepository, 'get_user_by_email', return_value=sample_user), \
             patch('app.services.user_service._verify_password', return_value=True):

            # Act
            response = await UserService.authenticate_user(mock_db_session, email, password)

            # Decode token to verify contents
            decoded = jwt.decode(
                response.access_token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )

            # Assert
            assert decoded["sub"] == str(sample_user.id)
            assert decoded["email"] == sample_user.email
