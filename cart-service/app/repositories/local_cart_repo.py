"""
Local in-memory repository for cart data
"""
from typing import Dict, List, Optional
from uuid import UUID
from app.models.cart import CartItem


class LocalCartRepo:
    """
    In-memory storage for shopping carts
    Key: user_id (UUID)
    Value: List of CartItem objects
    """

    def __init__(self):
        self._storage: Dict[UUID, List[CartItem]] = {}

    def get_cart(self, user_id: UUID) -> List[CartItem]:
        """
        Retrieve cart items for a specific user

        Args:
            user_id: User identifier

        Returns:
            List of cart items (empty list if cart doesn't exist)
        """
        return self._storage.get(user_id, [])

    def add_item(self, user_id: UUID, item: CartItem) -> List[CartItem]:
        """
        Add an item to user's cart
        If item already exists, increases quantity

        Args:
            user_id: User identifier
            item: Cart item to add

        Returns:
            Updated list of cart items
        """
        if user_id not in self._storage:
            self._storage[user_id] = []

        cart = self._storage[user_id]

        # Check if item already exists in cart
        existing_item = next(
            (i for i in cart if i.item_id == item.item_id),
            None
        )

        if existing_item:
            # Update quantity of existing item
            existing_item.quantity += item.quantity
        else:
            # Add new item to cart
            cart.append(item)

        return cart

    def remove_item(self, user_id: UUID, item_id: str) -> bool:
        """
        Remove an item from user's cart

        Args:
            user_id: User identifier
            item_id: Item identifier to remove

        Returns:
            True if item was removed, False if item or cart not found
        """
        if user_id not in self._storage:
            return False

        cart = self._storage[user_id]
        initial_length = len(cart)

        # Filter out the item with matching item_id
        self._storage[user_id] = [item for item in cart if item.item_id != item_id]

        # Return True if an item was actually removed
        return len(self._storage[user_id]) < initial_length

    def clear_cart(self, user_id: UUID) -> None:
        """
        Clear all items from user's cart

        Args:
            user_id: User identifier
        """
        if user_id in self._storage:
            self._storage[user_id] = []

    def get_all_carts(self) -> Dict[UUID, List[CartItem]]:
        """
        Retrieve all carts (mainly for debugging/testing)

        Returns:
            Dictionary of all carts
        """
        return self._storage
