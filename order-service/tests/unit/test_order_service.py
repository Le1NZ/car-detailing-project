"""Unit tests for OrderService business logic"""
import pytest
from unittest.mock import AsyncMock
from fastapi import HTTPException

from app.services.order_service import OrderService
from app.models.order import CreateOrderRequest, ReviewRequest


class TestOrderServiceCreateOrder:
    """Tests for create_order method"""

    @pytest.mark.asyncio
    async def test_create_order_success(
        self,
        mock_repository,
        mock_car_client,
        sample_order,
        sample_order_data
    ):
        """Test successful order creation when car exists"""
        # Setup mocks
        mock_car_client.verify_car_exists.return_value = True
        mock_repository.create_order.return_value = sample_order

        # Create service with mocked dependencies
        service = OrderService()
        service.repository = mock_repository
        service.car_client = mock_car_client

        # Create request
        request = CreateOrderRequest(**sample_order_data)

        # Execute
        result = await service.create_order(request)

        # Verify
        mock_car_client.verify_car_exists.assert_called_once_with(str(request.car_id))
        mock_repository.create_order.assert_called_once_with(
            car_id=request.car_id,
            appointment_time=request.desired_time,
            description=request.description
        )
        assert result.order_id == sample_order.order_id
        assert result.car_id == sample_order.car_id
        assert result.status == "created"

    @pytest.mark.asyncio
    async def test_create_order_car_not_found(
        self,
        mock_repository,
        mock_car_client,
        sample_order_data
    ):
        """Test order creation fails when car does not exist"""
        # Setup mocks
        mock_car_client.verify_car_exists.return_value = False

        # Create service with mocked dependencies
        service = OrderService()
        service.repository = mock_repository
        service.car_client = mock_car_client

        # Create request
        request = CreateOrderRequest(**sample_order_data)

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            await service.create_order(request)

        assert exc_info.value.status_code == 404
        assert "Car not found" in exc_info.value.detail

        # Verify car existence was checked but order was not created
        mock_car_client.verify_car_exists.assert_called_once()
        mock_repository.create_order.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_order_car_service_unavailable(
        self,
        mock_repository,
        mock_car_client,
        sample_order_data
    ):
        """Test order creation fails gracefully when car-service is unavailable"""
        # Setup mocks - car_client returns False on error
        mock_car_client.verify_car_exists.return_value = False

        # Create service with mocked dependencies
        service = OrderService()
        service.repository = mock_repository
        service.car_client = mock_car_client

        # Create request
        request = CreateOrderRequest(**sample_order_data)

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            await service.create_order(request)

        assert exc_info.value.status_code == 404
        mock_repository.create_order.assert_not_called()


