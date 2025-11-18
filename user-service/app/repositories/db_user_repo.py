"""
Database repository for User operations.
"""

import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.schemas.user import User

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for User database operations."""

    @staticmethod
    async def create_user(
        session: AsyncSession,
        email: str,
        password_hash: str,
        full_name: str,
        phone_number: str,
    ) -> User:
        """
        Create a new user in the database.

        Args:
            session: Async SQLAlchemy database session
            email: User email address
            password_hash: Hashed password
            full_name: User full name
            phone_number: User phone number

        Returns:
            Created User object

        Raises:
            IntegrityError: If email or phone_number already exists
        """
        user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            phone_number=phone_number,
        )

        session.add(user)

        try:
            await session.commit()
            await session.refresh(user)
            logger.info(f"User created successfully: {user.id}")
            return user
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"IntegrityError creating user: {e}")
            raise

    @staticmethod
    async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
        """
        Retrieve a user by email address.

        Args:
            session: Async SQLAlchemy database session
            email: User email address

        Returns:
            User object if found, None otherwise
        """
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def check_email_exists(session: AsyncSession, email: str) -> bool:
        """
        Check if an email address is already registered.

        Args:
            session: Async SQLAlchemy database session
            email: Email address to check

        Returns:
            True if email exists, False otherwise
        """
        user = await UserRepository.get_user_by_email(session, email)
        return user is not None

    @staticmethod
    async def check_phone_exists(session: AsyncSession, phone_number: str) -> bool:
        """
        Check if a phone number is already registered.

        Args:
            session: Async SQLAlchemy database session
            phone_number: Phone number to check

        Returns:
            True if phone number exists, False otherwise
        """
        stmt = select(User).where(User.phone_number == phone_number)
        result = await session.execute(stmt)
        return result.scalars().first() is not None
