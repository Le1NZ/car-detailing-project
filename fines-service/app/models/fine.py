"""
Pydantic models for Fines Service
"""
from datetime import date
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field


class Fine(BaseModel):
    """Internal Fine model"""
    fine_id: UUID
    license_plate: str
    amount: float
    description: str
    date: date
    paid: bool = False


class FineResponse(BaseModel):
    """Fine response model for API"""
    fine_id: UUID
    amount: float
    description: str
    date: date


class PayFineRequest(BaseModel):
    """Request model for paying a fine"""
    payment_method_id: str = Field(..., description="ID of payment method to use")


class PaymentResponse(BaseModel):
    """Response model for payment"""
    payment_id: UUID
    fine_id: UUID
    status: str
