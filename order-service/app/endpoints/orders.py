"""API endpoints for order management"""
import logging
from uuid import UUID

from fastapi import APIRouter, status, Query, Depends
from fastapi.responses import JSONResponse

from app.models.order import (
    CreateOrderRequest,
    OrderResponse,
    UpdateStatusRequest,
    ReviewRequest,
    ReviewResponse,
    ErrorResponse
)
from app.services.order_service import order_service
from app.auth import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Order created successfully"},
        401: {"description": "Unauthorized - invalid or missing token"},
        404: {"model": ErrorResponse, "description": "Car not found"},
        503: {"model": ErrorResponse, "description": "Car service unavailable"}
    },
    summary="Create a new order",
    description="Creates a new service order after verifying the car exists in car-service"
)
async def create_order(
    request: CreateOrderRequest,
    user_id: UUID = Depends(get_current_user_id)
) -> OrderResponse:
    """
    Create a new order for car service

    - **car_id**: UUID of the car to be serviced (must exist in car-service)
    - **desired_time**: Desired appointment time for the service
    - **description**: Description of the work to be done
    """
    return await order_service.create_order(request)


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Order status updated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid status transition"},
        401: {"description": "Unauthorized - invalid or missing token"},
        404: {"model": ErrorResponse, "description": "Order not found"}
    },
    summary="Update order status",
    description="Updates the status of an existing order with validation of status transitions"
)
async def update_order_status(
    order_id: UUID,
    request: UpdateStatusRequest,
    user_id: UUID = Depends(get_current_user_id)
) -> OrderResponse:
    """
    Update the status of an order

    Valid status transitions:
    - created → in_progress
    - in_progress → work_completed
    - work_completed → car_issued

    - **order_id**: UUID of the order to update
    - **status**: New status (in_progress, work_completed, or car_issued)
    """
    return await order_service.update_order_status(order_id, request.status)


@router.post(
    "/review",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Review created successfully"},
        401: {"description": "Unauthorized - invalid or missing token"},
        404: {"model": ErrorResponse, "description": "Order not found"},
        409: {"model": ErrorResponse, "description": "Review already exists"}
    },
    summary="Add a review to an order",
    description="Adds a review to a completed order"
)
async def add_review(
    order_id: UUID = Query(..., description="UUID of the order to review"),
    request: ReviewRequest = None,
    user_id: UUID = Depends(get_current_user_id)
) -> ReviewResponse:
    """
    Add a review to an order

    - **order_id**: UUID of the order (query parameter)
    - **rating**: Rating from 1 to 5
    - **comment**: Review comment text
    """
    return await order_service.add_review(order_id, request)
