"""
Pydantic models for Cart Service
"""
from typing import List
from uuid import UUID
from pydantic import BaseModel, Field


class CartItem(BaseModel):
    """
    Represents a single item in the shopping cart
    """
    item_id: str = Field(..., description="Unique identifier of the item (product or service)")
    type: str = Field(..., description="Type of item: 'product' or 'service'")
    name: str = Field(..., description="Display name of the item")
    quantity: int = Field(..., gt=0, description="Quantity of the item")
    price: float = Field(..., gt=0, description="Price per unit")

    class Config:
        json_schema_extra = {
            "example": {
                "item_id": "svc_oil_change",
                "type": "service",
                "name": "Замена масла",
                "quantity": 1,
                "price": 2500.00
            }
        }


class CartResponse(BaseModel):
    """
    Response model for cart operations
    """
    user_id: UUID = Field(..., description="User identifier")
    items: List[CartItem] = Field(default_factory=list, description="List of items in cart")
    total_price: float = Field(..., ge=0, description="Total price of all items")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "12345678-1234-5678-1234-567812345678",
                "items": [
                    {
                        "item_id": "svc_oil_change",
                        "type": "service",
                        "name": "Замена масла",
                        "quantity": 1,
                        "price": 2500.00
                    }
                ],
                "total_price": 2500.00
            }
        }


class AddItemRequest(BaseModel):
    """
    Request model for adding item to cart
    """
    item_id: str = Field(..., description="Catalog item identifier")
    type: str = Field(..., description="Type of item: 'product' or 'service'")
    quantity: int = Field(..., gt=0, description="Quantity to add")

    class Config:
        json_schema_extra = {
            "example": {
                "item_id": "svc_oil_change",
                "type": "service",
                "quantity": 1
            }
        }
