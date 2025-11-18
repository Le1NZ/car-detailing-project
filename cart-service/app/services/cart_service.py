"""
Business logic for Cart Service
"""
from typing import Dict, List
from uuid import UUID
from fastapi import HTTPException, status

from app.models.cart import CartItem, CartResponse, AddItemRequest
from app.repositories.local_cart_repo import LocalCartRepo


# Catalog of available products and services
CATALOG = {
    "svc_oil_change": {
        "type": "service",
        "name": "Замена масла",
        "price": 2500.00
    },
    "prod_oil_filter": {
        "type": "product",
        "name": "Масляный фильтр",
        "price": 1000.00
    },
    "svc_diagnostics": {
        "type": "service",
        "name": "Диагностика",
        "price": 1500.00
    }
}


class CartService:
    """
    Service layer for cart operations
    """

    def __init__(self, repository: LocalCartRepo):
        self.repo = repository

    def get_cart(self, user_id: UUID) -> CartResponse:
        """
        Retrieve user's cart with calculated total price

        Args:
            user_id: User identifier

        Returns:
            CartResponse with items and total price
        """
        items = self.repo.get_cart(user_id)
        total_price = self._calculate_total_price(items)

        return CartResponse(
            user_id=user_id,
            items=items,
            total_price=total_price
        )

    def add_item(self, user_id: UUID, request: AddItemRequest) -> CartResponse:
        """
        Add an item to user's cart from catalog

        Args:
            user_id: User identifier
            request: Add item request with item_id, type, and quantity

        Returns:
            Updated CartResponse

        Raises:
            HTTPException: If item_id not found in catalog
        """
        # Validate item exists in catalog
        if request.item_id not in CATALOG:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item '{request.item_id}' not found in catalog"
            )

        catalog_item = CATALOG[request.item_id]

        # Validate type matches
        if catalog_item["type"] != request.type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item type mismatch: expected '{catalog_item['type']}', got '{request.type}'"
            )

        # Create cart item from catalog data
        cart_item = CartItem(
            item_id=request.item_id,
            type=catalog_item["type"],
            name=catalog_item["name"],
            quantity=request.quantity,
            price=catalog_item["price"]
        )

        # Add to repository
        updated_items = self.repo.add_item(user_id, cart_item)
        total_price = self._calculate_total_price(updated_items)

        return CartResponse(
            user_id=user_id,
            items=updated_items,
            total_price=total_price
        )

    def remove_item(self, user_id: UUID, item_id: str) -> None:
        """
        Remove an item from user's cart

        Args:
            user_id: User identifier
            item_id: Item identifier to remove

        Raises:
            HTTPException: If item not found in user's cart
        """
        success = self.repo.remove_item(user_id, item_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item '{item_id}' not found in cart"
            )

    @staticmethod
    def _calculate_total_price(items: List[CartItem]) -> float:
        """
        Calculate total price of all items in cart

        Args:
            items: List of cart items

        Returns:
            Total price rounded to 2 decimal places
        """
        total = sum(item.price * item.quantity for item in items)
        return round(total, 2)

    def get_catalog(self) -> Dict:
        """
        Get available catalog items

        Returns:
            Catalog dictionary
        """
        return CATALOG
