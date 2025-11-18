"""Unit tests for LocalOrderRepository"""
import pytest
from datetime import datetime
from uuid import UUID

from app.repositories.local_order_repo import LocalOrderRepository
from app.models.order import Order, Review


class TestLocalOrderRepositoryOrderOperations:
    """Tests for order-related repository operations"""

    @pytest.mark.asyncio
    async def test_create_order(self, fresh_repository, test_car_id, test_datetime):
        """Test creating a new order"""
        order = await fresh_repository.create_order(
            car_id=test_car_id,
            appointment_time=test_datetime,
            description="Oil change"
        )

        assert isinstance(order, Order)
        assert isinstance(order.order_id, UUID)
        assert order.car_id == test_car_id
        assert order.status == "created"
        assert order.appointment_time == test_datetime
        assert order.description == "Oil change"
        assert isinstance(order.created_at, datetime)

    @pytest.mark.asyncio
    async def test_create_order_generates_unique_id(self, fresh_repository, test_car_id, test_datetime):
        """Test that each created order gets a unique ID"""
        order1 = await fresh_repository.create_order(
            car_id=test_car_id,
            appointment_time=test_datetime,
            description="Oil change"
        )

        order2 = await fresh_repository.create_order(
            car_id=test_car_id,
            appointment_time=test_datetime,
            description="Brake repair"
        )

        assert order1.order_id != order2.order_id

    @pytest.mark.asyncio
    async def test_create_order_initial_status(self, fresh_repository, test_car_id, test_datetime):
        """Test that newly created orders have 'created' status"""
        order = await fresh_repository.create_order(
            car_id=test_car_id,
            appointment_time=test_datetime,
            description="Oil change"
        )

        assert order.status == "created"

    @pytest.mark.asyncio
    async def test_get_order_by_id_existing(self, fresh_repository, test_car_id, test_datetime):
        """Test retrieving an existing order by ID"""
        created_order = await fresh_repository.create_order(
            car_id=test_car_id,
            appointment_time=test_datetime,
            description="Oil change"
        )

        retrieved_order = await fresh_repository.get_order_by_id(created_order.order_id)

        assert retrieved_order is not None
        assert retrieved_order.order_id == created_order.order_id
        assert retrieved_order.car_id == created_order.car_id
        assert retrieved_order.status == created_order.status

    @pytest.mark.asyncio
    async def test_get_order_by_id_nonexistent(self, fresh_repository, test_order_id):
        """Test retrieving a non-existent order returns None"""
        order = await fresh_repository.get_order_by_id(test_order_id)
        assert order is None

    @pytest.mark.asyncio
    async def test_update_order_status_existing(self, fresh_repository, test_car_id, test_datetime):
        """Test updating status of an existing order"""
        order = await fresh_repository.create_order(
            car_id=test_car_id,
            appointment_time=test_datetime,
            description="Oil change"
        )

        updated_order = await fresh_repository.update_order_status(
            order.order_id,
            "in_progress"
        )

        assert updated_order is not None
        assert updated_order.status == "in_progress"
        assert updated_order.order_id == order.order_id

    @pytest.mark.asyncio
    async def test_update_order_status_nonexistent(self, fresh_repository, test_order_id):
        """Test updating status of non-existent order returns None"""
        result = await fresh_repository.update_order_status(
            test_order_id,
            "in_progress"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_update_order_status_persistence(self, fresh_repository, test_car_id, test_datetime):
        """Test that status updates persist in repository"""
        order = await fresh_repository.create_order(
            car_id=test_car_id,
            appointment_time=test_datetime,
            description="Oil change"
        )

        await fresh_repository.update_order_status(order.order_id, "in_progress")
        retrieved_order = await fresh_repository.get_order_by_id(order.order_id)

        assert retrieved_order.status == "in_progress"


class TestLocalOrderRepositoryReviewOperations:
    """Tests for review-related repository operations"""

    @pytest.mark.asyncio
    async def test_create_review(self, fresh_repository, test_car_id, test_datetime):
        """Test creating a new review"""
        # First create an order
        order = await fresh_repository.create_order(
            car_id=test_car_id,
            appointment_time=test_datetime,
            description="Oil change"
        )

        # Create review
        review = await fresh_repository.create_review(
            order_id=order.order_id,
            rating=5,
            comment="Great service!"
        )

        assert isinstance(review, Review)
        assert isinstance(review.review_id, UUID)
        assert review.order_id == order.order_id
        assert review.status == "published"
        assert review.rating == 5
        assert review.comment == "Great service!"
        assert isinstance(review.created_at, datetime)

    @pytest.mark.asyncio
    async def test_create_review_generates_unique_id(self, fresh_repository, test_car_id, test_datetime):
        """Test that each created review gets a unique ID"""
        # Create two orders
        order1 = await fresh_repository.create_order(
            car_id=test_car_id,
            appointment_time=test_datetime,
            description="Oil change"
        )

        order2 = await fresh_repository.create_order(
            car_id=test_car_id,
            appointment_time=test_datetime,
            description="Brake repair"
        )

        # Create reviews for both orders
        review1 = await fresh_repository.create_review(
            order_id=order1.order_id,
            rating=5,
            comment="Great!"
        )

        review2 = await fresh_repository.create_review(
            order_id=order2.order_id,
            rating=4,
            comment="Good!"
        )

        assert review1.review_id != review2.review_id

    @pytest.mark.asyncio
    async def test_create_review_initial_status(self, fresh_repository, test_car_id, test_datetime):
        """Test that newly created reviews have 'published' status"""
        order = await fresh_repository.create_order(
            car_id=test_car_id,
            appointment_time=test_datetime,
            description="Oil change"
        )

        review = await fresh_repository.create_review(
            order_id=order.order_id,
            rating=5,
            comment="Great!"
        )

        assert review.status == "published"

    @pytest.mark.asyncio
    async def test_has_review_no_review(self, fresh_repository, test_car_id, test_datetime):
        """Test has_review returns False when order has no review"""
        order = await fresh_repository.create_order(
            car_id=test_car_id,
            appointment_time=test_datetime,
            description="Oil change"
        )

        has_review = await fresh_repository.has_review(order.order_id)
        assert has_review is False

    @pytest.mark.asyncio
    async def test_has_review_with_review(self, fresh_repository, test_car_id, test_datetime):
        """Test has_review returns True when order has a review"""
        order = await fresh_repository.create_order(
            car_id=test_car_id,
            appointment_time=test_datetime,
            description="Oil change"
        )

        await fresh_repository.create_review(
            order_id=order.order_id,
            rating=5,
            comment="Great!"
        )

        has_review = await fresh_repository.has_review(order.order_id)
        assert has_review is True

    @pytest.mark.asyncio
    async def test_has_review_nonexistent_order(self, fresh_repository, test_order_id):
        """Test has_review returns False for non-existent order"""
        has_review = await fresh_repository.has_review(test_order_id)
        assert has_review is False

    @pytest.mark.asyncio
    async def test_get_review_by_order_id_existing(self, fresh_repository, test_car_id, test_datetime):
        """Test retrieving review by order ID"""
        order = await fresh_repository.create_order(
            car_id=test_car_id,
            appointment_time=test_datetime,
            description="Oil change"
        )

        created_review = await fresh_repository.create_review(
            order_id=order.order_id,
            rating=5,
            comment="Great!"
        )

        retrieved_review = await fresh_repository.get_review_by_order_id(order.order_id)

        assert retrieved_review is not None
        assert retrieved_review.review_id == created_review.review_id
        assert retrieved_review.order_id == order.order_id
        assert retrieved_review.rating == 5
        assert retrieved_review.comment == "Great!"

    @pytest.mark.asyncio
    async def test_get_review_by_order_id_no_review(self, fresh_repository, test_car_id, test_datetime):
        """Test get_review_by_order_id returns None when no review exists"""
        order = await fresh_repository.create_order(
            car_id=test_car_id,
            appointment_time=test_datetime,
            description="Oil change"
        )

        review = await fresh_repository.get_review_by_order_id(order.order_id)
        assert review is None

    @pytest.mark.asyncio
    async def test_get_review_by_order_id_nonexistent_order(self, fresh_repository, test_order_id):
        """Test get_review_by_order_id returns None for non-existent order"""
        review = await fresh_repository.get_review_by_order_id(test_order_id)
        assert review is None


class TestLocalOrderRepositoryDataPersistence:
    """Tests for data persistence across multiple operations"""

    @pytest.mark.asyncio
    async def test_multiple_orders_persistence(self, fresh_repository, test_car_id, test_datetime):
        """Test that multiple orders can be stored and retrieved"""
        order1 = await fresh_repository.create_order(
            car_id=test_car_id,
            appointment_time=test_datetime,
            description="Oil change"
        )

        order2 = await fresh_repository.create_order(
            car_id=test_car_id,
            appointment_time=test_datetime,
            description="Brake repair"
        )

        retrieved1 = await fresh_repository.get_order_by_id(order1.order_id)
        retrieved2 = await fresh_repository.get_order_by_id(order2.order_id)

        assert retrieved1.order_id == order1.order_id
        assert retrieved2.order_id == order2.order_id
        assert retrieved1.description == "Oil change"
        assert retrieved2.description == "Brake repair"

    @pytest.mark.asyncio
    async def test_order_review_association(self, fresh_repository, test_car_id, test_datetime):
        """Test that reviews are correctly associated with orders"""
        order = await fresh_repository.create_order(
            car_id=test_car_id,
            appointment_time=test_datetime,
            description="Oil change"
        )

        review = await fresh_repository.create_review(
            order_id=order.order_id,
            rating=5,
            comment="Great!"
        )

        retrieved_review = await fresh_repository.get_review_by_order_id(order.order_id)

        assert retrieved_review.review_id == review.review_id
        assert retrieved_review.order_id == order.order_id
