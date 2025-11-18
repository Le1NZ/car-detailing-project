"""
User endpoints for registration and authentication.
"""

import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse
)
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    response_model_by_alias=False,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email, password, full name, and phone number",
    responses={
        201: {"description": "User successfully registered"},
        409: {"description": "Email or phone number already registered"},
        422: {"description": "Validation error (e.g., password too short)"}
    }
)
async def register(
    user_data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
) -> RegisterResponse:
    """
    Register a new user.

    Args:
        user_data: User registration information
        db: Async database session

    Returns:
        Created user information

    Raises:
        HTTPException: 409 if email or phone already exists
        HTTPException: 422 if validation fails
    """
    logger.info(f"POST /api/users/register - Registering user: {user_data.email}")
    return await UserService.register_user(db, user_data)


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticate user with email and password, returns JWT access token",
    responses={
        200: {"description": "Successfully authenticated"},
        401: {"description": "Incorrect email or password"},
        422: {"description": "Validation error (missing email or password)"}
    }
)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    """
    Authenticate user and return access token.

    Args:
        credentials: User login credentials
        db: Async database session

    Returns:
        JWT access token and expiration information

    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 422 if email or password is missing
    """
    logger.info(f"POST /api/users/login - Login attempt for: {credentials.email}")
    return await UserService.authenticate_user(db, credentials.email, credentials.password)
