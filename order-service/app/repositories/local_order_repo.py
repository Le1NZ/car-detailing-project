"""In-memory repository for orders and reviews"""
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID, uuid4

from app.models.order import Order, Review


class LocalOrderRepository:
    """In-memory storage for orders and reviews"""

    def __init__(self):
        self._orders: Dict[UUID, Order] = {}
        self._reviews: Dict[UUID, Review] = {}
        self._order_reviews: Dict[UUID, UUID] = {}  # order_id -> review_id mapping

    async def create_order(
        self,
        car_id: UUID,
        appointment_time: datetime,
        description: str
    ) -> Order:
        """Create a new order"""
        order_id = uuid4()
        order = Order(
            order_id=order_id,
            car_id=car_id,
            status="created",
            appointment_time=appointment_time,
            description=description,
            created_at=datetime.now()
        )
        self._orders[order_id] = order
        return order

    async def get_order_by_id(self, order_id: UUID) -> Optional[Order]:
        """Get order by ID"""
        return self._orders.get(order_id)

    async def update_order_status(self, order_id: UUID, new_status: str) -> Optional[Order]:
        """Update order status"""
        order = self._orders.get(order_id)
        if order:
            order.status = new_status
        return order

    async def create_review(
        self,
        order_id: UUID,
        rating: int,
        comment: str
    ) -> Review:
        """Create a new review for an order"""
        review_id = uuid4()
        review = Review(
            review_id=review_id,
            order_id=order_id,
            status="published",
            rating=rating,
            comment=comment,
            created_at=datetime.now()
        )
        self._reviews[review_id] = review
        self._order_reviews[order_id] = review_id
        return review

    async def has_review(self, order_id: UUID) -> bool:
        """Check if order already has a review"""
        return order_id in self._order_reviews

    async def get_review_by_order_id(self, order_id: UUID) -> Optional[Review]:
        """Get review by order ID"""
        review_id = self._order_reviews.get(order_id)
        if review_id:
            return self._reviews.get(review_id)
        return None


# Singleton instance
order_repository = LocalOrderRepository()
