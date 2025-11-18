"""Unit tests for Pydantic models"""
import pytest
from datetime import datetime
from uuid import UUID
from pydantic import ValidationError

from app.models.order import (
    CreateOrderRequest,
    UpdateStatusRequest,
    ReviewRequest,
    OrderResponse,
    ReviewResponse,
    ErrorResponse,
    Order,
    Review
)


class TestCreateOrderRequest:
    """Tests for CreateOrderRequest model"""

    def test_valid_create_order_request(self, test_car_id, test_datetime):
        """Test creating a valid order request"""
        request = CreateOrderRequest(
            car_id=test_car_id,
            desired_time=test_datetime,
            description="Oil change"
        )

        assert request.car_id == test_car_id
        assert request.desired_time == test_datetime
        assert request.description == "Oil change"

    def test_create_order_request_with_string_uuid(self, test_datetime):
        """Test creating order request with UUID as string"""
        request = CreateOrderRequest(
            car_id="123e4567-e89b-12d3-a456-426614174000",
            desired_time=test_datetime,
            description="Oil change"
        )

        assert isinstance(request.car_id, UUID)
        assert str(request.car_id) == "123e4567-e89b-12d3-a456-426614174000"

    def test_create_order_request_invalid_uuid(self, test_datetime):
        """Test creating order request with invalid UUID"""
        with pytest.raises(ValidationError) as exc_info:
            CreateOrderRequest(
                car_id="not-a-uuid",
                desired_time=test_datetime,
                description="Oil change"
            )

        assert "UUID" in str(exc_info.value)

    def test_create_order_request_empty_description(self, test_car_id, test_datetime):
        """Test creating order request with empty description"""
        with pytest.raises(ValidationError) as exc_info:
            CreateOrderRequest(
                car_id=test_car_id,
                desired_time=test_datetime,
                description=""
            )

        errors = exc_info.value.errors()
        assert any("at least 1 character" in str(error) for error in errors)

    def test_create_order_request_description_too_long(self, test_car_id, test_datetime):
        """Test creating order request with description exceeding max length"""
        with pytest.raises(ValidationError) as exc_info:
            CreateOrderRequest(
                car_id=test_car_id,
                desired_time=test_datetime,
                description="x" * 501  # Max is 500
            )

        errors = exc_info.value.errors()
        assert any("at most 500 character" in str(error) for error in errors)

    def test_create_order_request_missing_required_fields(self):
        """Test creating order request with missing required fields"""
        with pytest.raises(ValidationError) as exc_info:
            CreateOrderRequest()

        errors = exc_info.value.errors()
        assert len(errors) == 3  # All three fields are required

    def test_create_order_request_invalid_datetime(self, test_car_id):
        """Test creating order request with invalid datetime"""
        with pytest.raises(ValidationError):
            CreateOrderRequest(
                car_id=test_car_id,
                desired_time="not-a-datetime",
                description="Oil change"
            )


class TestUpdateStatusRequest:
    """Tests for UpdateStatusRequest model"""

    def test_valid_status_in_progress(self):
        """Test creating request with in_progress status"""
        request = UpdateStatusRequest(status="in_progress")
        assert request.status == "in_progress"

    def test_valid_status_work_completed(self):
        """Test creating request with work_completed status"""
        request = UpdateStatusRequest(status="work_completed")
        assert request.status == "work_completed"

    def test_valid_status_car_issued(self):
        """Test creating request with car_issued status"""
        request = UpdateStatusRequest(status="car_issued")
        assert request.status == "car_issued"

    def test_invalid_status(self):
        """Test creating request with invalid status"""
        with pytest.raises(ValidationError) as exc_info:
            UpdateStatusRequest(status="invalid_status")

        errors = exc_info.value.errors()
        assert any("literal" in str(error).lower() for error in errors)

    def test_status_created_not_allowed(self):
        """Test that 'created' status is not allowed in update request"""
        with pytest.raises(ValidationError):
            UpdateStatusRequest(status="created")


class TestReviewRequest:
    """Tests for ReviewRequest model"""

    def test_valid_review_request(self):
        """Test creating a valid review request"""
        request = ReviewRequest(rating=5, comment="Great service!")
        assert request.rating == 5
        assert request.comment == "Great service!"

    def test_review_request_rating_minimum(self):
        """Test review request with minimum rating"""
        request = ReviewRequest(rating=1, comment="Poor service")
        assert request.rating == 1

    def test_review_request_rating_maximum(self):
        """Test review request with maximum rating"""
        request = ReviewRequest(rating=5, comment="Excellent!")
        assert request.rating == 5

    def test_review_request_rating_below_minimum(self):
        """Test review request with rating below minimum"""
        with pytest.raises(ValidationError) as exc_info:
            ReviewRequest(rating=0, comment="Bad")

        errors = exc_info.value.errors()
        assert any("greater than or equal to 1" in str(error) for error in errors)

    def test_review_request_rating_above_maximum(self):
        """Test review request with rating above maximum"""
        with pytest.raises(ValidationError) as exc_info:
            ReviewRequest(rating=6, comment="Too high")

        errors = exc_info.value.errors()
        assert any("less than or equal to 5" in str(error) for error in errors)

    def test_review_request_empty_comment(self):
        """Test review request with empty comment"""
        with pytest.raises(ValidationError) as exc_info:
            ReviewRequest(rating=5, comment="")

        errors = exc_info.value.errors()
        assert any("at least 1 character" in str(error) for error in errors)

    def test_review_request_comment_too_long(self):
        """Test review request with comment exceeding max length"""
        with pytest.raises(ValidationError) as exc_info:
            ReviewRequest(rating=5, comment="x" * 1001)  # Max is 1000

        errors = exc_info.value.errors()
        assert any("at most 1000 character" in str(error) for error in errors)


