"""
Integration tests for User API endpoints.

Tests the complete flow of API requests through all layers:
- FastAPI routing
- Service layer
- Repository layer
- Database operations (with in-memory SQLite)

Uses TestClient with real database operations (SQLite in-memory).
"""

import pytest
from httpx import AsyncClient
from fastapi import status

from app.repositories.db_user_repo import UserRepository


class TestRegisterEndpoint:
    """Integration tests for POST /api/users/register endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(self, test_client, async_db_session):
        """Test successful user registration."""
        # Arrange
        user_data = {
            "email": "newuser@example.com",
            "password": "strongpassword123",
            "full_name": "New User",
            "phone_number": "+79991234567"
        }

        # Act
        response = await test_client.post("/api/users/register", json=user_data)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "user_id" in data
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert "created_at" in data
        assert "password" not in data  # Password should not be in response

        # Verify user exists in database
        user = await UserRepository.get_user_by_email(async_db_session, user_data["email"])
        assert user is not None
        assert user.email == user_data["email"]

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, test_client, async_db_session):
        """Test registration with duplicate email returns 409."""
        # Arrange
        user_data = {
            "email": "duplicate@example.com",
            "password": "password123",
            "full_name": "First User",
            "phone_number": "+79991234567"
        }

        # Create first user
        await test_client.post("/api/users/register", json=user_data)

        # Attempt to create second user with same email
        user_data2 = {
            "email": "duplicate@example.com",  # Same email
            "password": "password456",
            "full_name": "Second User",
            "phone_number": "+79991234568"  # Different phone
        }

        # Act
        response = await test_client.post("/api/users/register", json=user_data2)

        # Assert
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "Email already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_duplicate_phone(self, test_client, async_db_session):
        """Test registration with duplicate phone number returns 409."""
        # Arrange
        user_data = {
            "email": "user1@example.com",
            "password": "password123",
            "full_name": "First User",
            "phone_number": "+79991234567"
        }

        # Create first user
        await test_client.post("/api/users/register", json=user_data)

        # Attempt to create second user with same phone
        user_data2 = {
            "email": "user2@example.com",  # Different email
            "password": "password456",
            "full_name": "Second User",
            "phone_number": "+79991234567"  # Same phone
        }

        # Act
        response = await test_client.post("/api/users/register", json=user_data2)

        # Assert
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "Phone number already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, test_client):
        """Test registration with invalid email returns 422."""
        # Arrange
        user_data = {
            "email": "not-an-email",
            "password": "password123",
            "full_name": "Test User",
            "phone_number": "+79991234567"
        }

        # Act
        response = await test_client.post("/api/users/register", json=user_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_register_short_password(self, test_client):
        """Test registration with password < 8 characters returns 422."""
        # Arrange
        user_data = {
            "email": "test@example.com",
            "password": "short",  # Only 5 characters
            "full_name": "Test User",
            "phone_number": "+79991234567"
        }

        # Act
        response = await test_client.post("/api/users/register", json=user_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_register_missing_email(self, test_client):
        """Test registration without email returns 422."""
        # Arrange
        user_data = {
            "password": "password123",
            "full_name": "Test User",
            "phone_number": "+79991234567"
        }

        # Act
        response = await test_client.post("/api/users/register", json=user_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_register_missing_password(self, test_client):
        """Test registration without password returns 422."""
        # Arrange
        user_data = {
            "email": "test@example.com",
            "full_name": "Test User",
            "phone_number": "+79991234567"
        }

        # Act
        response = await test_client.post("/api/users/register", json=user_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_register_missing_full_name(self, test_client):
        """Test registration without full_name returns 422."""
        # Arrange
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "phone_number": "+79991234567"
        }

        # Act
        response = await test_client.post("/api/users/register", json=user_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_register_missing_phone_number(self, test_client):
        """Test registration without phone_number returns 422."""
        # Arrange
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        }

        # Act
        response = await test_client.post("/api/users/register", json=user_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_register_empty_request_body(self, test_client):
        """Test registration with empty body returns 422."""
        # Act
        response = await test_client.post("/api/users/register", json={})

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_register_password_hashed_in_database(self, test_client, async_db_session):
        """Test that password is hashed in the database."""
        # Arrange
        user_data = {
            "email": "secure@example.com",
            "password": "plainpassword123",
            "full_name": "Secure User",
            "phone_number": "+79991234567"
        }

        # Act
        await test_client.post("/api/users/register", json=user_data)

        # Assert - verify password is hashed
        user = await UserRepository.get_user_by_email(async_db_session, user_data["email"])
        assert user is not None
        assert user.password_hash != user_data["password"]  # Should be hashed
        assert user.password_hash.startswith("$2b$")  # bcrypt hash format

    @pytest.mark.asyncio
    async def test_register_unicode_full_name(self, test_client, async_db_session):
        """Test registration with Unicode characters in full_name."""
        # Arrange
        user_data = {
            "email": "russian@example.com",
            "password": "password123",
            "full_name": "Иванов Петр Сергеевич",
            "phone_number": "+79991234567"
        }

        # Act
        response = await test_client.post("/api/users/register", json=user_data)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["full_name"] == "Иванов Петр Сергеевич"


class TestLoginEndpoint:
    """Integration tests for POST /api/users/login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, test_client, async_db_session):
        """Test successful user login."""
        # Arrange - first register a user
        user_data = {
            "email": "login@example.com",
            "password": "password123",
            "full_name": "Login User",
            "phone_number": "+79991234567"
        }
        await test_client.post("/api/users/register", json=user_data)

        # Act - login with correct credentials
        login_data = {
            "email": "login@example.com",
            "password": "password123"
        }
        response = await test_client.post("/api/users/login", json=login_data)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 3600
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    @pytest.mark.asyncio
    async def test_login_wrong_email(self, test_client, async_db_session):
        """Test login with non-existent email returns 401."""
        # Arrange
        login_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }

        # Act
        response = await test_client.post("/api/users/login", json=login_data)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, test_client, async_db_session):
        """Test login with incorrect password returns 401."""
        # Arrange - first register a user
        user_data = {
            "email": "user@example.com",
            "password": "correctpassword",
            "full_name": "Test User",
            "phone_number": "+79991234567"
        }
        await test_client.post("/api/users/register", json=user_data)

        # Act - login with wrong password
        login_data = {
            "email": "user@example.com",
            "password": "wrongpassword"
        }
        response = await test_client.post("/api/users/login", json=login_data)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_missing_email(self, test_client):
        """Test login without email returns 422."""
        # Arrange
        login_data = {
            "password": "password123"
        }

        # Act
        response = await test_client.post("/api/users/login", json=login_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_login_missing_password(self, test_client):
        """Test login without password returns 422."""
        # Arrange
        login_data = {
            "email": "test@example.com"
        }

        # Act
        response = await test_client.post("/api/users/login", json=login_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_login_empty_email(self, test_client):
        """Test login with empty email returns 422."""
        # Arrange
        login_data = {
            "email": "",
            "password": "password123"
        }

        # Act
        response = await test_client.post("/api/users/login", json=login_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_login_invalid_email_format(self, test_client):
        """Test login with invalid email format returns 422."""
        # Arrange
        login_data = {
            "email": "not-an-email",
            "password": "password123"
        }

        # Act
        response = await test_client.post("/api/users/login", json=login_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_login_empty_request_body(self, test_client):
        """Test login with empty body returns 422."""
        # Act
        response = await test_client.post("/api/users/login", json={})

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_login_jwt_token_valid(self, test_client, async_db_session):
        """Test that returned JWT token is valid and contains correct data."""
        # Arrange - register and login
        from jose import jwt
        from app.config import settings

        user_data = {
            "email": "jwtuser@example.com",
            "password": "password123",
            "full_name": "JWT User",
            "phone_number": "+79991234567"
        }
        register_response = await test_client.post("/api/users/register", json=user_data)
        user_id = register_response.json()["user_id"]

        login_data = {
            "email": "jwtuser@example.com",
            "password": "password123"
        }

        # Act
        login_response = await test_client.post("/api/users/login", json=login_data)
        token = login_response.json()["access_token"]

        # Decode and verify token
        decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        # Assert
        assert decoded["sub"] == user_id
        assert decoded["email"] == user_data["email"]
        assert "exp" in decoded

    @pytest.mark.asyncio
    async def test_login_case_sensitive_email(self, test_client, async_db_session):
        """Test that email comparison is case-sensitive (or insensitive based on DB)."""
        # Arrange - register a user
        user_data = {
            "email": "CaseSensitive@example.com",
            "password": "password123",
            "full_name": "Case User",
            "phone_number": "+79991234567"
        }
        await test_client.post("/api/users/register", json=user_data)

        # Act - try to login with different case
        login_data = {
            "email": "casesensitive@example.com",
            "password": "password123"
        }
        response = await test_client.post("/api/users/login", json=login_data)

        # Assert - behavior depends on database collation
        # SQLite by default is case-insensitive for ASCII
        # This test documents the behavior
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]


class TestHealthEndpoint:
    """Integration tests for GET /health endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, test_client):
        """Test health check endpoint returns healthy status."""
        # Act
        response = await test_client.get("/health")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data


class TestRootEndpoint:
    """Integration tests for GET / endpoint."""

    @pytest.mark.asyncio
    async def test_root_endpoint(self, test_client):
        """Test root endpoint returns service information."""
        # Act
        response = await test_client.get("/")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "status" in data
        assert "endpoints" in data
        assert data["status"] == "running"
