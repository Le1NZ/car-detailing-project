"""Integration tests for API endpoints"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime
from uuid import uuid4

from app.main import app
from app.repositories.local_order_repo import LocalOrderRepository


# Mock user_id for tests
TEST_USER_ID = uuid4()


def mock_get_current_user_id():
    """Mock function that returns a test user ID without checking JWT"""
    return TEST_USER_ID


@pytest.fixture
def test_client():
    """Fixture providing FastAPI TestClient with mocked auth"""
    # Override the auth dependency
    from app.auth import get_current_user_id
    from app.endpoints import orders
    
    app.dependency_overrides[get_current_user_id] = mock_get_current_user_id
    
    client = TestClient(app)
    yield client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def clean_repository():
    """Fixture providing a clean repository for each test"""
    repo = LocalOrderRepository()
    yield repo
    # Clean up after test
    repo._orders.clear()
    repo._reviews.clear()
    repo._order_reviews.clear()


class TestHealthEndpoint:
    """Tests for health check endpoint"""

    def test_health_endpoint(self, test_client):
        """Test GET /health returns healthy status"""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Order Service"
        assert "version" in data

    def test_root_endpoint(self, test_client):
        """Test GET / returns service info"""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Order Service"
        assert data["status"] == "running"
        assert "version" in data


class TestCreateOrderEndpoint:
    """Tests for POST /api/orders endpoint"""

    @patch('app.services.car_client.car_client.verify_car_exists')
    def test_create_order_success(
        self,
        mock_verify_car,
        test_client,
        clean_repository,
        sample_order_data
    ):
        """Test successful order creation"""
        # Mock car verification
        mock_verify_car.return_value = True

        # Patch repository
        with patch('app.services.order_service.order_repository', clean_repository):
            # Make request
            response = test_client.post(
                "/api/orders",
                json={
                    "car_id": str(sample_order_data["car_id"]),
                    "desired_time": sample_order_data["desired_time"].isoformat(),
                    "description": sample_order_data["description"]
                }
            )

        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert "order_id" in data
        assert data["car_id"] == str(sample_order_data["car_id"])
        assert data["status"] == "created"
        assert data["description"] == sample_order_data["description"]
        assert "created_at" in data
        assert "appointment_time" in data

    @patch('app.services.car_client.car_client.verify_car_exists')
    def test_create_order_car_not_found(
        self,
        mock_verify_car,
        test_client,
        sample_order_data
    ):
        """Test order creation fails when car not found"""
        # Mock car verification to return False
        mock_verify_car.return_value = False

        # Make request
        response = test_client.post(
            "/api/orders",
            json={
                "car_id": str(sample_order_data["car_id"]),
                "desired_time": sample_order_data["desired_time"].isoformat(),
                "description": sample_order_data["description"]
            }
        )

        # Verify response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Car not found" in data["detail"]

    def test_create_order_invalid_uuid(self, test_client, test_datetime):
        """Test order creation with invalid car_id UUID"""
        response = test_client.post(
            "/api/orders",
            json={
                "car_id": "not-a-uuid",
                "desired_time": test_datetime.isoformat(),
                "description": "Oil change"
            }
        )

        assert response.status_code == 422  # Unprocessable Entity

    def test_create_order_missing_fields(self, test_client):
        """Test order creation with missing required fields"""
        response = test_client.post(
            "/api/orders",
            json={}
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_create_order_empty_description(
        self,
        test_client,
        test_car_id,
        test_datetime
    ):
        """Test order creation with empty description"""
        response = test_client.post(
            "/api/orders",
            json={
                "car_id": str(test_car_id),
                "desired_time": test_datetime.isoformat(),
                "description": ""
            }
        )

        assert response.status_code == 422

    def test_create_order_description_too_long(
        self,
        test_client,
        test_car_id,
        test_datetime
    ):
        """Test order creation with description exceeding max length"""
        response = test_client.post(
            "/api/orders",
            json={
                "car_id": str(test_car_id),
                "desired_time": test_datetime.isoformat(),
                "description": "x" * 501  # Max is 500
            }
        )

        assert response.status_code == 422


class TestUpdateOrderStatusEndpoint:
    """Tests for PATCH /api/orders/{order_id}/status endpoint"""

    @patch('app.services.car_client.car_client.verify_car_exists')
    def test_update_status_success(
        self,
        mock_verify_car,
        test_client,
        clean_repository,
        sample_order_data
    ):
        """Test successful status update"""
        # Mock car verification
        mock_verify_car.return_value = True

        # Patch repository
        with patch('app.services.order_service.order_repository', clean_repository):
            # Create an order first
            create_response = test_client.post(
                "/api/orders",
                json={
                    "car_id": str(sample_order_data["car_id"]),
                    "desired_time": sample_order_data["desired_time"].isoformat(),
                    "description": sample_order_data["description"]
                }
            )
            order_id = create_response.json()["order_id"]

            # Update status
            update_response = test_client.patch(
                f"/api/orders/{order_id}/status",
                json={"status": "in_progress"}
            )

        # Verify response
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["order_id"] == order_id
        assert data["status"] == "in_progress"

    @patch('app.services.car_client.car_client.verify_car_exists')
    def test_update_status_invalid_transition(
        self,
        mock_verify_car,
        test_client,
        clean_repository,
        sample_order_data
    ):
        """Test status update with invalid transition"""
        # Mock car verification
        mock_verify_car.return_value = True

        # Patch repository
        with patch('app.services.order_service.order_repository', clean_repository):
            # Create an order first
            create_response = test_client.post(
                "/api/orders",
                json={
                    "car_id": str(sample_order_data["car_id"]),
                    "desired_time": sample_order_data["desired_time"].isoformat(),
                    "description": sample_order_data["description"]
                }
            )
            order_id = create_response.json()["order_id"]

            # Try invalid transition (created -> work_completed, skipping in_progress)
            update_response = test_client.patch(
                f"/api/orders/{order_id}/status",
                json={"status": "work_completed"}
            )

        # Verify response
        assert update_response.status_code == 400
        data = update_response.json()
        assert "Invalid status transition" in data["detail"]

    def test_update_status_order_not_found(self, test_client, test_order_id):
        """Test status update for non-existent order"""
        response = test_client.patch(
            f"/api/orders/{test_order_id}/status",
            json={"status": "in_progress"}
        )

        assert response.status_code == 404
        data = response.json()
        assert "Order not found" in data["detail"]

    @patch('app.services.car_client.car_client.verify_car_exists')
    def test_update_status_full_workflow(
        self,
        mock_verify_car,
        test_client,
        clean_repository,
        sample_order_data
    ):
        """Test complete status workflow from created to car_issued"""
        # Mock car verification
        mock_verify_car.return_value = True

        # Patch repository
        with patch('app.services.order_service.order_repository', clean_repository):
            # Create an order
            create_response = test_client.post(
                "/api/orders",
                json={
                    "car_id": str(sample_order_data["car_id"]),
                    "desired_time": sample_order_data["desired_time"].isoformat(),
                    "description": sample_order_data["description"]
                }
            )
            order_id = create_response.json()["order_id"]

            # Transition: created -> in_progress
            response1 = test_client.patch(
                f"/api/orders/{order_id}/status",
                json={"status": "in_progress"}
            )
            assert response1.status_code == 200
            assert response1.json()["status"] == "in_progress"

            # Transition: in_progress -> work_completed
            response2 = test_client.patch(
                f"/api/orders/{order_id}/status",
                json={"status": "work_completed"}
            )
            assert response2.status_code == 200
            assert response2.json()["status"] == "work_completed"

            # Transition: work_completed -> car_issued
            response3 = test_client.patch(
                f"/api/orders/{order_id}/status",
                json={"status": "car_issued"}
            )
            assert response3.status_code == 200
            assert response3.json()["status"] == "car_issued"

    def test_update_status_invalid_status_value(self, test_client, test_order_id):
        """Test status update with invalid status value"""
        response = test_client.patch(
            f"/api/orders/{test_order_id}/status",
            json={"status": "invalid_status"}
        )

        assert response.status_code == 422


class TestAddReviewEndpoint:
    """Tests for POST /api/orders/review endpoint"""

    @patch('app.services.car_client.car_client.verify_car_exists')
    def test_add_review_success(
        self,
        mock_verify_car,
        test_client,
        clean_repository,
        sample_order_data,
        sample_review_data
    ):
        """Test successfully adding a review"""
        # Mock car verification
        mock_verify_car.return_value = True

        # Patch repository
        with patch('app.services.order_service.order_repository', clean_repository):
            # Create an order first
            create_response = test_client.post(
                "/api/orders",
                json={
                    "car_id": str(sample_order_data["car_id"]),
                    "desired_time": sample_order_data["desired_time"].isoformat(),
                    "description": sample_order_data["description"]
                }
            )
            order_id = create_response.json()["order_id"]

            # Add review
            review_response = test_client.post(
                f"/api/orders/review?order_id={order_id}",
                json=sample_review_data
            )

        # Verify response
        assert review_response.status_code == 201
        data = review_response.json()
        assert "review_id" in data
        assert data["order_id"] == order_id
        assert data["status"] == "published"
        assert data["rating"] == sample_review_data["rating"]
        assert data["comment"] == sample_review_data["comment"]
        assert "created_at" in data

    def test_add_review_order_not_found(
        self,
        test_client,
        test_order_id,
        sample_review_data
    ):
        """Test adding review to non-existent order"""
        response = test_client.post(
            f"/api/orders/review?order_id={test_order_id}",
            json=sample_review_data
        )

        assert response.status_code == 404
        data = response.json()
        assert "Order not found" in data["detail"]

    @patch('app.services.car_client.car_client.verify_car_exists')
    def test_add_review_duplicate(
        self,
        mock_verify_car,
        test_client,
        clean_repository,
        sample_order_data,
        sample_review_data
    ):
        """Test adding duplicate review to an order"""
        # Mock car verification
        mock_verify_car.return_value = True

        # Patch repository
        with patch('app.services.order_service.order_repository', clean_repository):
            # Create an order first
            create_response = test_client.post(
                "/api/orders",
                json={
                    "car_id": str(sample_order_data["car_id"]),
                    "desired_time": sample_order_data["desired_time"].isoformat(),
                    "description": sample_order_data["description"]
                }
            )
            order_id = create_response.json()["order_id"]

            # Add first review
            test_client.post(
                f"/api/orders/review?order_id={order_id}",
                json=sample_review_data
            )

            # Try to add duplicate review
            duplicate_response = test_client.post(
                f"/api/orders/review?order_id={order_id}",
                json=sample_review_data
            )

        # Verify response
        assert duplicate_response.status_code == 409
        data = duplicate_response.json()
        assert "Review for this order already exists" in data["detail"]

    @patch('app.services.car_client.car_client.verify_car_exists')
    def test_add_review_invalid_rating_below_minimum(
        self,
        mock_verify_car,
        test_client,
        clean_repository,
        sample_order_data
    ):
        """Test adding review with rating below minimum (0)"""
        # Mock car verification
        mock_verify_car.return_value = True

        # Patch repository
        with patch('app.services.order_service.order_repository', clean_repository):
            # Create an order first
            create_response = test_client.post(
                "/api/orders",
                json={
                    "car_id": str(sample_order_data["car_id"]),
                    "desired_time": sample_order_data["desired_time"].isoformat(),
                    "description": sample_order_data["description"]
                }
            )
            order_id = create_response.json()["order_id"]

            # Try to add review with invalid rating
            response = test_client.post(
                f"/api/orders/review?order_id={order_id}",
                json={"rating": 0, "comment": "Bad"}
            )

        assert response.status_code == 422

    @patch('app.services.car_client.car_client.verify_car_exists')
    def test_add_review_invalid_rating_above_maximum(
        self,
        mock_verify_car,
        test_client,
        clean_repository,
        sample_order_data
    ):
        """Test adding review with rating above maximum (6)"""
        # Mock car verification
        mock_verify_car.return_value = True

        # Patch repository
        with patch('app.services.order_service.order_repository', clean_repository):
            # Create an order first
            create_response = test_client.post(
                "/api/orders",
                json={
                    "car_id": str(sample_order_data["car_id"]),
                    "desired_time": sample_order_data["desired_time"].isoformat(),
                    "description": sample_order_data["description"]
                }
            )
            order_id = create_response.json()["order_id"]

            # Try to add review with invalid rating
            response = test_client.post(
                f"/api/orders/review?order_id={order_id}",
                json={"rating": 6, "comment": "Too high"}
            )

        assert response.status_code == 422

    @patch('app.services.car_client.car_client.verify_car_exists')
    def test_add_review_empty_comment(
        self,
        mock_verify_car,
        test_client,
        clean_repository,
        sample_order_data
    ):
        """Test adding review with empty comment"""
        # Mock car verification
        mock_verify_car.return_value = True

        # Patch repository
        with patch('app.services.order_service.order_repository', clean_repository):
            # Create an order first
            create_response = test_client.post(
                "/api/orders",
                json={
                    "car_id": str(sample_order_data["car_id"]),
                    "desired_time": sample_order_data["desired_time"].isoformat(),
                    "description": sample_order_data["description"]
                }
            )
            order_id = create_response.json()["order_id"]

            # Try to add review with empty comment
            response = test_client.post(
                f"/api/orders/review?order_id={order_id}",
                json={"rating": 5, "comment": ""}
            )

        assert response.status_code == 422

    @patch('app.services.car_client.car_client.verify_car_exists')
    def test_add_review_missing_fields(
        self,
        mock_verify_car,
        test_client,
        clean_repository,
        sample_order_data
    ):
        """Test adding review with missing required fields"""
        # Mock car verification
        mock_verify_car.return_value = True

        # Patch repository
        with patch('app.services.order_service.order_repository', clean_repository):
            # Create an order first
            create_response = test_client.post(
                "/api/orders",
                json={
                    "car_id": str(sample_order_data["car_id"]),
                    "desired_time": sample_order_data["desired_time"].isoformat(),
                    "description": sample_order_data["description"]
                }
            )
            order_id = create_response.json()["order_id"]

            # Try to add review with missing fields
            response = test_client.post(
                f"/api/orders/review?order_id={order_id}",
                json={}
            )

        assert response.status_code == 422


class TestEndToEndWorkflow:
    """End-to-end integration tests for complete workflows"""

    @patch('app.services.car_client.car_client.verify_car_exists')
    def test_complete_order_workflow(
        self,
        mock_verify_car,
        test_client,
        clean_repository,
        sample_order_data,
        sample_review_data
    ):
        """Test complete order workflow from creation to review"""
        # Mock car verification
        mock_verify_car.return_value = True

        # Patch repository
        with patch('app.services.order_service.order_repository', clean_repository):
            # Step 1: Create order
            create_response = test_client.post(
                "/api/orders",
                json={
                    "car_id": str(sample_order_data["car_id"]),
                    "desired_time": sample_order_data["desired_time"].isoformat(),
                    "description": sample_order_data["description"]
                }
            )
            assert create_response.status_code == 201
            order_id = create_response.json()["order_id"]
            assert create_response.json()["status"] == "created"

            # Step 2: Update to in_progress
            response1 = test_client.patch(
                f"/api/orders/{order_id}/status",
                json={"status": "in_progress"}
            )
            assert response1.status_code == 200
            assert response1.json()["status"] == "in_progress"

            # Step 3: Update to work_completed
            response2 = test_client.patch(
                f"/api/orders/{order_id}/status",
                json={"status": "work_completed"}
            )
            assert response2.status_code == 200
            assert response2.json()["status"] == "work_completed"

            # Step 4: Add review
            review_response = test_client.post(
                f"/api/orders/review?order_id={order_id}",
                json=sample_review_data
            )
            assert review_response.status_code == 201
            assert review_response.json()["order_id"] == order_id

            # Step 5: Update to car_issued
            response3 = test_client.patch(
                f"/api/orders/{order_id}/status",
                json={"status": "car_issued"}
            )
            assert response3.status_code == 200
            assert response3.json()["status"] == "car_issued"
