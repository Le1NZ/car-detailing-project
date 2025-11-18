"""Pydantic models for bonus service"""
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class ApplyPromocodeRequest(BaseModel):
    """Request model for applying a promocode"""
    order_id: UUID = Field(..., description="Order identifier")
    promocode: str = Field(..., min_length=1, description="Promocode string")


class PromocodeResponse(BaseModel):
    """Response model for promocode application"""
    order_id: UUID = Field(..., description="Order identifier")
    promocode: str = Field(..., description="Applied promocode")
    status: str = Field(..., description="Application status")
    discount_amount: float = Field(..., description="Discount amount in RUB")


class SpendBonusesRequest(BaseModel):
    """Request model for spending bonuses"""
    order_id: UUID = Field(..., description="Order identifier")
    amount: int = Field(..., gt=0, description="Amount of bonuses to spend")

    @field_validator('amount', mode='before')
    @classmethod
    def convert_float_to_int(cls, v):
        """Convert float amounts to int by truncating decimal part"""
        if isinstance(v, float):
            return int(v)
        return v


class SpendBonusesResponse(BaseModel):
    """Response model for spending bonuses"""
    order_id: UUID = Field(..., description="Order identifier")
    bonuses_spent: int = Field(..., description="Amount of bonuses spent")
    new_balance: float = Field(..., description="New bonus balance")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
