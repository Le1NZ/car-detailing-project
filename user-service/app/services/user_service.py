"""
User service layer containing business logic.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from jose import jwt
from fastapi import HTTPException, status

from app.config import settings
from app.repositories.db_user_repo import UserRepository
from app.models.user import RegisterRequest, RegisterResponse, LoginResponse
from app.schemas.user import User

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def _create_access_token(data: Dict[str, Any], expires_delta: timedelta) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


class UserService:
    """Service for user-related business logic."""

    @staticmethod
    async def register_user(
        db: AsyncSession,
        user_data: RegisterRequest
    ) -> RegisterResponse:
        """
        Register a new user with validation and password hashing.

        Args:
            db: Async database session
            user_data: User registration data

        Returns:
            RegisterResponse with user information

        Raises:
            HTTPException: 409 if email or phone already exists
            HTTPException: 422 if validation fails
        """
        logger.info(f"Attempting to register user with email: {user_data.email}")

        # Check if email already exists
        if await UserRepository.check_email_exists(db, user_data.email):
            logger.warning(f"Registration failed: Email already exists - {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )

        # Check if phone number already exists
        if await UserRepository.check_phone_exists(db, user_data.phone_number):
            logger.warning(f"Registration failed: Phone already exists - {user_data.phone_number}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone number already registered"
            )

        # Hash the password
        password_hash = _hash_password(user_data.password)

        # Create user in database
        try:
            user = await UserRepository.create_user(
                session=db,
                email=user_data.email,
                password_hash=password_hash,
                full_name=user_data.full_name,
                phone_number=user_data.phone_number,
            )
            logger.info(f"User registered successfully: {user.id}")
        except IntegrityError as e:
            logger.error(f"IntegrityError during registration: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email or phone number already registered"
            )

        # Return response
        return RegisterResponse(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at
        )

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        email: str,
        password: str
    ) -> LoginResponse:
        """
        Authenticate a user and generate JWT token.

        Args:
            db: Async database session
            email: User email
            password: User password

        Returns:
            LoginResponse with access token

        Raises:
            HTTPException: 401 if authentication fails
            HTTPException: 422 if email or password is missing
        """
        logger.info(f"Authentication attempt for email: {email}")

        # Validate input
        if not email or not password:
            logger.warning("Authentication failed: Missing email or password")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Email and password are required"
            )

        # Get user from database
        user = await UserRepository.get_user_by_email(db, email)

        # Check if user exists and password is correct
        if not user or not _verify_password(password, user.password_hash):
            logger.warning(f"Authentication failed for email: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Create access token
        access_token_expires = timedelta(seconds=settings.JWT_ACCESS_TOKEN_EXPIRE_SECONDS)
        access_token = _create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires
        )

        logger.info(f"User authenticated successfully: {user.id}")

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_SECONDS
        )
