"""
Unit tests for UserRepository.

Tests all database operations in the repository layer with mocked database sessions.
All tests are isolated from actual database connections.
"""

import pytest
from unittest.mock import AsyncMock, Mock
from sqlalchemy.exc import IntegrityError
from uuid import uuid4

from app.repositories.db_user_repo import UserRepository
from app.schemas.user import User


class TestUserRepositoryCreateUser:
    """Test UserRepository.create_user method."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, mock_db_session, sample_user):
        """Test successful user creation."""
        # Arrange
        mock_db_session.refresh.side_effect = lambda user: setattr(user, 'id', sample_user.id)

        # Act
        user = await UserRepository.create_user(
            session=mock_db_session,
            email="test@example.com",
            password_hash="hashed_password",
            full_name="Test User",
            phone_number="+79991234567"
        )

        # Assert
        assert isinstance(user, User)
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"
        assert user.full_name == "Test User"
        assert user.phone_number == "+79991234567"
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_calls_commit(self, mock_db_session):
        """Test that create_user commits the transaction."""
        # Arrange & Act
        await UserRepository.create_user(
            session=mock_db_session,
            email="test@example.com",
            password_hash="hashed_password",
            full_name="Test User",
            phone_number="+79991234567"
        )

        # Assert
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email_raises_integrity_error(self, mock_db_session):
        """Test that duplicate email raises IntegrityError."""
        # Arrange
        mock_db_session.commit.side_effect = IntegrityError(
            "duplicate key value violates unique constraint",
            params={},
            orig=Exception()
        )

        # Act & Assert
        with pytest.raises(IntegrityError):
            await UserRepository.create_user(
                session=mock_db_session,
                email="duplicate@example.com",
                password_hash="hashed_password",
                full_name="Test User",
                phone_number="+79991234567"
            )

        # Verify rollback was called
        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_phone_raises_integrity_error(self, mock_db_session):
        """Test that duplicate phone number raises IntegrityError."""
        # Arrange
        mock_db_session.commit.side_effect = IntegrityError(
            "duplicate key value violates unique constraint",
            params={},
            orig=Exception()
        )

        # Act & Assert
        with pytest.raises(IntegrityError):
            await UserRepository.create_user(
                session=mock_db_session,
                email="test@example.com",
                password_hash="hashed_password",
                full_name="Test User",
                phone_number="+79991234567"
            )

        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_rolls_back_on_error(self, mock_db_session):
        """Test that transaction is rolled back on error."""
        # Arrange
        mock_db_session.commit.side_effect = IntegrityError(
            "database error",
            params={},
            orig=Exception()
        )

        # Act & Assert
        with pytest.raises(IntegrityError):
            await UserRepository.create_user(
                session=mock_db_session,
                email="test@example.com",
                password_hash="hashed_password",
                full_name="Test User",
                phone_number="+79991234567"
            )

        mock_db_session.rollback.assert_called_once()


class TestUserRepositoryGetUserByEmail:
    """Test UserRepository.get_user_by_email method."""

    @pytest.mark.asyncio
    async def test_get_user_by_email_found(self, mock_db_session, sample_user):
        """Test retrieving an existing user by email."""
        # Arrange
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = sample_user
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        # Act
        user = await UserRepository.get_user_by_email(mock_db_session, "test@example.com")

        # Assert
        assert user is not None
        assert user.email == sample_user.email
        assert user.id == sample_user.id
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, mock_db_session):
        """Test retrieving a non-existent user by email."""
        # Arrange
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        # Act
        user = await UserRepository.get_user_by_email(mock_db_session, "nonexistent@example.com")

        # Assert
        assert user is None
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_by_email_case_sensitive(self, mock_db_session, sample_user):
        """Test that email search is case-sensitive (depends on DB collation)."""
        # Arrange
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        # Act
        user = await UserRepository.get_user_by_email(mock_db_session, "TEST@EXAMPLE.COM")

        # Assert - this tests the query behavior, actual case sensitivity depends on DB
        mock_db_session.execute.assert_called_once()


class TestUserRepositoryCheckEmailExists:
    """Test UserRepository.check_email_exists method."""

    @pytest.mark.asyncio
    async def test_check_email_exists_returns_true(self, mock_db_session, sample_user):
        """Test checking if email exists returns True when user found."""
        # Arrange
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = sample_user
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        # Act
        exists = await UserRepository.check_email_exists(mock_db_session, "test@example.com")

        # Assert
        assert exists is True

    @pytest.mark.asyncio
    async def test_check_email_exists_returns_false(self, mock_db_session):
        """Test checking if email exists returns False when user not found."""
        # Arrange
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        # Act
        exists = await UserRepository.check_email_exists(mock_db_session, "nonexistent@example.com")

        # Assert
        assert exists is False


class TestUserRepositoryCheckPhoneExists:
    """Test UserRepository.check_phone_exists method."""

    @pytest.mark.asyncio
    async def test_check_phone_exists_returns_true(self, mock_db_session, sample_user):
        """Test checking if phone exists returns True when user found."""
        # Arrange
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = sample_user
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        # Act
        exists = await UserRepository.check_phone_exists(mock_db_session, "+79991234567")

        # Assert
        assert exists is True
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_phone_exists_returns_false(self, mock_db_session):
        """Test checking if phone exists returns False when user not found."""
        # Arrange
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        # Act
        exists = await UserRepository.check_phone_exists(mock_db_session, "+79991234567")

        # Assert
        assert exists is False
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_phone_exists_with_different_formats(self, mock_db_session):
        """Test checking phone existence with different phone number formats."""
        # Arrange
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.first.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        # Act - test with different phone formats
        exists1 = await UserRepository.check_phone_exists(mock_db_session, "+79991234567")
        exists2 = await UserRepository.check_phone_exists(mock_db_session, "79991234567")

        # Assert
        assert exists1 is False
        assert exists2 is False
        assert mock_db_session.execute.call_count == 2
