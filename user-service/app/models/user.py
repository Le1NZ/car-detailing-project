"""
Pydantic models for User API requests and responses.
"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """Request model for user registration."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (minimum 8 characters)")
    full_name: str = Field(..., min_length=1, description="User full name")
    phone_number: str = Field(..., description="Phone number")

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password requirements."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class RegisterResponse(BaseModel):
    """Response model for successful user registration."""

    user_id: UUID = Field(..., alias="id", description="Unique user identifier")
    email: str = Field(..., description="User email address")
    full_name: str = Field(..., description="User full name")
    created_at: datetime = Field(..., description="Registration timestamp")

    class Config:
        from_attributes = True
        populate_by_name = True
        by_alias = False  # Use field names, not aliases, in serialization


class LoginRequest(BaseModel):
    """Request model for user login."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class LoginResponse(BaseModel):
    """Response model for successful login."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
