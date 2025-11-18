"""Pydantic models for car-service API."""

from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from app.config import settings


class AddCarRequest(BaseModel):
    """Request model for adding a new car."""

    owner_id: UUID = Field(..., description="UUID of the car owner")
    license_plate: str = Field(..., min_length=1, max_length=20, description="Vehicle license plate number")
    vin: str = Field(..., min_length=17, max_length=17, description="Vehicle Identification Number (17 characters)")
    make: str = Field(..., min_length=1, max_length=50, description="Car manufacturer")
    model: str = Field(..., min_length=1, max_length=50, description="Car model")
    year: int = Field(..., ge=settings.min_car_year, le=settings.max_car_year, description="Manufacturing year")

    @field_validator('vin')
    @classmethod
    def validate_vin(cls, v: str) -> str:
        """Validate VIN format."""
        if not v.isalnum():
            raise ValueError("VIN must contain only alphanumeric characters")
        return v.upper()

    @field_validator('license_plate')
    @classmethod
    def validate_license_plate(cls, v: str) -> str:
        """Normalize license plate."""
        return v.strip().upper()


class CarResponse(BaseModel):
    """Response model for car information."""

    car_id: UUID = Field(..., description="Unique car identifier")
    license_plate: str = Field(..., description="Vehicle license plate number")
    vin: str = Field(..., description="Vehicle Identification Number")
    make: str = Field(..., description="Car manufacturer")
    model: str = Field(..., description="Car model")
    year: int = Field(..., description="Manufacturing year")


class AddDocumentRequest(BaseModel):
    """Request model for adding a document to a car."""

    document_type: str = Field(..., min_length=1, max_length=100, description="Type of document (e.g., 'registration', 'insurance')")
    file: Optional[str] = Field(None, description="Optional file content or reference")


class DocumentResponse(BaseModel):
    """Response model for document information."""

    car_id: UUID = Field(..., description="UUID of the car this document belongs to")
    document_id: UUID = Field(..., description="Unique document identifier")
    document_type: str = Field(..., description="Type of document")
    status: str = Field(..., description="Document status (e.g., 'pending', 'approved')")
