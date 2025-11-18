"""Business logic for order management"""
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status

from app.models.order import (
    CreateOrderRequest,
    OrderResponse,
    ReviewRequest,
    ReviewResponse,
    Order,
    Review
)
from app.repositories.local_order_repo import order_repository
from app.services.car_client import car_client

logger = logging.getLogger(__name__)


class OrderService:
    """Service layer for order operations"""

    # Valid status transitions
    STATUS_TRANSITIONS = {
        "created": ["in_progress"],
        "in_progress": ["work_completed"],
        "work_completed": ["car_issued"],
        "car_issued": []  # Terminal state
    }

    def __init__(self):
        self.repository = order_repository
        self.car_client = car_client

    async def create_order(self, request: CreateOrderRequest) -> OrderResponse:
        """
        Create a new order after verifying car exists

        Args:
            request: Order creation request

        Returns:
            Created order response

        Raises:
            HTTPException: 404 if car not found, 503 if car-service unavailable
        """
        # Verify car exists in car-service
        car_exists = await self.car_client.verify_car_exists(str(request.car_id))

        if not car_exists:
            logger.warning(f"Attempted to create order for non-existent car: {request.car_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Car not found"
            )

        # Create order in repository
        order = await self.repository.create_order(
            car_id=request.car_id,
            appointment_time=request.desired_time,
            description=request.description
        )

        logger.info(f"Created order {order.order_id} for car {request.car_id}")
        return order.to_response()

    async def update_order_status(self, order_id: UUID, new_status: str) -> OrderResponse:
        """
        Update order status with validation

        Args:
            order_id: UUID of the order to update
            new_status: New status to set

        Returns:
            Updated order response

        Raises:
            HTTPException: 404 if order not found, 400 if invalid status transition
        """
        # Get existing order
        order = await self.repository.get_order_by_id(order_id)

        if not order:
            logger.warning(f"Attempted to update non-existent order: {order_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        # Validate status transition
        current_status = order.status
        valid_transitions = self.STATUS_TRANSITIONS.get(current_status, [])

        if new_status not in valid_transitions:
            logger.warning(
                f"Invalid status transition for order {order_id}: "
                f"{current_status} -> {new_status}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from '{current_status}' to '{new_status}'. "
                       f"Valid transitions: {valid_transitions}"
            )

        # Update status
        updated_order = await self.repository.update_order_status(order_id, new_status)

        logger.info(f"Updated order {order_id} status: {current_status} -> {new_status}")
        return updated_order.to_response()

    async def add_review(self, order_id: UUID, request: ReviewRequest) -> ReviewResponse:
        """
        Add a review to an order

        Args:
            order_id: UUID of the order to review
            request: Review details

        Returns:
            Created review response

        Raises:
            HTTPException: 404 if order not found, 409 if review already exists
        """
        # Verify order exists
        order = await self.repository.get_order_by_id(order_id)

        if not order:
            logger.warning(f"Attempted to review non-existent order: {order_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        # Check if review already exists
        has_review = await self.repository.has_review(order_id)

        if has_review:
            logger.warning(f"Attempted to create duplicate review for order: {order_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Review for this order already exists"
            )

        # Create review
        review = await self.repository.create_review(
            order_id=order_id,
            rating=request.rating,
            comment=request.comment
        )

        logger.info(f"Created review {review.review_id} for order {order_id}")
        return review.to_response()


# Singleton instance
order_service = OrderService()