class TestOrderResponse:
    """Tests for OrderResponse model"""

    def test_valid_order_response(self, test_order_id, test_car_id, test_datetime):
        """Test creating a valid order response"""
        created_at = datetime(2025, 11, 15, 14, 30, 0)
        response = OrderResponse(
            order_id=test_order_id,
            car_id=test_car_id,
            status="created",
            appointment_time=test_datetime,
            description="Oil change",
            created_at=created_at
        )

        assert response.order_id == test_order_id
        assert response.car_id == test_car_id
        assert response.status == "created"
        assert response.appointment_time == test_datetime
        assert response.description == "Oil change"
        assert response.created_at == created_at

    def test_order_response_with_string_uuids(self, test_datetime):
        """Test order response with UUIDs as strings"""
        created_at = datetime(2025, 11, 15, 14, 30, 0)
        response = OrderResponse(
            order_id="550e8400-e29b-41d4-a716-446655440000",
            car_id="123e4567-e89b-12d3-a456-426614174000",
            status="created",
            appointment_time=test_datetime,
            description="Oil change",
            created_at=created_at
        )

        assert isinstance(response.order_id, UUID)
        assert isinstance(response.car_id, UUID)


class TestReviewResponse:
    """Tests for ReviewResponse model"""

    def test_valid_review_response(self, test_review_id, test_order_id):
        """Test creating a valid review response"""
        created_at = datetime(2025, 11, 20, 15, 0, 0)
        response = ReviewResponse(
            review_id=test_review_id,
            order_id=test_order_id,
            status="published",
            rating=5,
            comment="Great service!",
            created_at=created_at
        )

        assert response.review_id == test_review_id
        assert response.order_id == test_order_id
        assert response.status == "published"
        assert response.rating == 5
        assert response.comment == "Great service!"
        assert response.created_at == created_at


class TestErrorResponse:
    """Tests for ErrorResponse model"""

    def test_valid_error_response(self):
        """Test creating a valid error response"""
        response = ErrorResponse(message="Car not found")
        assert response.message == "Car not found"

    def test_error_response_empty_message(self):
        """Test creating error response with empty message"""
        response = ErrorResponse(message="")
        assert response.message == ""


class TestOrderClass:
    """Tests for Order internal data class"""

    def test_order_initialization(self, test_order_id, test_car_id, test_datetime):
        """Test Order class initialization"""
        created_at = datetime(2025, 11, 15, 14, 30, 0)
        order = Order(
            order_id=test_order_id,
            car_id=test_car_id,
            status="created",
            appointment_time=test_datetime,
            description="Oil change",
            created_at=created_at
        )

        assert order.order_id == test_order_id
        assert order.car_id == test_car_id
        assert order.status == "created"
        assert order.appointment_time == test_datetime
        assert order.description == "Oil change"
        assert order.created_at == created_at

    def test_order_to_response(self, sample_order):
        """Test converting Order to OrderResponse"""
        response = sample_order.to_response()

        assert isinstance(response, OrderResponse)
        assert response.order_id == sample_order.order_id
        assert response.car_id == sample_order.car_id
        assert response.status == sample_order.status
        assert response.appointment_time == sample_order.appointment_time
        assert response.description == sample_order.description
        assert response.created_at == sample_order.created_at


class TestReviewClass:
    """Tests for Review internal data class"""

    def test_review_initialization(self, test_review_id, test_order_id):
        """Test Review class initialization"""
        created_at = datetime(2025, 11, 20, 15, 0, 0)
        review = Review(
            review_id=test_review_id,
            order_id=test_order_id,
            status="published",
            rating=5,
            comment="Great service!",
            created_at=created_at
        )

        assert review.review_id == test_review_id
        assert review.order_id == test_order_id
        assert review.status == "published"
        assert review.rating == 5
        assert review.comment == "Great service!"
        assert review.created_at == created_at

    def test_review_to_response(self, sample_review):
        """Test converting Review to ReviewResponse"""
        response = sample_review.to_response()

        assert isinstance(response, ReviewResponse)
        assert response.review_id == sample_review.review_id
        assert response.order_id == sample_review.order_id
        assert response.status == sample_review.status
        assert response.rating == sample_review.rating
        assert response.comment == sample_review.comment
        assert response.created_at == sample_review.created_at