class TestOrderServiceUpdateOrderStatus:
    """Tests for update_order_status method"""

    @pytest.mark.asyncio
    async def test_update_status_created_to_in_progress(
        self,
        mock_repository,
        sample_order,
        test_order_id
    ):
        """Test valid status transition: created -> in_progress"""
        # Setup mocks
        sample_order.status = "created"
        mock_repository.get_order_by_id.return_value = sample_order

        # Create a separate instance for the updated order to avoid mutation
        from app.models.order import Order
        updated_order = Order(
            order_id=sample_order.order_id,
            car_id=sample_order.car_id,
            status="in_progress",
            appointment_time=sample_order.appointment_time,
            description=sample_order.description,
            created_at=sample_order.created_at
        )
        mock_repository.update_order_status.return_value = updated_order

        # Create service
        service = OrderService()
        service.repository = mock_repository

        # Execute
        result = await service.update_order_status(test_order_id, "in_progress")

        # Verify
        mock_repository.get_order_by_id.assert_called_once_with(test_order_id)
        mock_repository.update_order_status.assert_called_once_with(
            test_order_id,
            "in_progress"
        )
        assert result.status == "in_progress"

    @pytest.mark.asyncio
    async def test_update_status_in_progress_to_work_completed(
        self,
        mock_repository,
        sample_order,
        test_order_id
    ):
        """Test valid status transition: in_progress -> work_completed"""
        # Setup mocks
        sample_order.status = "in_progress"
        mock_repository.get_order_by_id.return_value = sample_order

        # Create a separate instance for the updated order to avoid mutation
        from app.models.order import Order
        updated_order = Order(
            order_id=sample_order.order_id,
            car_id=sample_order.car_id,
            status="work_completed",
            appointment_time=sample_order.appointment_time,
            description=sample_order.description,
            created_at=sample_order.created_at
        )
        mock_repository.update_order_status.return_value = updated_order

        # Create service
        service = OrderService()
        service.repository = mock_repository

        # Execute
        result = await service.update_order_status(test_order_id, "work_completed")

        # Verify
        assert result.status == "work_completed"

    @pytest.mark.asyncio
    async def test_update_status_work_completed_to_car_issued(
        self,
        mock_repository,
        sample_order,
        test_order_id
    ):
        """Test valid status transition: work_completed -> car_issued"""
        # Setup mocks
        sample_order.status = "work_completed"
        mock_repository.get_order_by_id.return_value = sample_order

        # Create a separate instance for the updated order to avoid mutation
        from app.models.order import Order
        updated_order = Order(
            order_id=sample_order.order_id,
            car_id=sample_order.car_id,
            status="car_issued",
            appointment_time=sample_order.appointment_time,
            description=sample_order.description,
            created_at=sample_order.created_at
        )
        mock_repository.update_order_status.return_value = updated_order

        # Create service
        service = OrderService()
        service.repository = mock_repository

        # Execute
        result = await service.update_order_status(test_order_id, "car_issued")

        # Verify
        assert result.status == "car_issued"

    @pytest.mark.asyncio
    async def test_update_status_invalid_transition(
        self,
        mock_repository,
        sample_order,
        test_order_id
    ):
        """Test invalid status transition raises error"""
        # Setup mocks - order is in 'created' status
        sample_order.status = "created"
        mock_repository.get_order_by_id.return_value = sample_order

        # Create service
        service = OrderService()
        service.repository = mock_repository

        # Try to jump directly to work_completed (invalid)
        with pytest.raises(HTTPException) as exc_info:
            await service.update_order_status(test_order_id, "work_completed")

        assert exc_info.value.status_code == 400
        assert "Invalid status transition" in exc_info.value.detail
        mock_repository.update_order_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_status_from_terminal_state(
        self,
        mock_repository,
        sample_order,
        test_order_id
    ):
        """Test that terminal state (car_issued) cannot be updated"""
        # Setup mocks - order is in terminal 'car_issued' status
        sample_order.status = "car_issued"
        mock_repository.get_order_by_id.return_value = sample_order

        # Create service
        service = OrderService()
        service.repository = mock_repository

        # Try to update terminal state
        with pytest.raises(HTTPException) as exc_info:
            await service.update_order_status(test_order_id, "in_progress")

        assert exc_info.value.status_code == 400
        assert "Invalid status transition" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_update_status_order_not_found(
        self,
        mock_repository,
        test_order_id
    ):
        """Test updating status of non-existent order"""
        # Setup mocks
        mock_repository.get_order_by_id.return_value = None

        # Create service
        service = OrderService()
        service.repository = mock_repository

        # Execute and verify
        with pytest.raises(HTTPException) as exc_info:
            await service.update_order_status(test_order_id, "in_progress")

        assert exc_info.value.status_code == 404
        assert "Order not found" in exc_info.value.detail
        mock_repository.update_order_status.assert_not_called()


