"""
Cart API endpoints
"""
from fastapi import APIRouter, Depends, status, Response
from uuid import UUID

from app.models.cart import CartResponse, AddItemRequest
from app.services.cart_service import CartService
from app.repositories.local_cart_repo import LocalCartRepo
from app.auth import get_current_user_id


# Create router
router = APIRouter(prefix="/api/cart", tags=["cart"])

# Initialize repository and service (singleton pattern)
cart_repo = LocalCartRepo()
cart_service = CartService(cart_repo)


def get_cart_service() -> CartService:
    """
    Dependency injection for cart service
    """
    return cart_service


@router.get(
    "",
    response_model=CartResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user's shopping cart",
    description="Retrieve the current user's shopping cart with all items and total price"
)
def get_cart(
    user_id: UUID = Depends(get_current_user_id),
    service: CartService = Depends(get_cart_service)
) -> CartResponse:
    """
    Get user's cart

    Returns:
        CartResponse with items and calculated total price
    """
    return service.get_cart(user_id)


@router.post(
    "/items",
    response_model=CartResponse,
    status_code=status.HTTP_200_OK,
    summary="Add item to cart",
    description="Add a product or service from the catalog to the shopping cart"
)
def add_item(
    request: AddItemRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: CartService = Depends(get_cart_service)
) -> CartResponse:
    """
    Add an item to cart

    Args:
        request: AddItemRequest with item_id, type, and quantity

    Returns:
        Updated CartResponse

    Raises:
        HTTPException 404: If item_id not found in catalog
        HTTPException 400: If item type mismatch
    """
    return service.add_item(user_id, request)


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove item from cart",
    description="Remove a specific item from the shopping cart"
)
def remove_item(
    item_id: str,
    user_id: UUID = Depends(get_current_user_id),
    service: CartService = Depends(get_cart_service)
) -> Response:
    """
    Remove an item from cart

    Args:
        item_id: Identifier of the item to remove

    Returns:
        204 No Content on success

    Raises:
        HTTPException 404: If item not found in user's cart
    """
    service.remove_item(user_id, item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
