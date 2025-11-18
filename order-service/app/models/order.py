"""Pydantic models for Order Service"""
from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field, validator


# Request models
class CreateOrderRequest(BaseModel):
    """Request model for creating a new order"""
    car_id: UUID = Field(..., description="UUID of the car to be serviced")
    desired_time: datetime = Field(..., description="Desired appointment time")
    description: str = Field(..., min_length=1, max_length=500, description="Order description")

    class Config:
        json_schema_extra = {
            "example": {
                "car_id": "123e4567-e89b-12d3-a456-426614174000",
                "desired_time": "2025-11-20T10:00:00",
                "description": "Engine oil change and filter replacement"
            }
        }


class UpdateStatusRequest(BaseModel):
    """Request model for updating order status"""
    status: Literal["in_progress", "work_completed", "car_issued"] = Field(
        ...,
        description="New status for the order"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "in_progress"
            }
        }


class ReviewRequest(BaseModel):
    """Request model for adding a review to an order"""
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: str = Field(..., min_length=1, max_length=1000, description="Review comment")

    @validator('rating')
    def validate_rating(cls, v):
        if not 1 <= v <= 5:
            raise ValueError('Rating must be between 1 and 5')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "rating": 5,
                "comment": "Excellent service, very professional staff"
            }
        }


# Response models
class OrderResponse(BaseModel):
    """Response model for order information"""
    order_id: UUID = Field(..., description="Unique order identifier")
    car_id: UUID = Field(..., description="UUID of the car")
    status: str = Field(..., description="Current order status")
    appointment_time: datetime = Field(..., description="Scheduled appointment time")
    description: str = Field(..., description="Order description")
    created_at: datetime = Field(..., description="Order creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "550e8400-e29b-41d4-a716-446655440000",
                "car_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "created",
                "appointment_time": "2025-11-20T10:00:00",
                "description": "Engine oil change and filter replacement",
                "created_at": "2025-11-15T14:30:00"
            }
        }


class ReviewResponse(BaseModel):
    """Response model for review information"""
    review_id: UUID = Field(..., description="Unique review identifier")
    order_id: UUID = Field(..., description="Associated order UUID")
    status: str = Field(..., description="Review status")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: str = Field(..., description="Review comment")
    created_at: datetime = Field(..., description="Review creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "review_id": "660e8400-e29b-41d4-a716-446655440001",
                "order_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "published",
                "rating": 5,
                "comment": "Excellent service, very professional staff",
                "created_at": "2025-11-20T15:00:00"
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response model"""
    message: str = Field(..., description="Error message")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Car not found"
            }
        }


# Internal data models
class Order:
    """Internal order data model for in-memory storage"""

    def __init__(
        self,
        order_id: UUID,
        car_id: UUID,
        status: str,
        appointment_time: datetime,
        description: str,
        created_at: datetime
    ):
        self.order_id = order_id
        self.car_id = car_id
        self.status = status
        self.appointment_time = appointment_time
        self.description = description
        self.created_at = created_at

    def to_response(self) -> OrderResponse:
        """Convert to response model"""
        return OrderResponse(
            order_id=self.order_id,
            car_id=self.car_id,
            status=self.status,
            appointment_time=self.appointment_time,
            description=self.description,
            created_at=self.created_at
        )


class Review:
    """Internal review data model for in-memory storage"""

    def __init__(
        self,
        review_id: UUID,
        order_id: UUID,
        status: str,
        rating: int,
        comment: str,
        created_at: datetime
    ):
        self.review_id = review_id
        self.order_id = order_id
        self.status = status
        self.rating = rating
        self.comment = comment
        self.created_at = created_at

    def to_response(self) -> ReviewResponse:
        """Convert to response model"""
        return ReviewResponse(
            review_id=self.review_id,
            order_id=self.order_id,
            status=self.status,
            rating=self.rating,
            comment=self.comment,
            created_at=self.created_at
        )