class TestOrderServiceAddReview:
    """Tests for add_review method"""

    @pytest.mark.asyncio
    async def test_add_review_success(
        self,
        mock_repository,
        sample_order,
        sample_review,
        sample_review_data,
        test_order_id
    ):
        """Test successfully adding a review to an order"""
        # Setup mocks
        mock_repository.get_order_by_id.return_value = sample_order
        mock_repository.has_review.return_value = False
        mock_repository.create_review.return_value = sample_review

        # Create service
        service = OrderService()
        service.repository = mock_repository

        # Create request
        request = ReviewRequest(**sample_review_data)

        # Execute
        result = await service.add_review(test_order_id, request)

        # Verify
        mock_repository.get_order_by_id.assert_called_once_with(test_order_id)
        mock_repository.has_review.assert_called_once_with(test_order_id)
        mock_repository.create_review.assert_called_once_with(
            order_id=test_order_id,
            rating=request.rating,
            comment=request.comment
        )
        assert result.review_id == sample_review.review_id
        assert result.order_id == test_order_id
        assert result.rating == 5
        assert result.status == "published"

    @pytest.mark.asyncio
    async def test_add_review_order_not_found(
        self,
        mock_repository,
        sample_review_data,
        test_order_id
    ):
        """Test adding review to non-existent order"""
        # Setup mocks
        mock_repository.get_order_by_id.return_value = None

        # Create service
        service = OrderService()
        service.repository = mock_repository

        # Create request
        request = ReviewRequest(**sample_review_data)

        # Execute and verify
        with pytest.raises(HTTPException) as exc_info:
            await service.add_review(test_order_id, request)

        assert exc_info.value.status_code == 404
        assert "Order not found" in exc_info.value.detail
        mock_repository.has_review.assert_not_called()
        mock_repository.create_review.assert_not_called()

    @pytest.mark.asyncio
    async def test_add_review_duplicate(
        self,
        mock_repository,
        sample_order,
        sample_review_data,
        test_order_id
    ):
        """Test adding duplicate review to an order"""
        # Setup mocks
        mock_repository.get_order_by_id.return_value = sample_order
        mock_repository.has_review.return_value = True

        # Create service
        service = OrderService()
        service.repository = mock_repository

        # Create request
        request = ReviewRequest(**sample_review_data)

        # Execute and verify
        with pytest.raises(HTTPException) as exc_info:
            await service.add_review(test_order_id, request)

        assert exc_info.value.status_code == 409
        assert "Review for this order already exists" in exc_info.value.detail
        mock_repository.create_review.assert_not_called()

    @pytest.mark.asyncio
    async def test_add_review_with_minimum_rating(
        self,
        mock_repository,
        sample_order,
        sample_review,
        test_order_id
    ):
        """Test adding review with minimum rating (1)"""
        # Setup mocks
        mock_repository.get_order_by_id.return_value = sample_order
        mock_repository.has_review.return_value = False
        mock_repository.create_review.return_value = sample_review

        # Create service
        service = OrderService()
        service.repository = mock_repository

        # Create request with minimum rating
        request = ReviewRequest(rating=1, comment="Poor service")

        # Execute
        result = await service.add_review(test_order_id, request)

        # Verify
        mock_repository.create_review.assert_called_once()
        call_args = mock_repository.create_review.call_args
        assert call_args[1]['rating'] == 1

    @pytest.mark.asyncio
    async def test_add_review_with_maximum_rating(
        self,
        mock_repository,
        sample_order,
        sample_review,
        test_order_id
    ):
        """Test adding review with maximum rating (5)"""
        # Setup mocks
        mock_repository.get_order_by_id.return_value = sample_order
        mock_repository.has_review.return_value = False
        mock_repository.create_review.return_value = sample_review

        # Create service
        service = OrderService()
        service.repository = mock_repository

        # Create request with maximum rating
        request = ReviewRequest(rating=5, comment="Excellent service")

        # Execute
        result = await service.add_review(test_order_id, request)

        # Verify
        mock_repository.create_review.assert_called_once()
        call_args = mock_repository.create_review.call_args
        assert call_args[1]['rating'] == 5


class TestOrderServiceStatusTransitions:
    """Tests for status transition validation logic"""

    def test_status_transitions_dict_structure(self):
        """Test that STATUS_TRANSITIONS dict has correct structure"""
        service = OrderService()

        assert "created" in service.STATUS_TRANSITIONS
        assert "in_progress" in service.STATUS_TRANSITIONS
        assert "work_completed" in service.STATUS_TRANSITIONS
        assert "car_issued" in service.STATUS_TRANSITIONS

    def test_created_status_valid_transitions(self):
        """Test valid transitions from 'created' status"""
        service = OrderService()

        valid_transitions = service.STATUS_TRANSITIONS["created"]

        assert "in_progress" in valid_transitions
        assert len(valid_transitions) == 1

    def test_in_progress_status_valid_transitions(self):
        """Test valid transitions from 'in_progress' status"""
        service = OrderService()

        valid_transitions = service.STATUS_TRANSITIONS["in_progress"]

        assert "work_completed" in valid_transitions
        assert len(valid_transitions) == 1

    def test_work_completed_status_valid_transitions(self):
        """Test valid transitions from 'work_completed' status"""
        service = OrderService()

        valid_transitions = service.STATUS_TRANSITIONS["work_completed"]

        assert "car_issued" in valid_transitions
        assert len(valid_transitions) == 1

    def test_car_issued_terminal_state(self):
        """Test that 'car_issued' is a terminal state"""
        service = OrderService()

        valid_transitions = service.STATUS_TRANSITIONS["car_issued"]

        assert len(valid_transitions) == 0

    def test_no_backwards_transitions(self):
        """Test that there are no backwards transitions allowed"""
        service = OrderService()

        # in_progress should not allow transition back to created
        assert "created" not in service.STATUS_TRANSITIONS["in_progress"]

        # work_completed should not allow transition back to in_progress
        assert "in_progress" not in service.STATUS_TRANSITIONS["work_completed"]

        # car_issued should not allow any transitions
        assert len(service.STATUS_TRANSITIONS["car_issued"]) == 0


class TestOrderServiceInitialization:
    """Tests for OrderService initialization"""

    def test_service_initialization(self):
        """Test OrderService initializes with correct dependencies"""
        service = OrderService()

        assert service.repository is not None
        assert service.car_client is not None
        assert hasattr(service, 'STATUS_TRANSITIONS')

    def test_service_singleton_dependencies(self):
        """Test that service uses singleton instances"""
        from app.repositories.local_order_repo import order_repository
        from app.services.car_client import car_client

        service = OrderService()

        assert service.repository is order_repository
        assert service.car_client is car_client
