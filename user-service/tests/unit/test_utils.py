"""
Unit tests for utility functions (password hashing, JWT tokens).

Tests the internal helper functions used by the UserService:
- Password hashing with bcrypt
- Password verification
- JWT token creation and validation
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from jose import jwt, JWTError

from app.services.user_service import _hash_password, _verify_password, _create_access_token
from app.config import settings


class TestPasswordHashing:
    """Test password hashing and verification functions."""

    def test_hash_password_returns_different_hash_each_time(self):
        """Test that hashing the same password twice produces different hashes."""
        # Arrange
        password = "testpassword123"

        # Act
        hash1 = _hash_password(password)
        hash2 = _hash_password(password)

        # Assert
        assert hash1 != hash2
        assert hash1 is not None
        assert hash2 is not None

    def test_hash_password_returns_string(self):
        """Test that password hashing returns a string."""
        # Arrange
        password = "testpassword123"

        # Act
        hashed = _hash_password(password)

        # Assert
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_with_special_characters(self):
        """Test password hashing with special characters."""
        # Arrange
        password = "p@$$w0rd!#%^&*()"

        # Act
        hashed = _hash_password(password)

        # Assert
        assert isinstance(hashed, str)
        assert hashed is not None

    def test_verify_password_correct_password(self):
        """Test password verification with correct password."""
        # Arrange
        password = "correctpassword"
        hashed = _hash_password(password)

        # Act
        result = _verify_password(password, hashed)

        # Assert
        assert result is True

    def test_verify_password_incorrect_password(self):
        """Test password verification with incorrect password."""
        # Arrange
        correct_password = "correctpassword"
        wrong_password = "wrongpassword"
        hashed = _hash_password(correct_password)

        # Act
        result = _verify_password(wrong_password, hashed)

        # Assert
        assert result is False

    def test_verify_password_empty_password(self):
        """Test password verification with empty password."""
        # Arrange
        password = "correctpassword"
        hashed = _hash_password(password)

        # Act
        result = _verify_password("", hashed)

        # Assert
        assert result is False

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive."""
        # Arrange
        password = "Password123"
        hashed = _hash_password(password)

        # Act
        result_lowercase = _verify_password("password123", hashed)
        result_uppercase = _verify_password("PASSWORD123", hashed)

        # Assert
        assert result_lowercase is False
        assert result_uppercase is False


class TestJWTTokenCreation:
    """Test JWT token creation and validation."""

    def test_create_access_token_returns_string(self):
        """Test that token creation returns a string."""
        # Arrange
        data = {"sub": "user123"}
        expires_delta = timedelta(hours=1)

        # Act
        token = _create_access_token(data, expires_delta)

        # Assert
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_encodes_user_data(self):
        """Test that user data is correctly encoded in the token."""
        # Arrange
        user_id = "c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d"
        email = "test@example.com"
        data = {"sub": user_id, "email": email}
        expires_delta = timedelta(hours=1)

        # Act
        token = _create_access_token(data, expires_delta)
        decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        # Assert
        assert decoded["sub"] == user_id
        assert decoded["email"] == email
        assert "exp" in decoded

    def test_create_access_token_sets_expiration(self):
        """Test that token expiration is correctly set."""
        # Arrange
        data = {"sub": "user123"}
        expires_delta = timedelta(hours=1)

        # Act - create token with real datetime (no mocking)
        before_time = datetime.utcnow()
        token = _create_access_token(data, expires_delta)
        after_time = datetime.utcnow()

        # Decode without verifying expiration
        decoded = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": False}
        )

        # Assert - verify the expiration is approximately correct
        # The token should expire expires_delta seconds from now
        # Note: JWT timestamps are in seconds (not microseconds), so we lose precision
        expected_exp_min = (before_time + expires_delta).replace(microsecond=0)
        expected_exp_max = (after_time + expires_delta).replace(microsecond=0)
        actual_exp = datetime.utcfromtimestamp(decoded["exp"])

        # Verify the expiration is within the expected range (with 2 second tolerance for processing time)
        assert expected_exp_min <= actual_exp <= expected_exp_max + timedelta(seconds=2)

    def test_create_access_token_with_short_expiration(self):
        """Test token creation with short expiration time."""
        # Arrange
        data = {"sub": "user123"}
        expires_delta = timedelta(seconds=30)

        # Act
        token = _create_access_token(data, expires_delta)
        decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        # Assert
        assert "exp" in decoded
        assert isinstance(token, str)

    def test_create_access_token_with_empty_data(self):
        """Test token creation with minimal data."""
        # Arrange
        data = {}
        expires_delta = timedelta(hours=1)

        # Act
        token = _create_access_token(data, expires_delta)
        decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        # Assert
        assert "exp" in decoded
        assert isinstance(token, str)

    def test_create_access_token_with_additional_claims(self):
        """Test token creation with additional custom claims."""
        # Arrange
        data = {
            "sub": "user123",
            "email": "test@example.com",
            "role": "admin",
            "permissions": ["read", "write"]
        }
        expires_delta = timedelta(hours=1)

        # Act
        token = _create_access_token(data, expires_delta)
        decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        # Assert
        assert decoded["sub"] == "user123"
        assert decoded["email"] == "test@example.com"
        assert decoded["role"] == "admin"
        assert decoded["permissions"] == ["read", "write"]

    def test_token_can_be_decoded_with_correct_key(self):
        """Test that token can be decoded with the correct secret key."""
        # Arrange
        data = {"sub": "user123"}
        expires_delta = timedelta(hours=1)
        token = _create_access_token(data, expires_delta)

        # Act
        decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        # Assert
        assert decoded["sub"] == "user123"

    def test_token_cannot_be_decoded_with_wrong_key(self):
        """Test that token cannot be decoded with incorrect secret key."""
        # Arrange
        data = {"sub": "user123"}
        expires_delta = timedelta(hours=1)
        token = _create_access_token(data, expires_delta)

        # Act & Assert
        with pytest.raises(JWTError):
            jwt.decode(token, "wrong-secret-key", algorithms=[settings.JWT_ALGORITHM])

    def test_token_cannot_be_decoded_with_wrong_algorithm(self):
        """Test that token cannot be decoded with incorrect algorithm."""
        # Arrange
        data = {"sub": "user123"}
        expires_delta = timedelta(hours=1)
        token = _create_access_token(data, expires_delta)

        # Act & Assert
        with pytest.raises(JWTError):
            jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS512"])
